"""
Agentic Reasoning Pipeline Package — Lean Hybrid 4-Stage Architecture.

- dispute_config: Dynamic dispute-reason configurations
- graph_retrieval: Bounded 2-query context retrieval from Neo4j
- reasoning_engine: 4-stage hybrid reasoning engine (case_analyst, deterministic_evaluator, decision_synthesizer)
- orchestrator: Pipeline runner

Usage:
    from worker.agents import DisputeReasoningOrchestrator
    result = DisputeReasoningOrchestrator().run("DSP-2026-00201")
"""

from worker.agents.dispute_config import (
    get_dispute_config,
    normalize_dispute_reason,
    DISPUTE_CONFIG,
)
from worker.agents.graph_retrieval import (
    fetch_case_reasoning_context,
    query_similar_assertions,
    query_similar_facts,
)
from worker.graph.case_briefing_builder import build_case_briefing
from worker.agents.reasoning_engine import (
    analyze_case,
    run_deterministic_evaluations,
    synthesize_verdict,
    CaseAnalysis,
    DeterministicEvaluationResult,
    VerdictPackage,
)
from worker.agents.orchestrator import DisputeReasoningOrchestrator

__all__ = [
    "DisputeReasoningOrchestrator",
    "get_dispute_config",
    "normalize_dispute_reason",
    "DISPUTE_CONFIG",
    "fetch_case_reasoning_context",
    "query_similar_assertions",
    "query_similar_facts",
    "build_case_briefing",
    "analyze_case",
    "run_deterministic_evaluations",
    "synthesize_verdict",
    "CaseAnalysis",
    "DeterministicEvaluationResult",
    "VerdictPackage",
]
