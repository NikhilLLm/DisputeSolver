"""
Fair Weighing Engine Module.

Symmetric fair-weighing model that evaluates both sides equally using:
Relevance Weight x Confidence x Source Tier Weight x Effect Direction.
"""

from __future__ import annotations

from typing import Any, Dict, List
from worker.agents.reasoning_engine.common import _EFFECT_DIRECTION, _RELEVANCE_WEIGHT


def fair_weighing(
    evaluations: List[Dict[str, Any]],
    conflicts: List[Dict[str, Any]],
    findings: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """Symmetric fair-weighing model incorporating evidence source tiers.

    Evaluates BOTH SIDES equally using relevance x confidence x tier_weight x effect direction.
    Does NOT automatically favor either party.

    Returns:
      - cardholder_support: aggregated strength for cardholder
      - merchant_support: aggregated strength for merchant
      - cardholder_pct: normalized percentage
      - merchant_pct: normalized percentage
      - net_direction: which party has stronger overall support (CARDHOLDER / MERCHANT / CONTESTED)
      - breakdown: per-evaluation contribution details
    """
    cardholder_score = 0.0
    merchant_score = 0.0
    breakdown: List[Dict[str, Any]] = []

    # Map finding_id -> finding dict if findings provided
    finding_map = {f["finding_id"]: f for f in findings} if findings else {}

    for ev in evaluations:
        effect = ev.get("effect", "NEUTRAL")
        relevance = ev.get("relevance", "MEDIUM")
        confidence = ev.get("confidence", 0.5)
        fid = ev.get("finding_id", "")

        finding = finding_map.get(fid, {})
        tier_weight = finding.get("tier_weight", 1.0 if ev.get("eval_type") == "deterministic" else 0.7)

        rel_weight = _RELEVANCE_WEIGHT.get(relevance, 0.35)
        party, direction = _EFFECT_DIRECTION.get(effect, (None, 0.0))

        contribution = rel_weight * confidence * tier_weight * abs(direction)

        if party == "cardholder":
            if direction > 0:
                cardholder_score += contribution
            else:
                cardholder_score -= contribution * 0.5
        elif party == "merchant":
            if direction > 0:
                merchant_score += contribution
            else:
                merchant_score -= contribution * 0.5

        breakdown.append({
            "eval_id": ev.get("eval_id", ""),
            "finding_id": fid,
            "effect": effect,
            "relevance": relevance,
            "confidence": confidence,
            "tier_weight": tier_weight,
            "contribution": round(contribution, 4),
            "benefits_party": party if direction > 0 else ("merchant" if party == "cardholder" else "cardholder") if party else None,
        })

    # Apply penalty for detected misstatements from conflicts
    for c in conflicts:
        misstated_party = c.get("misstatement_detected")
        if misstated_party == "merchant":
            merchant_score = max(0.0, merchant_score - 0.15)
        elif misstated_party == "cardholder":
            cardholder_score = max(0.0, cardholder_score - 0.15)

    # Normalize to prevent negative scores
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

    return {
        "cardholder_support": round(cardholder_score, 4),
        "merchant_support": round(merchant_score, 4),
        "cardholder_pct": cardholder_pct,
        "merchant_pct": merchant_pct,
        "net_direction": net_direction,
        "breakdown": breakdown,
    }
