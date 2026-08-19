"""
Common definitions, enums, constants, and LLM utilities for the reasoning pipeline.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Tuple

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# --------------------------------------------------------------
# ENUMS & CONSTANTS (categorical, NOT arbitrary 0-100)
# --------------------------------------------------------------

RELEVANCE_LEVELS = ["NONE", "LOW", "MEDIUM", "HIGH", "DIRECT"]
EFFECT_TYPES = [
    "SUPPORTS_CARDHOLDER",
    "SUPPORTS_MERCHANT",
    "CONTRADICTS_CARDHOLDER",
    "CONTRADICTS_MERCHANT",
    "NEUTRAL",
    "INSUFFICIENT",
]
OUTCOMES = ["CARDHOLDER", "MERCHANT", "INSUFFICIENT_EVIDENCE"]

# --------------------------------------------------------------
# EVIDENCE SOURCE TIERS (Hierarchy of Truth)
# --------------------------------------------------------------

EVIDENCE_SOURCE_TIERS: Dict[str, float] = {
    "TIER_1_TELEMETRY": 1.0,      # Tamper-resistant 3rd-party data (GPS, carrier scans, 3DS crypto, ARNs)
    "TIER_2_COMMUNICATION": 0.7,  # Contemporaneous timestamped emails, chat transcripts, SMS
    "TIER_3_ASSERTION": 0.35,     # Post-dispute subjective form narratives
}

EVIDENCE_TYPE_TO_TIER: Dict[str, str] = {
    "DELIVERY_PROOF": "TIER_1_TELEMETRY",
    "TRACKING_REPORT": "TIER_1_TELEMETRY",
    "PROCESSOR_LOG": "TIER_1_TELEMETRY",
    "USAGE_LOG": "TIER_1_TELEMETRY",
    "COMMUNICATION_LOG": "TIER_2_COMMUNICATION",
    "PURCHASE_RECORD": "TIER_2_COMMUNICATION",
    "MERCHANT_POLICY": "TIER_2_COMMUNICATION",
    "DISPUTE_FORM": "TIER_3_ASSERTION",
}


def get_source_tier(evidence_type: str, finding_type: str = "") -> Tuple[str, float]:
    """Resolve evidence source tier and weight based on evidence envelope and finding type."""
    if finding_type == "assertion":
        tier = "TIER_3_ASSERTION"
    elif finding_type == "policy":
        tier = "TIER_2_COMMUNICATION"
    else:
        tier = EVIDENCE_TYPE_TO_TIER.get(evidence_type, "TIER_3_ASSERTION")

    weight = EVIDENCE_SOURCE_TIERS.get(tier, 0.35)
    return tier, weight


# Categorical relevance -> numeric weight for fair weighing
_RELEVANCE_WEIGHT: Dict[str, float] = {
    "NONE": 0.0,
    "LOW": 0.15,
    "MEDIUM": 0.35,
    "HIGH": 0.65,
    "DIRECT": 1.0,
}

# Effect direction: positive = supports that party, negative = contradicts
_EFFECT_DIRECTION: Dict[str, Tuple[str | None, float]] = {
    "SUPPORTS_CARDHOLDER": ("cardholder", 1.0),
    "SUPPORTS_MERCHANT": ("merchant", 1.0),
    "CONTRADICTS_CARDHOLDER": ("cardholder", -1.0),
    "CONTRADICTS_MERCHANT": ("merchant", -1.0),
    "NEUTRAL": (None, 0.0),
    "INSUFFICIENT": (None, 0.0),
}


# --------------------------------------------------------------
# LLM CLIENT
# --------------------------------------------------------------

def _get_llm_client() -> OpenAI:
    """Create Groq-compatible OpenAI client."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set")
    return OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )


def _llm_json_call(
    client: OpenAI,
    system_prompt: str,
    user_prompt: str,
    model: Optional[str] = None,
    max_retries: int = 3,
) -> Dict[str, Any]:
    """Make an LLM call expecting JSON output using openai/gpt-oss-120b."""
    chosen_model = model or os.getenv("GROQ_TEXT_MODEL", "openai/gpt-oss-120b")

    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=chosen_model,
                temperature=0.0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            raw = response.choices[0].message.content or "{}"
            return json.loads(raw)
        except Exception as e:
            if attempt == max_retries:
                raise e
            import time
            wait_sec = attempt * 2
            print(f"  [LLM RETRY] Attempt {attempt} failed ({e}), retrying in {wait_sec}s...")
            time.sleep(wait_sec)

    return {}
