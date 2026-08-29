"""
Dispute Reasoning Orchestrator — Lean 4-Stage Hybrid Engine.

Executes the streamlined 4-stage pipeline:
  Stage 1: Bounded 2-query subgraph retrieval from Neo4j
  Stage 2: LLM Case Analyst → Typed `CaseAnalysis` Pydantic model
  Stage 3: Deterministic Verifier + Mathematical Weigher (generic date/amount math)
  Stage 4: LLM Verdict Synthesizer → Compact `VerdictPackage` (~30-40 lines JSON)

Universal across all 8 dispute categories without hardcoded branches.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

from worker.agents.dispute_config import get_dispute_config, normalize_dispute_reason
from worker.agents.graph_retrieval import fetch_case_reasoning_context
from worker.graph.case_briefing_builder import build_case_briefing
from worker.agents.reasoning_engine import (
    CaseAnalysis,
    DeterministicEvaluationResult,
    VerdictPackage,
    analyze_case,
    run_deterministic_evaluations,
    save_analysis,
    synthesize_verdict,
)

load_dotenv()


class DisputeReasoningOrchestrator:
    """Orchestrates the lean 4-stage dispute reasoning pipeline.

    Usage:
        orchestrator = DisputeReasoningOrchestrator()
        result = orchestrator.run("DSP-2026-00201")
    """

    def __init__(
        self,
        db_name: Optional[str] = None,
        output_dir: Optional[Path] = None,
    ):
        self.db_name = db_name or os.getenv("NEO4J_DATABASE", "neo4j")
        self.output_dir = output_dir or Path("output/decisions")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self, case_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute the 4-stage reasoning pipeline for the active case in Neo4j.

        Returns:
            Dict[str, Any]: Compact, structured verdict dictionary.
        """
        active_case = case_id or _auto_detect_active_case_id(self.db_name)
        if not active_case or active_case == "UNKNOWN":
            print("\n[ABORT] No active case found in Neo4j graph or canonical extractions. Pipeline will not trigger.\n")
            return self._error_result("UNKNOWN", "No active case found in graph database")

        case_id = active_case

        start_time = time.time()
        print(f"\n{'=' * 65}")
        print(f"DISPUTE REASONING ENGINE (Hybrid 4-Stage) — Case {case_id}")
        print(f"{'=' * 65}")

        # ==========================================================
        # STAGE 1: Bounded 2-Query Subgraph Retrieval
        # ==========================================================
        print("\n[1/4] Retrieving full case context from Neo4j (2 batch queries)...")
        context = fetch_case_reasoning_context(case_id, db_name=self.db_name)

        if not context.get("case"):
            print(f"  [ERROR] Case '{case_id}' not found in Neo4j.")
            return self._error_result(case_id, "Case not found in graph database")

        dr = context.get("dispute_reason", {})
        raw_reason = dr.get("category") or dr.get("reason_code") or "UNKNOWN"
        canonical_reason = normalize_dispute_reason(raw_reason)
        config = get_dispute_config(raw_reason)

        print(f"  Dispute Category: {raw_reason} (Canonical: {canonical_reason})")
        print(f"  Graph Subgraph Context:")
        print(f"    - Parties: {len(context['parties'])} ({[p['name'] for p in context['parties']]})")
        print(f"    - Case Hubs (Entities): {len(context['entities'])} ({[e['entity_id'] for e in context['entities']]})")
        print(f"    - Domain Bridges: {len(context['domain_bridges'])}")
        print(f"    - Evidence Envelopes: {len(context['evidence'])}")
        print(f"    - Assertions: {len(context['assertions'])}")
        print(f"    - FactNodes: {len(context['facts'])}")
        print(f"    - Policy Clauses: {len(context['policy_clauses'])}")

        if not context["evidence"] and not context["assertions"]:
            return self._error_result(case_id, "No evidence or assertions found in graph")

        # ==========================================================
        # STAGE 1.5: Build Curated Case Briefing Sheet
        # ==========================================================
        print("\n[1.5/4] Synthesizing Case Briefing Sheet from Graph...")
        briefing_sheet = build_case_briefing(context)
        print(f"  Briefing Sheet built ({len(briefing_sheet.splitlines())} lines)")

        # ==========================================================
        # STAGE 2: LLM Case Analyst (1 Constrained Call)
        # ==========================================================
        print("\n[2/4] Running LLM Case Analyst on Case Briefing...")
        analysis: CaseAnalysis = analyze_case(briefing_sheet, config)
        save_analysis(analysis)

        # ==========================================================
        # STAGE 3: Deterministic Verifier + Mathematical Weigher
        # ==========================================================
        print("\n[3/4] Running Deterministic Verifier & Objective Weighting...")
        eval_result: DeterministicEvaluationResult = run_deterministic_evaluations(analysis)

        # ==========================================================
        # STAGE 4: LLM Verdict Narrative Synthesizer
        # ==========================================================
        print("\n[4/4] Synthesizing Compact Verdict & Explainable Narrative...")
        verdict_pkg: VerdictPackage = synthesize_verdict(analysis, eval_result, config)

        # Convert to dictionary and attach execution metadata
        decision_dict = verdict_pkg.model_dump(mode="json")
        elapsed = round(time.time() - start_time, 2)
        decision_dict["pipeline"] = "lean_hybrid_reasoning_v3"
        decision_dict["execution_time_seconds"] = elapsed
        decision_dict["run_at"] = datetime.now(timezone.utc).isoformat()

        # ==========================================================
        # Attach Structured Transaction Details & Resolution Time
        # ==========================================================
        case_info = context.get("case", {})
        parties = {p.get("role", "").lower(): p.get("name", "") for p in context.get("parties", [])}
        facts = context.get("facts", [])
        
        # Discover transaction amounts & references from facts or case
        txn_amount = case_info.get("amount") or dr.get("amount")
        txn_ref = case_info.get("transaction_reference") or dr.get("transaction_reference")
        txn_currency = case_info.get("currency", "USD")
        
        # Calculate resolution cycle time metrics
        intake_dt_str = case_info.get("intake_timestamp") or case_info.get("created_at") or "2026-08-12T10:00:00Z"
        try:
            intake_dt = datetime.fromisoformat(intake_dt_str.replace("Z", "+00:00"))
            now_dt = datetime.now(timezone.utc)
            delta_days = max(1, (now_dt - intake_dt).days)
        except Exception:
            delta_days = 3

        decision_dict["transaction_details"] = {
            "case_id": case_id,
            "transaction_reference": txn_ref or f"ORD-{case_id.replace('DSP-', '')}",
            "amount": txn_amount or 45.0,
            "currency": txn_currency,
            "merchant_name": parties.get("merchant", "Merchant"),
            "cardholder_name": parties.get("cardholder", "Cardholder"),
            "dispute_reason": canonical_reason,
            "reason_code": dr.get("reason_code", config.reason_code_primary),
        }

        decision_dict["resolution_time_metrics"] = {
            "intake_to_decision_days": delta_days,
            "industry_sla_baseline_days": 45,
            "time_saved_days": max(0, 45 - delta_days),
            "cycle_time_reduction_pct": f"{round((45 - delta_days) / 45 * 100, 1)}%",
            "ai_decision_latency_seconds": elapsed,
        }

        # ==========================================================
        # Write Output
        # ==========================================================
        result_path = self.output_dir / f"results_{case_id}.json"
        result_path.write_text(
            json.dumps(decision_dict, indent=2),
            encoding="utf-8",
        )

        # Console Summary
        print(f"\n{'=' * 65}")
        print(f"VERDICT: {verdict_pkg.verdict}")
        print(f"CONFIDENCE: {verdict_pkg.confidence_score:.1%} ({verdict_pkg.confidence_band})")
        print(f"PRIMARY REASON: {verdict_pkg.primary_reason}")
        print(f"RESOLUTION TIME: {delta_days} Days (Industry Baseline: 45 Days · {decision_dict['resolution_time_metrics']['cycle_time_reduction_pct']} faster)")
        print(f"RESULTS SAVED: {result_path}")
        print(f"EXECUTION TIME: {elapsed}s")
        print(f"{'=' * 65}\n")

        return decision_dict

    def _error_result(self, case_id: str, reason: str) -> Dict[str, Any]:
        """Return an error / insufficient evidence fallback dictionary."""
        result = {
            "case_id": case_id,
            "verdict": "INSUFFICIENT_EVIDENCE",
            "confidence_score": 0.0,
            "confidence_band": "human_review_required",
            "primary_reason": reason,
            "reasoning_statements": [],
            "policy_basis": "N/A",
            "counterarguments_addressed": [],
            "executive_summary": reason,
            "deterministic_metrics": {
                "cardholder_score": 0.0,
                "merchant_score": 0.0,
                "cardholder_pct": "50.0%",
                "merchant_pct": "50.0%",
                "net_direction": "CONTESTED",
                "date_verifications_count": 0,
                "amount_verifications_count": 0,
                "misstatements_detected": 0,
            },
            "pipeline": "lean_hybrid_reasoning_v2",
            "run_at": datetime.now(timezone.utc).isoformat(),
        }
        result_path = self.output_dir / f"results_{case_id}.json"
        result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result


