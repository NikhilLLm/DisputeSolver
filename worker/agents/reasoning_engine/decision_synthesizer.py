"""
Decision Synthesizer Module — Compact Pydantic Verdict & Explainable Narrative.

Stage 4 of the reasoning pipeline:
  1. Takes the deterministic scores and verification results from Stage 3.
  2. The final verdict and confidence score are ALREADY mathematically decided:
     NO LLM hallucination in verdict or weights.
  3. Uses a single constrained LLM call to write an executive narrative,
     explain why the winning party's evidence prevails, and address counterarguments.
  4. Returns a clean, compact `VerdictPackage` (~30-40 lines JSON).
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Literal, Optional
from openai import OpenAI
from pydantic import BaseModel, Field

from worker.agents.reasoning_engine.case_analyst import CaseAnalysis
from worker.agents.reasoning_engine.deterministic_evaluator import DeterministicEvaluationResult
from worker.agents.reasoning_engine.common import _get_llm_client, _llm_json_call


# ==========================================================
# PYDANTIC OUTPUT MODELS FOR THE VERDICT
# ==========================================================

class ReasoningStatement(BaseModel):
    """A single weighted evidence statement justifying the verdict."""
    statement: str = Field(description="Clear factual statement")
    weight: float = Field(description="Deterministic contribution score (0.0 - 1.0)")
    source_tier: str = Field(description="TIER_1_TELEMETRY, TIER_2_COMMUNICATION, or TIER_3_ASSERTION")
    supports: str = Field(description="cardholder or merchant")
    evidence_ids: List[str] = Field(default_factory=list)


class DeterministicMetrics(BaseModel):
    """Objective scoring summary calculated deterministically in Stage 3."""
    cardholder_score: float
    merchant_score: float
    cardholder_pct: str
    merchant_pct: str
    net_direction: str
    date_verifications_count: int
    amount_verifications_count: int
    misstatements_detected: int


class VerdictPackage(BaseModel):
    """The final compact, auditable decision package."""
    case_id: str
    verdict: Literal["CARDHOLDER", "MERCHANT", "INSUFFICIENT_EVIDENCE"]
    confidence_score: float = Field(ge=0.0, le=1.0)
    confidence_band: str = Field(description="high_confidence, moderate_confidence, low_confidence, human_review_required")
    primary_reason: str = Field(description="One-sentence decisive reason for the verdict")
    reasoning_statements: List[ReasoningStatement] = Field(default_factory=list, description="Top weighted supporting statements")
    policy_basis: str = Field(default="N/A", description="Applicable policy rule evaluation")
    counterarguments_addressed: List[str] = Field(default_factory=list, description="Opposing claims and why they were rebutted")
    executive_summary: str = Field(description="2-4 sentence executive narrative")
    deterministic_metrics: DeterministicMetrics


# ==========================================================
# CONFIDENCE BAND HELPER
# ==========================================================

def _confidence_band(score: float) -> str:
    if score >= 0.85:
        return "high_confidence"
    elif score >= 0.65:
        return "moderate_confidence"
    elif score >= 0.45:
        return "low_confidence"
    else:
        return "human_review_required"


# ==========================================================
# PROMPT & SYNTHESIS
# ==========================================================

_SYNTHESIZER_SYSTEM_PROMPT = """You are a neutral financial dispute arbitrator.

Your job is to produce a concise, professional, and explainable verdict narrative for a chargeback case.

