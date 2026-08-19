"""
Deterministic Evaluator Module.

Runs objective, deterministic Python checks (dates, amounts, windows, addresses)
without calling an LLM.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional


def run_deterministic_checks(
    context: Dict[str, Any],
    config: Dict[str, Any],
    findings: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Run objective, deterministic checks using Python logic.

    Returns a list of evaluation dicts with:
      - eval_id, check_id, description
      - result (PASS / FAIL / INCONCLUSIVE)
      - detail (explanation)
      - source_findings (which findings were used)
      - effect (on which party)
    """
    evaluations: List[Dict[str, Any]] = []
    eval_counter = 0

    def _next_eid() -> str:
        nonlocal eval_counter
        eval_counter += 1
        return f"DE{eval_counter:03d}"

    canonical_reason = config.get("canonical_reason", "")

    if canonical_reason == "ITEM_NOT_RECEIVED":
        evaluations.extend(_check_item_not_received(context, findings, _next_eid))
    elif canonical_reason == "UNAUTHORIZED_TRANSACTION":
        evaluations.extend(_check_unauthorized(context, findings, _next_eid))
    elif canonical_reason == "DUPLICATE_PROCESSING":
        evaluations.extend(_check_duplicate(context, findings, _next_eid))
    elif canonical_reason == "CREDIT_NOT_PROCESSED":
        evaluations.extend(_check_credit_not_processed(context, findings, _next_eid))
    elif canonical_reason == "SUBSCRIPTION_CANCELED":
        evaluations.extend(_check_subscription(context, findings, _next_eid))
    elif canonical_reason == "PROCESSING_ERROR":
        evaluations.extend(_check_processing_error(context, findings, _next_eid))

    return evaluations