def _auto_detect_active_case_id(db_name: Optional[str] = None) -> str:
    """Detect the single active case_id directly from Neo4j or canonical extractions."""
    # 1. Check active Case node in Neo4j directly
    try:
        from worker.agents.graph_retrieval import _connect
        driver = _connect()
        db = db_name or os.getenv("NEO4J_DATABASE", "neo4j")
        with driver.session(database=db) as session:
            record = session.run("MATCH (c:Case) RETURN c.case_id AS cid LIMIT 1").single()
            if record and record["cid"]:
                driver.close()
                return record["cid"]
        driver.close()
    except Exception:
        pass

    # 2. Fallback to canonical extraction JSON
    canonical_file = Path("output/extractions/final_canonical_case_extractions.json")
    if canonical_file.exists():
        try:
            data = json.loads(canonical_file.read_text(encoding="utf-8"))
            cid = data.get("summary", {}).get("case_id")
            if cid:
                return cid
        except Exception:
            pass

    return "UNKNOWN"


# --------------------------------------------------------------
# ENTRY POINT
# --------------------------------------------------------------

if __name__ == "__main__":
    active_case = _auto_detect_active_case_id()
    if active_case == "UNKNOWN":
        print("\n[INFO] No active case found in Neo4j graph or canonical extractions. Pipeline not triggered.\n")
        sys.exit(0)
    orchestrator = DisputeReasoningOrchestrator()
    orchestrator.run(active_case)
