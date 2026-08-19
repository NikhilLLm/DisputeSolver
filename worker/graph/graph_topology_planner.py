"""
Graph Topology Planner — Controlled LLM-Guided Entity Classification & Alias Resolution.

Uses a single constrained LLM call to:
1. Classify each discovered entity as a Strong Hub (case-level node) or Weak Attribute (FactNode property)
2. Resolve fragmented entity_id variants to canonical names (e.g., "PF-WRLS-BLK" → "ProFit Wireless Headphones")
3. Propose domain bridges between case hubs (e.g., Order → EXPECTS_ITEM → OrderedItem)
4. Wire evidence envelopes to their primary hub targets

Includes robust Python-side normalization to seamlessly map any LLM naming variations
into the exact Pydantic schema before validation.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from dotenv import load_dotenv
from openai import OpenAI, APIError, RateLimitError
from pydantic import BaseModel, Field

from worker.graph.graph_schema import (
    HUB_LABEL_VOCABULARY,
    DOMAIN_BRIDGE_VOCABULARY,
)

load_dotenv()

# ==========================================================
# PYDANTIC MODELS — Strict output schema for the LLM
# ==========================================================

HubLabelType = Literal[
    "Order", "Tracking", "Merchant", "Customer",
    "OrderedItem", "ReceivedItem", "Item",
    "Inspector", "PoliceReport", "Device", "UserAccount",
    "Report", "PolicyClause",
]

BridgeRelType = Literal[
    "HAS_SHIPMENT", "EXPECTS_ITEM", "RECEIVED_AS",
    "CONTAINS_ITEM", "HAS_POLICE_REPORT", "DUPLICATE_OF",
    "PURCHASED_FROM",
]

WiringRelType = Literal["ABOUT", "PROVES_DELIVERY", "CLAIMS_DEFECT"]


class GraphHub(BaseModel):
    """A case-level entity that should become a top-level Neo4j node."""
    hub_label: HubLabelType
    canonical_id: str = Field(description="The single canonical entity_id to use in Neo4j")
    display_name: str = Field(default="", description="Human-readable display name")
    source_entity_type: str = Field(default="", description="Original entity_type from the canonical JSON")


class EntityAliasEntry(BaseModel):
    """Maps fragmented entity_ids to their single canonical_id."""
    canonical_id: str = Field(description="The canonical entity_id that all aliases resolve to")
    aliases: List[str] = Field(default_factory=list, description="All variant IDs that refer to this same real-world entity")


class DomainBridge(BaseModel):
    """A structural relationship between two case hubs."""
    source_canonical_id: str
    target_canonical_id: str
    relationship_type: BridgeRelType


class EvidenceWiring(BaseModel):
    """Maps an evidence envelope to its primary case hub target."""
    document_id: str
    target_canonical_id: str
    relationship_type: WiringRelType = "ABOUT"


class GraphTopologyPlan(BaseModel):
    """Complete topology plan for building a single dispute case graph."""
    case_id: str
    canonical_reason: str
    case_hubs: List[GraphHub] = Field(default_factory=list)
    entity_alias_map: List[EntityAliasEntry] = Field(default_factory=list)
    domain_bridges: List[DomainBridge] = Field(default_factory=list)
    evidence_wirings: List[EvidenceWiring] = Field(default_factory=list)


# ==========================================================
# LLM CLIENT & CALL
# ==========================================================

def _get_client() -> OpenAI:
    """Create Groq-compatible OpenAI client."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set in environment")
    return OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
    )


def _llm_topology_call(
    client: OpenAI,
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    max_retries: int = 3,
) -> Dict[str, Any]:
    """Call LLM with JSON output mode and retry logic."""
    model = model or os.getenv("GROQ_TEXT_MODEL", "openai/gpt-oss-120b")

    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                temperature=0.0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            raw = response.choices[0].message.content or "{}"
            return json.loads(raw)
        except (APIError, RateLimitError) as e:
            wait = 2.0 * attempt
            print(f"  [Attempt {attempt}/{max_retries}] LLM API error: {e}. Retrying in {wait}s...")
            time.sleep(wait)
        except json.JSONDecodeError as e:
            print(f"  [Attempt {attempt}/{max_retries}] JSON parse error: {e}. Retrying...")
            time.sleep(1.0)

    raise RuntimeError(f"Graph Topology Planner LLM call failed after {max_retries} attempts")