RULES:
1. The mathematical verdict (CARDHOLDER, MERCHANT, or INSUFFICIENT_EVIDENCE) and confidence score have ALREADY been computed deterministically. You MUST respect them.
2. Formulate the primary_reason and executive_summary based strictly on the verified facts, deterministic check results, and policy evaluations provided.
3. Explicitly explain how opposing counterarguments were rebutted by higher-tier evidence (Tier 1 Telemetry > Tier 2 Communication > Tier 3 Assertion).
4. Return ONLY valid JSON matching the specified schema."""


def synthesize_verdict(
    analysis: CaseAnalysis,
    eval_result: DeterministicEvaluationResult,
    config: Dict[str, Any],
) -> VerdictPackage:
    """Run Stage 4: Synthesize explainable verdict narrative and compact JSON output.

    Args:
        analysis: CaseAnalysis from Stage 2.
        eval_result: DeterministicEvaluationResult from Stage 3.
        config: Dispute configuration dict.

    Returns:
        VerdictPackage: Validated compact verdict model.
    """
    client = _get_llm_client()

    # Determine mathematically grounded verdict
    if eval_result.net_direction == "CONTESTED" or (eval_result.cardholder_score < 0.2 and eval_result.merchant_score < 0.2):
        verdict = "INSUFFICIENT_EVIDENCE"
        confidence = 0.5
    elif eval_result.net_direction == "CARDHOLDER":
        verdict = "CARDHOLDER"
        confidence = eval_result.cardholder_pct
    else:
        verdict = "MERCHANT"
        confidence = eval_result.merchant_pct

    conf_band = _confidence_band(confidence)

    # Sort weighted evidence points to select the top supporting points for the winner
    winner_str = "cardholder" if verdict == "CARDHOLDER" else "merchant"
    winning_points = [
        wp for wp in eval_result.weighted_evidence
        if wp.benefits_party == winner_str
    ]
    winning_points.sort(key=lambda x: x.contribution, reverse=True)
    top_supporting = winning_points[:5]

    # Convert top points to ReasoningStatement models
    reasoning_stmts = [
        ReasoningStatement(
            statement=p.statement,
            weight=p.contribution,
            source_tier=p.source_tier,
            supports=p.supports,
            evidence_ids=[p.point_id],
        )
        for p in top_supporting
    ]

    # Build prompt context for LLM narrative generation
    prompt_context = {
        "case_id": analysis.case_id,
        "dispute_category": analysis.dispute_category,
        "mathematical_verdict": verdict,
        "confidence_score": confidence,
        "cardholder_score": eval_result.cardholder_score,
        "merchant_score": eval_result.merchant_score,
        "cardholder_pct": f"{eval_result.cardholder_pct:.1%}",
        "merchant_pct": f"{eval_result.merchant_pct:.1%}",
        "date_verifications": [dv.model_dump() for dv in eval_result.date_verifications],
        "amount_verifications": [av.model_dump() for av in eval_result.amount_verifications],
        "top_supporting_evidence": [p.model_dump() for p in top_supporting],
        "policy_evaluations": [pe.model_dump() for pe in analysis.policy_evaluations],
        "conflicts": [cf.model_dump() for cf in analysis.conflicts],
        "misstatements": eval_result.misstatements,
    }

    user_prompt = f"""Synthesize the final verdict explanation for this dispute case.

CASE ANALYSIS & VERIFICATION RESULTS:
{json.dumps(prompt_context, indent=2)}

Return a JSON object with these exact keys:
{{
  "primary_reason": "One-sentence decisive reason explaining why {verdict} won this dispute",
  "policy_basis": "Summary of applicable policy clause compliance if policies were evaluated, or 'Not applicable —no merchant policy submitted for this dispute category' if none exist",
  "counterarguments_addressed": [
    "Opposing party's claim and how it was rebutted by higher-tier evidence or mathematical verification"
  ],
  "executive_summary": "2-4 sentence clear, professional narrative summarizing the claim, the decisive evidence, and the resolution"
}}"""

    print("  [LLM] Calling verdict narrative synthesizer...")
    start = time.time()
    raw_narrative = _llm_json_call(client, _SYNTHESIZER_SYSTEM_PROMPT, user_prompt)
    elapsed = round(time.time() - start, 2)
    print(f"  [LLM] Verdict synthesizer responded in {elapsed}s")

    metrics = DeterministicMetrics(
        cardholder_score=eval_result.cardholder_score,
        merchant_score=eval_result.merchant_score,
        cardholder_pct=f"{eval_result.cardholder_pct:.1%}",
        merchant_pct=f"{eval_result.merchant_pct:.1%}",
        net_direction=eval_result.net_direction,
        date_verifications_count=len(eval_result.date_verifications),
        amount_verifications_count=len(eval_result.amount_verifications),
        misstatements_detected=len(eval_result.misstatements),
    )

    package = VerdictPackage(
        case_id=analysis.case_id,
        verdict=verdict,
        confidence_score=round(confidence, 4),
        confidence_band=conf_band,
        primary_reason=raw_narrative.get("primary_reason", f"Verdict based on {analysis.dispute_category} evidence analysis."),
        reasoning_statements=reasoning_stmts,
        policy_basis=raw_narrative.get("policy_basis", "N/A"),
        counterarguments_addressed=raw_narrative.get("counterarguments_addressed", []),
        executive_summary=raw_narrative.get("executive_summary", "Decision reached based on evidence hierarchy and deterministic verification."),
        deterministic_metrics=metrics,
    )

    return package
