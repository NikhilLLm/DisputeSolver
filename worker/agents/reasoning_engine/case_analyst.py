"""
Case Analyst Module — LLM-Driven Structured Case Analysis.

Mirrors the graph_topology_planner pattern:
  1. Single constrained LLM call reads the full case context
  2. Outputs a typed Pydantic `CaseAnalysis` model
  3. Python `_normalize_analysis()` fixes LLM output variations
  4. Downstream stages consume the typed model (no per-category branches)

The LLM assigns CATEGORICAL labels (relevance: HIGH, source_tier: TIER_1_TELEMETRY)
but NEVER assigns numeric weights — those are computed deterministically in Stage 3.
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field, field_validator

from worker.agents.reasoning_engine.common import (
    EVIDENCE_TYPE_TO_TIER,
    RELEVANCE_LEVELS,
    EFFECT_TYPES,
    _get_llm_client,
    _llm_json_call,
)

load_dotenv()


# ==========================================================
# PYDANTIC MODELS — Strict output schema for the LLM
# ==========================================================

class EvidencePoint(BaseModel):
    """A single piece of evidence extracted from the graph."""
    point_id: str = Field(description="Unique ID like EP-01, EP-02")
    statement: str = Field(description="Human-readable statement of what this evidence says")
    source_type: str = Field(default="", description="Evidence envelope type e.g. TRACKING_REPORT")
    source_tier: Literal[
        "TIER_1_TELEMETRY", "TIER_2_COMMUNICATION", "TIER_3_ASSERTION"
    ] = Field(default="TIER_3_ASSERTION")
    owner: Literal["cardholder", "merchant", "system"] = Field(default="system")
    supports: Literal["cardholder", "merchant", "neutral"] = Field(default="neutral")
    relevance: Literal["NONE", "LOW", "MEDIUM", "HIGH", "DIRECT"] = Field(default="MEDIUM")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    @field_validator("relevance", mode="before")
    @classmethod
    def _clamp_relevance(cls, v):
        if isinstance(v, str):
            v = v.upper().strip()
        return v if v in ("NONE", "LOW", "MEDIUM", "HIGH", "DIRECT") else "MEDIUM"

    @field_validator("source_tier", mode="before")
    @classmethod
    def _clamp_tier(cls, v):
        if isinstance(v, str):
            v = v.upper().strip().replace(" ", "_")
        valid = ("TIER_1_TELEMETRY", "TIER_2_COMMUNICATION", "TIER_3_ASSERTION")
        return v if v in valid else "TIER_3_ASSERTION"


class DateClaim(BaseModel):
    """A date-based claim that needs deterministic verification."""
    claim_id: str = Field(description="Unique ID like DC-01")
    description: str = Field(description="What this date check verifies")
    date_a: str = Field(description="First date in ISO format (YYYY-MM-DD or full ISO)")
    date_a_label: str = Field(default="date_a", description="Label e.g. delivery_date")
    date_b: str = Field(description="Second date in ISO format")
    date_b_label: str = Field(default="date_b", description="Label e.g. complaint_date")
    expected_max_gap_days: Optional[int] = Field(
        default=None,
        description="Policy window days if applicable (e.g. 30 for a 30-day return window)"
    )
    claimed_by: str = Field(default="system", description="Who made or benefits from this claim")


class AmountClaim(BaseModel):
    """An amount-based claim that needs deterministic verification."""
    claim_id: str = Field(description="Unique ID like AC-01")
    description: str = Field(description="What this amount check verifies")
    amount_a: float = Field(description="First amount")
    amount_a_label: str = Field(default="amount_a")
    amount_b: float = Field(description="Second amount")
    amount_b_label: str = Field(default="amount_b")
    should_match: bool = Field(
        default=True,
        description="True if amounts should be equal (duplicate check), False if discrepancy expected"
    )


class PolicyEvaluation(BaseModel):
    """LLM's assessment of a policy clause against case facts."""
    clause_id: str = Field(default="", description="Clause identifier e.g. 7.2")
    clause_text: str = Field(default="", description="The policy clause text")
    status: Literal[
        "SATISFIED", "VIOLATED", "PARTIALLY_SATISFIED", "NOT_APPLICABLE", "INCONCLUSIVE"
    ] = Field(default="INCONCLUSIVE")
    explanation: str = Field(default="")
    supports: Literal["cardholder", "merchant", "neutral"] = Field(default="neutral")

    @field_validator("status", mode="before")
    @classmethod
    def _clamp_status(cls, v):
        if isinstance(v, str):
            v = v.upper().strip().replace(" ", "_")
        valid = ("SATISFIED", "VIOLATED", "PARTIALLY_SATISFIED", "NOT_APPLICABLE", "INCONCLUSIVE")
        # Map common LLM alternatives
        alt_map = {
            "SATISFIES": "SATISFIED",
            "VIOLATES": "VIOLATED",
            "PARTIAL": "PARTIALLY_SATISFIED",
            "N/A": "NOT_APPLICABLE",
            "NA": "NOT_APPLICABLE",
        }
        return alt_map.get(v, v) if v not in valid else v


