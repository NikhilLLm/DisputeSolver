"""
Universal Anti-Corruption Knowledge Graph Builder — Neo4j.

Implements dynamic, 5-layer graph building logic driven by the Graph Topology Planner:
1. Layer 1: Case Anchor, Dynamic DisputeReason & Case-Bound Entity Hubs
   - Driven by `GraphTopologyPlan.case_hubs` (Order, Tracking, OrderedItem, ReceivedItem, Merchant, etc.)
2. Layer 2: Provenance Layer -> (c)-[:HAS_PARTY]->(p:Party)-[:SUBMITTED]->(s:Submission)
3. Layer 3: Evidence Envelope -> (s)-[:HAS_EVIDENCE]->(e:Evidence)
4. Layer 4: Assertions & FactNodes ->
     - (e)-[:STATES]->(a:Assertion)-[:ABOUT]->(EntityHub) (Directly ingested from canonical JSON)
     - (e)-[:INCLUDES]->(f:FactNode) (Handlers for all 12 evidence schemas)
5. Layer 5: Dynamic Domain Bridges -> (src:Entity)-[:RELATIONSHIP]->(tgt:Entity)
   - Driven by `GraphTopologyPlan.domain_bridges` (EXPECTS_ITEM, HAS_SHIPMENT, RECEIVED_AS, etc.)
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from neo4j import Driver, GraphDatabase

from worker.graph.graph_schema import CONSTRAINTS, DOMAIN_BRIDGE_VOCABULARY
from worker.graph.graph_topology_planner import (
    GraphTopologyPlan,
    build_alias_lookup,
    plan_graph_topology,
    resolve_entity_id,
)

load_dotenv()


def _q(session, cypher: str, params: Dict[str, Any] | None = None):
    """Run Cypher query with parameters."""
    return session.run(cypher, params or {})


def connect() -> Driver:
    """Connect to Neo4j database using environment variables."""
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    username = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")
    driver = GraphDatabase.driver(uri, auth=(username, password))
    driver.verify_connectivity()
    print(f"[Graph] Connected to Neo4j -> {uri}")
    return driver


def wipe_graph(driver: Driver, db: str) -> None:
    """Wipe existing graph database for a clean rebuild."""
    with driver.session(database=db) as s:
        s.run("MATCH (n) DETACH DELETE n")
    print("[Graph] Database wiped cleanly.")


def apply_constraints(driver: Driver, db: str) -> None:
    """Apply Neo4j uniqueness and schema constraints."""
    with driver.session(database=db) as s:
        for stmt in CONSTRAINTS:
            try:
                s.run(stmt)
            except Exception as ex:
                print(f"[Graph] Constraint warning ({stmt[:40]}...): {ex}")
    print(f"[Graph] Applied schema constraints.")


def build_5layer_graph(
    canonical_json_path: Path = Path("output/extractions/final_canonical_case_extractions.json"),
    topology_plan: Optional[GraphTopologyPlan] = None,
    db_name: Optional[str] = None,
) -> GraphTopologyPlan:
    """
    Build Neo4j Knowledge Graph using the Dynamic Anti-Corruption 5-Layer Logic.

    If topology_plan is not provided, it will be automatically computed and persisted.
    """
    if not canonical_json_path.exists():
        raise FileNotFoundError(f"Canonical JSON file not found at: {canonical_json_path}")

    canon_data = json.loads(canonical_json_path.read_text(encoding="utf-8"))
    case_id = canon_data.get("case_id", "UNKNOWN")
    extractions: List[Dict[str, Any]] = canon_data.get("extractions", [])

    # Step 0: Plan or load topology
    if topology_plan is None:
        topology_plan = plan_graph_topology(canonical_json_path)

    alias_lookup = build_alias_lookup(topology_plan)

    driver = connect()
    db = db_name or os.getenv("NEO4J_DATABASE", "neo4j")

    print("\n-- Wiping previous graph... --")
    wipe_graph(driver, db)
    apply_constraints(driver, db)

    with driver.session(database=db) as session:
        # ---------------------------------------------------------------------
        # Layer 1a: Case Anchor & Dynamic DisputeReason
        # ---------------------------------------------------------------------
        print("\n-- Layer 1a: Case Anchor & DisputeReason --------------------")
        _q(
            session,
            """
            MERGE (c:Case {case_id: $case_id})
            ON CREATE SET c.generated_at = $gen_at
            """,
            {"case_id": case_id, "gen_at": canon_data.get("generated_at")},
        )
        print(f"  [Case Anchor] Created/Merged (c:Case {{case_id: '{case_id}'}})")

        # Dynamically determine dispute reason
        canon_reason = topology_plan.canonical_reason or "UNKNOWN"
        reason_code = "UNKNOWN"
        dispute_category = canon_reason

        for env in extractions:
            p = env.get("payload", {})
            if p.get("dispute_reason"):
                dispute_category = str(p["dispute_reason"])
                if p.get("dispute_reason") in ("13.1", "13.3", "10.4", "12.1", "13.2", "13.6"):
                    reason_code = str(p["dispute_reason"])
                elif "13.1" in dispute_category or "Not Received" in dispute_category:
                    reason_code = "13.1"
                elif "13.3" in dispute_category or "Not as Described" in dispute_category:
                    reason_code = "13.3"
                elif "10.4" in dispute_category or "Fraud" in dispute_category:
                    reason_code = "10.4"
                elif "12.1" in dispute_category or "Duplicate" in dispute_category:
                    reason_code = "12.1"
                elif "13.2" in dispute_category or "Recurring" in dispute_category or "Subscription" in dispute_category:
                    reason_code = "13.2"
                elif "13.6" in dispute_category or "Credit" in dispute_category:
                    reason_code = "13.6"
            if p.get("canonical_dispute_reason"):
                canon_reason = p["canonical_dispute_reason"]

        if reason_code == "UNKNOWN":
            reason_code = dispute_category

        _q(
            session,
            """
            MATCH (c:Case {case_id: $cid})
            MERGE (dr:DisputeReason {reason_code: $code, case_id: $cid})
            ON CREATE SET dr.category = $cat,
                          dr.canonical_reason = $canon_reason,
                          dr.network = 'Visa'
            MERGE (c)-[:HAS_DISPUTE_REASON]->(dr)
            """,
            {
                "cid": case_id,
                "code": reason_code,
                "cat": dispute_category,
                "canon_reason": canon_reason,
            },
        )
        print(f"  [DisputeReason] Merged code={reason_code} ({dispute_category}) [Canonical: {canon_reason}]")

        # ---------------------------------------------------------------------
        # Layer 1b: Dynamic Case-Bound Entity Hubs (from Topology Plan)
        # ---------------------------------------------------------------------
        print("\n-- Layer 1b: Case-Bound Entity Hubs (from Topology Plan) ---")
        for hub in topology_plan.case_hubs:
            hub_label = hub.hub_label
            canon_id = hub.canonical_id
            disp_name = hub.display_name

            # Dynamic node creation using sanitized label
            cypher_hub = f"""
            MATCH (c:Case {{case_id: $cid}})
            MERGE (ent:Entity:{hub_label} {{entity_id: $eid, case_id: $cid}})
            ON CREATE SET ent.name = $name,
                          ent.entity_type = $htype,
                          ent.display_name = $disp_name
            MERGE (c)-[:HAS_ENTITY]->(ent)
            """
            _q(session, cypher_hub, {
                "cid": case_id,
                "eid": canon_id,
                "name": disp_name,
                "htype": hub_label,
                "disp_name": disp_name,
            })

            # Add explicit helper relationships for standard hub types
            if hub_label == "Order":
                _q(session, """
                MATCH (c:Case {case_id: $cid}), (o:Entity:Order {entity_id: $eid, case_id: $cid})
                MERGE (c)-[:HAS_ORDER]->(o)
                """, {"cid": case_id, "eid": canon_id})
            elif hub_label == "Merchant":
                _q(session, """
                MATCH (c:Case {case_id: $cid}), (m:Entity:Merchant {entity_id: $eid, case_id: $cid})
                MERGE (c)-[:HAS_MERCHANT]->(m)
                """, {"cid": case_id, "eid": canon_id})
            elif hub_label == "Customer":
                _q(session, """
                MATCH (c:Case {case_id: $cid}), (cust:Entity:Customer {entity_id: $eid, case_id: $cid})
                MERGE (c)-[:HAS_CUSTOMER]->(cust)
                """, {"cid": case_id, "eid": canon_id})
            elif hub_label == "Tracking":
                _q(session, """
                MATCH (c:Case {case_id: $cid}), (t:Entity:Tracking {entity_id: $eid, case_id: $cid})
                MERGE (c)-[:HAS_TRACKING]->(t)
                """, {"cid": case_id, "eid": canon_id})
            elif hub_label in ("PoliceReport", "Report"):
                _q(session, """
                MATCH (c:Case {case_id: $cid}), (rep:Entity {entity_id: $eid, case_id: $cid})
                MERGE (c)-[:HAS_POLICE_REPORT]->(rep)
                """, {"cid": case_id, "eid": canon_id})
            elif hub_label == "Device":
                _q(session, """
                MATCH (c:Case {case_id: $cid}), (dev:Entity:Device {entity_id: $eid, case_id: $cid})
                MERGE (c)-[:HAS_DEVICE]->(dev)
                """, {"cid": case_id, "eid": canon_id})
            elif hub_label == "UserAccount":
                _q(session, """
                MATCH (c:Case {case_id: $cid}), (acc:Entity:UserAccount {entity_id: $eid, case_id: $cid})
                MERGE (c)-[:HAS_ACCOUNT]->(acc)
                """, {"cid": case_id, "eid": canon_id})
            elif hub_label == "Subscription":
                _q(session, """
                MATCH (c:Case {case_id: $cid}), (sub:Entity:Subscription {entity_id: $eid, case_id: $cid})
                MERGE (c)-[:HAS_SUBSCRIPTION]->(sub)
                """, {"cid": case_id, "eid": canon_id})

            print(f"  [Entity:{hub_label}] Merged entity_id='{canon_id}' ({disp_name})")

        # Find primary hubs for contextual fallbacks
        primary_order_id = next((h.canonical_id for h in topology_plan.case_hubs if h.hub_label == "Order"), None)
        primary_tracking_num = next((h.canonical_id for h in topology_plan.case_hubs if h.hub_label == "Tracking"), None)
        primary_ordered_item = next((h.canonical_id for h in topology_plan.case_hubs if h.hub_label == "OrderedItem"), None)
        primary_received_item = next((h.canonical_id for h in topology_plan.case_hubs if h.hub_label == "ReceivedItem"), None)

        # ---------------------------------------------------------------------
        # Layers 2-4: Submissions, Evidence Envelopes, Direct Assertions & Facts
        # ---------------------------------------------------------------------
        print("\n-- Layers 2-4: Submissions, Evidence Envelopes, Assertions & Facts ---")
        for env_idx, env in enumerate(extractions, 1):
            meta = env.get("meta", {})
            payload = env.get("payload", {})
            extraction = env.get("extraction", {})

            doc_id = meta.get("document_id", f"doc-{env_idx}")
            file_name = meta.get("file_name", "unknown")
            owner = meta.get("owner", "cardholder")
            ev_type = meta.get("evidence_type", "PURCHASE_RECORD")
            extracted_at = meta.get("extracted_at")
            confidence = meta.get("confidence", 0.95)
            processed_by = meta.get("processed_by", "system")

            print(f"\n  [{env_idx}/{len(extractions)}] {owner.upper()} Submission: {doc_id} ({file_name})")

            # Layer 2: Party & Submission Provenance Chain
            _q(
                session,
                """
                MATCH (c:Case {case_id: $cid})
                MERGE (p:Party {name: $owner, case_id: $cid})
                SET p.role = $owner
                MERGE (c)-[:HAS_PARTY]->(p)
                """,
                {"owner": owner, "cid": case_id},
            )

            _q(
                session,
                """
                MATCH (p:Party {name: $owner, case_id: $cid})
                MERGE (s:Submission {document_id: $doc_id})
                ON CREATE SET s.file_name     = $file_name,
                              s.evidence_type = $ev_type,
                              s.extracted_at  = $extracted_at,
                              s.confidence    = $confidence,
                              s.processed_by  = $processed_by,
                              s.owner         = $owner,
                              s.case_id       = $cid
                MERGE (p)-[:SUBMITTED]->(s)
                """,
                {
                    "doc_id": doc_id,
                    "file_name": file_name,
                    "ev_type": ev_type,
                    "extracted_at": extracted_at,
                    "confidence": confidence,
                    "processed_by": processed_by,
                    "owner": owner,
                    "cid": case_id,
                },
            )

            # Layer 3: Evidence Envelope Anchor
            evidence_id = f"ev-{doc_id}"
            _q(
                session,
                """
                MATCH (s:Submission {document_id: $doc_id})
                MERGE (e:Evidence {evidence_id: $eid})
                ON CREATE SET e.evidence_type = $ev_type,
                              e.file_name     = $file_name,
                              e.owner         = $owner,
                              e.case_id       = $cid
                MERGE (s)-[:HAS_EVIDENCE]->(e)
                """,
                {
                    "doc_id": doc_id,
                    "eid": evidence_id,
                    "ev_type": ev_type,
                    "file_name": file_name,
                    "owner": owner,
                    "cid": case_id,
                },
            )

            # Evidence-to-Hub Linkage: Apply EvidenceWirings from topology plan
            for wiring in topology_plan.evidence_wirings:
                if wiring.document_id == doc_id or wiring.document_id in doc_id or doc_id in wiring.document_id:
                    target_id = resolve_entity_id(wiring.target_canonical_id, alias_lookup)
                    _q(
                        session,
                        """
                        MATCH (e:Evidence {evidence_id: $eid})
                        MATCH (ent:Entity {entity_id: $tid, case_id: $cid})
                        MERGE (e)-[:ABOUT]->(ent)
                        """,
                        {"eid": evidence_id, "tid": target_id, "cid": case_id},
                    )

            # Layer 4a: Direct Assertion Ingestion from Canonical JSON
            raw_assertions = extraction.get("assertions", [])
            print(f"     -> Ingesting {len(raw_assertions)} Assertion(s) directly from canonical JSON")

            for a_idx, a_item in enumerate(raw_assertions, 1):
                raw_aid = a_item.get("claim_id") or f"ast-{doc_id}-{a_idx}"
                aid = f"ast-{doc_id}-{raw_aid}" if not str(raw_aid).startswith("ast-") else str(raw_aid)
                atext = a_item.get("assertion_text") or a_item.get("text", "")
                raw_subject = a_item.get("subject_entity") or a_item.get("subject", "case")

                # Resolve subject entity through alias map
                canonical_subject = resolve_entity_id(str(raw_subject), alias_lookup)

                # Extract numeric days if present
                avd = a_item.get("asserted_value_days")
                if avd is None and atext:
                    d_match = re.search(r"(\d+)\s*days|within\s*(\d+)\s*days", atext, re.IGNORECASE)
                    if d_match:
                        avd = int(d_match.group(1) or d_match.group(2))

                _q(
                    session,
                    """
                    MATCH (e:Evidence {evidence_id: $eid})
                    MERGE (a:Assertion {assertion_id: $aid})
                    ON CREATE SET a.subject              = $subj,
                                  a.raw_subject          = $raw_subj,
                                  a.canonical_subject    = $canon_subj,
                                  a.text                 = $atext,
                                  a.owner                = $owner,
                                  a.source_file          = $file_name,
                                  a.asserted_value_days  = $avd
                    MERGE (e)-[:STATES]->(a)
                    """,
                    {
                        "eid": evidence_id,
                        "aid": aid,
                        "subj": canonical_subject,
                        "raw_subj": str(raw_subject),
                        "canon_subj": canonical_subject,
                        "atext": atext,
                        "owner": owner,
                        "file_name": file_name,
                        "avd": avd,
                    },
                )

                # Link Assertion -> Entity Hub via [:ABOUT]
                # Try canonical subject first, then fallback hints
                target_hub_id = canonical_subject
                _q(
                    session,
                    """
                    MATCH (a:Assertion {assertion_id: $aid})
                    MATCH (ent:Entity {entity_id: $tid, case_id: $cid})
                    MERGE (a)-[:ABOUT]->(ent)
                    """,
                    {"aid": aid, "tid": target_hub_id, "cid": case_id},
                )

            # Layer 4b: FactNodes for structured payload items
            # 1. Communication Log Messages
            if ev_type == "COMMUNICATION_LOG" and payload.get("messages"):
                channel = payload.get("channel", "email")
                for m_idx, msg in enumerate(payload["messages"], 1):
                    fid = f"fact-{doc_id}-msg-{m_idx}"
                    _q(
                        session,
                        """
                        MATCH (e:Evidence {evidence_id: $eid})
                        MERGE (f:FactNode {fact_id: $fid})
                        ON CREATE SET f.fact_type    = 'message',
                                      f.evidence_type= $ev_type,
                                      f.channel      = $channel,
                                      f.sender       = $sender,
                                      f.recipient    = $recipient,
                                      f.timestamp    = $ts,
                                      f.body         = $body,
                                      f.owner        = $owner
                        MERGE (e)-[:INCLUDES]->(f)
                        """,
                        {
                            "eid": evidence_id,
                            "fid": fid,
                            "ev_type": ev_type,
                            "channel": channel,
                            "sender": msg.get("sender", "unknown"),
                            "recipient": msg.get("recipient", "unknown"),
                            "ts": str(msg.get("timestamp", "")),
                            "body": msg.get("body", ""),
                            "owner": owner,
                        },
                    )
                    if primary_order_id:
                        _q(
                            session,
                            """
                            MATCH (f:FactNode {fact_id: $fid})
                            MATCH (o:Entity:Order {entity_id: $oid, case_id: $cid})
                            MERGE (f)-[:ABOUT]->(o)
                            """,
                            {"fid": fid, "oid": primary_order_id, "cid": case_id},
                        )

            # 2. Purchase Record Items
            elif ev_type == "PURCHASE_RECORD" and payload.get("items"):
                rec_order_id = payload.get("order_id") or primary_order_id
                for item_idx, item in enumerate(payload["items"], 1):
                    fid = f"fact-{doc_id}-item-{item_idx}"
                    item_name = item.get("name", "Item")
                    item_sku = item.get("sku", "")
                    canon_item = resolve_entity_id(item_name, alias_lookup)

                    _q(
                        session,
                        """
                        MATCH (e:Evidence {evidence_id: $eid})
                        MERGE (f:FactNode {fact_id: $fid})
                        ON CREATE SET f.fact_type    = 'purchase_item',
                                      f.evidence_type= $ev_type,
                                      f.item_name    = $name,
                                      f.sku          = $sku,
                                      f.canonical_item = $canon_item,
                                      f.quantity     = $qty,
                                      f.price        = $price,
                                      f.owner        = $owner
                        MERGE (e)-[:INCLUDES]->(f)
                        """,
                        {
                            "eid": evidence_id,
                            "fid": fid,
                            "ev_type": ev_type,
                            "name": item_name,
                            "sku": item_sku,
                            "canon_item": canon_item,
                            "qty": item.get("quantity", 1),
                            "price": item.get("price", 0.0),
                            "owner": owner,
                        },
                    )
                    if rec_order_id:
                        _q(
                            session,
                            """
                            MATCH (f:FactNode {fact_id: $fid})
                            MATCH (o:Entity:Order {entity_id: $oid, case_id: $cid})
                            MERGE (f)-[:ABOUT]->(o)
                            """,
                            {"fid": fid, "oid": rec_order_id, "cid": case_id},
                        )
                    # Wire item fact to OrderedItem hub if present
                    if canon_item:
                        _q(
                            session,
                            """
                            MATCH (f:FactNode {fact_id: $fid})
                            MATCH (i:Entity {entity_id: $cid_item, case_id: $cid})
                            MERGE (f)-[:ABOUT]->(i)
                            """,
                            {"fid": fid, "cid_item": canon_item, "cid": case_id},
                        )

            # 3. Merchant Policy Clauses
            elif ev_type == "MERCHANT_POLICY" and payload.get("clauses"):
                policy_name = payload.get("policy_name")
                for c_idx, clause in enumerate(payload["clauses"], 1):
                    fid = f"fact-{doc_id}-clause-{c_idx}"
                    c_text = clause.get("text", "")
                    c_num = clause.get("clause_id", f"{c_idx}")

                    window_days = None
                    w_match = re.search(r"(\d+)\s*business days|within\s*(\d+)\s*days", c_text, re.IGNORECASE)
                    if w_match:
                        window_days = int(w_match.group(1) or w_match.group(2))

                    _q(
                        session,
                        """
                        MATCH (e:Evidence {evidence_id: $eid})
                        MERGE (f:FactNode {fact_id: $fid})
                        ON CREATE SET f.fact_type    = 'policy_rule',
                                      f.evidence_type= $ev_type,
                                      f.clause_id    = $cnum,
                                      f.text         = $text,
                                      f.policy_name  = $pname,
                                      f.window_days  = $wdays,
                                      f.owner        = $owner
                        MERGE (e)-[:INCLUDES]->(f)
                        """,
                        {
                            "eid": evidence_id,
                            "fid": fid,
                            "ev_type": ev_type,
                            "cnum": c_num,
                            "text": c_text,
                            "pname": policy_name,
                            "wdays": window_days,
                            "owner": owner,
                        },
                    )
                    _q(
                        session,
                        """
                        MATCH (f:FactNode {fact_id: $fid})
                        MATCH (dr:DisputeReason {case_id: $cid})
                        MERGE (f)-[:APPLIES_TO]->(dr)
                        """,
                        {"fid": fid, "cid": case_id},
                    )

            # 4. Tracking Report Events
            elif ev_type == "TRACKING_REPORT" and payload.get("timeline"):
                for tr_idx, te in enumerate(payload["timeline"], 1):
                    fid = f"fact-{doc_id}-track-{tr_idx}"
                    _q(
                        session,
                        """
                        MATCH (e:Evidence {evidence_id: $eid})
                        MERGE (f:FactNode {fact_id: $fid})
                        ON CREATE SET f.fact_type    = 'status_event',
                                      f.evidence_type= $ev_type,
                                      f.status       = $status,
                                      f.timestamp    = $ts,
                                      f.location     = $loc,
                                      f.owner        = $owner
                        MERGE (e)-[:INCLUDES]->(f)
                        """,
                        {
                            "eid": evidence_id,
                            "fid": fid,
                            "ev_type": ev_type,
                            "status": te.get("status", "UPDATE"),
                            "ts": str(te.get("timestamp", "")),
                            "loc": te.get("location"),
                            "owner": owner,
                        },
                    )
                    if primary_tracking_num:
                        _q(
                            session,
                            """
                            MATCH (f:FactNode {fact_id: $fid})
                            MATCH (t:Entity:Tracking {entity_id: $tn, case_id: $cid})
                            MERGE (f)-[:ABOUT]->(t)
                            """,
                            {"fid": fid, "tn": primary_tracking_num, "cid": case_id},
                        )

            # 5. Delivery Proof
            elif ev_type == "DELIVERY_PROOF":
                tn = payload.get("tracking_number") or primary_tracking_num
                fid = f"fact-{doc_id}-delproof"
                _q(
                    session,
                    """
                    MATCH (e:Evidence {evidence_id: $eid})
                    MERGE (f:FactNode {fact_id: $fid})
                    ON CREATE SET f.fact_type          = 'delivery_proof',
                                  f.evidence_type      = $ev_type,
                                  f.delivery_date      = $del_date,
                                  f.tracking_number    = $tn,
                                  f.signature_collected= false,
                                  f.owner              = $owner
                    MERGE (e)-[:INCLUDES]->(f)
                    """,
                    {
                        "eid": evidence_id,
                        "fid": fid,
                        "ev_type": ev_type,
                        "del_date": str(payload.get("delivery_date", "")),
                        "tn": tn,
                        "owner": owner,
                    },
                )
                if tn:
                    _q(
                        session,
                        """
                        MATCH (f:FactNode {fact_id: $fid})
                        MATCH (t:Entity:Tracking {entity_id: $tn, case_id: $cid})
                        MERGE (f)-[:ABOUT]->(t)
                        """,
                        {"fid": fid, "tn": tn, "cid": case_id},
                    )
                # If Delivery Proof is about a received item mismatch (e.g. photo of wrong item)
                if primary_received_item:
                    _q(
                        session,
                        """
                        MATCH (f:FactNode {fact_id: $fid})
                        MATCH (i:Entity {entity_id: $ritem, case_id: $cid})
                        MERGE (f)-[:ABOUT]->(i)
                        """,
                        {"fid": fid, "ritem": primary_received_item, "cid": case_id},
                    )

            # 6. Order Status Report (QC Logs / Packing Records)
            elif ev_type == "ORDER_STATUS_REPORT":
                fid = f"fact-{doc_id}-qc"
                insp_id = payload.get("inspection_id")
                notes = payload.get("notes", "")
                _q(
                    session,
                    """
                    MATCH (e:Evidence {evidence_id: $eid})
                    MERGE (f:FactNode {fact_id: $fid})
                    ON CREATE SET f.fact_type     = 'inspection_record',
                                  f.evidence_type = $ev_type,
                                  f.inspection_id = $insp_id,
                                  f.notes         = $notes,
                                  f.owner         = $owner
                    MERGE (e)-[:INCLUDES]->(f)
                    """,
                    {
                        "eid": evidence_id,
                        "fid": fid,
                        "ev_type": ev_type,
                        "insp_id": insp_id,
                        "notes": notes,
                        "owner": owner,
                    },
                )
                if primary_order_id:
                    _q(
                        session,
                        """
                        MATCH (f:FactNode {fact_id: $fid})
                        MATCH (o:Entity:Order {entity_id: $oid, case_id: $cid})
                        MERGE (f)-[:ABOUT]->(o)
                        """,
                        {"fid": fid, "oid": primary_order_id, "cid": case_id},
                    )
                if primary_ordered_item:
                    _q(
                        session,
                        """
                        MATCH (f:FactNode {fact_id: $fid})
                        MATCH (i:Entity {entity_id: $oitem, case_id: $cid})
                        MERGE (f)-[:ABOUT]->(i)
                        """,
                        {"fid": fid, "oitem": primary_ordered_item, "cid": case_id},
                    )

            # 7. Police Report (Fraud / Theft cases)
            elif ev_type == "POLICE_REPORT":
                fid = f"fact-{doc_id}-police"
                rep_num = payload.get("report_number")
                precinct = payload.get("precinct")
                _q(
                    session,
                    """
                    MATCH (e:Evidence {evidence_id: $eid})
                    MERGE (f:FactNode {fact_id: $fid})
                    ON CREATE SET f.fact_type     = 'police_report_record',
                                  f.evidence_type = $ev_type,
                                  f.report_number = $rep_num,
                                  f.precinct      = $precinct,
                                  f.owner         = $owner
                    MERGE (e)-[:INCLUDES]->(f)
                    """,
                    {
                        "eid": evidence_id,
                        "fid": fid,
                        "ev_type": ev_type,
                        "rep_num": rep_num,
                        "precinct": precinct,
                        "owner": owner,
                    },
                )

            # 8. Usage Log (Subscription / Streaming / Login Events)
            elif ev_type == "USAGE_LOG":
                events = payload.get("events") or [payload] if payload else []
                for u_idx, u_evt in enumerate(events, 1):
                    fid = f"fact-{doc_id}-usage-{u_idx}"
                    _q(
                        session,
                        """
                        MATCH (e:Evidence {evidence_id: $eid})
                        MERGE (f:FactNode {fact_id: $fid})
                        ON CREATE SET f.fact_type         = 'usage_event',
                                      f.evidence_type     = $ev_type,
                                      f.session_id        = $sess_id,
                                      f.ip_address        = $ip,
                                      f.timestamp         = $ts,
                                      f.duration_minutes  = $dur,
                                      f.action            = $act,
                                      f.owner             = $owner
                        MERGE (e)-[:INCLUDES]->(f)
                        """,
                        {
                            "eid": evidence_id,
                            "fid": fid,
                            "ev_type": ev_type,
                            "sess_id": str(u_evt.get("session_id", "")),
                            "ip": str(u_evt.get("ip_address", "")),
                            "ts": str(u_evt.get("timestamp", "")),
                            "dur": u_evt.get("duration_minutes") or u_evt.get("duration"),
                            "act": str(u_evt.get("action") or u_evt.get("activity", "")),
                            "owner": owner,
                        },
                    )

            # 9. Processor Log (Authorization / Refund / Security Checks)
            elif ev_type == "PROCESSOR_LOG":
                fid = f"fact-{doc_id}-proc"
                _q(
                    session,
                    """
                    MATCH (e:Evidence {evidence_id: $eid})
                    MERGE (f:FactNode {fact_id: $fid})
                    ON CREATE SET f.fact_type      = 'processor_record',
                                  f.evidence_type  = $ev_type,
                                  f.arn            = $arn,
                                  f.auth_code      = $acode,
                                  f.avs_result     = $avs,
                                  f.cvv_result     = $cvv,
                                  f.risk_score     = $risk,
                                  f.three_ds_status= $tds,
                                  f.payment_status = $pstatus,
                                  f.owner          = $owner
                    MERGE (e)-[:INCLUDES]->(f)
                    """,
                    {
                        "eid": evidence_id,
                        "fid": fid,
                        "ev_type": ev_type,
                        "arn": str(payload.get("arn", "")),
                        "acode": str(payload.get("auth_code", "")),
                        "avs": str(payload.get("avs_result", "")),
                        "cvv": str(payload.get("cvv_result", "")),
                        "risk": payload.get("risk_score") or payload.get("fraud_score"),
                        "tds": str(payload.get("three_ds_status") or payload.get("3ds_status", "")),
                        "pstatus": str(payload.get("payment_status", "")),
                        "owner": owner,
                    },
                )

            # 10. Account / Bank Statement
            elif ev_type == "ACCOUNT_STATEMENT":
                txns = payload.get("transactions") or [payload] if payload else []
                for t_idx, txn in enumerate(txns, 1):
                    fid = f"fact-{doc_id}-stmt-{t_idx}"
                    _q(
                        session,
                        """
                        MATCH (e:Evidence {evidence_id: $eid})
                        MERGE (f:FactNode {fact_id: $fid})
                        ON CREATE SET f.fact_type      = 'account_event',
                                      f.evidence_type  = $ev_type,
                                      f.transaction_id = $txid,
                                      f.posting_date   = $pdate,
                                      f.amount         = $amt,
                                      f.description    = $desc,
                                      f.owner          = $owner
                        MERGE (e)-[:INCLUDES]->(f)
                        """,
                        {
                            "eid": evidence_id,
                            "fid": fid,
                            "ev_type": ev_type,
                            "txid": str(txn.get("transaction_id", "")),
                            "pdate": str(txn.get("posting_date") or txn.get("date", "")),
                            "amt": txn.get("amount"),
                            "desc": str(txn.get("description", "")),
                            "owner": owner,
                        },
                    )

            # 11. Transaction Comparison
            elif ev_type == "TRANSACTION_COMPARISON":
                fid = f"fact-{doc_id}-comparison"
                _q(
                    session,
                    """
                    MATCH (e:Evidence {evidence_id: $eid})
                    MERGE (f:FactNode {fact_id: $fid})
                    ON CREATE SET f.fact_type              = 'transaction_record',
                                  f.evidence_type          = $ev_type,
                                  f.session_a_id           = $sa,
                                  f.session_b_id           = $sb,
                                  f.ip_match               = $ipm,
                                  f.card_hash_match        = $chm,
                                  f.time_difference_seconds= $tdiff,
                                  f.owner                  = $owner
                    MERGE (e)-[:INCLUDES]->(f)
                    """,
                    {
                        "eid": evidence_id,
                        "fid": fid,
                        "ev_type": ev_type,
                        "sa": str(payload.get("session_a_id", "")),
                        "sb": str(payload.get("session_b_id", "")),
                        "ipm": payload.get("ip_match", False),
                        "chm": payload.get("card_hash_match", False),
                        "tdiff": payload.get("time_difference_seconds"),
                        "owner": owner,
                    },
                )

        # ---------------------------------------------------------------------
        # Layer 5: Dynamic Domain Bridges (from Topology Plan)
        # ---------------------------------------------------------------------
        print("\n-- Layer 5: Domain Relationship Bridges (from Topology Plan) --")
        for bridge in topology_plan.domain_bridges:
            src_id = resolve_entity_id(bridge.source_canonical_id, alias_lookup)
            tgt_id = resolve_entity_id(bridge.target_canonical_id, alias_lookup)
            rel_type = bridge.relationship_type

            if rel_type not in DOMAIN_BRIDGE_VOCABULARY:
                print(f"  [Warning] Skipping unrecognized bridge relation '{rel_type}'")
                continue

            cypher_bridge = f"""
            MATCH (src:Entity {{entity_id: $src_id, case_id: $cid}})
            MATCH (tgt:Entity {{entity_id: $tgt_id, case_id: $cid}})
            MERGE (src)-[r:{rel_type}]->(tgt)
            """
            _q(session, cypher_bridge, {
                "src_id": src_id,
                "tgt_id": tgt_id,
                "cid": case_id,
            })
            print(f"  [Domain Bridge] Merged ({src_id})-[:{rel_type}]->({tgt_id})")

        print(f"\n============================================================")
        print(f"[Graph Builder] Anti-Corruption Graph construction complete for Case {case_id}!")
        print(f"============================================================")

    driver.close()
    return topology_plan


if __name__ == "__main__":
    build_5layer_graph()
