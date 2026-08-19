"""
Graph Retrieval Module — Bounded 2-Query Subgraph Retrieval.

Pulls the entire case context from Neo4j in just 2 parameterized batch queries:
  1. Full Case Subgraph: Case, DisputeReason, Parties, Submissions, Evidence, Assertions, FactNodes, and Entity Hubs.
  2. Domain Bridges: All relationships between case entities (e.g. EXPECTS_ITEM, RECEIVED_AS, HAS_SHIPMENT).

Universal across all 8 dispute categories without rigid label or fact-type filtering.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from neo4j import Driver, GraphDatabase

load_dotenv()


def _connect() -> Driver:
    """Connect to Neo4j using environment variables."""
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    driver = GraphDatabase.driver(uri, auth=(username, password))
    driver.verify_connectivity()
    return driver


def fetch_case_reasoning_context(
    case_id: str,
    dispute_reason_config: Optional[Dict[str, Any]] = None,
    db_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieve the complete case context from Neo4j using 2 efficient batch queries.

    Returns a clean dictionary containing:
      - case_id: case identifier
      - case: case properties
      - dispute_reason: DisputeReason node properties
      - parties: list of Party nodes
      - entities: all Case Hub entity nodes (Order, Merchant, OrderedItem, ReceivedItem, Tracking, Device, etc.)
      - domain_bridges: all structural relationships between entities
      - evidence: evidence envelopes
      - assertions: party assertions with provenance
      - facts: all FactNode nodes (telemetry, QC inspections, messages, etc.)
      - policy_clauses: merchant policy rules
      - timeline_events: status events ordered chronologically
    """
    driver = _connect()
    db = db_name or os.getenv("NEO4J_DATABASE", "neo4j")

    context: Dict[str, Any] = {
        "case_id": case_id,
        "case": {},
        "dispute_reason": {},
        "parties": [],
        "entities": [],
        "domain_bridges": [],
        "evidence": [],
        "assertions": [],
        "facts": [],
        "policy_clauses": [],
        "timeline_events": [],
    }

    with driver.session(database=db) as session:
        # ==========================================================
        # BATCH QUERY 1: Full Case Subgraph
        # ==========================================================
        query_subgraph = """
        MATCH (c:Case {case_id: $cid})
        OPTIONAL MATCH (c)-[:HAS_DISPUTE_REASON]->(dr:DisputeReason)
        OPTIONAL MATCH (c)-[:HAS_PARTY]->(p:Party)
        OPTIONAL MATCH (c)-[:HAS_ENTITY]->(ent:Entity)
        OPTIONAL MATCH (p)-[:SUBMITTED]->(s:Submission)-[:HAS_EVIDENCE]->(e:Evidence)
        OPTIONAL MATCH (e)-[:STATES]->(a:Assertion)
        OPTIONAL MATCH (e)-[:INCLUDES]->(f:FactNode)
        RETURN c {.case_id, .generated_at} AS case_props,
               dr {.reason_code, .category, .network, .case_id} AS dr_props,
               collect(DISTINCT p {.name, .role, .case_id}) AS parties,
               collect(DISTINCT ent {.*, labels: labels(ent)}) AS entities,
               collect(DISTINCT e {.evidence_id, .evidence_type, .file_name, .owner, .case_id}) AS evidence,
               collect(DISTINCT a {.*, source_evidence_id: e.evidence_id, source_evidence_type: e.evidence_type}) AS assertions,
               collect(DISTINCT f {.*, source_evidence_id: e.evidence_id, source_evidence_type: e.evidence_type, evidence_owner: e.owner}) AS facts
        """
        res = session.run(query_subgraph, {"cid": case_id}).single()

        if res:
            if res["case_props"]:
                context["case"] = dict(res["case_props"])
            if res["dr_props"]:
                context["dispute_reason"] = dict(res["dr_props"])
            context["parties"] = [dict(p) for p in res["parties"] if p and p.get("name")]
            context["entities"] = [dict(ent) for ent in res["entities"] if ent and ent.get("entity_id")]
            context["evidence"] = [dict(e) for e in res["evidence"] if e and e.get("evidence_id")]
            context["assertions"] = [dict(a) for a in res["assertions"] if a and a.get("assertion_id")]
            
            # Segregate facts, policy clauses, and timeline events
            raw_facts = [dict(f) for f in res["facts"] if f and f.get("fact_id")]
            for f in raw_facts:
                ft = f.get("fact_type")
                if ft == "policy_rule":
                    context["policy_clauses"].append(f)
                elif ft == "status_event":
                    context["timeline_events"].append(f)
                    context["facts"].append(f)
                else:
                    context["facts"].append(f)

            # Sort timeline events by timestamp
            context["timeline_events"].sort(key=lambda x: str(x.get("timestamp", "")))

        # ==========================================================
        # BATCH QUERY 2: Domain Bridges between Entity Hubs
        # ==========================================================
        query_bridges = """
        MATCH (src:Entity {case_id: $cid})-[r]->(tgt:Entity {case_id: $cid})
        WHERE NOT type(r) IN ['HAS_ENTITY', 'STATES', 'INCLUDES', 'ABOUT']
        RETURN src.entity_id AS source,
               type(r) AS rel_type,
               tgt.entity_id AS target,
               properties(r) AS props
        """
        for record in session.run(query_bridges, {"cid": case_id}):
            context["domain_bridges"].append({
                "source": record["source"],
                "rel_type": record["rel_type"],
                "target": record["target"],
                "properties": dict(record["props"]) if record["props"] else {},
            })

    driver.close()
    return context


if __name__ == "__main__":
    import json
    case = "DSP-2026-00201"
    ctx = fetch_case_reasoning_context(case)
    print(f"--- Bounded Context for {case} ---")
    print(f"Dispute Reason: {ctx['dispute_reason']}")
    print(f"Parties ({len(ctx['parties'])}): {[p['name'] for p in ctx['parties']]}")
    print(f"Entities ({len(ctx['entities'])}): {[e['entity_id'] for e in ctx['entities']]}")
    print(f"Domain Bridges ({len(ctx['domain_bridges'])}): {ctx['domain_bridges']}")
    print(f"Evidence Envelopes ({len(ctx['evidence'])}): {len(ctx['evidence'])}")
    print(f"Assertions ({len(ctx['assertions'])}): {len(ctx['assertions'])}")
    print(f"Facts ({len(ctx['facts'])}): {len(ctx['facts'])}")
    print(f"Policy Clauses ({len(ctx['policy_clauses'])}): {len(ctx['policy_clauses'])}")