class ConflictPoint(BaseModel):
    """Where two parties' evidence directly contradicts."""
    conflict_id: str = Field(description="Unique ID like CF-01")
    subject: str = Field(description="Topic of conflict e.g. delivery_status, item_condition")
    cardholder_claim: str = Field(default="")
    merchant_claim: str = Field(default="")
    stronger_evidence_tier: Literal[
        "TIER_1_TELEMETRY", "TIER_2_COMMUNICATION", "TIER_3_ASSERTION", "EQUAL"
    ] = Field(default="EQUAL")
    resolution_favors: Literal["cardholder", "merchant", "unresolved"] = Field(default="unresolved")


class CaseAnalysis(BaseModel):
    """Complete structured analysis of a dispute case — output of Stage 2."""
    case_id: str = Field(default="")
    dispute_category: str = Field(default="")
    evidence_points: List[EvidencePoint] = Field(default_factory=list)
    date_claims: List[DateClaim] = Field(default_factory=list)
    amount_claims: List[AmountClaim] = Field(default_factory=list)
    policy_evaluations: List[PolicyEvaluation] = Field(default_factory=list)
    conflicts: List[ConflictPoint] = Field(default_factory=list)
    preliminary_lean: Literal["cardholder", "merchant", "contested"] = Field(default="contested")


# ==========================================================
# LLM PROMPT & CALL
# ==========================================================

_SYSTEM_PROMPT = """You are an impartial dispute case analyst for financial chargebacks.

Your job: Read the full case context from a Neo4j knowledge graph and produce a structured JSON analysis.

RULES:
1. Extract ALL meaningful evidence points — do NOT skip any evidence or assertion.
2. For each evidence point, assign:
   - source_tier: TIER_1_TELEMETRY (carrier scans, GPS, processor logs, 3DS, QC inspections) 
                   TIER_2_COMMUNICATION (timestamped emails, chat transcripts, purchase records, policies)
                   TIER_3_ASSERTION (post-dispute form narratives, unverified claims)
   - relevance: NONE / LOW / MEDIUM / HIGH / DIRECT
   - supports: cardholder / merchant / neutral
   - confidence: 0.0-1.0 (how reliable is this evidence?)
3. Extract date-based claims that need mathematical verification (policy windows, timing gaps).
4. Extract amount-based claims that need comparison (duplicate charges, refund amounts).
5. Evaluate each policy clause against case facts.
6. Identify conflicts where parties' evidence directly contradicts.
7. State a preliminary_lean based on evidence weight, but this is advisory only.
8. Be FAIR — do not assume either party is lying without contradictory evidence.
9. Return ONLY valid JSON matching the schema exactly."""


