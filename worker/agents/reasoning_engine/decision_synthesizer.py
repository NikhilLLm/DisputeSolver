"""
Decision Synthesizer Module.

Produces the final structured dispute decision with:
1. An Executive Summary (compact, distilled snapshot with verdict, confidence, decisive evidence, and balance).
2. Full Provenance & Audit Trail (complete evaluations, finding nodes, and reasoning trace).
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from openai import OpenAI
from worker.agents.reasoning_engine.common import _get_llm_client, _llm_json_call


def synthesize_decision(
    case_id: str,
    config: Dict[str, Any],
    findings: List[Dict[str, Any]],
    deterministic_evals: List[Dict[str, Any]],
    semantic_evals: List[Dict[str, Any]],
    conflicts: List[Dict[str, Any]],
    weighing: Dict[str, Any],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """Produce the final structured decision with an executive summary and full audit trail."""
    client = _get_llm_client()
    all_evals = deterministic_evals + semantic_evals

    net = weighing.get("net_direction", "CONTESTED")
    ch_pct = weighing.get("cardholder_pct", 0.5)
    me_pct = weighing.get("merchant_pct", 0.5)

    total_meaningful_evals = sum(
        1 for e in all_evals
        if e.get("effect") not in ("NEUTRAL", "INSUFFICIENT")
    )

    if total_meaningful_evals < 2:
        outcome = "INSUFFICIENT_EVIDENCE"
        confidence = 0.3
    elif net == "CONTESTED":
        outcome = "INSUFFICIENT_EVIDENCE"
        confidence = max(ch_pct, me_pct)
    elif net == "CARDHOLDER":
        outcome = "CARDHOLDER"
        confidence = ch_pct
    else:
        outcome = "MERCHANT"
        confidence = me_pct

    key_factors: List[str] = []
    evidence_basis: List[str] = []
    policy_basis: List[str] = []
    counterarguments: List[str] = []
    decisive_supporting_evidence: List[Dict[str, Any]] = []

    finding_map = {f["finding_id"]: f for f in findings}

    for ev in all_evals:
        relevance = ev.get("relevance", "MEDIUM")
        effect = ev.get("effect", "NEUTRAL")
        fid = ev.get("finding_id", "")
        finding = finding_map.get(fid, {})
        reason = ev.get("reason", ev.get("detail", ""))

        factor_text = f"[{ev.get('eval_id', '')}->{fid}] {reason}"

        if relevance in ("HIGH", "DIRECT"):
            if ev.get("eval_type") == "policy":
                policy_basis.append(factor_text)
            else:
                evidence_basis.append(factor_text)

            if effect in ("SUPPORTS_CARDHOLDER", "CONTRADICTS_MERCHANT"):
                if outcome == "MERCHANT":
                    counterarguments.append(factor_text)
                else:
                    key_factors.append(factor_text)
                    decisive_supporting_evidence.append({
                        "finding_id": fid,
                        "source_tier": finding.get("source_tier", "TIER_2_COMMUNICATION"),
                        "statement": finding.get("statement", reason),
                        "evidence_id": finding.get("source_evidence", []),
                        "impact": "SUPPORTS_CARDHOLDER",
                    })
            elif effect in ("SUPPORTS_MERCHANT", "CONTRADICTS_CARDHOLDER"):
                if outcome == "CARDHOLDER":
                    counterarguments.append(factor_text)
                else:
                    key_factors.append(factor_text)
                    decisive_supporting_evidence.append({
                        "finding_id": fid,
                        "source_tier": finding.get("source_tier", "TIER_1_TELEMETRY"),
                        "statement": finding.get("statement", reason),
                        "evidence_id": finding.get("source_evidence", []),
                        "impact": "SUPPORTS_MERCHANT",
                    })

    explanation = _generate_explanation(
        client, case_id, config, outcome, confidence,
        findings, all_evals, conflicts, weighing
    )

    insufficient = []
    for q in config.get("evaluation_questions", []):
        addressed = any(
            ev.get("addresses_question", "") and q.lower() in ev.get("addresses_question", "").lower()
            for ev in semantic_evals
        )
        if not addressed:
            det_addressed = any(
                q.lower()[:30] in ev.get("description", "").lower()
                for ev in deterministic_evals
            )
            if not det_addressed:
                insufficient.append(q)

    # Build concise executive summary block
    executive_summary = {
        "case_id": case_id,
        "verdict": outcome,
        "confidence": f"{round(confidence * 100, 1)}% ({_confidence_band(confidence)})",
        "primary_decision_rationale": explanation.get("primary_reason", ""),
        "narrative_summary": explanation.get("narrative", ""),
        "decisive_supporting_evidence": decisive_supporting_evidence[:4],
        "contested_points_and_counterarguments": counterarguments[:3],
        "evidence_balance": {
            "merchant_weight": f"{weighing['merchant_pct']:.1%}",
            "cardholder_weight": f"{weighing['cardholder_pct']:.1%}",
            "net_direction": weighing["net_direction"],
        },
    }

    return {
        "executive_summary": executive_summary,
        "case_id": case_id,
        "verdict": outcome,
        "confidence_score": round(confidence, 4),
        "confidence_band": _confidence_band(confidence),
        "primary_reason": explanation.get("primary_reason", ""),
        "key_factors": key_factors,
        "counterarguments_considered": counterarguments,
        "policy_basis": policy_basis,
        "evidence_basis": evidence_basis,
        "insufficient_evidence": insufficient,
        "explanation": explanation.get("narrative", ""),
        "conflicts": conflicts,
        "weighing_summary": {
            "cardholder_support": weighing["cardholder_support"],
            "merchant_support": weighing["merchant_support"],
            "cardholder_pct": weighing["cardholder_pct"],
            "merchant_pct": weighing["merchant_pct"],
        },
        "findings": [
            {
                "finding_id": f["finding_id"],
                "subject": f["subject"],
                "statement": f["statement"],
                "owner": f["owner"],
                "source_evidence": f["source_evidence"],
                "source_nodes": f["source_nodes"],
                "source_tier": f.get("source_tier", "TIER_3_ASSERTION"),
                "tier_weight": f.get("tier_weight", 0.35),
                "dispute_relevance": f["dispute_relevance"],
                "finding_type": f["finding_type"],
            }
            for f in findings
        ],
        "evaluations": {
            "deterministic": deterministic_evals,
            "semantic": semantic_evals,
        },
        "reasoning_trace": _build_reasoning_trace(outcome, all_evals, conflicts, findings),
        "pipeline": "hybrid_reasoning_engine_v1",
    }


def _confidence_band(score: float) -> str:
    if score >= 0.85:
        return "high_confidence"
    elif score >= 0.65:
        return "moderate_confidence"
    elif score >= 0.45:
        return "low_confidence"
    else:
        return "human_review_required"


def _generate_explanation(
    client: OpenAI,
    case_id: str,
    config: Dict[str, Any],
    outcome: str,
    confidence: float,
    findings: List[Dict[str, Any]],
    evaluations: List[Dict[str, Any]],
    conflicts: List[Dict[str, Any]],
    weighing: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate a human-readable explanation grounded in evaluations."""
    canonical_reason = config.get("canonical_reason", "UNKNOWN")

    evals_text = []
    for ev in evaluations:
        evals_text.append(
            f"  {ev.get('eval_id', '')}: finding={ev.get('finding_id', '')}, "
            f"effect={ev.get('effect', '')}, relevance={ev.get('relevance', '')}, "
            f"confidence={ev.get('confidence', '')}, "
            f"reason=\"{ev.get('reason', ev.get('detail', ''))}\""
        )

    conflicts_text = []
    for c in conflicts:
        conflicts_text.append(
            f"  {c['conflict_id']}: {c['proposition']} -- "
            f"cardholder strength={c['side_a']['strength']}, "
            f"merchant strength={c['side_b']['strength']}, "
            f"resolution={c['resolution']}"
        )

    system_prompt = (
        "You are a neutral dispute resolution report writer. "
        "Produce a clear, fair explanation of a dispute outcome. "
        "You must ONLY reference evidence and evaluations provided -- never invent facts. "
        "Cite finding IDs and evaluation IDs. "
        "Return ONLY valid JSON."
    )

    user_prompt = f"""Write the final decision explanation for this dispute.

CASE: {case_id}
DISPUTE TYPE: {canonical_reason}
OUTCOME: {outcome}
CONFIDENCE: {confidence}

WEIGHING:
  Cardholder support: {weighing['cardholder_support']} ({weighing['cardholder_pct']:.1%})
  Merchant support: {weighing['merchant_support']} ({weighing['merchant_pct']:.1%})

EVALUATIONS:
{chr(10).join(evals_text)}

CONFLICTS:
{chr(10).join(conflicts_text) if conflicts_text else '  None identified'}

Return a JSON object with:
- "primary_reason": one-sentence summary of why the outcome was reached
- "narrative": 3-5 sentence explanation citing specific finding IDs and evaluation IDs
  explaining the reasoning chain: what the cardholder claimed, what evidence the merchant
  provided, what objective checks showed, what policy conditions applied, and why the
  final outcome was reached. If there are conflicts, explain how they were resolved.
"""

    result = _llm_json_call(client, system_prompt, user_prompt)
    return {
        "primary_reason": result.get("primary_reason", f"Decision based on {canonical_reason} evaluation"),
        "narrative": result.get("narrative", "Unable to generate narrative explanation."),
    }


def _build_reasoning_trace(
    outcome: str,
    evaluations: List[Dict[str, Any]],
    conflicts: List[Dict[str, Any]],
    findings: List[Dict[str, Any]],
) -> List[str]:
    """Build a human-readable reasoning trace for auditability."""
    trace: List[str] = []

    trace.append(f"Final outcome: {outcome}")
    trace.append(f"Total evaluations: {len(evaluations)}")
    trace.append(f"Conflicts identified: {len(conflicts)}")

    high_impact = [e for e in evaluations if e.get("relevance") in ("HIGH", "DIRECT")]
    for ev in high_impact:
        fid = ev.get("finding_id", "?")
        finding = next((f for f in findings if f["finding_id"] == fid), None)
        source = finding.get("source_evidence", []) if finding else []
        trace.append(
            f"  {ev.get('eval_id', '')} -> {fid} -> {source}: "
            f"effect={ev.get('effect', '')}, relevance={ev.get('relevance', '')}"
        )

    for c in conflicts:
        trace.append(
            f"  Conflict on '{c['proposition']}': resolved as {c['resolution']}"
        )

    return trace
