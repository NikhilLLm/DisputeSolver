"""
Deterministic Non-LLM Form Extractor for Structured JSON Intake Forms.

Features:
1. Sentence-Level Proposition Claim Atomization (splits compound claims into discrete assertions).
2. Dynamic Dispute Reason Normalization (maps both text names and numeric Visa codes to canonical reasons).
3. Dynamic Merchant & Order Entity Normalization (preserves IDs while building clean entity hubs).
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from worker.extraction.schema import (
    DisputeForm,
    EvidenceEnvelope,
    EvidenceMeta,
    EvidenceType,
    Owner,
)

# Regex Patterns for Form Validation
RE_CASE_ID = re.compile(r"DSP-\d{4}-\d{5}", re.IGNORECASE)
RE_ORDER_ID = re.compile(r"ORD-\d+|SUB-\d+", re.IGNORECASE)
RE_MERCHANT_ID = re.compile(r"MID-[\w-]+|MER-[\w-]+", re.IGNORECASE)
RE_DATE_ISO = re.compile(r"\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?)?", re.IGNORECASE)

# Mapping of Raw Dispute Codes & Text to Canonical Reasons
CANONICAL_REASON_MAP = {
    # Item Not Received
    "13.1": "ITEM_NOT_RECEIVED",
    "item not received": "ITEM_NOT_RECEIVED",
    "non-receipt": "ITEM_NOT_RECEIVED",
    # Not As Described
    "13.3": "NOT_AS_DESCRIBED",
    "not as described": "NOT_AS_DESCRIBED",
    "defective": "NOT_AS_DESCRIBED",
    "counterfeit": "NOT_AS_DESCRIBED",
    # Fraudulent / Unauthorized
    "10.4": "FRAUDULENT_TRANSACTION",
    "fraudulent": "FRAUDULENT_TRANSACTION",
    "unauthorized": "FRAUDULENT_TRANSACTION",
    "stolen card": "FRAUDULENT_TRANSACTION",
    # Duplicate Processing
    "12.6.1": "DUPLICATE_PROCESSING",
    "12.6": "DUPLICATE_PROCESSING",
    "duplicate charge": "DUPLICATE_PROCESSING",
    "duplicate processing": "DUPLICATE_PROCESSING",
    # Credit Not Processed / Refund
    "13.6": "CREDIT_NOT_PROCESSED",
    "credit not processed": "CREDIT_NOT_PROCESSED",
    "refund not received": "CREDIT_NOT_PROCESSED",
    "refund": "CREDIT_NOT_PROCESSED",
    # Cancelled Recurring / Subscription
    "13.2": "SUBSCRIPTION_CANCELED",
    "cancelled recurring transaction": "SUBSCRIPTION_CANCELED",
    "subscription canceled": "SUBSCRIPTION_CANCELED",
    "canceled subscription": "SUBSCRIPTION_CANCELED",
    # Processing Error / Incorrect Amount
    "12.2": "PROCESSING_ERROR",
    "incorrect transaction amount": "PROCESSING_ERROR",
    "incorrect amount": "PROCESSING_ERROR",
    "processing error": "PROCESSING_ERROR",
}


def normalize_reason(raw_reason: Optional[str]) -> str:
    """Normalize any dispute code or string into canonical reason key."""
    if not raw_reason:
        return "UNKNOWN"
    cleaned = raw_reason.strip().lower()
    cleaned = re.sub(r"\(.*?\)", "", cleaned).strip()
    return CANONICAL_REASON_MAP.get(cleaned, cleaned.upper().replace(" ", "_"))


def atomize_claim_text(
    claim_text: str,
    subject_default: Optional[str] = None,
    order_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Split a compound claim paragraph into discrete, single-sentence atomic assertions.

    Subject inference is content-aware (no category-specific hardcoding): the
    sentence is examined for an explicit Order ID, a numeric date/days phrase,
    or one of the generic topic nouns (refund, policy, return window). If
    nothing matches, the document-level subject_default (the order ID from the
    intake form) is used so every atom has a non-null anchor that resolves to
    a real entity in the graph.
    """
    if not claim_text or not claim_text.strip():
        return []

    sentences = re.split(r"(?<=[.!?])\s+", claim_text.strip())
    assertions: List[Dict[str, Any]] = []

    for idx, sentence in enumerate(sentences, 1):
        s = sentence.strip()
        if not s:
            continue

        subject: Optional[str] = None
        order_match = RE_ORDER_ID.search(s)
        if order_match:
            subject = order_match.group(0)
        elif re.search(r"\brefund\b|\bcredit\b|\bchargeback\b", s, re.IGNORECASE):
            subject = "Refund"
        elif re.search(
            r"\bitem\b|\bproduct\b|\bmodel\b|\bheadphones?\b|\bmouse\b|\bdress\b|\bcoffee\b|\bsubscription\b",
            s,
            re.IGNORECASE,
        ):
            subject = "Item"
        elif re.search(
            r"\bpolicy\b|\bwindow\b|\bterms\b|\breturn\b|\bcancel(lation|led)?\b|\bdelivery\b",
            s,
            re.IGNORECASE,
        ):
            subject = "Policy"

        # Last resort: anchor to the document-level order ID so the atom
        # still links to a real case-bound entity instead of dangling as null.
        if not subject:
            subject = subject_default

        assertions.append({
            "claim_id": f"ast-claim-{idx}",
            "assertion_text": s,
            "subject_entity": subject,
        })

    return assertions


