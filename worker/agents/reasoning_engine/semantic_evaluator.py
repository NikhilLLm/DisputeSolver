"""
Semantic Evaluator Module.

Performs bounded LLM evaluations on evidence findings and policy rules
against the dispute evaluation framework.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from openai import OpenAI
from worker.agents.reasoning_engine.common import (
    EFFECT_TYPES,
    RELEVANCE_LEVELS,
    _get_llm_client,
    _llm_json_call,
)


def run_semantic_evaluations(
    findings: List[Dict[str, Any]],
    config: Dict[str, Any],
    context: Dict[str, Any],
    deterministic_evals: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Run LLM semantic evaluations on findings that require interpretation.

    Evaluates:
      - Finding relevance to dispute questions (NONE/LOW/MEDIUM/HIGH/DIRECT)
      - Finding effect (SUPPORTS_CARDHOLDER / SUPPORTS_MERCHANT / NEUTRAL / etc.)
      - Policy satisfaction / violation (grounded in verified deterministic facts)
      - Confidence score for each evaluation
    """
    client = _get_llm_client()
    eval_questions = config.get("evaluation_questions", [])
    canonical_reason = config.get("canonical_reason", "UNKNOWN")

    assertion_findings = [f for f in findings if f["finding_type"] == "assertion"]
    fact_findings = [f for f in findings if f["finding_type"] == "fact"]
    policy_findings = [f for f in findings if f["finding_type"] == "policy"]

    case_summary = _build_case_summary(context, findings, config, deterministic_evals)

    evidence_findings = assertion_findings + fact_findings
    evaluations: List[Dict[str, Any]] = []

    if evidence_findings:
        eval_result = _llm_evaluate_evidence_batch(
            client, case_summary, evidence_findings, eval_questions, canonical_reason
        )
        evaluations.extend(eval_result)

    if policy_findings:
        policy_evals = _llm_evaluate_policies(
            client, case_summary, policy_findings, findings, canonical_reason, deterministic_evals
        )
        evaluations.extend(policy_evals)

    return evaluations


