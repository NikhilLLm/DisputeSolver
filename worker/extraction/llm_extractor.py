
"""
LLM Extractor with Content-Aware Router, Vision VLM, OCR, and Schema Normalization.

Architecture:
1. Stage 1 Text Extraction:
   - Images (.jpg, .jpeg, .png, .webp): Uses Vision VLM to transcribe all text/facts.
   - PDF & TXT (.pdf, .txt): Uses OCR/fitz text extraction.
2. Content-Aware Router:
   - Classifies document into precise EvidenceType and Owner using filename and extracted raw text content.
3. Stage 2 Final Text LLM:
   - Normalizes facts into dedicated Pydantic schemas -> EvidenceEnvelope.
   - Atomizes claims and filters out false/generic noun entities.
"""

from __future__ import annotations

import base64
import json
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Type

from dotenv import load_dotenv
from openai import OpenAI, APIError, RateLimitError
from pydantic import BaseModel, ValidationError

from worker.extraction.document_text_extractor import extract_document_text
from worker.extraction.schema import (
    AccountStatement,
    CommunicationLog,
    DeliveryProof,
    DisputeForm,
    EntityType,
    EvidenceEnvelope,
    EvidenceMeta,
    EvidenceType,
    MerchantPolicy,
    OrderStatusReport,
    Owner,
    PoliceReport,
    ProcessorLog,
    PurchaseRecord,
    TrackingReport,
    TransactionComparison,
    UsageLog,
)

load_dotenv()

# Schema mapping for target Pydantic models
SCHEMA_MAP: Dict[str, Type[BaseModel]] = {
    "DISPUTE_FORM": DisputeForm,
    "PURCHASE_RECORD": PurchaseRecord,
    "TRACKING_REPORT": TrackingReport,
    "DELIVERY_PROOF": DeliveryProof,
    "COMMUNICATION_LOG": CommunicationLog,
    "MERCHANT_POLICY": MerchantPolicy,
    "USAGE_LOG": UsageLog,
    "PROCESSOR_LOG": ProcessorLog,
    "POLICE_REPORT": PoliceReport,
    "ACCOUNT_STATEMENT": AccountStatement,
    "ORDER_STATUS_REPORT": OrderStatusReport,
    "TRANSACTION_COMPARISON": TransactionComparison,
}

STOP_NOUNS = {
    "return", "refund", "subscription", "order", "item", "status",
    "delivery", "billing cycle", "product", "dispute", "case", "unknown",
    "policy", "electronics", "clearance item", "merchant policy",
    # CHANGED: added a few more known hallucinated / generic phrases found
    # while auditing real extraction runs (e.g. "Discrepancy Report" was
    # minted as a standalone entity when no such report existed anywhere
    # in the source text).
    "discrepancy report", "quality check", "service fee",
}


