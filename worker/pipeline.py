"""
End-to-End Master Pipeline Runner for DisputeSolver.

Wires the complete 4-stage pipeline:
  1. Extraction: Master Canonical Builder (regex form extraction + document envelopes)
  2. Graph Building: 5-Layer Anti-Corruption Knowledge Graph Builder (Neo4j)
  3. Graph Validation: Dynamic topology & constraint validator (stops pipeline on failure)
  4. Reasoning Engine: Tri-Agent Hybrid Orchestrator (deterministic arithmetic + verdict synthesis)

Accepts category ID, case ID, or folder path, automatically resolves files, and executes end-to-end.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from worker.extraction.master_canonical_builder import build_final_canonical_json
from worker.graph.graph_builder import build_5layer_graph
from worker.graph.graph_validator import run_validations
from worker.agents.orchestrator import DisputeReasoningOrchestrator


def resolve_category_dir(
    category_or_case: str,
    data_dir: Union[Path, str] = Path("data"),
) -> Path:
    """
    Resolve a category directory in data/ given:
    - category folder name (e.g. 'category_0_item_not_recieved', 'category_0')
    - case ID (e.g. 'DSP-2026-00187')
    - dispute reason text (e.g. 'Item Not Received')
    """
    data_path = Path(data_dir)
    if not data_path.is_dir():
        data_path = ROOT_DIR / "data"

    cat_dirs = sorted([d for d in data_path.glob("category_*") if d.is_dir()])
    if not cat_dirs:
        raise FileNotFoundError(f"No category directories found in {data_path}")

    query = str(category_or_case).strip()

    # 1. Match by category number regex (e.g. "category_0", "0", "cat_0")
    num_match = re.search(r"category_?(\d+)", query, re.IGNORECASE)
    if not num_match:
        num_match = re.match(r"^(\d+)$", query)
    
    if num_match:
        cat_num = num_match.group(1)
        for d in cat_dirs:
            if re.search(rf"category_{cat_num}\b", d.name):
                return d

    # 2. Match by direct folder name substring
    for d in cat_dirs:
        if query.lower() in d.name.lower() or d.name.lower() in query.lower():
            return d

    # 3. Match by Case ID inside cardholder_intake_form.json
    for d in cat_dirs:
        c_form = d / "cardholder" / "cardholder_intake_form.json"
        if c_form.exists():
            try:
                data = json.loads(c_form.read_text(encoding="utf-8"))
                if query.upper() in data.get("case_id", "").upper():
                    return d
                # Also check dispute reason
                reason = data.get("fields", {}).get("dispute_reason_dropdown", "")
                if query.lower() in reason.lower() or reason.lower() in query.lower():
                    return d
            except Exception:
                continue

    # Default to first category if not matched
    return cat_dirs[0]


def run_full_pipeline(
    category_or_case: str,
    data_dir: Union[Path, str] = Path("data"),
    output_dir: Union[Path, str] = Path("output"),
    db_name: Optional[str] = None,
    validate: bool = True,
) -> Dict[str, Any]:
    """
    Execute the complete 4-stage pipeline for a dispute category:
      1. Ingest files & build canonical JSON
      2. Construct 5-layer graph in Neo4j
      3. Validate graph integrity (stops on error)
      4. Run multi-agent reasoning orchestrator & return final verdict

    Returns:
        Dict[str, Any]: The structured verdict package and pipeline telemetry.
    """
    pipeline_start = time.time()
    out_path = Path(output_dir)
    extractions_dir = out_path / "extractions"
    decisions_dir = out_path / "decisions"
    extractions_dir.mkdir(parents=True, exist_ok=True)
    decisions_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------
    # STAGE 0: Resolve Target Category Directory
    # -------------------------------------------------------------
    target_dir = resolve_category_dir(category_or_case, data_dir=data_dir)
    print(f"\n{'=' * 70}")
    print(f"MASTER DISPUTE PIPELINE: Ingesting {target_dir.name}")
    print(f"{'=' * 70}")

    # -------------------------------------------------------------
    # STAGE 1: Document & Form Extraction -> Canonical JSON
    # -------------------------------------------------------------
    print("\n[Stage 1/4] Running Master Canonical Builder (Regex & Schema Extraction)...")
    canonical_data = build_final_canonical_json(data_dir=target_dir, output_dir=extractions_dir)
    case_id = canonical_data.get("case_id", "UNKNOWN")
    canonical_file = extractions_dir / "final_canonical_case_extractions.json"
    print(f"  -> Canonical extraction built for Case ID: {case_id} ({len(canonical_data.get('extractions', []))} envelopes)")

    # -------------------------------------------------------------
    # STAGE 2: 5-Layer Anti-Corruption Knowledge Graph Builder
    # -------------------------------------------------------------
    print(f"\n[Stage 2/4] Building 5-Layer Knowledge Graph in Neo4j for Case: {case_id}...")
    topology_plan = build_5layer_graph(
        canonical_json_path=canonical_file,
        db_name=db_name,
    )
    print(f"  -> Graph built: {len(topology_plan.case_hubs)} case hubs, {len(topology_plan.domain_bridges)} bridges.")

    # -------------------------------------------------------------
    # STAGE 3: Knowledge Graph Validation
    # -------------------------------------------------------------
    if validate:
        print(f"\n[Stage 3/4] Validating Graph Integrity & Schema Constraints...")
        is_valid = run_validations(
            canonical_json_path=canonical_file,
            db_name=db_name,
        )
        if not is_valid:
            error_msg = f"Graph validation failed for Case {case_id}. Pipeline stopped."
            print(f"  [CRITICAL ERROR] {error_msg}")
            raise RuntimeError(error_msg)
        print("  -> Graph validation passed.")

    # -------------------------------------------------------------
    # STAGE 4: Tri-Agent Reasoning Engine & Deterministic Scoring
    # -------------------------------------------------------------
    print(f"\n[Stage 4/4] Running Multi-Agent Reasoning Engine...")
    orchestrator = DisputeReasoningOrchestrator(output_dir=decisions_dir, db_name=db_name)
    decision = orchestrator.run(case_id)

    total_latency = time.time() - pipeline_start
    print(f"\n{'=' * 70}")
    print(f"PIPELINE COMPLETE: Verdict for Case {case_id} -> {decision.get('verdict')} ({decision.get('confidence_score')})")
    print(f"Total Pipeline Latency: {total_latency:.2f}s")
    print(f"{'=' * 70}\n")

    return {
        "status": "success",
        "case_id": case_id,
        "category_folder": target_dir.name,
        "execution_time_seconds": round(total_latency, 2),
        "decision": decision,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run complete DisputeSolver pipeline.")
    parser.add_argument("category", nargs="?", default="category_0", help="Category ID or Case ID")
    parser.add_argument("--data-dir", default="data", help="Path to data/ folder")
    parser.add_argument("--no-validate", action="store_true", help="Skip graph validation")
    args = parser.parse_args()

    result = run_full_pipeline(args.category, data_dir=args.data_dir, validate=not args.no_validate)
    print(json.dumps(result, indent=2))
