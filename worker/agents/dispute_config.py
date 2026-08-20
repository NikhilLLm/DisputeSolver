"""
Dispute Configuration Registry.

Maps each dispute reason category to its evaluation framework:
- evaluation_questions: What must be answered for this dispute type?
- relevant_fact_types: Which FactNode types matter?
- relevant_evidence_types: Which evidence envelopes matter?
- policy_types: Which policy categories apply?
- deterministic_checks: Objective checks that can be computed without LLM.

Configs do NOT declare outcomes -- outcomes emerge from evidence evaluation.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List


# --------------------------------------------------------------
# DISPUTE REASON NORMALIZATION
# --------------------------------------------------------------

# Reason code & alias lookup table
_REASON_CODE_MAP: Dict[str, str] = {
    "13.1": "ITEM_NOT_RECEIVED",
    "13.3": "ITEM_NOT_AS_DESCRIBED",
    "NOT_AS_DESCRIBED": "ITEM_NOT_AS_DESCRIBED",
    "10.4": "UNAUTHORIZED_TRANSACTION",
    "4837": "UNAUTHORIZED_TRANSACTION",
    "FRAUD": "UNAUTHORIZED_TRANSACTION",
    "12.6": "DUPLICATE_PROCESSING",
    "12.6.1": "DUPLICATE_PROCESSING",
    "4834": "DUPLICATE_PROCESSING",
    "DUPLICATE": "DUPLICATE_PROCESSING",
    "13.6": "CREDIT_NOT_PROCESSED",
    "4860": "CREDIT_NOT_PROCESSED",
    "REFUND_NOT_PROCESSED": "CREDIT_NOT_PROCESSED",
    "13.2": "SUBSCRIPTION_CANCELED",
    "4841": "SUBSCRIPTION_CANCELED",
    "SUBSCRIPTION": "SUBSCRIPTION_CANCELED",
    "CANCELLED_RECURRING": "SUBSCRIPTION_CANCELED",
    "12.2": "PROCESSING_ERROR",
    "INCORRECT_AMOUNT": "PROCESSING_ERROR",
}


def normalize_dispute_reason(raw_reason: str) -> str:
    """Format canonical dispute reason to uppercase standard key."""
    if not raw_reason:
        return "UNKNOWN"
    clean = re.sub(r"\(.*?\)", "", str(raw_reason)).strip()
    key = clean.upper().replace(" ", "_").replace("-", "_")

    if key in _REASON_CODE_MAP:
        return _REASON_CODE_MAP[key]
    if raw_reason in _REASON_CODE_MAP:
        return _REASON_CODE_MAP[raw_reason]
    if key in DISPUTE_CONFIG:
        return key
    for canonical in DISPUTE_CONFIG:
        if canonical in key or key in canonical:
            return canonical
    return key


# --------------------------------------------------------------
# DISPUTE CONFIGURATIONS
# --------------------------------------------------------------

DISPUTE_CONFIG: Dict[str, Dict[str, Any]] = {

    "ITEM_NOT_RECEIVED": {
        "evaluation_questions": [
            "Was the item shipped to the correct address?",
            "Was delivery confirmed by carrier tracking evidence?",
            "Does the delivery address match the order/billing address?",
            "Was the dispute reported within the merchant's policy window?",
            "Did the merchant provide tracking information?",
            "Is there photographic or signature proof of delivery?",
            "Did the cardholder attempt to resolve with the merchant before disputing?",
            "Does the cardholder's non-receipt claim contradict delivery evidence?",
        ],
        "relevant_fact_types": [
            "status_event",       # tracking timeline events
            "delivery_proof",     # photo/signature proof
            "message",            # communication between parties
            "purchase_item",      # what was ordered
            "policy_rule",        # merchant delivery/dispute policies
        ],
        "relevant_evidence_types": [
            "DISPUTE_FORM",
            "TRACKING_REPORT",
            "DELIVERY_PROOF",
            "PURCHASE_RECORD",
            "COMMUNICATION_LOG",
            "MERCHANT_POLICY",
        ],
        "policy_types": [
            "delivery_confirmation",
            "non_receipt_reporting_window",
            "pre_claim_verification",
            "post_delivery_liability",
        ],
        "deterministic_checks": [
            {
                "check_id": "reporting_window",
                "description": "Was the dispute reported within the policy-defined window after delivery?",
                "requires": ["delivery_date", "report_date", "policy_window_days"],
            },
            {
                "check_id": "address_match",
                "description": "Does the delivery address match the order shipping address?",
                "requires": ["delivery_address", "shipping_address"],
            },
            {
                "check_id": "delivery_status",
                "description": "Does tracking show a 'Delivered' status?",
                "requires": ["tracking_status"],
            },
        ],
    },

    "UNAUTHORIZED_TRANSACTION": {
        "evaluation_questions": [
            "Was the transaction authenticated via 3D Secure or equivalent?",
            "Did AVS (Address Verification) pass?",
            "Did CVV verification pass?",
            "Is there device fingerprint or IP data linking the cardholder?",
            "Does the cardholder have prior legitimate order history with this merchant?",
            "Was the card reported lost or stolen?",
            "Are there other unrecognized transactions suggesting a pattern?",
        ],
        "relevant_fact_types": [
            "authorization_data",
            "usage_event",
            "processor_record",
            "purchase_item",
        ],
        "relevant_evidence_types": [
            "DISPUTE_FORM",
            "PROCESSOR_LOG",
            "USAGE_LOG",
            "PURCHASE_RECORD",
        ],
        "policy_types": [
            "fraud_liability",
            "authentication_requirements",
        ],
        "deterministic_checks": [
            {
                "check_id": "avs_match",
                "description": "Did AVS verification pass?",
                "requires": ["avs_result"],
            },
            {
                "check_id": "cvv_match",
                "description": "Did CVV verification pass?",
                "requires": ["cvv_result"],
            },
            {
                "check_id": "three_ds_status",
                "description": "Was 3D Secure authentication completed?",
                "requires": ["three_ds_status"],
            },
        ],
    },

    "ITEM_NOT_AS_DESCRIBED": {
        "evaluation_questions": [
            "What was the advertised description of the product/service?",
            "What did the cardholder actually receive?",
            "Is there photographic evidence of the discrepancy?",
            "Did the cardholder attempt to return the item?",
            "Does the merchant's return policy apply?",
            "Did the merchant respond to the complaint?",
        ],
        "relevant_fact_types": [
            "purchase_item",
            "message",
            "policy_rule",
        ],
        "relevant_evidence_types": [
            "DISPUTE_FORM",
            "PURCHASE_RECORD",
            "COMMUNICATION_LOG",
            "MERCHANT_POLICY",
        ],
        "policy_types": [
            "return_policy",
            "product_description_accuracy",
        ],
        "deterministic_checks": [
            {
                "check_id": "return_window",
                "description": "Is the return/complaint within the merchant's return window?",
                "requires": ["purchase_date", "complaint_date", "return_window_days"],
            },
        ],
    },

    "DUPLICATE_PROCESSING": {
        "evaluation_questions": [
            "Are there multiple charges for the same transaction?",
            "Do the charges have different transaction/order IDs?",
            "Is there a time gap between the charges?",
            "Did the cardholder complete separate purchase actions?",
            "Has one of the duplicate charges been refunded?",
        ],
        "relevant_fact_types": [
            "processor_record",
            "purchase_item",
        ],
        "relevant_evidence_types": [
            "DISPUTE_FORM",
            "PURCHASE_RECORD",
            "PROCESSOR_LOG",
        ],
        "policy_types": [
            "duplicate_charge_handling",
        ],
        "deterministic_checks": [
            {
                "check_id": "transaction_id_match",
                "description": "Do the two charges share the same transaction ID?",
                "requires": ["transaction_ids"],
            },
            {
                "check_id": "amount_match",
                "description": "Are the charge amounts identical?",
                "requires": ["charge_amounts"],
            },
        ],
    },

    "CREDIT_NOT_PROCESSED": {
        "evaluation_questions": [
            "Was a refund/credit promised by the merchant?",
            "Is there evidence the item was returned?",
            "Has the refund processing window elapsed?",
            "Does the merchant's refund policy support the claim?",
            "Is there a processor record showing the refund was issued?",
        ],
        "relevant_fact_types": [
            "processor_record",
            "message",
            "policy_rule",
        ],
        "relevant_evidence_types": [
            "DISPUTE_FORM",
            "COMMUNICATION_LOG",
            "PROCESSOR_LOG",
            "MERCHANT_POLICY",
        ],
        "policy_types": [
            "refund_policy",
            "refund_processing_timeline",
        ],
        "deterministic_checks": [
            {
                "check_id": "refund_issued",
                "description": "Is there a processor record showing a refund was issued?",
                "requires": ["refund_timestamp"],
            },
        ],
    },

    "SUBSCRIPTION_CANCELED": {
        "evaluation_questions": [
            "Did the cardholder request cancellation?",
            "Is there a cancellation confirmation?",
            "Was the cancellation within the allowed window?",
            "Did the cardholder continue using the service after claimed cancellation?",
            "Were renewal reminder emails sent?",
        ],
        "relevant_fact_types": [
            "usage_event",
            "message",
            "policy_rule",
        ],
        "relevant_evidence_types": [
            "DISPUTE_FORM",
            "USAGE_LOG",
            "COMMUNICATION_LOG",
            "MERCHANT_POLICY",
        ],
        "policy_types": [
            "cancellation_policy",
            "renewal_terms",
        ],
        "deterministic_checks": [
            {
                "check_id": "cancellation_before_billing",
                "description": "Was the cancellation request made before the billing date?",
                "requires": ["cancellation_date", "billing_date"],
            },
            {
                "check_id": "usage_after_cancellation",
                "description": "Was the service used after the claimed cancellation date?",
                "requires": ["cancellation_date", "usage_events"],
            },
        ],
    },

    "PROCESSING_ERROR": {
        "evaluation_questions": [
            "What amount was the cardholder expecting to be charged?",
            "What amount was actually charged?",
            "Is there a receipt or confirmation showing the expected amount?",
            "Does POS/system data corroborate either amount?",
        ],
        "relevant_fact_types": [
            "processor_record",
            "purchase_item",
        ],
        "relevant_evidence_types": [
            "DISPUTE_FORM",
            "PURCHASE_RECORD",
            "PROCESSOR_LOG",
        ],
        "policy_types": [
            "pricing_accuracy",
        ],
        "deterministic_checks": [
            {
                "check_id": "amount_discrepancy",
                "description": "Does the charged amount differ from the expected amount?",
                "requires": ["expected_amount", "charged_amount"],
            },
        ],
    },
}


def get_dispute_config(dispute_reason: str) -> Dict[str, Any]:
    """Get the evaluation configuration for a normalized dispute reason.

    Returns a copy of the config dict, or a minimal fallback for unknown reasons.
    """
    canonical = normalize_dispute_reason(dispute_reason)
    config = DISPUTE_CONFIG.get(canonical)
  

    if config is None:
        return {
            "canonical_reason": canonical,
            "evaluation_questions": [
                "What is the cardholder's claim?",
                "What evidence does the merchant provide?",
                "Are there policy clauses that apply?",
            ],
            "relevant_fact_types": [],
            "relevant_evidence_types": ["DISPUTE_FORM"],
            "policy_types": [],
            "deterministic_checks": [],
        }

    return {**config, "canonical_reason": canonical}