def encode_image(image_path: Path) -> str:
    """Base64 encode an image file."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _estimate_confidence(processed_by: str, raw_text: str) -> float:
    """Heuristic extraction confidence based on extraction path and content richness.

    CHANGED: this replaces a hardcoded `confidence: 0.95` that was applied
    to every document regardless of extraction quality. A flat constant
    made the downstream confidence-band gating meaningless -- a document
    that yielded almost no raw text (a failed OCR pass, a garbled image)
    looked identical to a clean, fully-read document. This isn't a
    substitute for real per-token OCR confidence (that would need to be
    threaded through from document_text_extractor.py), but it's a
    materially better signal than a constant.
    """
    text_len = len(raw_text.strip())
    if text_len == 0:
        return 0.15  # extraction produced nothing at all -- treat as a red flag

    base = {
        "structured_form_parser": 0.98,  # JSON forms, no OCR/vision uncertainty
        "ocr_pdf_txt_extractor": 0.85,   # native PDF text layer, fairly reliable
        "groq_vision_vlm": 0.75,         # vision transcription, more error-prone
    }.get(processed_by, 0.7)

    if text_len < 40:
        base -= 0.25  # very sparse content is a red flag regardless of method

    return round(max(0.1, min(base, 0.99)), 2)


def router_classify_document(file_path: Path, raw_text: Optional[str] = None) -> Tuple[EvidenceType, Owner]:
    """Content-Aware Router: Classifies document type and owner based on path, filename, and raw content."""
    name = file_path.name.lower()
    path_str = str(file_path).lower()
    text = (raw_text or "").lower()

    # Determine owner by directory path or explicit cues
    owner = Owner.CARDHOLDER if "cardholder" in path_str else Owner.MERCHANT

    # 1. Police Report / Incident Affidavits
    if "police" in name or "police department" in text or "incident report" in text or "pr-202" in text or "officer" in text:
        return EvidenceType.POLICE_REPORT, owner

    # 2. Bank / Account Statements
    if "bank_statement" in name or "account_statement" in name or "bank statement" in text or "opening balance" in text or "ending balance" in text:
        return EvidenceType.ACCOUNT_STATEMENT, owner

    # 3. Transaction / Order Comparison Sheets
    if "comparison" in name or "session_logs" in name or "session a" in text or "session b" in text or "transaction comparison" in text:
        return EvidenceType.TRANSACTION_COMPARISON, owner

    # 4. Processor / Security / AVS / 3DS / Device Fingerprint / Fraud Scores
    #    CHANGED: added "unauthorized" (name) and "refund"+"confirmation"
    #    (name) -- both previously fell through to the silent PURCHASE_RECORD
    #    default. "unauthorized_statement.pdf" is a fraud-context security
    #    statement; "refund_confirmation.pdf" carries refund_timestamp/
    #    payment_status fields that fit ProcessorLog, not PurchaseRecord,
    #    which has no refund-specific fields at all. The refund+confirmation
    #    combo check is deliberately narrow (needs BOTH words in the
    #    filename) so it never fires on "refund_agreement_email.pdf",
    #    which correctly stays COMMUNICATION_LOG via rule 8.
    if (
        "processor" in name
        or "fingerprint" in name
        or "risk_score" in name
        or "metadata" in name
        or "pos_system" in name
        or "unauthorized" in name
        or ("refund" in name and "confirmation" in name)
        or "3d secure" in text
        or "avs result" in text
        or "cvv result" in text
        or "risk score" in text
        or "auth_success" in text
        or "arn" in text
    ):
        return EvidenceType.PROCESSOR_LOG, owner

    # 5. Internal Order Status / Quality Check / Fulfillment Logs
    if "quality_check" in name or "internal_order_status" in name or "qc-" in text or "untracked" in text or "fulfillment status" in text:
        return EvidenceType.ORDER_STATUS_REPORT, owner

    # 6. Usage Logs / Streaming / Activity Events
    if "usage" in name or "stream started" in text or "login event" in text or "account activity" in text:
        return EvidenceType.USAGE_LOG, owner

    # 7. Policies, Return Policies, Terms of Service, Pricing Schedules
    if "terms" in name or "policy" in name or "pricing_breakdown" in name or "return_policy" in name or "clause" in text or "terms of service" in text:
        return EvidenceType.MERCHANT_POLICY, owner

    # 8. Communication Logs (Email, Chat, Tickets, Merchant listings/advertisements)
    #    CHANGED: added "cancellation" -- "cancellation_confirmation.pdf" is
    #    functionally a confirmation message (same shape as a confirmation
    #    email), and previously fell through to the PURCHASE_RECORD default.
    if (
        "email" in name
        or "chat" in name
        or "comm" in name
        or "advert" in name
        or "screenshot" in name
        or "cancellation" in name
        or "message" in text
        or "from:" in text and "to:" in text
        or "hi " in text and "support" in text
    ):
        return EvidenceType.COMMUNICATION_LOG, owner

    # 9. Delivery Proof (Photos, Signatures, Dropoff slips)
    if "delivery" in name or "received_item" in name or "proof" in name or "doorstep" in text or "gps" in text or "delivered to" in text:
        return EvidenceType.DELIVERY_PROOF, owner

    # 10. Tracking Reports (Carrier Timelines)
    if "tracking" in name or "shipment" in name or "carrier" in text and "delivered" in text or "in transit" in text:
        return EvidenceType.TRACKING_REPORT, owner

    # 11. Dispute Forms
    if "form" in name or file_path.suffix.lower() == ".json":
        return EvidenceType.DISPUTE_FORM, owner

    # 12. Receipts / Invoices / Purchase Records / Internal product listings
    if "receipt" in name or "order_confirmation" in name or "product_listing" in name or "invoice" in name or "purchase" in name or "total amount" in text:
        return EvidenceType.PURCHASE_RECORD, owner

    return EvidenceType.PURCHASE_RECORD, owner


class LLMExtractor:
    """
    Multi-stage LLM Extractor:
    - Vision VLM for image text transcription.
    - OCR/fitz for PDF & TXT files.
    - Content-Aware Router for dynamic schema selection.
    - Final Text LLM for canonical extraction into EvidenceEnvelope.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        vision_model: Optional[str] = None,
        text_model: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set.")

        self.vision_model = vision_model or os.getenv("GROQ_VISION_MODEL", "qwen/qwen3.6-27b")
        self.text_model = text_model or os.getenv("GROQ_TEXT_MODEL", "openai/gpt-oss-120b")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.groq.com/openai/v1",
        )

    def extract_raw_text_from_image(self, file_path: Path) -> str:
        """Stage 1: Transcribe text from image using local OCR with VLM fallback."""
        ocr_text = extract_document_text(file_path)
        if ocr_text and len(ocr_text.strip()) > 10:
            return ocr_text

        # Fallback to Vision VLM if OCR is sparse and model configured
        try:
            b64_img = encode_image(file_path)
            prompt = (
                "You are an OCR and document text transcription expert. "
                "Examine this dispute evidence image carefully. "
                "Transcribe ALL visible text, numbers, dates, addresses, tracking details, and statements word-for-word."
            )
            response = self.client.chat.completions.create(
                model=self.vision_model,
                temperature=0.0,
                messages=[
                    {"role": "system", "content": "You transcribe all text from dispute evidence images."},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{b64_img}"},
                            },
                        ],
                    },
                ],
            )
            return response.choices[0].message.content or ocr_text
        except Exception:
            return ocr_text

    def get_document_raw_content(self, file_path: Path) -> Tuple[str, str]:
        """Stage 1: Extract complete raw text content from the file."""
        suffix = file_path.suffix.lower()

        if suffix in [".jpg", ".jpeg", ".png", ".webp"]:
            content = self.extract_raw_text_from_image(file_path)
            return content, "ocr_image_extractor"
        elif suffix in [".pdf", ".txt"]:
            content = extract_document_text(file_path)
            return content, "ocr_pdf_txt_extractor"
        elif suffix == ".json":
            content = file_path.read_text(encoding="utf-8")
            return content, "structured_form_parser"
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    def extract_canonical_envelope(
        self,
        file_path: Path,
        case_id: Optional[str] = None,
        max_retries: int = 3,
        backoff_seconds: float = 3.0,
    ) -> Dict[str, Any]:
        """
        Stage 2 Final Text LLM:
        Takes extracted whole text, classifies content into precise schema,
        and normalizes facts and assertions into Pydantic EvidenceEnvelope.
        """
        raw_text, processed_by = self.get_document_raw_content(file_path)
        evidence_type, owner = router_classify_document(file_path, raw_text)
        doc_id = f"doc-{file_path.stem[:20]}-{int(time.time())}"

        # Discover case_id from text if not explicitly provided
        if not case_id:
            m = re.search(r"DSP-\d{4}-\d{5}", raw_text, re.IGNORECASE)
            case_id = m.group(0).upper() if m else "DSP-UNKNOWN"

        target_model = SCHEMA_MAP[evidence_type.value]
        schema_json = json.dumps(target_model.model_json_schema(), indent=2)

        prompt = f"""You are an expert financial dispute evidence analyst.
Analyze the following document raw text extracted from {file_path.name} (Processed by: {processed_by}).

DOCUMENT CLASSIFICATION:
- Owner: {owner.value}
- Evidence Type: {evidence_type.value}

DOCUMENT RAW TEXT CONTENT:
\"\"\"
{raw_text}
\"\"\"

TARGET SCHEMA JSON DEFINITION ({evidence_type.value}):
{schema_json}

INSTRUCTIONS:
1. Extract the structured fields according to the schema JSON definition. All dates must be in ISO-8601 format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ).
2. For "assertions":
   - Extract discrete, atomic factual statements made in the document.
   - Do NOT combine multiple facts into a single run-on sentence.
   - For each assertion, provide a "subject_entity" (e.g. Order ID, Tracking Number, Merchant Name, or specific Item SKU/name).
3. For "entities":
   - Allowed entity_type values: 'Order', 'OrderedItem', 'ReceivedItem', 'Item', 'Tracking', 'Merchant', 'Customer', 'Report', 'Session', 'Device', 'Inspector', 'PolicyClause'.
   - For 'Order' entities: 'entity_id' is the Order/Transaction number (e.g. 'ORD-123456'). 'name' must be the Order ID — NEVER put product names or item descriptions in an Order entity's name field.
   - For items: use 'OrderedItem' for items listed on receipts/invoices/merchant listings/QC records; use 'ReceivedItem' for items delivered/received by customer/in photos/complaint descriptions; use 'Item' for general items.
   - DO NOT extract generic common nouns as entities (e.g., do NOT extract "return", "refund", "subscription", "order", "item", "status" as entity_id).
   - DO NOT invent an entity for something not literally present in the source text (e.g. do not create a "Discrepancy Report" entity unless a document with that exact name/reference is actually mentioned).
   - DO NOT emit empty/null entities where both entity_id and name are null.
   - If an entity has an explicit ID (e.g., 'ORD-123456', 'PR-2026-9901', 'user-8822', 'sess_abc123'), include it.
4. For merchant identification fields (DISPUTE_FORM schema only):
   - "merchant_name" must be the merchant's business/display name (e.g. "NovaMart", "TechGadgets Inc.") -- never a code.
   - "merchant_id" must be a distinct system identifier ONLY if one is explicitly stated in the text (e.g. "MID-TECH-998"). Do NOT repeat merchant_name into merchant_id -- if no separate system ID is stated, leave merchant_id null.

OUTPUT FORMAT:
Return ONLY valid JSON matching this structure:
{{
  "payload": <fields matching the {evidence_type.value} target schema>,
  "extraction": {{
    "assertions": [
      {{
        "claim_id": "claim-1",
        "assertion_text": "...",
        "subject_entity": "..."
      }}
    ],
    "entities": [
      {{
        "entity_type": "Order",
        "entity_id": "ORD-...",
        "name": "ORD-..."
      }}
    ]
  }}
}}
"""

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.text_model,
                    temperature=0.0,
                    response_format={"type": "json_object"},
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a precise financial dispute evidence normalizer. "
                                "Output strictly valid JSON with payload and extraction blocks. "
                                "Never include markdown formatting outside the JSON."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                )
                output_str = response.choices[0].message.content or "{}"
                data = json.loads(output_str)

                payload_data = data.get("payload", {})
                extraction_data = data.get("extraction", {})

                # Validate payload with Pydantic
                validated_payload = target_model.model_validate(payload_data)

                # Filter assertions
                clean_assertions = []
                for a in extraction_data.get("assertions", []):
                    txt = a.get("assertion_text", "").strip()
                    if txt:
                        clean_assertions.append({
                            "claim_id": a.get("claim_id", f"claim-{len(clean_assertions)+1}"),
                            "assertion_text": txt,
                            "subject_entity": a.get("subject_entity")
                        })

                # Filter + validate entities.
                # CHANGED (fix 1): the original stop-noun check had an
                # operator-precedence bug --
                #     eid.lower() in STOP_NOUNS or ename.lower() in STOP_NOUNS and not re.search(...)
                # -- `and` binds tighter than `or` in Python, so the digit
                # guard only ever applied to the `ename` side, never to
                # `eid`. Rewritten below with explicit booleans so the
                # guard applies symmetrically to both fields.
                # CHANGED (fix 2): entity_type is now validated against the
                # schema.EntityType enum instead of being passed through as
                # an unchecked raw string. This is the actual enforcement
                # point for the Enum fix made in schema.py -- previously
                # that enum existed but nothing here ever called it, so
                # invalid/hallucinated entity_type values (e.g. "Policy",
                # "Electronics") still made it into the final envelope.
                clean_entities = []
                for e in extraction_data.get("entities", []):
                    eid = (e.get("entity_id") or "").strip()
                    ename = (e.get("name") or "").strip()
                    etype_raw = e.get("entity_type", "")

                    if not eid and not ename:
                        continue  # no identifying info at all

                    eid_is_stop = eid.lower() in STOP_NOUNS
                    ename_is_stop = ename.lower() in STOP_NOUNS
                    has_digit = bool(re.search(r"\d", eid) or re.search(r"\d", ename))
                    if (eid_is_stop or ename_is_stop) and not has_digit:
                        continue

                    try:
                        validated_type = EntityType(etype_raw).value
                    except ValueError:
                        print(
                            f"  [WARN] Dropping entity with invalid entity_type={etype_raw!r} "
                            f"(eid={eid!r}, name={ename!r}) for {file_path.name} -- "
                            f"not in EntityType enum."
                        )
                        continue

                    final_name = (eid or ename) if validated_type == "Order" else (ename or eid)
                    clean_entities.append({
                        "entity_type": validated_type,
                        "entity_id": eid or ename,
                        "name": final_name
                    })

                envelope = {
                    "meta": {
                        "case_id": case_id,
                        "document_id": doc_id,
                        "file_name": file_path.name,
                        "owner": owner.value,
                        "evidence_type": evidence_type.value,
                        "extracted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "confidence": _estimate_confidence(processed_by, raw_text),
                        "processed_by": processed_by,
                    },
                    "payload": validated_payload.model_dump(mode="json", exclude_none=True),
                    "extraction": {
                        "assertions": clean_assertions,
                        "entities": clean_entities,
                    },
                }
                return envelope

            except (RateLimitError, APIError) as e:
                print(f"  [Attempt {attempt+1}/{max_retries}] LLM API error: {e}. Retrying in {backoff_seconds}s...")
                time.sleep(backoff_seconds)
            except Exception as e:
                print(f"  [Attempt {attempt+1}/{max_retries}] Extraction error for {file_path.name}: {e}")
                if attempt == max_retries - 1:
                    raise e
                time.sleep(backoff_seconds)

        raise RuntimeError(f"Failed to extract {file_path.name} after {max_retries} retries.")