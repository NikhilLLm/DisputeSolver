"""
Dynamic Graph Validator Module.

Runs dynamic post-build verification queries against Neo4j to validate graph shape,
node counts, property types, multi-hop reachability, and domain bridges derived
directly from the active case's canonical JSON and GraphTopologyPlan.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from neo4j import Driver, GraphDatabase

from worker.graph.graph_topology_planner import (
    GraphTopologyPlan,
    build_alias_lookup,
    plan_graph_topology,
    resolve_entity_id,
)

load_dotenv()


def connect() -> Driver:
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    return GraphDatabase.driver(uri, auth=(username, password))


def run_validations(
    canonical_json_path: Path = Path("output/extractions/final_canonical_case_extractions.json"),
    topology_plan_path: Optional[Path] = None,
    db_name: Optional[str] = None,
) -> bool:
    """
    Dynamically validate the Neo4j graph against the active case's canonical JSON
    and GraphTopologyPlan.
    """
    if not canonical_json_path.exists():
        print(f"[Validator Error] Canonical JSON not found: {canonical_json_path}")
        return False

    canon_data = json.loads(canonical_json_path.read_text(encoding="utf-8"))
    case_id = canon_data.get("case_id", "UNKNOWN")
    extractions: List[Dict[str, Any]] = canon_data.get("extractions", [])

    # Load or generate topology plan
    plan: GraphTopologyPlan
    if topology_plan_path and topology_plan_path.exists():
        raw_plan = json.loads(topology_plan_path.read_text(encoding="utf-8"))
        plan = GraphTopologyPlan(**raw_plan)
    else:
        latest_plan_path = canonical_json_path.parent / "graph_topology_plan.json"
        if latest_plan_path.exists():
            raw_plan = json.loads(latest_plan_path.read_text(encoding="utf-8"))
            plan = GraphTopologyPlan(**raw_plan)
        else:
            plan = plan_graph_topology(canonical_json_path)

    alias_lookup = build_alias_lookup(plan)

    driver = connect()
    db = db_name or os.getenv("NEO4J_DATABASE", "neo4j")
    all_passed = True

    print("\n============================================================")
    print(f"RUNNING DYNAMIC GRAPH VALIDATION SUITE FOR CASE: {case_id}")
    print(f"Dispute Reason: {plan.canonical_reason}")
    print(f"============================================================\n")

    with driver.session(database=db) as s:
        # -----------------------------------------------------------------
        # V1: Case Anchor & DisputeReason Verification
        # -----------------------------------------------------------------
        print("[+] [V1] Checking Case Anchor & DisputeReason...")
        res1 = s.run(
            """
            MATCH (c:Case {case_id: $cid})-[:HAS_DISPUTE_REASON]->(dr:DisputeReason)
            RETURN c.case_id AS case_id, dr.reason_code AS code, dr.canonical_reason AS canon_reason
            """,
            {"cid": case_id},
        ).single()

        if res1 and res1["case_id"] == case_id:
            print(f"  [PASS] Case anchor '{case_id}' linked to DisputeReason '{res1['code']}' (Canonical: {res1['canon_reason']}).")
        else:
            all_passed = False
            print(f"  [FAIL] Case anchor or DisputeReason missing for case '{case_id}'")

        # -----------------------------------------------------------------
        # V2: Dynamic Case Hubs Verification (from Topology Plan)
        # -----------------------------------------------------------------
        print("\n[+] [V2] Checking Case Hubs from Topology Plan...")
        missing_hubs = []
        for hub in plan.case_hubs:
            hub_label = hub.hub_label
            canon_id = hub.canonical_id
            cypher_check = f"""
                MATCH (ent:Entity:{hub_label} {{entity_id: $eid, case_id: $cid}})
                RETURN count(ent) AS cnt
            """
            r = s.run(cypher_check, {"eid": canon_id, "cid": case_id}).single()
            cnt = r["cnt"] if r else 0
            if cnt >= 1:
                print(f"  [PASS] Hub ({hub_label}) '{canon_id}' instantiated in Neo4j.")
            else:
                missing_hubs.append(f"({hub_label}) {canon_id}")
                all_passed = False
                print(f"  [FAIL] Hub ({hub_label}) '{canon_id}' missing in Neo4j.")

        if not missing_hubs:
            print(f"  [Summary] All {len(plan.case_hubs)} case hubs successfully verified.")

        # -----------------------------------------------------------------
        # V3: Domain Bridges Verification (from Topology Plan)
        # -----------------------------------------------------------------
        print("\n[+] [V3] Checking Domain Bridges from Topology Plan...")
        if not plan.domain_bridges:
            print("  [INFO] No domain bridges declared in topology plan for this case.")
        else:
            for bridge in plan.domain_bridges:
                src_id = resolve_entity_id(bridge.source_canonical_id, alias_lookup)
                tgt_id = resolve_entity_id(bridge.target_canonical_id, alias_lookup)
                rel_type = bridge.relationship_type

                cypher_bridge = f"""
                    MATCH (src:Entity {{entity_id: $src_id, case_id: $cid}})-[r:{rel_type}]->(tgt:Entity {{entity_id: $tgt_id, case_id: $cid}})
                    RETURN count(r) AS bridge_count
                """
                res3 = s.run(cypher_bridge, {"src_id": src_id, "tgt_id": tgt_id, "cid": case_id}).single()
                b_count = res3["bridge_count"] if res3 else 0
                if b_count >= 1:
                    print(f"  [PASS] Domain bridge ({src_id})-[:{rel_type}]->({tgt_id}) exists ({b_count} link).")
                else:
                    all_passed = False
                    print(f"  [FAIL] Domain bridge ({src_id})-[:{rel_type}]->({tgt_id}) NOT found in Neo4j.")

        # -----------------------------------------------------------------
        # V4: Dynamic Assertion Counts per Party
        # -----------------------------------------------------------------
        print("\n[+] [V4] Checking Assertion counts against canonical JSON...")
        expected_counts: Dict[str, int] = {}
        for env in extractions:
            owner = env.get("meta", {}).get("owner", "cardholder")
            num_ast = len(env.get("extraction", {}).get("assertions", []))
            expected_counts[owner] = expected_counts.get(owner, 0) + num_ast

        res4 = list(s.run(
            """
            MATCH (e:Evidence {case_id: $cid})-[:STATES]->(a:Assertion)
            RETURN e.owner AS owner, count(a) AS assertion_count
            ORDER BY owner
            """,
            {"cid": case_id},
        ))
        actual_counts = {r["owner"]: r["assertion_count"] for r in res4}

        for owner, exp_cnt in expected_counts.items():
            act_cnt = actual_counts.get(owner, 0)
            if act_cnt == exp_cnt:
                print(f"  [PASS] {owner.capitalize()} assertions: {act_cnt} (matches canonical JSON: {exp_cnt}).")
            else:
                all_passed = False
                print(f"  [FAIL] {owner.capitalize()} assertions: actual={act_cnt}, expected={exp_cnt}")

        # -----------------------------------------------------------------
        # V5: Multi-Party Reachability from Primary Case Hub
        # -----------------------------------------------------------------
        print("\n[+] [V5] Testing Multi-Party reachability from Primary Hubs...")
        primary_hub_id = None
        for hub in plan.case_hubs:
            if hub.hub_label in ("Order", "Tracking", "OrderedItem"):
                primary_hub_id = hub.canonical_id
                break

        if primary_hub_id:
            res5 = list(s.run(
                """
                MATCH (h:Entity {entity_id: $hid, case_id: $cid})
                MATCH path = (h)-[*1..3]-(n)
                WHERE n:Assertion OR n:FactNode OR n:Evidence OR n:Party
                RETURN DISTINCT COALESCE(n.owner, n.role, 'case') AS party
                """,
                {"hid": primary_hub_id, "cid": case_id},
            ))
            reachable_parties = set(r["party"] for r in res5)
            print(f"  Primary Hub '{primary_hub_id}' reachable parties: {sorted(list(reachable_parties))}")
            if "cardholder" in reachable_parties and "merchant" in reachable_parties:
                print(f"  [PASS] Multi-hop traversal from '{primary_hub_id}' connects BOTH cardholder and merchant.")
            else:
                print(f"  [WARN] Parties reachable from '{primary_hub_id}': {reachable_parties}")
        else:
            print("  [INFO] No primary hub identified for multi-party reachability test.")

        # -----------------------------------------------------------------
        # V6: Conditional Merchant Policy FactNode Verification
        # -----------------------------------------------------------------
        policy_envelopes = [e for e in extractions if e.get("meta", {}).get("evidence_type") == "MERCHANT_POLICY"]
        if policy_envelopes:
            print("\n[+] [V6] Checking Merchant Policy FactNodes & [:APPLIES_TO] links...")
            expected_clauses = sum(len(e.get("payload", {}).get("clauses", [])) for e in policy_envelopes)
            res6 = s.run(
                """
                MATCH (c:Case {case_id: $cid})-[:HAS_DISPUTE_REASON]->(dr:DisputeReason)
                      <-[:APPLIES_TO]-(f:FactNode {fact_type: 'policy_rule'})
                RETURN count(f) AS clause_count
                """,
                {"cid": case_id},
            ).single()
            act_clauses = res6["clause_count"] if res6 else 0
            if act_clauses == expected_clauses and act_clauses > 0:
                print(f"  [PASS] All {act_clauses} policy clauses linked to DisputeReason.")
            else:
                all_passed = False
                print(f"  [FAIL] Policy clauses: actual={act_clauses}, expected={expected_clauses}")
        else:
            print("\n[+] [V6] Merchant Policy: Not required for this dispute category (Skipped).")

        # -----------------------------------------------------------------
        # V7: Conditional Structured FactNodes Verification (Messages & QC Logs)
        # -----------------------------------------------------------------
        comm_envelopes = [e for e in extractions if e.get("meta", {}).get("evidence_type") == "COMMUNICATION_LOG"]
        qc_envelopes = [e for e in extractions if e.get("meta", {}).get("evidence_type") == "ORDER_STATUS_REPORT"]

        if comm_envelopes or qc_envelopes:
            print("\n[+] [V7] Checking Structured FactNodes (Communication / QC Logs)...")
            if comm_envelopes:
                exp_msgs = sum(len(e.get("payload", {}).get("messages", [])) for e in comm_envelopes)
                res7_msg = s.run(
                    """
                    MATCH (e:Evidence {case_id: $cid})-[:INCLUDES]->(f:FactNode {fact_type: 'message'})
                    RETURN count(f) AS msg_count
                    """,
                    {"cid": case_id},
                ).single()
                act_msgs = res7_msg["msg_count"] if res7_msg else 0
                if act_msgs == exp_msgs:
                    print(f"  [PASS] Communication Messages: {act_msgs}/{exp_msgs} verified.")
                else:
                    all_passed = False
                    print(f"  [FAIL] Communication Messages: actual={act_msgs}, expected={exp_msgs}")

            if qc_envelopes:
                res7_qc = s.run(
                    """
                    MATCH (e:Evidence {case_id: $cid})-[:INCLUDES]->(f:FactNode {fact_type: 'inspection_record'})
                    RETURN count(f) AS qc_count
                    """,
                    {"cid": case_id},
                ).single()
                act_qc = res7_qc["qc_count"] if res7_qc else 0
                if act_qc == len(qc_envelopes):
                    print(f"  [PASS] QC Inspection Records: {act_qc}/{len(qc_envelopes)} verified.")
                else:
                    all_passed = False
                    print(f"  [FAIL] QC Inspection Records: actual={act_qc}, expected={len(qc_envelopes)}")
        else:
            print("\n[+] [V7] Structured FactNodes: None required for this category (Skipped).")

    print("\n============================================================")
    if all_passed:
        print("ALL DYNAMIC GRAPH VALIDATION CHECKS PASSED PERFECTLY!")
    else:
        print("ONE OR MORE GRAPH VALIDATION CHECKS FAILED.")
    print("============================================================\n")

    driver.close()
    return all_passed


if __name__ == "__main__":
    run_validations()