# ==========================================================
# PROMPT CONSTRUCTION
# ==========================================================

SYSTEM_PROMPT = """You are a Graph Topology Planner for a dispute & chargeback knowledge graph system.

Your job is to analyze the entities discovered across all evidence documents in a dispute case and produce a structured topology plan.

RULES:
1. STRONG HUBS (case_hubs): Entities that are objective business objects tying the entire dispute together. Both parties make claims ABOUT these. Examples: Order, Merchant, Customer, OrderedItem, ReceivedItem, Tracking, PoliceReport.
2. WEAK ATTRIBUTES: Internal party-specific details that exist only within one piece of evidence (inspector IDs, packing station names, session IDs, AVS codes). These should NOT appear in case_hubs.
3. ENTITY ALIAS RESOLUTION (entity_alias_map): Multiple entity_ids that refer to the same real-world entity must be collapsed. For example, a product called "ProFit Wireless Headphones" might also appear as "PF-WRLS-BLK" (SKU) or "ProFit Wireless - Black" (variant name). All of these must resolve to ONE canonical_id.
4. DOMAIN BRIDGES (domain_bridges): Structural relationships between hubs.
   - Order -> EXPECTS_ITEM -> OrderedItem (what was supposed to be delivered)
   - Order -> RECEIVED_AS -> ReceivedItem (what was actually received, if different)
   - Order -> HAS_SHIPMENT -> Tracking (carrier tracking)
   - Order -> PURCHASED_FROM -> Merchant
   - Case -> HAS_POLICE_REPORT -> PoliceReport (fraud cases)
   - Order1 -> DUPLICATE_OF -> Order2 (duplicate charge cases)
5. EVIDENCE WIRINGS (evidence_wirings): Which evidence envelope is primarily ABOUT which case hub.

VALID hub_label values: Order, Tracking, Merchant, Customer, OrderedItem, ReceivedItem, Item, Inspector, PoliceReport, Device, UserAccount, Report, PolicyClause
VALID relationship_type values for domain_bridges: HAS_SHIPMENT, EXPECTS_ITEM, RECEIVED_AS, CONTAINS_ITEM, HAS_POLICE_REPORT, DUPLICATE_OF, PURCHASED_FROM
VALID relationship_type values for evidence_wirings: ABOUT, PROVES_DELIVERY, CLAIMS_DEFECT

JSON RESPONSE STRUCTURE EXAMPLE:
{
  "case_id": "DSP-2026-00201",
  "canonical_reason": "NOT_AS_DESCRIBED",
  "case_hubs": [
    {"hub_label": "Order", "canonical_id": "ORD-112233445", "display_name": "ORD-112233445", "source_entity_type": "Order"},
    {"hub_label": "Merchant", "canonical_id": "TechGadgets Inc.", "display_name": "TechGadgets Inc.", "source_entity_type": "Merchant"},
    {"hub_label": "OrderedItem", "canonical_id": "ProFit Wireless Headphones", "display_name": "ProFit Wireless Headphones", "source_entity_type": "OrderedItem"},
    {"hub_label": "ReceivedItem", "canonical_id": "White Standard model", "display_name": "White Standard model", "source_entity_type": "ReceivedItem"}
  ],
  "entity_alias_map": [
    {"canonical_id": "ProFit Wireless Headphones", "aliases": ["PF-WRLS-BLK", "ProFit Wireless - Black", "Black Pro model"]},
    {"canonical_id": "White Standard model", "aliases": ["White Standard Headphones"]}
  ],
  "domain_bridges": [
    {"source_canonical_id": "ORD-112233445", "target_canonical_id": "ProFit Wireless Headphones", "relationship_type": "EXPECTS_ITEM"},
    {"source_canonical_id": "ORD-112233445", "target_canonical_id": "White Standard model", "relationship_type": "RECEIVED_AS"},
    {"source_canonical_id": "ORD-112233445", "target_canonical_id": "TechGadgets Inc.", "relationship_type": "PURCHASED_FROM"}
  ],
  "evidence_wirings": [
    {"document_id": "doc-form-cardholder_intake_fo-1787035549", "target_canonical_id": "ORD-112233445", "relationship_type": "ABOUT"},
    {"document_id": "doc-cardholder_received_-1787035560", "target_canonical_id": "White Standard model", "relationship_type": "PROVES_DELIVERY"}
  ]
}"""


