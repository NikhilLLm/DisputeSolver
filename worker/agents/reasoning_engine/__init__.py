"""
Reasoning Engine Sub-Package — Lean Hybrid 4-Stage Architecture.

Stages:
  1. graph_retrieval: Bounded 2-query graph context retrieval
  2. case_analyst: Single LLM call producing typed `CaseAnalysis` Pydantic model
  3. deterministic_evaluator: Generic math verification & objective deterministic weighting
  4. decision_synthesizer: Compact `VerdictPackage` Pydantic model & explainable narrative
"""

from __future__ import annotations

from worker.agents.reasoning_engine.common import (
    EFFECT_TYPES,
    EVIDENCE_SOURCE_TIERS,
    EVIDENCE_TYPE_TO_TIER,
    OUTCOMES,
    RELEVANCE_LEVELS,
    _EFFECT_DIRECTION,
    _RELEVANCE_WEIGHT,
    _get_llm_client,
    _llm_json_call,
    get_source_tier,
)
from worker.agents.reasoning_engine.case_analyst import (
    AmountClaim,
    CaseAnalysis,
    ConflictPoint,
    DateClaim,
    EvidencePoint,
    PolicyEvaluation,
    analyze_case,
    save_analysis,
)
from worker.agents.reasoning_engine.deterministic_evaluator import (
    AmountVerificationResult,
    DateVerificationResult,
    DeterministicEvaluationResult,
    WeightedEvidencePoint,
    compute_deterministic_weights,
    parse_flexible_date,
    run_deterministic_evaluations,
    verify_amount_match,
    verify_date_gap,
)
from worker.agents.reasoning_engine.decision_synthesizer import (
    DeterministicMetrics,
    ReasoningStatement,
    VerdictPackage,
    _confidence_band,
    synthesize_verdict,
)

__all__ = [
    # Common Enums & Tiers
    "RELEVANCE_LEVELS",
    "EFFECT_TYPES",
    "OUTCOMES",
    "EVIDENCE_SOURCE_TIERS",
    "EVIDENCE_TYPE_TO_TIER",
    "get_source_tier",
    "_RELEVANCE_WEIGHT",
    "_EFFECT_DIRECTION",
    "_get_llm_client",
    "_llm_json_call",
    # Stage 2: Case Analyst
    "EvidencePoint",
    "DateClaim",
    "AmountClaim",
    "PolicyEvaluation",
    "ConflictPoint",
    "CaseAnalysis",
    "analyze_case",
    "save_analysis",
    # Stage 3: Deterministic Evaluator
    "DateVerificationResult",
    "AmountVerificationResult",
    "WeightedEvidencePoint",
    "DeterministicEvaluationResult",
    "parse_flexible_date",
    "verify_date_gap",
    "verify_amount_match",
    "compute_deterministic_weights",
    "run_deterministic_evaluations",
    # Stage 4: Decision Synthesizer
    "ReasoningStatement",
    "DeterministicMetrics",
    "VerdictPackage",
    "_confidence_band",
    "synthesize_verdict",
]
