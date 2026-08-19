"""
Dispute Reasoning Orchestrator.

Runs the full reasoning pipeline:
  1. Read dispute reason from graph
  2. Load dispute configuration
  3. Retrieve shared graph context (once)
  4. Generate structured findings
  5. Run deterministic checks (Python)
  6. Run semantic evaluations (LLM)
  7. Detect conflicts
  8. Fair weighing
  9. Synthesize decision with provenance
  10. Write results

This is the single entry point for the reasoning engine.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

from worker.agents.dispute_config import get_dispute_config, normalize_dispute_reason
from worker.agents.graph_retrieval import fetch_case_reasoning_context
from worker.agents.reasoning_engine import (
    generate_findings,
    run_deterministic_checks,
    run_semantic_evaluations,
    detect_conflicts,
    fair_weighing,
    synthesize_decision,
)

load_dotenv()


class DisputeReasoningOrchestrator:
    """Orchestrates the full dispute reasoning pipeline.

    Usage:
        orchestrator = DisputeReasoningOrchestrator()
        result = orchestrator.run("DSP-2026-00187")
    """

    def __init__(
        self,
        db_name: Optional[str] = None,
        output_dir: Optional[Path] = None,
    ):
        self.db_name = db_name or os.getenv("NEO4J_DATABASE", "neo4j")
        self.output_dir = output_dir or Path("worker/agents")

    def run(self, case_id: str) -> Dict[str, Any]:
        """Execute the full reasoning pipeline for a case.

        Returns the structured decision dict.
        """
        start_time = time.time()
        print(f"\n{'=' * 60}")
        print(f"DISPUTE REASONING ENGINE -- Case {case_id}")
        print(f"{'=' * 60}")

        # -- Step 1: Read dispute reason from graph ----------
        print("\n[1/9] Reading dispute reason from graph...")
        # First do a lightweight query just for the dispute reason
        from worker.agents.graph_retrieval import _connect
        driver = _connect()
        db = self.db_name

        with driver.session(database=db) as session:
            result = session.run(
                """
                MATCH (c:Case {case_id: $cid})-[:HAS_DISPUTE_REASON]->(dr:DisputeReason)
                RETURN dr.category AS category, dr.reason_code AS code
                """,
                {"cid": case_id},
            ).single()

        driver.close()

        if not result:
            print(f"  [ERROR] No Case or DisputeReason found for {case_id}")
            return self._error_result(case_id, "Case or DisputeReason not found in graph")

        raw_reason = result["category"] or result["code"] or "UNKNOWN"
        canonical_reason = normalize_dispute_reason(raw_reason)
        print(f"  Dispute reason: {raw_reason} -> {canonical_reason}")

        # -- Step 2: Load dispute configuration --------------
        print("\n[2/9] Loading dispute configuration...")
        config = get_dispute_config(raw_reason)
        print(f"  Canonical reason: {config['canonical_reason']}")
        print(f"  Evaluation questions: {len(config.get('evaluation_questions', []))}")
        print(f"  Relevant fact types: {config.get('relevant_fact_types', [])}")
        print(f"  Deterministic checks: {len(config.get('deterministic_checks', []))}")

        # -- Step 3: Retrieve shared graph context (ONCE) ----
        print("\n[3/9] Retrieving shared graph context...")
        context = fetch_case_reasoning_context(case_id, config, self.db_name)

        print(f"  Parties: {len(context['parties'])}")
        print(f"  Orders: {len(context['orders'])}")
        print(f"  Tracking: {len(context['tracking'])}")
        print(f"  Evidence envelopes: {len(context['evidence'])}")
        print(f"  Assertions: {len(context['assertions'])}")
        print(f"  Facts: {len(context['facts'])}")
        print(f"  Policy clauses: {len(context['policy_clauses'])}")
        print(f"  Timeline events: {len(context['timeline_events'])}")

        if not context["evidence"] and not context["assertions"]:
            return self._error_result(case_id, "No evidence or assertions found in graph")

        # -- Step 4: Generate structured findings ------------
        print("\n[4/9] Generating structured findings from graph context...")
        findings = generate_findings(context, config)
        print(f"  Generated {len(findings)} findings:")

        by_type = {}
        for f in findings:
            t = f["finding_type"]
            by_type[t] = by_type.get(t, 0) + 1
        for t, count in by_type.items():
            print(f"    - {t}: {count}")

        # -- Step 5: Deterministic evaluation ----------------
        print("\n[5/9] Running deterministic checks (Python logic)...")
        det_evals = run_deterministic_checks(context, config, findings)
        print(f"  Completed {len(det_evals)} deterministic evaluations:")
        for de in det_evals:
            print(f"    [{de['eval_id']}] {de['check_id']}: {de['result']} -- {de['effect']}")

        # -- Step 6: Semantic evaluation (LLM) ---------------
        print("\n[6/9] Running semantic evaluations (LLM)...")
        try:
            sem_evals = run_semantic_evaluations(findings, config, context, deterministic_evals=det_evals)
            print(f"  Completed {len(sem_evals)} semantic evaluations")
            for se in sem_evals:
                print(f"    [{se['eval_id']}] {se['finding_id']}: {se['effect']} "
                      f"(relevance={se['relevance']}, confidence={se.get('confidence', 'N/A')})")
        except Exception as e:
            print(f"  [WARNING] Semantic evaluation failed: {e}")
            print(f"  Proceeding with deterministic evaluations only.")
            sem_evals = []

        # -- Step 7: Conflict detection ----------------------
        print("\n[7/9] Detecting conflicts...")
        all_evals = det_evals + sem_evals
        conflicts = detect_conflicts(findings, all_evals)
        print(f"  Identified {len(conflicts)} conflicts:")
        for c in conflicts:
            print(f"    [{c['conflict_id']}] {c['proposition']}: {c['resolution']}")

        # -- Step 8: Fair weighing ---------------------------
        print("\n[8/9] Running fair weighing model...")
        weighing_result = fair_weighing(all_evals, conflicts, findings=findings)
        print(f"  Cardholder support: {weighing_result['cardholder_support']:.4f} "
              f"({weighing_result['cardholder_pct']:.1%})")
        print(f"  Merchant support: {weighing_result['merchant_support']:.4f} "
              f"({weighing_result['merchant_pct']:.1%})")
        print(f"  Net direction: {weighing_result['net_direction']}")

        # -- Step 9: Decision synthesis ----------------------
        print("\n[9/9] Synthesizing final decision...")
        decision = synthesize_decision(
            case_id=case_id,
            config=config,
            findings=findings,
            deterministic_evals=det_evals,
            semantic_evals=sem_evals,
            conflicts=conflicts,
            weighing=weighing_result,
            context=context,
        )

        # Add execution metadata
        elapsed = round(time.time() - start_time, 2)
        decision["run_at"] = datetime.now(timezone.utc).isoformat()
        decision["execution_time_seconds"] = elapsed

        # -- Write results -----------------------------------
        result_path = self.output_dir / f"results_{case_id}.json"
        result_path.write_text(
            json.dumps(decision, indent=2, default=str),
            encoding="utf-8",
        )
        print(f"\n{'=' * 60}")
        print(f"DECISION: {decision['verdict']}")
        print(f"CONFIDENCE: {decision['confidence_score']:.4f} ({decision['confidence_band']})")
        print(f"PRIMARY REASON: {decision.get('primary_reason', 'N/A')}")
        print(f"Results written to: {result_path}")
        print(f"Execution time: {elapsed}s")
        print(f"{'=' * 60}\n")

        return decision

    def _error_result(self, case_id: str, reason: str) -> Dict[str, Any]:
        """Return an error/insufficient-evidence result."""
        result = {
            "case_id": case_id,
            "verdict": "INSUFFICIENT_EVIDENCE",
            "confidence_score": 0.0,
            "confidence_band": "human_review_required",
            "primary_reason": reason,
            "key_factors": [],
            "counterarguments_considered": [],
            "explanation": reason,
            "findings": [],
            "evaluations": {"deterministic": [], "semantic": []},
            "conflicts": [],
            "reasoning_trace": [reason],
            "pipeline": "hybrid_reasoning_engine_v1",
            "run_at": datetime.now(timezone.utc).isoformat(),
        }
        result_path = self.output_dir / f"results_{case_id}.json"
        result_path.write_text(
            json.dumps(result, indent=2, default=str),
            encoding="utf-8",
        )
        return result


# --------------------------------------------------------------
# CLI ENTRY POINT
# --------------------------------------------------------------

if __name__ == "__main__":
    import sys
    case = sys.argv[1] if len(sys.argv) > 1 else "DSP-2026-00187"
    orchestrator = DisputeReasoningOrchestrator()
    orchestrator.run(case)
