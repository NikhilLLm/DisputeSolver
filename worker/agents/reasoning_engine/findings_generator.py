"""
Findings Generator Module.

Converts retrieved graph context into structured findings (F001, F002, etc.),
enriched with evidence source tiers (Tier 1 Telemetry, Tier 2 Communication, Tier 3 Assertion).
"""

from __future__ import annotations

import json
from typing import Any, Dict, List
from worker.agents.reasoning_engine.common import get_source_tier


def generate_findings(
    context: Dict[str, Any],
    config: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Convert retrieved graph context into structured findings.

    Each finding has:
      - finding_id
      - subject (what it's about)
      - statement (human-readable summary)
      - source_evidence (list of evidence IDs)
      - source_nodes (list of node IDs)
      - source_tier (TIER_1_TELEMETRY / TIER_2_COMMUNICATION / TIER_3_ASSERTION)
      - tier_weight (1.0 / 0.7 / 0.35)
      - owner (cardholder / merchant / system)
      - dispute_relevance (HIGH / MEDIUM / LOW)
      - finding_type (assertion / fact / policy / timeline)
      - about_entity (linked entity ID if any)
      - raw_data (original node properties)
    """
    findings: List[Dict[str, Any]] = []
    fid_counter = 0

    def _next_fid() -> str:
        nonlocal fid_counter
        fid_counter += 1
        return f"F{fid_counter:03d}"

    # -- From assertions -------------------------------------
    for ast in context.get("assertions", []):
        subject = ast.get("subject", "unknown")
        relevance = "HIGH" if subject != "unknown" else "LOW"
        ev_type = ast.get("source_evidence_type", "DISPUTE_FORM")
        tier, tier_weight = get_source_tier(ev_type, "assertion")

        findings.append({
            "finding_id": _next_fid(),
            "subject": subject,
            "statement": ast.get("text", ""),
            "source_evidence": [ast.get("source_evidence_id")],
            "source_nodes": [ast.get("assertion_id")],
            "source_tier": tier,
            "tier_weight": tier_weight,
            "owner": ast.get("owner", "unknown"),
            "dispute_relevance": relevance,
            "finding_type": "assertion",
            "about_entity": ast.get("about_entity"),
            "raw_data": ast,
        })

    # -- From facts (status_event, delivery_proof, message, etc.) -
    for fact in context.get("facts", []):
        fact_type = fact.get("fact_type", "")
        owner = fact.get("evidence_owner", fact.get("owner", "system"))
        ev_type = fact.get("source_evidence_type", "")
        tier, tier_weight = get_source_tier(ev_type, "fact")

        statement = _fact_to_statement(fact)
        relevance = "HIGH" if fact_type in config.get("relevant_fact_types", []) else "MEDIUM"

        findings.append({
            "finding_id": _next_fid(),
            "subject": fact_type,
            "statement": statement,
            "source_evidence": [fact.get("source_evidence_id")],
            "source_nodes": [fact.get("fact_id")],
            "source_tier": tier,
            "tier_weight": tier_weight,
            "owner": owner,
            "dispute_relevance": relevance,
            "finding_type": "fact",
            "about_entity": fact.get("about_entity"),
            "raw_data": fact,
        })

    # -- From policy clauses ---------------------------------
    for clause in context.get("policy_clauses", []):
        tier, tier_weight = get_source_tier("MERCHANT_POLICY", "policy")

        findings.append({
            "finding_id": _next_fid(),
            "subject": "policy_rule",
            "statement": clause.get("text", ""),
            "source_evidence": [],
            "source_nodes": [clause.get("fact_id")],
            "source_tier": tier,
            "tier_weight": tier_weight,
            "owner": "merchant",
            "dispute_relevance": "HIGH",
            "finding_type": "policy",
            "about_entity": clause.get("about_entity"),
            "raw_data": clause,
        })

    return findings


def _fact_to_statement(fact: Dict[str, Any]) -> str:
    """Convert a raw FactNode into a human-readable statement."""
    ft = fact.get("fact_type", "")

    if ft == "status_event":
        status = fact.get("status", "Unknown")
        ts = fact.get("timestamp", "")
        loc = fact.get("location", "")
        return f"Tracking event: {status} at {loc} on {ts}"

    elif ft == "delivery_proof":
        dd = fact.get("delivery_date", "")
        tn = fact.get("tracking_number", "")
        sig = fact.get("signature_collected", False)
        sig_text = "with signature" if sig else "no signature collected"
        return f"Delivery proof for tracking {tn}: delivered {dd}, {sig_text}"

    elif ft == "message":
        sender = fact.get("sender", "unknown")
        ts = fact.get("timestamp", "")
        body = fact.get("body", "")
        if len(body) > 150:
            body = body[:147] + "..."
        return f"Email from {sender} on {ts}: {body}"

    elif ft == "purchase_item":
        name = fact.get("item_name", "unknown item")
        qty = fact.get("quantity", 1)
        price = fact.get("price", "N/A")
        return f"Purchase: {qty}x {name} at ${price}"

    elif ft == "policy_rule":
        cid = fact.get("clause_id", "")
        text = fact.get("text", "")
        return f"Policy clause {cid}: {text}"

    else:
        return json.dumps({k: v for k, v in fact.items()
                          if k not in ("source_evidence_id", "source_evidence_type",
                                       "evidence_owner", "about_entity")})