def _build_context_brief(context: Dict[str, Any], config: Dict[str, Any]) -> str:
    """Serialize the graph retrieval context into a structured text brief for the LLM."""
    lines = []

    # Case header
    dr = context.get("dispute_reason", {})
    lines.append(f"CASE ID: {context.get('case_id', 'unknown')}")
    lines.append(f"DISPUTE CATEGORY: {dr.get('category', 'unknown')}")
    lines.append(f"REASON CODE: {dr.get('reason_code', 'N/A')}")
    lines.append(f"CANONICAL TYPE: {config.get('canonical_reason', 'UNKNOWN')}")
    lines.append("")

    # Parties
    lines.append("PARTIES:")
    for p in context.get("parties", []):
        lines.append(f"  - {p.get('role', 'unknown')}: {p.get('name', 'N/A')}")
    lines.append("")

    # Entities (all hubs — universal, no label filtering)
    entities = context.get("entities", [])
    if entities:
        lines.append("ENTITIES (Case Hubs):")
        for ent in entities:
            labels = ent.get("labels", [])
            lines.append(f"  - [{', '.join(labels)}] {ent.get('entity_id', '?')} "
                         f"(type: {ent.get('entity_type', '?')})")
        lines.append("")

    # Domain bridges
    bridges = context.get("domain_bridges", [])
    if bridges:
        lines.append("DOMAIN BRIDGES (relationships between entities):")
        for b in bridges:
            lines.append(f"  - ({b['source']}) -[:{b['rel_type']}]-> ({b['target']})")
        lines.append("")

    # Evidence envelopes
    lines.append("EVIDENCE ENVELOPES:")
    for ev in context.get("evidence", []):
        lines.append(f"  - [{ev.get('evidence_id', '?')}] type={ev.get('evidence_type', '?')}, "
                     f"owner={ev.get('owner', '?')}, file={ev.get('file_name', '?')}")
    lines.append("")

    # Assertions
    lines.append("ASSERTIONS (party claims):")
    for ast in context.get("assertions", []):
        lines.append(f"  - [{ast.get('assertion_id', '?')}] owner={ast.get('owner', '?')}, "
                     f"subject={ast.get('subject', '?')}: \"{ast.get('text', '')}\"")
        if ast.get("asserted_value_days") is not None:
            lines.append(f"    (asserted_value_days: {ast['asserted_value_days']})")
    lines.append("")

    # FactNodes (ALL types — universal)
    lines.append("FACT NODES (structured evidence data):")
    for fact in context.get("facts", []):
        ft = fact.get("fact_type", "?")
        owner = fact.get("evidence_owner", fact.get("owner", "system"))
        src = fact.get("source_evidence_type", "?")
        # Serialize key properties (exclude internal metadata)
        props = {k: v for k, v in fact.items()
                 if k not in ("source_evidence_id", "source_evidence_type",
                              "evidence_owner", "about_entity", "case_id")}
        lines.append(f"  - [{ft}] owner={owner}, source={src}: {json.dumps(props, default=str)}")
    lines.append("")

    # Policy clauses
    if context.get("policy_clauses"):
        lines.append("POLICY CLAUSES:")
        for clause in context["policy_clauses"]:
            cid = clause.get("clause_id", "?")
            lines.append(f"  - Clause {cid}: \"{clause.get('text', '')}\"")
            if clause.get("window_days"):
                lines.append(f"    (window_days: {clause['window_days']})")
        lines.append("")

    # Timeline events
    if context.get("timeline_events"):
        lines.append("TIMELINE (tracking events, chronological):")
        for evt in context["timeline_events"]:
            lines.append(f"  - {evt.get('timestamp', '?')}: {evt.get('status', '?')} "
                         f"at {evt.get('location', '?')}")
        lines.append("")

    # Evaluation guidance from dispute config
    questions = config.get("evaluation_questions", [])
    if questions:
        lines.append("EVALUATION QUESTIONS TO CONSIDER:")
        for q in questions:
            lines.append(f"  - {q}")

    return "\n".join(lines)


