"""
Graph Retrieval Module.

Provides a reusable context retrieval layer that fetches a bounded
reasoning context from Neo4j, parameterized by case_id and dispute_reason.

Avoids repeated independent deep traversals -- a single call returns
all parties, evidence, assertions, facts, policies, and relationships
needed for reasoning.
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
    dispute_reason_config: Dict[str, Any],
    db_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieve a bounded reasoning context for a dispute case.

    Returns a dict containing:
      - case: case-level properties
      - dispute_reason: the DisputeReason node properties
      - parties: list of Party nodes
      - orders: list of Order entity nodes
      - tracking: list of Tracking entity nodes
      - merchants: list of Merchant entity nodes
      - evidence: list of Evidence nodes with owner and type
      - assertions: list of Assertion nodes with provenance
      - facts: list of FactNode nodes with provenance
      - policy_clauses: list of policy_rule FactNodes linked to DisputeReason
      - relationships: list of key relationship tuples
    """
    driver = _connect()
    db = db_name or os.getenv("NEO4J_DATABASE", "neo4j")

    relevant_fact_types = dispute_reason_config.get("relevant_fact_types", [])
    relevant_evidence_types = dispute_reason_config.get("relevant_evidence_types", [])

    context: Dict[str, Any] = {
        "case_id": case_id,
        "case": {},
        "dispute_reason": {},
        "parties": [],
        "orders": [],
        "tracking": [],
        "merchants": [],
        "evidence": [],
        "assertions": [],
        "facts": [],
        "policy_clauses": [],
        "timeline_events": [],
    }

    with driver.session(database=db) as session:

        # -- Case + DisputeReason --------------------------------
        result = session.run(
            """
            MATCH (c:Case {case_id: $cid})-[:HAS_DISPUTE_REASON]->(dr:DisputeReason)
            RETURN c {.case_id, .generated_at} AS case_props,
                   dr {.reason_code, .category, .network, .case_id} AS dr_props
            """,
            {"cid": case_id},
        ).single()

        if result:
            context["case"] = dict(result["case_props"])
            context["dispute_reason"] = dict(result["dr_props"])

        # -- Parties ---------------------------------------------
        for record in session.run(
            """
            MATCH (c:Case {case_id: $cid})-[:HAS_PARTY]->(p:Party)
            RETURN p {.name, .role, .case_id} AS party
            """,
            {"cid": case_id},
        ):
            context["parties"].append(dict(record["party"]))

        # -- Orders ----------------------------------------------
        for record in session.run(
            """
            MATCH (c:Case {case_id: $cid})-[:HAS_ORDER]->(o:Entity:Order)
            RETURN o {.entity_id, .entity_type, .case_id} AS order_node
            """,
            {"cid": case_id},
        ):
            context["orders"].append(dict(record["order_node"]))

        # -- Tracking --------------------------------------------
        for record in session.run(
            """
            MATCH (c:Case {case_id: $cid})-[:HAS_ORDER]->(o:Entity:Order)
                  -[:HAS_SHIPMENT]->(t:Entity:Tracking)
            RETURN t {.entity_id, .entity_type, .case_id} AS tracking_node,
                   o.entity_id AS order_id
            """,
            {"cid": case_id},
        ):
            node = dict(record["tracking_node"])
            node["linked_order"] = record["order_id"]
            context["tracking"].append(node)

        # -- Merchants -------------------------------------------
        for record in session.run(
            """
            MATCH (c:Case {case_id: $cid})-[:HAS_MERCHANT]->(m:Entity:Merchant)
            RETURN m {.entity_id, .name, .case_id} AS merchant_node
            """,
            {"cid": case_id},
        ):
            context["merchants"].append(dict(record["merchant_node"]))

        # -- Evidence envelopes ----------------------------------
        for record in session.run(
            """
            MATCH (c:Case {case_id: $cid})-[:HAS_PARTY]->(p:Party)
                  -[:SUBMITTED]->(s:Submission)-[:HAS_EVIDENCE]->(e:Evidence)
            RETURN e {.evidence_id, .evidence_type, .file_name, .owner, .case_id} AS ev,
                   s {.document_id, .file_name, .confidence, .extracted_at} AS sub
            """,
            {"cid": case_id},
        ):
            ev = dict(record["ev"])
            ev["submission"] = dict(record["sub"])
            context["evidence"].append(ev)

        # -- Assertions (with source evidence provenance) --------
        for record in session.run(
            """
            MATCH (e:Evidence {case_id: $cid})-[:STATES]->(a:Assertion)
            OPTIONAL MATCH (a)-[:ABOUT]->(ent:Entity)
            RETURN a {.assertion_id, .subject, .text, .owner,
                      .source_file, .asserted_value_days} AS assertion,
                   e.evidence_id AS source_evidence_id,
                   e.evidence_type AS source_evidence_type,
                   ent.entity_id AS about_entity
            """,
            {"cid": case_id},
        ):
            ast = dict(record["assertion"])
            ast["source_evidence_id"] = record["source_evidence_id"]
            ast["source_evidence_type"] = record["source_evidence_type"]
            ast["about_entity"] = record["about_entity"]
            context["assertions"].append(ast)

        # -- FactNodes (filtered by relevant types) --------------
        fact_type_filter = relevant_fact_types if relevant_fact_types else []
        for record in session.run(
            """
            MATCH (e:Evidence {case_id: $cid})-[:INCLUDES]->(f:FactNode)
            WHERE size($types) = 0 OR f.fact_type IN $types
            OPTIONAL MATCH (f)-[:ABOUT]->(ent:Entity)
            RETURN f {.*} AS fact,
                   e.evidence_id AS source_evidence_id,
                   e.evidence_type AS source_evidence_type,
                   e.owner AS evidence_owner,
                   ent.entity_id AS about_entity
            """,
            {"cid": case_id, "types": fact_type_filter},
        ):
            fact = dict(record["fact"])
            fact["source_evidence_id"] = record["source_evidence_id"]
            fact["source_evidence_type"] = record["source_evidence_type"]
            fact["evidence_owner"] = record["evidence_owner"]
            fact["about_entity"] = record["about_entity"]
            context["facts"].append(fact)

        # -- Policy clauses (linked to DisputeReason via APPLIES_TO) -
        for record in session.run(
            """
            MATCH (c:Case {case_id: $cid})-[:HAS_DISPUTE_REASON]->(dr:DisputeReason)
                  <-[:APPLIES_TO]-(f:FactNode {fact_type: 'policy_rule'})
            RETURN f {.*} AS clause,
                   dr.reason_code AS applies_to_reason
            """,
            {"cid": case_id},
        ):
            clause = dict(record["clause"])
            clause["applies_to_reason"] = record["applies_to_reason"]
            context["policy_clauses"].append(clause)

        # -- Timeline events (tracking status_event facts) -------
        for record in session.run(
            """
            MATCH (e:Evidence {case_id: $cid})-[:INCLUDES]->(f:FactNode {fact_type: 'status_event'})
            RETURN f {.*} AS event,
                   e.evidence_id AS source_evidence_id
            ORDER BY f.timestamp ASC
            """,
            {"cid": case_id},
        ):
            evt = dict(record["event"])
            evt["source_evidence_id"] = record["source_evidence_id"]
            context["timeline_events"].append(evt)

    driver.close()
    return context
if __name__ == "__main__":
    import json
    from worker.agents.dispute_config import get_dispute_config
    case_id = "DSP-2026-00187"
    
    # 1. Load the dispute configuration for this case type (e.g. ITEM_NOT_RECEIVED)
    config = get_dispute_config("ITEM_NOT_RECEIVED")
    
    # 2. Fetch the bounded reasoning context from Neo4j
    context = fetch_case_reasoning_context(
        case_id=case_id,
        dispute_reason_config=config,
    )
    
    # 3. Print the retrieved graph context
    print(f"--- Context for {case_id} ---")
    print(f"Dispute Reason: {context['dispute_reason']}")
    print(f"Parties ({len(context['parties'])}): {context['parties']}")
    print(f"Evidence Envelopes ({len(context['evidence'])}): {context['evidence']}")
    print(f"Assertions ({len(context['assertions'])}): {context['assertions']}")
    print(f"Facts ({len(context['facts'])}): {context['facts']}")
    print(f"Timeline Events ({len(context['timeline_events'])}): {context['timeline_events']}")