def _build_user_prompt(canon_data: Dict[str, Any]) -> str:
    """Build a compact user prompt from canonical JSON for the topology planner."""
    case_id = canon_data.get("case_id", "UNKNOWN")
    summary = canon_data.get("summary", {})
    unique_entities = summary.get("unique_entities_discovered", {})
    extractions = canon_data.get("extractions", [])

    # Extract canonical_dispute_reason from the first DISPUTE_FORM
    canonical_reason = "UNKNOWN"
    for env in extractions:
        p = env.get("payload", {})
        if p.get("canonical_dispute_reason"):
            canonical_reason = p["canonical_dispute_reason"]
            break

    # Build compact per-envelope entity summary
    envelope_summaries = []
    for env in extractions:
        meta = env.get("meta", {})
        extraction = env.get("extraction", {})
        entities = extraction.get("entities", [])
        assertions = extraction.get("assertions", [])

        envelope_summaries.append({
            "document_id": meta.get("document_id", "?"),
            "file_name": meta.get("file_name", "?"),
            "owner": meta.get("owner", "?"),
            "evidence_type": meta.get("evidence_type", "?"),
            "entities": entities,
            "assertion_count": len(assertions),
            "assertion_subjects": [a.get("subject_entity", "") for a in assertions],
        })

    user_prompt = f"""CASE: {case_id}
DISPUTE REASON: {canonical_reason}

GLOBAL UNIQUE ENTITIES DISCOVERED:
{json.dumps(unique_entities, indent=2)}

PER-DOCUMENT ENTITIES AND ASSERTION TARGETS:
{json.dumps(envelope_summaries, indent=2)}

Analyze these entities and produce the GraphTopologyPlan JSON adhering strictly to the JSON schema."""

    return user_prompt


# ==========================================================
# ROBUST PRE-PROCESSOR & NORMALIZER
# ==========================================================