def _build_user_prompt(context_brief: str, config: Dict[str, Any]) -> str:
    """Build the user prompt for the case analyst LLM call."""
    canonical = config.get("canonical_reason", "UNKNOWN")

    return f"""Analyze this dispute case and produce a structured CaseAnalysis JSON.

CASE CONTEXT:
{context_brief}

DISPUTE TYPE: {canonical}

Return a JSON object with these exact keys:
{{
  "case_id": "<the case ID>",
  "dispute_category": "{canonical}",
  "evidence_points": [
    {{
      "point_id": "EP-01",
      "statement": "Human-readable statement of what this evidence proves",
      "source_type": "TRACKING_REPORT",
      "source_tier": "TIER_1_TELEMETRY | TIER_2_COMMUNICATION | TIER_3_ASSERTION",
      "owner": "cardholder | merchant | system",
      "supports": "cardholder | merchant | neutral",
      "relevance": "NONE | LOW | MEDIUM | HIGH | DIRECT",
      "confidence": 0.0-1.0
    }}
  ],
  "date_claims": [
    {{
      "claim_id": "DC-01",
      "description": "What this date check verifies",
      "date_a": "YYYY-MM-DD",
      "date_a_label": "delivery_date",
      "date_b": "YYYY-MM-DD",
      "date_b_label": "complaint_date",
      "expected_max_gap_days": 30,
      "claimed_by": "cardholder | merchant"
    }}
  ],
  "amount_claims": [
    {{
      "claim_id": "AC-01",
      "description": "What this amount check verifies",
      "amount_a": 199.99,
      "amount_a_label": "charged_amount",
      "amount_b": 199.99,
      "amount_b_label": "refund_amount",
      "should_match": true
    }}
  ],
  "policy_evaluations": [
    {{
      "clause_id": "7.2",
      "clause_text": "The policy clause text",
      "status": "SATISFIED | VIOLATED | PARTIALLY_SATISFIED | NOT_APPLICABLE | INCONCLUSIVE",
      "explanation": "How case facts relate to this clause",
      "supports": "cardholder | merchant | neutral"
    }}
  ],
  "conflicts": [
    {{
      "conflict_id": "CF-01",
      "subject": "delivery_status",
      "cardholder_claim": "Item was not received",
      "merchant_claim": "Carrier tracking shows delivered",
      "stronger_evidence_tier": "TIER_1_TELEMETRY | TIER_2_COMMUNICATION | TIER_3_ASSERTION | EQUAL",
      "resolution_favors": "cardholder | merchant | unresolved"
    }}
  ],
  "preliminary_lean": "cardholder | merchant | contested"
}}

IMPORTANT:
- Extract ALL evidence points, not just the most relevant ones.
- For date_claims: extract ANY date pairs that need mathematical verification (policy windows, timing gaps, cancellation vs billing dates, etc.)
- For amount_claims: extract ANY amount pairs that need comparison (duplicate charges, expected vs actual, refund amounts)
- Evaluate EVERY policy clause listed in the case context.
- Identify ALL conflicts where parties contradict each other.
- Use ONLY facts present in the case context. Do NOT invent evidence."""


# ==========================================================
# NORMALIZATION (same pattern as graph_topology_planner)
# ==========================================================