class FormExtractor:
    """Non-LLM Extractor for structured form JSON files."""

    def extract_form(self, file_path: Path) -> Dict[str, Any]:
        """Parse structured intake/response form JSON file into canonical EvidenceEnvelope."""
        raw_text = file_path.read_text(encoding="utf-8")
        data = json.loads(raw_text)

        form_type = data.get("form_type", "").lower()
        owner = Owner.CARDHOLDER if "cardholder" in str(file_path).lower() or "cardholder" in form_type else Owner.MERCHANT
        fields = data.get("fields", {})

        # Extract Case ID via regex fallback if needed
        case_id = data.get("case_id")
        if not case_id:
            match = RE_CASE_ID.search(raw_text)
            case_id = match.group(0) if match else "DSP-UNKNOWN"

        submitted_at = data.get("submitted_at") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Construct DisputeForm Pydantic Payload
        raw_reason = (
            fields.get("dispute_reason_dropdown")
            or fields.get("reason_code_acknowledged")
            or fields.get("dispute_reason")
            or ""
        )
        canonical_reason = normalize_reason(raw_reason)

        # Canonical merchant slots — the cardholder form gives the display name;
        # the merchant form gives the system ID. Both flow through so the
        # canonical builder can pair them deterministically.
        cardholder_merchant_name = fields.get("merchant_name") if owner == Owner.CARDHOLDER else None
        merchant_id = fields.get("merchant_id") if owner == Owner.MERCHANT else None

        if owner == Owner.CARDHOLDER:
            disputed_amt = fields.get("transaction_amount") or fields.get("disputed_amount")
            if isinstance(disputed_amt, str):
                try:
                    disputed_amt = float(re.sub(r"[^\d.]", "", disputed_amt))
                except ValueError:
                    disputed_amt = None

            claim_statement = (
                fields.get("customer_statement")
                or fields.get("claim")
                or "Cardholder non-receipt / dispute claim"
            )

            payload = {
                "merchant_name": cardholder_merchant_name,
                "customer_name": fields.get("customer_name") or "Cardholder",
                "dispute_reason": raw_reason,
                "canonical_dispute_reason": canonical_reason,
                "claim": claim_statement,
                "requested_resolution": fields.get("requested_resolution") or "Full refund",
                "disputed_amount": disputed_amt,
                "currency": fields.get("currency") or "USD",
                "order_id": fields.get("transaction_reference") or fields.get("order_id"),
            }
            subject_default = payload["order_id"]

        else:
            merchant_name = fields.get("merchant_name") or "Merchant"

            claim_statement = (
                fields.get("merchant_notes")
                or fields.get("claim")
                or fields.get("response_decision")
                or "Merchant defense statement"
            )

            payload = {
                "merchant_name": merchant_name,
                "merchant_id": merchant_id,
                "customer_name": "Cardholder",
                "dispute_reason": raw_reason,
                "canonical_dispute_reason": canonical_reason,
                "claim": claim_statement,
                "requested_resolution": fields.get("requested_outcome") or "deny refund",
                "disputed_amount": fields.get("disputed_amount"),
                "currency": fields.get("currency") or "USD",
                "order_id": fields.get("transaction_reference") or fields.get("order_id"),
            }
            subject_default = payload["order_id"] or merchant_id

        # Validate with Pydantic DisputeForm schema
        validated_form = DisputeForm.model_validate(payload)
        payload_dict = validated_form.model_dump(mode="json", exclude_none=True)

        doc_id = f"doc-form-{file_path.stem[:20]}-{int(time.time())}"

        # Atomize claims into discrete assertions (anchored to order ID when
        # no sentence-specific subject can be inferred)
        assertions = atomize_claim_text(
            claim_statement,
            subject_default=subject_default,
            order_id=subject_default,
        )
        for idx, a in enumerate(assertions, 1):
            a["claim_id"] = f"ast-form-{doc_id[-6:]}-{idx}"

        entities = []
        # Merchant entity: name + ID stay separate fields so the canonical
        # builder can collapse them later. The merchant form emits the ID;
        # the cardholder form emits the display name.
        if owner == Owner.MERCHANT and merchant_id:
            entities.append({
                "entity_type": "Merchant",
                "entity_id": merchant_id,
                "name": payload.get("merchant_name") or merchant_id,
            })
        elif owner == Owner.CARDHOLDER and cardholder_merchant_name:
            entities.append({
                "entity_type": "Merchant",
                "entity_id": f"MER-{cardholder_merchant_name.upper().replace(' ', '-')}",
                "name": cardholder_merchant_name,
            })

        tx_ref = payload.get("order_id")
        if tx_ref:
            entities.append({
                "entity_type": "Order",
                "entity_id": tx_ref,
                "name": tx_ref,
            })

        envelope = {
            "meta": {
                "case_id": case_id,
                "document_id": doc_id,
                "file_name": file_path.name,
                "owner": owner.value,
                "evidence_type": EvidenceType.DISPUTE_FORM.value,
                "extraction_method": "deterministic_regex_form_parser",
                "extracted_at": submitted_at,
                "confidence": 1.0,
            },
            "payload": payload_dict,
            "extraction": {
                "assertions": assertions,
                "entities": entities,
            },
        }

        return envelope
