"""
Reasoning Engine Sub-Package.

Modular pipeline stages for dispute reasoning:
- common: Constants, enums, LLM utilities, and evidence source tiers
- findings_generator: Finding generation from graph context
- deterministic_evaluator: Deterministic checks (dates, amounts, windows)
- semantic_evaluator: LLM semantic evaluation & policy checks
- conflict_engine: Evidence contradiction & resolution with tier hierarchy
- weighing_engine: Symmetric fair-weighing model
- decision_synthesizer: Final decision synthesis with executive summary & audit trace
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
from worker.agents.reasoning_engine.conflict_engine import detect_conflicts
from worker.agents.reasoning_engine.decision_synthesizer import (
    _build_reasoning_trace,
    _confidence_band,
    _generate_explanation,
    synthesize_decision,
)
from worker.agents.reasoning_engine.deterministic_evaluator import (
    _check_credit_not_processed,
    _check_duplicate,
    _check_item_not_received,
    _check_processing_error,
    _check_subscription,
    _check_unauthorized,
    _extract_delivery_address,
    _extract_delivery_date,
    _extract_report_date,
    _extract_shipping_address,
    _parse_date,
    run_deterministic_checks,
)
from worker.agents.reasoning_engine.findings_generator import (
    _fact_to_statement,
    generate_findings,
)
from worker.agents.reasoning_engine.semantic_evaluator import (
    _build_case_summary,
    _llm_evaluate_evidence_batch,
    _llm_evaluate_policies,
    run_semantic_evaluations,
)
from worker.agents.reasoning_engine.weighing_engine import fair_weighing

__all__ = [
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
    "generate_findings",
    "_fact_to_statement",
    "run_deterministic_checks",
    "_parse_date",
    "_extract_delivery_date",
    "_extract_report_date",
    "_extract_shipping_address",
    "_extract_delivery_address",
    "_check_item_not_received",
    "_check_unauthorized",
    "_check_duplicate",
    "_check_credit_not_processed",
    "_check_subscription",
    "_check_processing_error",
    "run_semantic_evaluations",
    "_build_case_summary",
    "_llm_evaluate_evidence_batch",
    "_llm_evaluate_policies",
    "detect_conflicts",
    "fair_weighing",
    "synthesize_decision",
    "_confidence_band",
    "_generate_explanation",
    "_build_reasoning_trace",
]
