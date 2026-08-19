"""
Deterministic Evaluator Module — Generic Math Verification & Deterministic Weighing.

Consumes the typed `CaseAnalysis` from Stage 2:
  1. Runs generic mathematical verifications (date gaps, amount checks, policy windows)
     without category-specific branching.
  2. Computes deterministic evidence weights using the fixed 5-level relevance
     and 3-level tier weight formulas (NO LLM hallucination in numeric scores).
  3. Calculates final objective support scores, normalized percentages, and net direction.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from worker.agents.reasoning_engine.case_analyst import CaseAnalysis, DateClaim, AmountClaim, EvidencePoint
from worker.agents.reasoning_engine.common import (
    EVIDENCE_SOURCE_TIERS,
    _RELEVANCE_WEIGHT,
    _EFFECT_DIRECTION,
)


# ==========================================================
# PYDANTIC MODELS FOR VERIFICATION RESULTS
# ==========================================================

class DateVerificationResult(BaseModel):
    """Result of a date gap / window calculation."""
    claim_id: str
    description: str
    date_a: str
    date_b: str
    gap_days: int
    expected_max_gap_days: Optional[int] = None
    status: str = Field(description="PASS, FAIL, or INCONCLUSIVE")
    detail: str
    claimed_by: str = "system"


class AmountVerificationResult(BaseModel):
    """Result of an amount comparison."""
    claim_id: str
    description: str
    amount_a: float
    amount_b: float
    difference: float
    status: str = Field(description="MATCH, MISMATCH, or INCONCLUSIVE")
    detail: str


class WeightedEvidencePoint(BaseModel):
    """Evidence point with mathematically calculated weight contribution."""
    point_id: str
    statement: str
    source_tier: str
    relevance: str
    confidence: float
    supports: str
    tier_weight: float
    relevance_weight: float
    contribution: float
    benefits_party: Optional[str]


class DeterministicEvaluationResult(BaseModel):
    """Complete output of Stage 3: Verification + Deterministic Weighing."""
    case_id: str
    date_verifications: List[DateVerificationResult] = Field(default_factory=list)
    amount_verifications: List[AmountVerificationResult] = Field(default_factory=list)
    weighted_evidence: List[WeightedEvidencePoint] = Field(default_factory=list)
    cardholder_score: float
    merchant_score: float
    cardholder_pct: float
    merchant_pct: float
    net_direction: str = Field(description="CARDHOLDER, MERCHANT, or CONTESTED")
    misstatements: List[Dict[str, Any]] = Field(default_factory=list)


# ==========================================================
# 1. GENERIC DATE & AMOUNT MATH UTILITIES
# ==========================================================

def parse_flexible_date(date_str: str) -> Optional[datetime]:
    """Parse flexible date formats (ISO, standard dates, natural month names)."""
    if not date_str:
        return None
    
    clean_str = str(date_str).strip()
    # Normalize ISO with 'Z'
    clean_str = clean_str.replace("Z", "+00:00")
    
    # Common ISO formats
    for fmt in (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d %B %Y",
        "%d %b %Y",
    ):
        try:
            return datetime.strptime(clean_str, fmt)
        except (ValueError, TypeError):
            continue
            
    # Regex fallback for "Month Day, Year" or "Month Day"
    match = re.search(r"([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?(?:,?\s+(\d{4}))?", clean_str)
    if match:
        month_name, day, year = match.groups()
        year = year or "2026"
        try:
            return datetime.strptime(f"{month_name} {day} {year}", "%B %d %Y")
        except ValueError:
            try:
                return datetime.strptime(f"{month_name} {day} {year}", "%b %d %Y")
            except ValueError:
                pass

    return None


def verify_date_gap(claim: DateClaim) -> DateVerificationResult:
    """Universal date math: computes absolute or directed gap and verifies against expected window."""
    dt_a = parse_flexible_date(claim.date_a)
    dt_b = parse_flexible_date(claim.date_b)

    if not dt_a or not dt_b:
        return DateVerificationResult(
            claim_id=claim.claim_id,
            description=claim.description,
            date_a=claim.date_a,
            date_b=claim.date_b,
            gap_days=-1,
            expected_max_gap_days=claim.expected_max_gap_days,
            status="INCONCLUSIVE",
            detail=f"Could not parse one of the dates ({claim.date_a_label}: {claim.date_a}, {claim.date_b_label}: {claim.date_b})",
            claimed_by=claim.claimed_by,
        )

    # Normalize tz-aware vs naive
    if dt_a.tzinfo is not None and dt_b.tzinfo is None:
        dt_a = dt_a.replace(tzinfo=None)
    elif dt_b.tzinfo is not None and dt_a.tzinfo is None:
        dt_b = dt_b.replace(tzinfo=None)

    gap = abs((dt_b - dt_a).days)
    
    if claim.expected_max_gap_days is not None:
        within_window = gap <= claim.expected_max_gap_days
        status = "PASS" if within_window else "FAIL"
        detail = (
            f"Gap between {claim.date_a_label} ({claim.date_a[:10]}) and {claim.date_b_label} ({claim.date_b[:10]}) "
            f"is {gap} days. Policy max is {claim.expected_max_gap_days} days -> {'Within window' if within_window else 'Exceeded window'}."
        )
    else:
        status = "PASS"
        detail = f"Gap between {claim.date_a_label} ({claim.date_a[:10]}) and {claim.date_b_label} ({claim.date_b[:10]}) is {gap} days."

    return DateVerificationResult(
        claim_id=claim.claim_id,
        description=claim.description,
        date_a=claim.date_a,
        date_b=claim.date_b,
        gap_days=gap,
        expected_max_gap_days=claim.expected_max_gap_days,
        status=status,
        detail=detail,
        claimed_by=claim.claimed_by,
    )


def verify_amount_match(claim: AmountClaim, tolerance: float = 0.01) -> AmountVerificationResult:
    """Universal amount math: verifies equality or calculates discrepancy."""
    diff = round(abs(claim.amount_a - claim.amount_b), 2)
    is_match = diff <= tolerance

    if claim.should_match:
        status = "MATCH" if is_match else "MISMATCH"
        detail = (
            f"{claim.amount_a_label} (${claim.amount_a:.2f}) matches {claim.amount_b_label} (${claim.amount_b:.2f})"
            if is_match else
            f"{claim.amount_a_label} (${claim.amount_a:.2f}) differs from {claim.amount_b_label} (${claim.amount_b:.2f}) by ${diff:.2f}"
        )
    else:
        status = "DISCREPANCY_CONFIRMED" if not is_match else "UNEXPECTED_MATCH"
        detail = (
            f"Discrepancy confirmed: {claim.amount_a_label} (${claim.amount_a:.2f}) vs {claim.amount_b_label} (${claim.amount_b:.2f}) (diff: ${diff:.2f})"
            if not is_match else
            f"Amounts are identical (${claim.amount_a:.2f})"
        )

    return AmountVerificationResult(
        claim_id=claim.claim_id,
        description=claim.description,
        amount_a=claim.amount_a,
        amount_b=claim.amount_b,
        difference=diff,
        status=status,
        detail=detail,
    )


# ==========================================================
# 2. DETERMINISTIC WEIGHING CALCULATION
# ==========================================================

def compute_deterministic_weights(
    evidence_points: List[EvidencePoint],
    misstatements: Optional[List[Dict[str, Any]]] = None,
) -> tuple[List[WeightedEvidencePoint], float, float, float, float, str]:
    """Calculate objective evidence scores and normalized percentages.

    Formula per evidence point:
      Weight = Relevance (5-level) x Confidence (0-1) x TierWeight (3-level)
    """
    cardholder_score = 0.0
    merchant_score = 0.0
    weighted_list: List[WeightedEvidencePoint] = []

    for ep in evidence_points:
        tier_weight = EVIDENCE_SOURCE_TIERS.get(ep.source_tier, 0.35)
        rel_weight = _RELEVANCE_WEIGHT.get(ep.relevance, 0.35)
        conf = max(0.0, min(1.0, float(ep.confidence)))

        contribution = round(rel_weight * conf * tier_weight, 4)

        benefits_party = None
        if ep.supports == "cardholder":
            cardholder_score += contribution
            benefits_party = "cardholder"
        elif ep.supports == "merchant":
            merchant_score += contribution
            benefits_party = "merchant"

        weighted_list.append(WeightedEvidencePoint(
            point_id=ep.point_id,
            statement=ep.statement,
            source_tier=ep.source_tier,
            relevance=ep.relevance,
            confidence=conf,
            supports=ep.supports,
            tier_weight=tier_weight,
            relevance_weight=rel_weight,
            contribution=contribution,
            benefits_party=benefits_party,
        ))

    # Apply penalty for detected misstatements
    if misstatements:
        for m in misstatements:
            party = m.get("misstated_party")
            if party == "merchant":
                merchant_score = max(0.0, merchant_score - 0.15)
            elif party == "cardholder":
                cardholder_score = max(0.0, cardholder_score - 0.15)

    cardholder_score = max(0.0, cardholder_score)
    merchant_score = max(0.0, merchant_score)
    total = cardholder_score + merchant_score

    if total > 0:
        cardholder_pct = round(cardholder_score / total, 4)
        merchant_pct = round(merchant_score / total, 4)
    else:
        cardholder_pct = 0.5
        merchant_pct = 0.5

    if abs(cardholder_pct - merchant_pct) < 0.05:
        net_direction = "CONTESTED"
    elif cardholder_pct > merchant_pct:
        net_direction = "CARDHOLDER"
    else:
        net_direction = "MERCHANT"

    return weighted_list, cardholder_score, merchant_score, cardholder_pct, merchant_pct, net_direction


# ==========================================================
# 3. MAIN EVALUATOR PIPELINE ENTRY POINT
# ==========================================================

def run_deterministic_evaluations(analysis: CaseAnalysis) -> DeterministicEvaluationResult:
    """Execute Stage 3: verify date/amount claims and compute objective weights.

    Args:
        analysis: Validated CaseAnalysis from Stage 2.

    Returns:
        DeterministicEvaluationResult containing verification outcomes and mathematically computed weights.
    """
    print("  [Deterministic] Running date & amount verifications...")
    date_results = [verify_date_gap(dc) for dc in analysis.date_claims]
    amount_results = [verify_amount_match(ac) for ac in analysis.amount_claims]

    # Detect party misstatements from date/amount checks
    misstatements: List[Dict[str, Any]] = []
    for dr in date_results:
        if dr.status == "FAIL" and dr.claimed_by in ("merchant", "cardholder"):
            misstatements.append({
                "claim_id": dr.claim_id,
                "misstated_party": dr.claimed_by,
                "reason": dr.detail,
            })

    print(f"  [Deterministic] Completed {len(date_results)} date checks and {len(amount_results)} amount checks")

    # Compute deterministic scores using fixed tier and relevance multipliers
    weighted_pts, ch_score, me_score, ch_pct, me_pct, net_dir = compute_deterministic_weights(
        analysis.evidence_points, misstatements
    )

    print(f"  [Deterministic] Evidence Scores -> Cardholder: {ch_score:.3f} ({ch_pct:.1%}) | "
          f"Merchant: {me_score:.3f} ({me_pct:.1%}) -> Net: {net_dir}")

    return DeterministicEvaluationResult(
        case_id=analysis.case_id,
        date_verifications=date_results,
        amount_verifications=amount_results,
        weighted_evidence=weighted_pts,
        cardholder_score=round(ch_score, 4),
        merchant_score=round(me_score, 4),
        cardholder_pct=ch_pct,
        merchant_pct=me_pct,
        net_direction=net_dir,
        misstatements=misstatements,
    )