def _build_case_summary(
    context: Dict[str, Any],
    findings: List[Dict[str, Any]],
    config: Dict[str, Any],
    deterministic_evals: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Build a concise, balanced textual summary of the case for LLM context."""
    dr = context.get("dispute_reason", {})
    lines = [
        f"CASE: {context.get('case_id', 'unknown')}",
        f"DISPUTE REASON: {dr.get('category', 'unknown')} (code: {dr.get('reason_code', 'N/A')})",
        f"CANONICAL TYPE: {config.get('canonical_reason', 'UNKNOWN')}",
        "",
        "PARTIES:",
    ]
    for p in context.get("parties", []):
        lines.append(f"  - {p.get('role', 'unknown')}: {p.get('name', 'N/A')}")

    # Add verified objective facts from deterministic evaluation
    if deterministic_evals:
        lines.append("")
        lines.append("VERIFIED OBJECTIVE CHECK RESULTS (GROUND TRUTH):")
        for de in deterministic_evals:
            lines.append(f"  - [{de.get('eval_id', 'DE')}] {de.get('check_id')}: {de.get('result')} -> {de.get('detail')} ({de.get('effect')})")
    for p in context.get("parties", []):
        lines.append(f"  - {p.get('role', 'unknown')}: {p.get('name', 'N/A')}")

    lines.append("")
    lines.append("CARDHOLDER ASSERTIONS:")
    for f in findings:
        if f["finding_type"] == "assertion" and f["owner"] == "cardholder":
            lines.append(f"  - [{f['finding_id']}] {f['statement']}")

    lines.append("")
    lines.append("MERCHANT ASSERTIONS:")
    for f in findings:
        if f["finding_type"] == "assertion" and f["owner"] == "merchant":
            lines.append(f"  - [{f['finding_id']}] {f['statement']}")

    lines.append("")
    lines.append("KEY EVIDENCE FACTS:")
    for f in findings:
        if f["finding_type"] == "fact":
            lines.append(f"  - [{f['finding_id']}] ({f['owner']}) {f['statement']}")

    lines.append("")
    lines.append("APPLICABLE POLICY CLAUSES:")
    for f in findings:
        if f["finding_type"] == "policy":
            clause_id = f.get("raw_data", {}).get("clause_id", "N/A")
            lines.append(f"  - [{f['finding_id']}] Clause {clause_id}: {f['statement']}")

    return "\n".join(lines)


def _llm_evaluate_evidence_batch(
    client: OpenAI,
    case_summary: str,
    evidence_findings: List[Dict[str, Any]],
    eval_questions: List[str],
    canonical_reason: str,
) -> List[Dict[str, Any]]:
    """Batch-evaluate all evidence findings via a single LLM call."""
    findings_text = []
    for f in evidence_findings:
        findings_text.append(
            f"  {f['finding_id']}: owner={f['owner']}, subject={f['subject']}, "
            f"type={f['finding_type']}, statement=\"{f['statement']}\""
        )

    questions_text = "\n".join(f"  - {q}" for q in eval_questions)

    system_prompt = (
        "You are an impartial dispute resolution analyst. "
        "You evaluate evidence findings for a financial dispute case. "
        "You must be fair to both cardholder and merchant. "
        "You must NOT invent evidence or facts not present in the case. "
        "You must return ONLY valid JSON."
    )

    user_prompt = f"""Evaluate each evidence finding below for the dispute case.

CASE SUMMARY:
{case_summary}

DISPUTE TYPE: {canonical_reason}

EVALUATION QUESTIONS TO ANSWER:
{questions_text}

FINDINGS TO EVALUATE:
{chr(10).join(findings_text)}

Return a JSON object with key "evaluations" containing an array.
Each evaluation must have:
- "finding_id": matching the finding ID exactly (e.g. "F001")
- "relevance": one of NONE, LOW, MEDIUM, HIGH, DIRECT
- "effect": one of SUPPORTS_CARDHOLDER, SUPPORTS_MERCHANT, CONTRADICTS_CARDHOLDER, CONTRADICTS_MERCHANT, NEUTRAL, INSUFFICIENT
- "confidence": float 0.0-1.0 (how confident are you in this evaluation?)
- "reason": brief 1-2 sentence explanation of WHY this effect and relevance were chosen
- "addresses_question": which evaluation question (from above) this finding helps answer, or "none"

RULES:
1. An assertion by the cardholder saying "I didn't receive it" SUPPORTS_CARDHOLDER (relevance: HIGH)
2. Carrier tracking showing "Delivered" SUPPORTS_MERCHANT and CONTRADICTS_CARDHOLDER (relevance: DIRECT)
3. Delivery photos/signatures SUPPORTS_MERCHANT (relevance: DIRECT)
4. Purchase receipts showing correct items SUPPORTS_MERCHANT for amount/order correctness (relevance: MEDIUM)
5. Emails showing prompt communication are NEUTRAL or mildly supportive of the sender
6. Be objective -- do not assume either party is lying without contradictory evidence
"""

    result = _llm_json_call(client, system_prompt, user_prompt)
    raw_evals = result.get("evaluations", [])

    evaluations = []
    for idx, ev in enumerate(raw_evals):
        effect = ev.get("effect", "NEUTRAL")
        if effect not in EFFECT_TYPES:
            effect = "NEUTRAL"

        relevance = ev.get("relevance", "MEDIUM")
        if relevance not in RELEVANCE_LEVELS:
            relevance = "MEDIUM"

        confidence = ev.get("confidence", 0.5)
        confidence = max(0.0, min(1.0, float(confidence)))

        evaluations.append({
            "eval_id": f"SE{idx + 1:03d}",
            "finding_id": ev.get("finding_id", ""),
            "eval_type": "semantic",
            "relevance": relevance,
            "effect": effect,
            "confidence": confidence,
            "reason": ev.get("reason", ""),
            "addresses_question": ev.get("addresses_question", "none"),
        })

    return evaluations


def _llm_evaluate_policies(
    client: OpenAI,
    case_summary: str,
    policy_findings: List[Dict[str, Any]],
    all_findings: List[Dict[str, Any]],
    canonical_reason: str,
    deterministic_evals: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Evaluate policy clauses against case facts."""
    policies_text = []
    for pf in policy_findings:
        clause_id = pf.get("raw_data", {}).get("clause_id", "N/A")
        policies_text.append(
            f"  {pf['finding_id']} (Clause {clause_id}): \"{pf['statement']}\""
        )

    system_prompt = (
        "You are an impartial policy analyst for financial disputes. "
        "Evaluate whether each policy clause's conditions are satisfied, "
        "violated, or not applicable based on the case facts. "
        "You must base timing and objective condition evaluations on VERIFIED OBJECTIVE CHECK RESULTS rather than unverified party claims. "
        "Return ONLY valid JSON."
    )

    user_prompt = f"""Evaluate each policy clause against the case facts.

CASE SUMMARY:
{case_summary}

DISPUTE TYPE: {canonical_reason}

POLICY CLAUSES TO EVALUATE:
{chr(10).join(policies_text)}

Return a JSON object with key "policy_evaluations" containing an array.
Each evaluation must have:
- "finding_id": the policy finding ID
- "clause_id": the clause identifier
- "status": one of SATISFIES, VIOLATES, PARTIALLY_SATISFIES, NOT_APPLICABLE, INCONCLUSIVE
- "effect": one of SUPPORTS_CARDHOLDER, SUPPORTS_MERCHANT, NEUTRAL
- "relevance": one of NONE, LOW, MEDIUM, HIGH, DIRECT
- "confidence": float 0.0-1.0 (confidence in this evaluation)
- "detail": explanation of how the facts relate to this policy condition
- "material_to_outcome": boolean -- does this clause materially affect the dispute outcome?

RULES:
1. Base evaluations ONLY on facts present in the case summary.
2. If a policy sets a reporting window (e.g. 5 days), check the VERIFIED OBJECTIVE CHECK RESULTS. If the customer reported within the window, the customer SATISFIES (or does not violate) the clause.
3. Consider both cardholder and merchant perspectives fairly.
"""

    result = _llm_json_call(client, system_prompt, user_prompt)
    raw_evals = result.get("policy_evaluations", [])

    evaluations = []
    for idx, ev in enumerate(raw_evals):
        effect = ev.get("effect", "NEUTRAL")
        if effect not in EFFECT_TYPES:
            effect = "NEUTRAL"

        relevance = ev.get("relevance", "HIGH")
        if relevance not in RELEVANCE_LEVELS:
            relevance = "HIGH"

        confidence = ev.get("confidence", 0.7)
        confidence = max(0.0, min(1.0, float(confidence)))

        evaluations.append({
            "eval_id": f"PE{idx + 1:03d}",
            "finding_id": ev.get("finding_id", ""),
            "eval_type": "policy",
            "clause_id": ev.get("clause_id", ""),
            "status": ev.get("status", "INCONCLUSIVE"),
            "effect": effect,
            "relevance": relevance,
            "confidence": confidence,
            "detail": ev.get("detail", ""),
            "material_to_outcome": ev.get("material_to_outcome", False),
        })

    return evaluations
