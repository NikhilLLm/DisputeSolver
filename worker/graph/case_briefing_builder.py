"""
Case Briefing Builder — Stage 1.5 of the Reasoning Pipeline.

Transforms the raw Neo4j graph retrieval dictionary into a clean, structured
Markdown Briefing Sheet that the LLM Case Analyst can consume efficiently.

Replaces the 2,000+ line raw JSON AST dump with a concise, high-signal
courtroom-grade document organized by evidence tier.

Design Principles:
  1. Tier-segregated sections (Telemetry → Business Records → Assertions)
  2. Chronological ordering within each section
  3. Structured numeric values (dates, amounts, windows) are presented
     in a format the LLM can read but deterministic evaluator will verify
  4. Universal across all 8 dispute categories — zero category branching
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from worker.graph.graph_schema import (
    EVIDENCE_SOURCE_TIERS,
    EVIDENCE_TYPE_TO_TIER,
)


# ==========================================================
# TIER CLASSIFICATION HELPERS
# ==========================================================

# Evidence types that produce Tier 1 telemetry facts
_TIER_1_EVIDENCE_TYPES = {
    k for k, v in EVIDENCE_TYPE_TO_TIER.items()
    if v == "TIER_1_TELEMETRY"
}

# Evidence types that produce Tier 2 business records
_TIER_2_EVIDENCE_TYPES = {
    k for k, v in EVIDENCE_TYPE_TO_TIER.items()
    if v == "TIER_2_COMMUNICATION"
}

# Fact types that are Tier 1 telemetry
_TIER_1_FACT_TYPES = {
    "status_event", "delivery_proof", "usage_event",
    "processor_record", "authorization_data", "transaction_record",
    "account_event",
}

# Fact types that are Tier 2 business records
_TIER_2_FACT_TYPES = {
    "message", "purchase_item", "policy_rule", "inspection_record",
}


def _safe_get(d: Dict[str, Any], *keys: str, default: str = "N/A") -> str:
    """Safely extract a value from a dict, trying multiple keys."""
    for k in keys:
        val = d.get(k)
        if val is not None and val != "":
            return str(val)
    return default


def _format_fact_summary(fact: Dict[str, Any]) -> str:
    """Format a single FactNode into a human-readable one-line summary."""
    ft = fact.get("fact_type", "unknown")
    fact_id = fact.get("fact_id", "?")

    if ft == "status_event":
        ts = _safe_get(fact, "timestamp")
        status = _safe_get(fact, "status")
        location = _safe_get(fact, "location")
        return f"[{ts}] Status: {status} at {location} (ID: {fact_id})"

    elif ft == "delivery_proof":
        ts = _safe_get(fact, "timestamp", "delivery_date")
        method = _safe_get(fact, "method", "proof_type")
        sig = _safe_get(fact, "signature_name", "signed_by")
        carrier = _safe_get(fact, "carrier")
        loc = _safe_get(fact, "location")
        sig_str = f", signed by: {sig}" if sig and sig != "N/A" else ""
        car_str = f" via {carrier}" if carrier and carrier != "N/A" else ""
        loc_str = f" at {loc}" if loc and loc != "N/A" else ""
        return f"[{ts}] Delivery proof{car_str}{loc_str}{sig_str} (ID: {fact_id})"

    elif ft == "processor_record":
        action = _safe_get(fact, "action", "payment_action", default="TRANSACTION")
        amount = _safe_get(fact, "amount", "refund_amount")
        status = _safe_get(fact, "payment_status", "status", default="RECORDED")
        ts = _safe_get(fact, "timestamp", "processed_at", "refund_timestamp")
        gateway = _safe_get(fact, "gateway", "gateway_name", "processor")
        arn = _safe_get(fact, "arn", "reference_number", "transaction_reference")
        amt_str = f" ${amount}" if amount and amount != "N/A" else ""
        arn_str = f", ARN={arn}" if arn and arn != "N/A" else ""
        gw_str = f", gateway={gateway}" if gateway and gateway != "N/A" else ""
        return f"[{ts}] Processor: {action}{amt_str}, status={status}{gw_str}{arn_str} (ID: {fact_id})"

    elif ft == "authorization_data":
        avs = _safe_get(fact, "avs_result")
        cvv = _safe_get(fact, "cvv_result")
        tds = _safe_get(fact, "three_ds_status", "3ds_status")
        risk = _safe_get(fact, "risk_score")
        return f"Authorization: AVS={avs}, CVV={cvv}, 3DS={tds}, Risk={risk} (ID: {fact_id})"

    elif ft == "usage_event":
        ts = _safe_get(fact, "timestamp")
        action = _safe_get(fact, "action", "event_type")
        ip = _safe_get(fact, "ip_address")
        duration = _safe_get(fact, "duration_minutes")
        return f"[{ts}] Usage: {action}, IP={ip}, duration={duration}min (ID: {fact_id})"

    elif ft == "transaction_record":
        session_a = _safe_get(fact, "session_a_id", "session_id_a")
        session_b = _safe_get(fact, "session_b_id", "session_id_b")
        ip_match = _safe_get(fact, "ip_match")
        time_diff = _safe_get(fact, "time_difference_seconds")
        return f"Transaction comparison: Session A={session_a}, Session B={session_b}, IP match={ip_match}, time gap={time_diff}s (ID: {fact_id})"

    elif ft == "account_event":
        ts = _safe_get(fact, "posting_date", "timestamp")
        amount = _safe_get(fact, "amount")
        desc = _safe_get(fact, "description")
        return f"[{ts}] Account event: {desc}, amount=${amount} (ID: {fact_id})"

    elif ft == "message":
        ts = _safe_get(fact, "timestamp")
        sender = _safe_get(fact, "sender")
        body = _safe_get(fact, "body", "text")
        # Truncate long message bodies for briefing clarity
        if len(body) > 200:
            body = body[:197] + "..."
        return f"[{ts}] {sender}: \"{body}\" (ID: {fact_id})"

    elif ft == "purchase_item":
        name = _safe_get(fact, "item_name", "product_name", "name")
        qty = _safe_get(fact, "quantity")
        price = _safe_get(fact, "unit_price", "price")
        return f"Purchase item: {name}, qty={qty}, price=${price} (ID: {fact_id})"

    elif ft == "policy_rule":
        clause_id = _safe_get(fact, "clause_id")
        text = _safe_get(fact, "text", "clause_text")
        window = fact.get("window_days")
        window_str = f" (window: {window} days)" if window else ""
        return f"Policy Clause {clause_id}: \"{text}\"{window_str} (ID: {fact_id})"

    elif ft == "inspection_record":
        ts = _safe_get(fact, "timestamp", "inspection_date")
        result = _safe_get(fact, "result", "outcome")
        inspector = _safe_get(fact, "inspector", "inspector_name")
        return f"[{ts}] Inspection by {inspector}: {result} (ID: {fact_id})"

    elif ft == "police_report_record":
        report_number = _safe_get(fact, "report_number")
        filed_date = _safe_get(fact, "filed_date", "timestamp")
        summary = _safe_get(fact, "summary", "description")
        return f"[{filed_date}] Police report #{report_number}: {summary} (ID: {fact_id})"

    else:
        # Generic fallback for any unknown fact type
        props = {k: v for k, v in fact.items()
                 if k not in ("fact_id", "fact_type", "case_id",
                              "source_evidence_id", "source_evidence_type",
                              "evidence_owner", "about_entity")}
        return f"[{ft}] {props} (ID: {fact_id})"


def _classify_fact_tier(fact: Dict[str, Any]) -> int:
    """Return 1, 2, or 3 for tier classification of a fact."""
    ft = fact.get("fact_type", "")
    src = fact.get("source_evidence_type", "")

    if ft in _TIER_1_FACT_TYPES or src in _TIER_1_EVIDENCE_TYPES:
        return 1
    elif ft in _TIER_2_FACT_TYPES or src in _TIER_2_EVIDENCE_TYPES:
        return 2
    else:
        return 3


# ==========================================================
# MAIN BRIEFING BUILDER
# ==========================================================

def build_case_briefing(context: Dict[str, Any]) -> str:
    """Transform a graph retrieval context dict into a structured Markdown Briefing Sheet.

    This is Stage 1.5 of the reasoning pipeline — sitting between
    graph retrieval (Stage 1) and the LLM Case Analyst (Stage 2).

    Args:
        context: Raw graph retrieval dict from fetch_case_reasoning_context().

    Returns:
        A clean Markdown string briefing organized by evidence tier.
    """
    lines: List[str] = []

    # ----------------------------------------------------------
    # SECTION 1: CASE HEADER
    # ----------------------------------------------------------
    case = context.get("case", {})
    dr = context.get("dispute_reason", {})
    parties = context.get("parties", [])

    case_id = context.get("case_id", case.get("case_id", "UNKNOWN"))
    category = dr.get("category", "Unknown Category")
    reason_code = dr.get("reason_code", "N/A")

    # Find party names
    cardholder_name = "Unknown"
    merchant_name = "Unknown"
    for p in parties:
        role = (p.get("role") or "").lower()
        if "cardholder" in role or "customer" in role:
            cardholder_name = p.get("name", "Unknown")
        elif "merchant" in role:
            merchant_name = p.get("name", "Unknown")

    lines.append(f"# DISPUTE CASE BRIEFING: {case_id}")
    lines.append(f"- **Category:** {category}")
    lines.append(f"- **Reason Code:** {reason_code}")
    lines.append(f"- **Cardholder:** {cardholder_name}")
    lines.append(f"- **Merchant:** {merchant_name}")
    lines.append(f"- **Parties:** {len(parties)}")
    lines.append("")

    # ----------------------------------------------------------
    # SECTION 2: ENTITY TOPOLOGY (Simplified Relationship Map)
    # ----------------------------------------------------------
    entities = context.get("entities", [])
    bridges = context.get("domain_bridges", [])

    if entities:
        lines.append("## CASE ENTITIES")
        for ent in entities:
            labels = ent.get("labels", [])
            eid = ent.get("entity_id", "?")
            etype = ent.get("entity_type", "?")
            # Extract key properties
            name = ent.get("name", ent.get("merchant_name", ent.get("customer_name", "")))
            extra = ""
            if name:
                extra = f", name=\"{name}\""
            lines.append(f"- [{', '.join(labels)}] {eid} (type: {etype}{extra})")
        lines.append("")

    if bridges:
        lines.append("## ENTITY RELATIONSHIPS")
        for b in bridges:
            lines.append(f"- ({b['source']}) -[:{b['rel_type']}]-> ({b['target']})")
        lines.append("")

    # ----------------------------------------------------------
    # SECTION 3: EVIDENCE ENVELOPES (Summary of submitted documents)
    # ----------------------------------------------------------
    evidence = context.get("evidence", [])
    if evidence:
        lines.append("## SUBMITTED EVIDENCE DOCUMENTS")
        for ev in evidence:
            ev_id = ev.get("evidence_id", "?")
            ev_type = ev.get("evidence_type", "?")
            owner = ev.get("owner", "?")
            fname = ev.get("file_name", "?")
            tier_label = EVIDENCE_TYPE_TO_TIER.get(ev_type, "TIER_3_ASSERTION")
            lines.append(f"- [{ev_id}] {ev_type} ({tier_label}) — submitted by {owner} — file: {fname}")
        lines.append("")

    # ----------------------------------------------------------
    # SECTION 4: TIER 1 — VERIFIED TELEMETRY & HARD FACTS
    # ----------------------------------------------------------
    all_facts = context.get("facts", [])
    tier_1_facts = [f for f in all_facts if _classify_fact_tier(f) == 1]
    tier_2_facts = [f for f in all_facts if _classify_fact_tier(f) == 2]
    tier_3_facts = [f for f in all_facts if _classify_fact_tier(f) == 3]

    if tier_1_facts:
        lines.append("## VERIFIED TELEMETRY (Tier 1 — Tamper-Resistant 3rd-Party Data)")
        # Sort by timestamp if available
        tier_1_facts.sort(key=lambda x: str(x.get("timestamp", "")))
        for i, fact in enumerate(tier_1_facts, 1):
            owner = fact.get("evidence_owner", fact.get("owner", "system"))
            lines.append(f"{i}. [{owner.upper()}] {_format_fact_summary(fact)}")
        lines.append("")

    # ----------------------------------------------------------
    # SECTION 5: TIER 2 — BUSINESS RECORDS, COMMUNICATIONS & POLICIES
    # ----------------------------------------------------------
    # Policy clauses get their own subsection
    policy_clauses = context.get("policy_clauses", [])
    non_policy_tier2 = [f for f in tier_2_facts if f.get("fact_type") != "policy_rule"]

    if non_policy_tier2:
        lines.append("## BUSINESS RECORDS & COMMUNICATIONS (Tier 2 — Timestamped Records)")
        non_policy_tier2.sort(key=lambda x: str(x.get("timestamp", "")))
        for i, fact in enumerate(non_policy_tier2, 1):
            owner = fact.get("evidence_owner", fact.get("owner", "system"))
            lines.append(f"{i}. [{owner.upper()}] {_format_fact_summary(fact)}")
        lines.append("")

    if policy_clauses:
        lines.append("## MERCHANT POLICY CLAUSES")
        for i, clause in enumerate(policy_clauses, 1):
            lines.append(f"{i}. {_format_fact_summary(clause)}")
        lines.append("")

    # ----------------------------------------------------------
    # SECTION 6: TIER 3 — ASSERTIONS & CLAIMS (Subjective Statements)
    # ----------------------------------------------------------
    assertions = context.get("assertions", [])

    # Separate by party
    cardholder_assertions = [a for a in assertions if (a.get("owner") or "").lower() in ("cardholder", "customer")]
    merchant_assertions = [a for a in assertions if (a.get("owner") or "").lower() == "merchant"]
    other_assertions = [a for a in assertions
                        if (a.get("owner") or "").lower() not in ("cardholder", "customer", "merchant")]

    if cardholder_assertions:
        lines.append("## CARDHOLDER CLAIMS & ASSERTIONS (Tier 3 — Post-Dispute Narratives)")
        for i, ast in enumerate(cardholder_assertions, 1):
            aid = ast.get("assertion_id", "?")
            subject = ast.get("subject", "general")
            text = ast.get("text", "")
            src_evidence = ast.get("source_evidence_id", "?")
            extra = ""
            if ast.get("asserted_value_days") is not None:
                extra = f" [asserted window: {ast['asserted_value_days']} days]"
            lines.append(f'{i}. [{aid}] ({subject}) "{text}"{extra} — from evidence {src_evidence}')
        lines.append("")

    if merchant_assertions:
        lines.append("## MERCHANT DEFENSE & ASSERTIONS (Tier 3 — Post-Dispute Narratives)")
        for i, ast in enumerate(merchant_assertions, 1):
            aid = ast.get("assertion_id", "?")
            subject = ast.get("subject", "general")
            text = ast.get("text", "")
            src_evidence = ast.get("source_evidence_id", "?")
            extra = ""
            if ast.get("asserted_value_days") is not None:
                extra = f" [asserted window: {ast['asserted_value_days']} days]"
            lines.append(f'{i}. [{aid}] ({subject}) "{text}"{extra} — from evidence {src_evidence}')
        lines.append("")

    if other_assertions:
        lines.append("## OTHER ASSERTIONS")
        for i, ast in enumerate(other_assertions, 1):
            aid = ast.get("assertion_id", "?")
            owner = ast.get("owner", "system")
            text = ast.get("text", "")
            lines.append(f'{i}. [{aid}] ({owner}) "{text}"')
        lines.append("")

    # ----------------------------------------------------------
    # SECTION 7: TIER 3 FACTS (if any unclassified)
    # ----------------------------------------------------------
    if tier_3_facts:
        lines.append("## OTHER FACTS (Tier 3)")
        for i, fact in enumerate(tier_3_facts, 1):
            owner = fact.get("evidence_owner", fact.get("owner", "system"))
            lines.append(f"{i}. [{owner.upper()}] {_format_fact_summary(fact)}")
        lines.append("")

    # ----------------------------------------------------------
    # SECTION 8: TIMELINE (Chronological Events)
    # ----------------------------------------------------------
    timeline = context.get("timeline_events", [])
    if timeline:
        lines.append("## CHRONOLOGICAL TIMELINE")
        for i, evt in enumerate(timeline, 1):
            ts = evt.get("timestamp", "?")
            status = evt.get("status", "?")
            location = evt.get("location", "")
            loc_str = f" at {location}" if location and location != "N/A" else ""
            lines.append(f"{i}. [{ts}] {status}{loc_str}")
        lines.append("")

    # ----------------------------------------------------------
    # FOOTER: Context Statistics
    # ----------------------------------------------------------
    lines.append("---")
    lines.append(f"*Briefing generated from {len(evidence)} evidence documents, "
                 f"{len(all_facts)} fact nodes, {len(assertions)} assertions, "
                 f"{len(policy_clauses)} policy clauses, {len(entities)} entities.*")

    return "\n".join(lines)
