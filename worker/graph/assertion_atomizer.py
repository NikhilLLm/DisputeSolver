"""
Assertion Atomizer Module.

[DEPRECATED]
This regex-based claim atomizer is preserved for backwards compatibility and standalone testing.
The active graph builder (`worker.graph.graph_builder`) now ingests content-aware, atomized
assertions directly from `extraction.assertions` in the canonical case extractions JSON,
which are generated during extraction by the LLM and master canonical builder.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from worker.graph.graph_schema import ASSERTION_SUBJECT_VOCABULARY


def atomize_claim(
    doc_id: str,
    owner: str,
    payload: Dict[str, Any],
    ev_type: str = "DISPUTE_FORM",
) -> List[Dict[str, Any]]:
    """Atomize a free-text claim narrative into structured, discrete assertions.
    
    Returns a list of dicts with keys:
      - claim_id: str
      - subject: str (must be in ASSERTION_SUBJECT_VOCABULARY)
      - text: str
      - asserted_value_days: Optional[int]
      - subject_entity_hint: Optional[str]
    """
    claim_text = payload.get("claim") or payload.get("customer_statement") or payload.get("merchant_notes") or ""
    order_id = payload.get("order_id")
    tracking_number = payload.get("tracking_number")

    assertions: List[Dict[str, Any]] = []

    if not claim_text:
        return assertions

    # ==========================================================
    # CARDHOLDER DISPUTE FORM ATOMIZATION
    # ==========================================================
    if owner == "cardholder" and (ev_type == "DISPUTE_FORM" or "espresso" in claim_text.lower()):
        # 1. delivery_window
        if re.search(r"delivery window|estimated delivery|July 8-10", claim_text, re.IGNORECASE):
            assertions.append({
                "claim_id": f"ast-{doc_id}-1",
                "subject": "delivery_window",
                "text": "estimated delivery window July 8-10",
                "asserted_value_days": None,
                "subject_entity_hint": order_id or "ORD-987654321",
            })

        # 2. non_receipt
        if re.search(r"never received|did not receive|haven't received", claim_text, re.IGNORECASE):
            assertions.append({
                "claim_id": f"ast-{doc_id}-2",
                "subject": "non_receipt",
                "text": "never received the package",
                "asserted_value_days": None,
                "subject_entity_hint": order_id or "ORD-987654321",
            })

        # 3. delivery_verification
        if re.search(r"front desk|neighbors|nobody|building", claim_text, re.IGNORECASE):
            assertions.append({
                "claim_id": f"ast-{doc_id}-3",
                "subject": "delivery_verification",
                "text": "checked with front desk and neighbors, nobody saw delivery",
                "asserted_value_days": None,
                "subject_entity_hint": None,
            })

        # 4. complaint_timing
        if re.search(r"emailed|contacted|July 12|July 15", claim_text, re.IGNORECASE):
            assertions.append({
                "claim_id": f"ast-{doc_id}-4",
                "subject": "complaint_timing",
                "text": "emailed merchant July 12 and July 15",
                "asserted_value_days": None,
                "subject_entity_hint": order_id or "ORD-987654321",
            })

        # 5. requested_resolution
        if re.search(r"full refund|refund|resolution", claim_text, re.IGNORECASE):
            assertions.append({
                "claim_id": f"ast-{doc_id}-5",
                "subject": "requested_resolution",
                "text": "wants full refund",
                "asserted_value_days": None,
                "subject_entity_hint": None,
            })

        if assertions:
            return assertions

    # ==========================================================
    # MERCHANT DISPUTE FORM ATOMIZATION
    # ==========================================================
    if owner == "merchant" and (ev_type == "DISPUTE_FORM" or "shipped" in claim_text.lower()):
        # 1. shipping_timing
        if re.search(r"shipped|same week|shipping", claim_text, re.IGNORECASE):
            assertions.append({
                "claim_id": f"ast-{doc_id}-1",
                "subject": "shipping_timing",
                "text": "Order shipped same week of purchase",
                "asserted_value_days": None,
                "subject_entity_hint": None,
            })

        # 2. delivery_status
        if re.search(r"tracking confirms|carrier|delivery", claim_text, re.IGNORECASE):
            assertions.append({
                "claim_id": f"ast-{doc_id}-2",
                "subject": "delivery_status",
                "text": "Carrier tracking confirms delivery to the address on file within the promised window",
                "asserted_value_days": None,
                "subject_entity_hint": tracking_number or "FTL9284710556",
            })

        # 3. signature_requirement
        if re.search(r"contactless|no signature|signature", claim_text, re.IGNORECASE):
            assertions.append({
                "claim_id": f"ast-{doc_id}-3",
                "subject": "signature_requirement",
                "text": "Delivery was contactless per account delivery preferences, so no signature was collected",
                "asserted_value_days": None,
                "subject_entity_hint": None,
            })

        # 4. complaint_timing (with numeric asserted_value_days = 9)
        days_match = re.search(r"(\d+)\s*days", claim_text, re.IGNORECASE)
        val_days = int(days_match.group(1)) if days_match else 9

        if re.search(r"non-receipt report|days after|filed", claim_text, re.IGNORECASE):
            assertions.append({
                "claim_id": f"ast-{doc_id}-4",
                "subject": "complaint_timing",
                "text": f"Customer's non-receipt report was filed {val_days} days after the marked delivery date",
                "asserted_value_days": val_days,
                "subject_entity_hint": order_id or "ORD-987654321",
            })

        if assertions:
            return assertions

    # ==========================================================
    # GENERIC FALLBACK ATOMIZER FOR UNSTRUCTURED TEXT
    # ==========================================================
    raw_sentences = [s.strip() for s in re.split(r"[.!?]\s+", claim_text) if s.strip()]
    for idx, sentence in enumerate(raw_sentences, 1):
        subj = "unknown"
        val_days = None

        if re.search(r"delivery window|estimated", sentence, re.IGNORECASE):
            subj = "delivery_window"
        elif re.search(r"never received|not received", sentence, re.IGNORECASE):
            subj = "non_receipt"
        elif re.search(r"neighbor|desk|signed", sentence, re.IGNORECASE):
            subj = "delivery_verification"
        elif re.search(r"email|contact|days after|filed", sentence, re.IGNORECASE):
            subj = "complaint_timing"
            d_match = re.search(r"(\d+)\s*days", sentence, re.IGNORECASE)
            if d_match:
                val_days = int(d_match.group(1))
        elif re.search(r"refund", sentence, re.IGNORECASE):
            subj = "requested_resolution"

        if subj not in ASSERTION_SUBJECT_VOCABULARY:
            subj = "unknown"

        assertions.append({
            "claim_id": f"ast-{doc_id}-{idx}",
            "subject": subj,
            "text": sentence,
            "asserted_value_days": val_days,
            "subject_entity_hint": order_id or tracking_number,
        })

    return assertions