def _normalize_raw_plan(raw_plan: Dict[str, Any], canon_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes the raw LLM output into the exact schema expected by GraphTopologyPlan.
    Handles field name variations (e.g. from_hub -> source_canonical_id, hub_id -> canonical_id).
    """
    case_id = raw_plan.get("case_id") or canon_data.get("case_id", "UNKNOWN")

    # Canonical Reason
    canonical_reason = raw_plan.get("canonical_reason")
    if not canonical_reason:
        for env in canon_data.get("extractions", []):
            p = env.get("payload", {})
            if p.get("canonical_dispute_reason"):
                canonical_reason = p["canonical_dispute_reason"]
                break
    canonical_reason = canonical_reason or "UNKNOWN"

    # 1. Normalize case_hubs
    raw_hubs = raw_plan.get("case_hubs") or raw_plan.get("hubs") or []
    norm_hubs: List[Dict[str, Any]] = []
    for h in raw_hubs:
        if not isinstance(h, dict):
            continue
        hub_label = h.get("hub_label") or h.get("label") or "Item"
        if hub_label not in HUB_LABEL_VOCABULARY:
            # Map common variants
            if "Order" in hub_label:
                hub_label = "Order"
            elif "Merchant" in hub_label:
                hub_label = "Merchant"
            elif "Customer" in hub_label:
                hub_label = "Customer"
            elif "Tracking" in hub_label:
                hub_label = "Tracking"
            elif "Ordered" in hub_label:
                hub_label = "OrderedItem"
            elif "Received" in hub_label:
                hub_label = "ReceivedItem"
            else:
                hub_label = "Item"

        canonical_id = str(h.get("canonical_id") or h.get("hub_id") or h.get("id") or h.get("entity_id") or "")
        if not canonical_id:
            continue

        display_name = str(h.get("display_name") or h.get("name") or canonical_id)
        source_type = str(h.get("source_entity_type") or h.get("entity_type") or hub_label)

        norm_hubs.append({
            "hub_label": hub_label,
            "canonical_id": canonical_id,
            "display_name": display_name,
            "source_entity_type": source_type,
        })

    # 2. Normalize entity_alias_map
    raw_aliases = (
        raw_plan.get("entity_alias_map")
        or raw_plan.get("alias_map")
        or raw_plan.get("aliases")
        or raw_plan.get("entity_aliases")
        or []
    )
    norm_aliases: List[Dict[str, Any]] = []
    if isinstance(raw_aliases, dict):
        for k, v in raw_aliases.items():
            aliases = v if isinstance(v, list) else [str(v)]
            norm_aliases.append({"canonical_id": str(k), "aliases": [str(a) for a in aliases]})
    elif isinstance(raw_aliases, list):
        for a in raw_aliases:
            if isinstance(a, dict):
                cid = str(a.get("canonical_id") or a.get("id") or a.get("canonical_name") or "")
                alist = a.get("aliases") or a.get("alias_list") or []
                if cid:
                    norm_aliases.append({"canonical_id": cid, "aliases": [str(x) for x in alist]})

    # 3. Normalize domain_bridges
    raw_bridges = raw_plan.get("domain_bridges") or raw_plan.get("bridges") or []
    norm_bridges: List[Dict[str, Any]] = []
    for b in raw_bridges:
        if not isinstance(b, dict):
            continue
        src_id = str(b.get("source_canonical_id") or b.get("from_hub") or b.get("source_hub") or b.get("source") or "")
        tgt_id = str(b.get("target_canonical_id") or b.get("to_hub") or b.get("target_hub") or b.get("target") or "")
        rel_type = str(b.get("relationship_type") or b.get("type") or b.get("relation") or "CONTAINS_ITEM")

        # Map common relationship variants
        rel_upper = rel_type.upper().replace("-", "_").replace(" ", "_")
        if rel_upper not in DOMAIN_BRIDGE_VOCABULARY:
            if "SHIP" in rel_upper or "TRACK" in rel_upper:
                rel_upper = "HAS_SHIPMENT"
            elif "EXPECT" in rel_upper or "PROMISE" in rel_upper:
                rel_upper = "EXPECTS_ITEM"
            elif "RECEIV" in rel_upper:
                rel_upper = "RECEIVED_AS"
            elif "PURCHAS" in rel_upper or "BUY" in rel_upper or "MERCHANT" in rel_upper:
                rel_upper = "PURCHASED_FROM"
            elif "POLICE" in rel_upper:
                rel_upper = "HAS_POLICE_REPORT"
            elif "DUPLICAT" in rel_upper:
                rel_upper = "DUPLICATE_OF"
            else:
                rel_upper = "CONTAINS_ITEM"

        if src_id and tgt_id:
            norm_bridges.append({
                "source_canonical_id": src_id,
                "target_canonical_id": tgt_id,
                "relationship_type": rel_upper,
            })

    # 4. Normalize evidence_wirings
    raw_wirings = raw_plan.get("evidence_wirings") or raw_plan.get("wirings") or []
    norm_wirings: List[Dict[str, Any]] = []
    for w in raw_wirings:
        if not isinstance(w, dict):
            continue
        doc_id = str(w.get("document_id") or w.get("doc_id") or w.get("id") or "")
        tgt_id = str(w.get("target_canonical_id") or w.get("target_hub") or w.get("target") or "")
        rel_type = str(w.get("relationship_type") or "ABOUT").upper()
        if rel_type not in ("ABOUT", "PROVES_DELIVERY", "CLAIMS_DEFECT"):
            rel_type = "ABOUT"

        if doc_id and tgt_id:
            norm_wirings.append({
                "document_id": doc_id,
                "target_canonical_id": tgt_id,
                "relationship_type": rel_type,
            })

    return {
        "case_id": case_id,
        "canonical_reason": canonical_reason,
        "case_hubs": norm_hubs,
        "entity_alias_map": norm_aliases,
        "domain_bridges": norm_bridges,
        "evidence_wirings": norm_wirings,
    }


# ==========================================================
# MAIN ENTRY POINT
# ==========================================================

def plan_graph_topology(
    canonical_json_path: Path = Path("output/extractions/final_canonical_case_extractions.json"),
    output_dir: Path = Path("output/extractions"),
) -> GraphTopologyPlan:
    """
    Generate a GraphTopologyPlan from canonical case JSON via controlled LLM call.

    The plan is persisted to disk with versioned filenames for debugging.
    Returns a validated GraphTopologyPlan Pydantic model.
    """
    if not canonical_json_path.exists():
        raise FileNotFoundError(f"Canonical JSON not found: {canonical_json_path}")

    canon_data = json.loads(canonical_json_path.read_text(encoding="utf-8"))
    case_id = canon_data.get("case_id", "UNKNOWN")

    print(f"\n{'='*60}")
    print(f"GRAPH TOPOLOGY PLANNER — Case {case_id}")
    print(f"{'='*60}")

    # Build prompts
    user_prompt = _build_user_prompt(canon_data)
    print(f"  [Prompt] Built user prompt ({len(user_prompt)} chars)")

    # Call LLM
    print(f"  [LLM] Calling topology planner...")
    client = _get_client()
    raw_plan = _llm_topology_call(client, SYSTEM_PROMPT, user_prompt)
    print(f"  [LLM] Received topology plan from model")

    # Normalize raw LLM output into strict schema
    normalized_plan = _normalize_raw_plan(raw_plan, canon_data)

    try:
        plan = GraphTopologyPlan(**normalized_plan)
    except Exception as e:
        print(f"  [ERROR] Pydantic validation failed: {e}")
        print(f"  [DEBUG] Normalized plan:\n{json.dumps(normalized_plan, indent=2)[:2000]}")
        raise

    # Print summary
    print(f"\n  [Plan Summary]")
    print(f"    Case Hubs: {len(plan.case_hubs)}")
    for hub in plan.case_hubs:
        print(f"      • ({hub.hub_label}) {hub.canonical_id} [{hub.display_name}]")
    print(f"    Alias Maps: {len(plan.entity_alias_map)}")
    for alias in plan.entity_alias_map:
        print(f"      • {alias.canonical_id} ← {alias.aliases}")
    print(f"    Domain Bridges: {len(plan.domain_bridges)}")
    for bridge in plan.domain_bridges:
        print(f"      • ({bridge.source_canonical_id})-[:{bridge.relationship_type}]->({bridge.target_canonical_id})")
    print(f"    Evidence Wirings: {len(plan.evidence_wirings)}")

    # Persist to disk with versioned filename
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    versioned_filename = f"graph_topology_plan_{timestamp}.json"
    versioned_path = output_dir / versioned_filename
    latest_path = output_dir / "graph_topology_plan.json"

    plan_dict = plan.model_dump()
    plan_dict["_generated_at"] = timestamp
    plan_dict["_source_json"] = str(canonical_json_path)

    versioned_path.write_text(json.dumps(plan_dict, indent=2, ensure_ascii=False), encoding="utf-8")
    latest_path.write_text(json.dumps(plan_dict, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n  [Persisted] {versioned_path}")
    print(f"  [Persisted] {latest_path} (latest)")
    print(f"{'='*60}\n")

    return plan


def build_alias_lookup(plan: GraphTopologyPlan) -> Dict[str, str]:
    """
    Build a flat lookup dict from the topology plan's entity_alias_map.

    Returns: { alias_string: canonical_id } for every alias.
    The canonical_id itself is also included as a key mapping to itself.
    """
    lookup: Dict[str, str] = {}
    for entry in plan.entity_alias_map:
        lookup[entry.canonical_id] = entry.canonical_id
        for alias in entry.aliases:
            lookup[alias] = entry.canonical_id
    return lookup


def resolve_entity_id(entity_id: str, alias_lookup: Dict[str, str]) -> str:
    """Resolve an entity_id through the alias lookup, returning the canonical form."""
    return alias_lookup.get(entity_id, entity_id)


# ==========================================================
# CLI ENTRY POINT
# ==========================================================

if __name__ == "__main__":
    plan = plan_graph_topology()
    print(f"\nTopology plan generated with {len(plan.case_hubs)} hubs, "
          f"{len(plan.entity_alias_map)} alias groups, "
          f"{len(plan.domain_bridges)} bridges.")