def _normalize_analysis(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Fix common LLM output variations before Pydantic validation.
    
    Same pattern as _normalize_raw_plan() in graph_topology_planner.py.
    """
    # Top-level key normalization
    key_map = {
        "caseId": "case_id",
        "case_id": "case_id",
        "disputeCategory": "dispute_category",
        "dispute_type": "dispute_category",
        "evidencePoints": "evidence_points",
        "evidence": "evidence_points",
        "dateClaims": "date_claims",
        "date_checks": "date_claims",
        "amountClaims": "amount_claims",
        "amount_checks": "amount_claims",
        "policyEvaluations": "policy_evaluations",
        "policy_checks": "policy_evaluations",
        "policy_results": "policy_evaluations",
        "conflictPoints": "conflicts",
        "conflict_points": "conflicts",
        "preliminaryLean": "preliminary_lean",
        "preliminary_direction": "preliminary_lean",
    }
    normalized = {}
    for k, v in raw.items():
        target_key = key_map.get(k, k)
        normalized[target_key] = v

    # Evidence point field normalization
    if "evidence_points" in normalized:
        for ep in normalized["evidence_points"]:
            if isinstance(ep, dict):
                # Fix common key variations
                if "id" in ep and "point_id" not in ep:
                    ep["point_id"] = ep.pop("id")
                if "pointId" in ep and "point_id" not in ep:
                    ep["point_id"] = ep.pop("pointId")
                if "tier" in ep and "source_tier" not in ep:
                    ep["source_tier"] = ep.pop("tier")
                if "sourceTier" in ep and "source_tier" not in ep:
                    ep["source_tier"] = ep.pop("sourceTier")
                if "sourceType" in ep and "source_type" not in ep:
                    ep["source_type"] = ep.pop("sourceType")
                if "evidence_type" in ep and "source_type" not in ep:
                    ep["source_type"] = ep.pop("evidence_type")
                # Clamp confidence to 0-1
                if "confidence" in ep:
                    try:
                        ep["confidence"] = max(0.0, min(1.0, float(ep["confidence"])))
                    except (ValueError, TypeError):
                        ep["confidence"] = 0.5

    # Date claim field normalization
    if "date_claims" in normalized:
        for dc in normalized["date_claims"]:
            if isinstance(dc, dict):
                if "id" in dc and "claim_id" not in dc:
                    dc["claim_id"] = dc.pop("id")
                if "claimId" in dc and "claim_id" not in dc:
                    dc["claim_id"] = dc.pop("claimId")
                if "max_gap_days" in dc and "expected_max_gap_days" not in dc:
                    dc["expected_max_gap_days"] = dc.pop("max_gap_days")
                if "window_days" in dc and "expected_max_gap_days" not in dc:
                    dc["expected_max_gap_days"] = dc.pop("window_days")

    # Amount claim field normalization
    if "amount_claims" in normalized:
        for ac in normalized["amount_claims"]:
            if isinstance(ac, dict):
                if "id" in ac and "claim_id" not in ac:
                    ac["claim_id"] = ac.pop("id")

    # Conflict field normalization
    if "conflicts" in normalized:
        for cf in normalized["conflicts"]:
            if isinstance(cf, dict):
                if "id" in cf and "conflict_id" not in cf:
                    cf["conflict_id"] = cf.pop("id")
                if "stronger_tier" in cf and "stronger_evidence_tier" not in cf:
                    cf["stronger_evidence_tier"] = cf.pop("stronger_tier")
                if "favors" in cf and "resolution_favors" not in cf:
                    cf["resolution_favors"] = cf.pop("favors")

    # Policy evaluation field normalization
    if "policy_evaluations" in normalized:
        for pe in normalized["policy_evaluations"]:
            if isinstance(pe, dict):
                if "clauseId" in pe and "clause_id" not in pe:
                    pe["clause_id"] = pe.pop("clauseId")
                if "clauseText" in pe and "clause_text" not in pe:
                    pe["clause_text"] = pe.pop("clauseText")

    return normalized


# ==========================================================
# MAIN ENTRY POINT
# ==========================================================

def analyze_case(
    context: Dict[str, Any],
    config: Dict[str, Any],
) -> CaseAnalysis:
    """Run the LLM Case Analyst — Stage 2 of the reasoning pipeline.

    Args:
        context: Graph retrieval context dict from Stage 1.
        config: Dispute configuration from dispute_config.py.

    Returns:
        CaseAnalysis: Typed, validated Pydantic model.
    """
    client = _get_llm_client()

    # Build the case brief from graph context
    context_brief = _build_context_brief(context, config)

    # Single LLM call
    print("  [LLM] Calling case analyst...")
    start = time.time()
    raw_result = _llm_json_call(client, _SYSTEM_PROMPT, _build_user_prompt(context_brief, config))
    elapsed = round(time.time() - start, 2)
    print(f"  [LLM] Case analyst responded in {elapsed}s")

    # Normalize LLM output (fix key variations)
    normalized = _normalize_analysis(raw_result)

    # Validate through Pydantic
    try:
        analysis = CaseAnalysis(**normalized)
    except Exception as e:
        print(f"  [WARN] Pydantic validation failed, attempting field-by-field recovery: {e}")
        analysis = _recover_partial_analysis(normalized, context)

    # Ensure case_id is set
    if not analysis.case_id:
        analysis.case_id = context.get("case_id", "unknown")
    if not analysis.dispute_category:
        analysis.dispute_category = config.get("canonical_reason", "UNKNOWN")

    print(f"  Analysis: {len(analysis.evidence_points)} evidence points, "
          f"{len(analysis.date_claims)} date claims, "
          f"{len(analysis.amount_claims)} amount claims, "
          f"{len(analysis.policy_evaluations)} policy evals, "
          f"{len(analysis.conflicts)} conflicts")
    print(f"  Preliminary lean: {analysis.preliminary_lean}")

    return analysis


def _recover_partial_analysis(
    raw: Dict[str, Any],
    context: Dict[str, Any],
) -> CaseAnalysis:
    """Attempt to recover a partial CaseAnalysis when full Pydantic validation fails."""
    safe = {
        "case_id": raw.get("case_id", context.get("case_id", "unknown")),
        "dispute_category": raw.get("dispute_category", ""),
        "preliminary_lean": raw.get("preliminary_lean", "contested"),
    }

    # Recover evidence points one by one
    eps = []
    for i, ep in enumerate(raw.get("evidence_points", [])):
        try:
            eps.append(EvidencePoint(**ep))
        except Exception:
            try:
                eps.append(EvidencePoint(
                    point_id=ep.get("point_id", f"EP-{i+1:02d}"),
                    statement=str(ep.get("statement", "")),
                ))
            except Exception:
                pass
    safe["evidence_points"] = eps

    # Recover date claims
    dcs = []
    for i, dc in enumerate(raw.get("date_claims", [])):
        try:
            dcs.append(DateClaim(**dc))
        except Exception:
            pass
    safe["date_claims"] = dcs

    # Recover amount claims
    acs = []
    for i, ac in enumerate(raw.get("amount_claims", [])):
        try:
            acs.append(AmountClaim(**ac))
        except Exception:
            pass
    safe["amount_claims"] = acs

    # Recover policy evaluations
    pes = []
    for pe in raw.get("policy_evaluations", []):
        try:
            pes.append(PolicyEvaluation(**pe))
        except Exception:
            pass
    safe["policy_evaluations"] = pes

    # Recover conflicts
    cfs = []
    for cf in raw.get("conflicts", []):
        try:
            cfs.append(ConflictPoint(**cf))
        except Exception:
            pass
    safe["conflicts"] = cfs

    return CaseAnalysis(**safe)


# ==========================================================
# PERSISTENCE (versioned output, same pattern as topology planner)
# ==========================================================

def save_analysis(analysis: CaseAnalysis, output_dir: str = "output/extractions") -> Path:
    """Save the case analysis to versioned JSON files."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    data = analysis.model_dump(mode="json")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    versioned = out / f"case_analysis_{analysis.case_id}_{ts}.json"
    latest = out / f"case_analysis_{analysis.case_id}.json"

    versioned.write_text(json.dumps(data, indent=2), encoding="utf-8")
    latest.write_text(json.dumps(data, indent=2), encoding="utf-8")

    print(f"  Analysis saved: {versioned.name}")
    return latest
