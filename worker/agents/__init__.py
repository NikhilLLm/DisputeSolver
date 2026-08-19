"""
Agentic Reasoning Pipeline Package.

Hybrid reasoning engine for dispute resolution:
- dispute_config: Dynamic dispute-reason configurations
- graph_retrieval: Shared context retrieval from Neo4j
- reasoning_engine: Hybrid evaluation (deterministic + LLM semantic)
- orchestrator: Pipeline runner

Usage:
    from worker.agents import DisputeReasoningOrchestrator
    result = DisputeReasoningOrchestrator().run("DSP-2026-00187")
"""

from worker.agents.dispute_config import (
    get_dispute_config,
    normalize_dispute_reason,
    DISPUTE_CONFIG,
)
from worker.agents.graph_retrieval import fetch_case_reasoning_context
from worker.agents.reasoning_engine import (
    generate_findings,
    run_deterministic_checks,
    run_semantic_evaluations,
    detect_conflicts,
    fair_weighing,
    synthesize_decision,
)
from worker.agents.orchestrator import DisputeReasoningOrchestrator

__all__ = [
    "DisputeReasoningOrchestrator",
    "get_dispute_config",
    "normalize_dispute_reason",
    "DISPUTE_CONFIG",
    "fetch_case_reasoning_context",
    "generate_findings",
    "run_deterministic_checks",
    "run_semantic_evaluations",
    "detect_conflicts",
    "fair_weighing",
    "synthesize_decision",
]