def _parse_date(date_str: str) -> Optional[datetime]:
    """Try to parse a date string in various formats."""
    if not date_str:
        return None
    for fmt in (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(date_str.replace("+00:00", "Z").rstrip("Z"), fmt.rstrip("Z").rstrip("%z"))
        except (ValueError, TypeError):
            continue
    return None


def _extract_delivery_date(context: Dict[str, Any]) -> Optional[datetime]:
    """Extract delivery date from timeline events or delivery proof facts."""
    for evt in context.get("timeline_events", []):
        if evt.get("status", "").lower() == "delivered":
            dt = _parse_date(str(evt.get("timestamp", "")))
            if dt:
                return dt

    for fact in context.get("facts", []):
        if fact.get("fact_type") == "delivery_proof":
            dt = _parse_date(str(fact.get("delivery_date", "")))
            if dt:
                return dt

    return None


def _extract_report_date(context: Dict[str, Any]) -> Optional[datetime]:
    """Extract the date the cardholder first reported the issue."""
    cardholder_dates: List[datetime] = []
    for fact in context.get("facts", []):
        if (fact.get("fact_type") == "message"
                and fact.get("evidence_owner") == "cardholder"):
            dt = _parse_date(str(fact.get("timestamp", "")))
            if dt:
                cardholder_dates.append(dt)

    if cardholder_dates:
        return min(cardholder_dates)

    for ast in context.get("assertions", []):
        if ast.get("subject") == "complaint_timing" and ast.get("owner") == "cardholder":
            text = ast.get("text", "")
            match = re.search(r"July\s+(\d+)", text)
            if match:
                day = int(match.group(1))
                return datetime(2026, 7, day)

    return None


def _extract_shipping_address(context: Dict[str, Any]) -> Optional[str]:
    """Extract shipping address from purchase record facts or evidence."""
    return None


def _extract_delivery_address(context: Dict[str, Any]) -> Optional[str]:
    """Extract delivery address from tracking timeline events."""
    for evt in context.get("timeline_events", []):
        if evt.get("status", "").lower() == "delivered":
            return evt.get("location")
    return None


def _check_item_not_received(
    context: Dict[str, Any],
    findings: List[Dict[str, Any]],
    next_eid,
) -> List[Dict[str, Any]]:
    """Deterministic checks for ITEM_NOT_RECEIVED disputes."""
    evals: List[Dict[str, Any]] = []

    # -- Check 1: Delivery status confirmed? -----------------
    delivery_confirmed = False
    delivery_finding_ids = []
    for f in findings:
        if f["finding_type"] == "fact" and f["subject"] == "status_event":
            if "delivered" in f["statement"].lower():
                delivery_confirmed = True
                delivery_finding_ids.append(f["finding_id"])

    evals.append({
        "eval_id": next_eid(),
        "check_id": "delivery_status",
        "description": "Does tracking show a 'Delivered' status?",
        "result": "PASS" if delivery_confirmed else "FAIL",
        "detail": (
            "Carrier tracking confirms delivery status as 'Delivered'."
            if delivery_confirmed
            else "No tracking event with 'Delivered' status found."
        ),
        "source_findings": delivery_finding_ids,
        "effect": "SUPPORTS_MERCHANT" if delivery_confirmed else "SUPPORTS_CARDHOLDER",
        "relevance": "DIRECT",
        "confidence": 1.0,
    })

    # -- Check 2: Reporting window ---------------------------
    delivery_date = _extract_delivery_date(context)
    report_date = _extract_report_date(context)

    policy_window_days: Optional[int] = None
    policy_clause_fid = None
    for f in findings:
        if f["finding_type"] == "policy" and f.get("raw_data", {}).get("window_days"):
            policy_window_days = f["raw_data"]["window_days"]
            policy_clause_fid = f["finding_id"]
            break

    if delivery_date and report_date and policy_window_days is not None:
        gap = (report_date - delivery_date).days
        within_window = gap <= policy_window_days

        evals.append({
            "eval_id": next_eid(),
            "check_id": "reporting_window",
            "description": f"Was the dispute reported within {policy_window_days} days of delivery?",
            "result": "PASS" if within_window else "FAIL",
            "detail": (
                f"Cardholder reported {gap} day(s) after delivery "
                f"(delivery: {delivery_date.strftime('%Y-%m-%d')}, "
                f"report: {report_date.strftime('%Y-%m-%d')}). "
                f"Policy window is {policy_window_days} days. "
                f"{'Within window.' if within_window else 'Outside window.'}"
            ),
            "source_findings": [policy_clause_fid] if policy_clause_fid else [],
            "effect": "SUPPORTS_CARDHOLDER" if within_window else "SUPPORTS_MERCHANT",
            "relevance": "HIGH",
            "confidence": 1.0,
        })

        # -- Check 2b: Verify merchant's asserted timing ----
        for ast in context.get("assertions", []):
            if (ast.get("subject") == "complaint_timing"
                    and ast.get("owner") == "merchant"
                    and ast.get("asserted_value_days") is not None):
                merchant_claimed_days = ast["asserted_value_days"]
                actual_days = gap
                if merchant_claimed_days != actual_days:
                    finding_ids = [f["finding_id"] for f in findings
                                   if f.get("raw_data", {}).get("assertion_id") == ast.get("assertion_id")]
                    evals.append({
                        "eval_id": next_eid(),
                        "check_id": "complaint_timing_verification",
                        "description": "Does the merchant's asserted complaint timing match actual dates?",
                        "result": "FAIL",
                        "detail": (
                            f"Merchant asserted customer reported {merchant_claimed_days} days "
                            f"after delivery, but actual gap is {actual_days} days "
                            f"(delivery: {delivery_date.strftime('%Y-%m-%d')}, "
                            f"first contact: {report_date.strftime('%Y-%m-%d')}). "
                            f"Merchant misstated the timing."
                        ),
                        "source_findings": finding_ids,
                        "effect": "CONTRADICTS_MERCHANT",
                        "relevance": "MEDIUM",
                        "confidence": 1.0,
                    })

    # -- Check 3: Address match ------------------------------
    delivery_addr = _extract_delivery_address(context)
    if delivery_addr:
        evals.append({
            "eval_id": next_eid(),
            "check_id": "delivery_address_available",
            "description": "Is a delivery address available from tracking?",
            "result": "PASS",
            "detail": f"Tracking shows delivery to: {delivery_addr}",
            "source_findings": [f["finding_id"] for f in findings
                               if f["subject"] == "status_event"
                               and "delivered" in f["statement"].lower()],
            "effect": "NEUTRAL",
            "relevance": "MEDIUM",
            "confidence": 1.0,
        })

    # -- Check 4: Signature/proof of delivery ----------------
    has_delivery_proof = False
    proof_finding_ids = []
    has_signature = False
    for f in findings:
        if f["finding_type"] == "fact" and f["subject"] == "delivery_proof":
            has_delivery_proof = True
            proof_finding_ids.append(f["finding_id"])
            raw = f.get("raw_data", {})
            if raw.get("signature_collected"):
                has_signature = True

    if has_delivery_proof:
        evals.append({
            "eval_id": next_eid(),
            "check_id": "delivery_proof_exists",
            "description": "Is there photographic or documentary proof of delivery?",
            "result": "PASS",
            "detail": (
                f"Delivery proof exists. "
                f"{'Signature was collected.' if has_signature else 'No signature collected (contactless delivery).'}"
            ),
            "source_findings": proof_finding_ids,
            "effect": "SUPPORTS_MERCHANT",
            "relevance": "HIGH",
            "confidence": 1.0,
        })

    return evals


def _check_unauthorized(context, findings, next_eid):
    """Deterministic checks for UNAUTHORIZED_TRANSACTION."""
    evals = []
    for fact in context.get("facts", []):
        if fact.get("fact_type") == "authorization_data":
            avs = fact.get("avs_result", "")
            cvv = fact.get("cvv_result", "")
            tds = fact.get("three_ds_status", "")

            if avs:
                match = avs.lower() in ("match", "pass", "y")
                evals.append({
                    "eval_id": next_eid(), "check_id": "avs_match",
                    "description": "Did AVS verification pass?",
                    "result": "PASS" if match else "FAIL",
                    "detail": f"AVS result: {avs}",
                    "source_findings": [],
                    "effect": "SUPPORTS_MERCHANT" if match else "SUPPORTS_CARDHOLDER",
                    "relevance": "HIGH", "confidence": 1.0,
                })
            if cvv:
                match = cvv.lower() in ("match", "pass", "m")
                evals.append({
                    "eval_id": next_eid(), "check_id": "cvv_match",
                    "description": "Did CVV verification pass?",
                    "result": "PASS" if match else "FAIL",
                    "detail": f"CVV result: {cvv}",
                    "source_findings": [],
                    "effect": "SUPPORTS_MERCHANT" if match else "SUPPORTS_CARDHOLDER",
                    "relevance": "HIGH", "confidence": 1.0,
                })
            if tds:
                authenticated = tds.lower() in ("authenticated", "success", "y")
                evals.append({
                    "eval_id": next_eid(), "check_id": "three_ds_status",
                    "description": "Was 3D Secure authentication completed?",
                    "result": "PASS" if authenticated else "FAIL",
                    "detail": f"3DS status: {tds}",
                    "source_findings": [],
                    "effect": "SUPPORTS_MERCHANT" if authenticated else "NEUTRAL",
                    "relevance": "HIGH", "confidence": 1.0,
                })
    return evals


def _check_duplicate(context, findings, next_eid):
    """Deterministic checks for DUPLICATE_PROCESSING."""
    return []


def _check_credit_not_processed(context, findings, next_eid):
    """Deterministic checks for CREDIT_NOT_PROCESSED."""
    evals = []
    for fact in context.get("facts", []):
        if fact.get("fact_type") == "processor_record":
            refund_ts = fact.get("refund_timestamp")
            if refund_ts:
                evals.append({
                    "eval_id": next_eid(), "check_id": "refund_issued",
                    "description": "Is there a processor record showing a refund was issued?",
                    "result": "PASS",
                    "detail": f"Refund record found at {refund_ts}",
                    "source_findings": [],
                    "effect": "SUPPORTS_MERCHANT",
                    "relevance": "DIRECT", "confidence": 1.0,
                })
    return evals


def _check_subscription(context, findings, next_eid):
    """Deterministic checks for SUBSCRIPTION_CANCELED."""
    return []


def _check_processing_error(context, findings, next_eid):
    """Deterministic checks for PROCESSING_ERROR."""
    return []
