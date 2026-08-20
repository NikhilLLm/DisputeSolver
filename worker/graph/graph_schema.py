"""
Knowledge Graph Schema — 5-Layer Dispute & Chargeback Architecture.

Layer 1: Case Anchor & Case-level Entities -> (c:Case {case_id}), (dr:DisputeReason), (o:Order), (t:Tracking), (m:Merchant)
Layer 2: Provenance Layer (Who & Where) -> (p:Party), (s:Submission)
Layer 3: Evidence Layer -> (e:Evidence)
Layer 4: Assertion & Fact Layer -> (a:Assertion), (f:FactNode)
Layer 5: Entity Cross-Links & Domain Bridges -> [:ABOUT], [:APPLIES_TO], [:HAS_SHIPMENT]
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Set

SCHEMA_VERSION = "v5_layered_atomized_hybrid"

# ==========================================================
# VECTOR EMBEDDING CONFIGURATION
# ==========================================================
# Using lightweight sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)
# for semantic similarity on text-heavy nodes (Assertions, FactNodes with
# message/policy_rule types). Cosine similarity for matching.

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384
EMBEDDING_SIMILARITY = "cosine"

# ==========================================================
# CANONICAL VOCABULARIES
# ==========================================================

ASSERTION_SUBJECT_VOCABULARY: Set[str] = {
    # Item Not Received
    "delivery_window",
    "non_receipt",
    "delivery_verification",
    "complaint_timing",
    "signature_requirement",
    "shipping_timing",
    "delivery_status",
    "requested_resolution",
    # Item Not as Described / Defective
    "item_description",
    "item_quality",
    "discrepancy_details",
    # Fraud / Unauthorized
    "authorization_claim",
    "fraud_indicators",
    "card_status",
    # Duplicate Processing
    "duplicate_charge",
    # Credit Not Processed
    "refund_promised",
    "return_proof",
    # Subscription / Recurring
    "cancellation_date",
    "continued_usage",
    # Processing Errors
    "amount_discrepancy",
    # Generic
    "unknown",
}

EVIDENCE_SOURCE_TIERS: Dict[str, float] = {
    "TIER_1_TELEMETRY": 1.0,      # Tamper-resistant 3rd-party data (GPS, carrier scans, 3DS crypto, ARNs)
    "TIER_2_COMMUNICATION": 0.7,  # Contemporaneous timestamped emails, chat transcripts, SMS
    "TIER_3_ASSERTION": 0.35,     # Post-dispute subjective form narratives
}

EVIDENCE_TYPE_TO_TIER: Dict[str, str] = {
    "DELIVERY_PROOF": "TIER_1_TELEMETRY",
    "TRACKING_REPORT": "TIER_1_TELEMETRY",
    "PROCESSOR_LOG": "TIER_1_TELEMETRY",
    "USAGE_LOG": "TIER_1_TELEMETRY",
    "COMMUNICATION_LOG": "TIER_2_COMMUNICATION",
    "PURCHASE_RECORD": "TIER_2_COMMUNICATION",
    "MERCHANT_POLICY": "TIER_2_COMMUNICATION",
    "DISPUTE_FORM": "TIER_3_ASSERTION",
}

FACT_TYPE_VOCABULARY: Set[str] = {
    "message",            # Communication log messages
    "purchase_item",      # Line items in purchase record
    "policy_rule",        # Merchant policy clauses
    "status_event",       # Tracking report timeline events
    "delivery_proof",     # Visual/timestamp proof of delivery
    "usage_event",        # Account access/usage log entries
    "processor_record",   # Processor log authorization/refund status
    "authorization_data", # Fraud check AVS/CVV/3DS records
    "inspection_record",  # QC / order status inspection records
    "police_report_record",  # Police report / sworn statement records
    "account_event",      # Account statement line items
    "transaction_record", # Transaction comparison records
}

RELATIONSHIP_VOCABULARY: Set[str] = {
    "HAS_PARTY",
    "HAS_ORDER",
    "HAS_MERCHANT",
    "HAS_DISPUTE_REASON",
    "HAS_SHIPMENT",
    "SUBMITTED",
    "HAS_EVIDENCE",
    "STATES",
    "INCLUDES",
    "ABOUT",
    "APPLIES_TO",
    # New dynamic domain bridges
    "EXPECTS_ITEM",
    "RECEIVED_AS",
    "CONTAINS_ITEM",
    "HAS_POLICE_REPORT",
    "DUPLICATE_OF",
}

# Valid hub labels that the topology planner can assign
HUB_LABEL_VOCABULARY: Set[str] = {
    "Order",
    "Tracking",
    "Merchant",
    "Customer",
    "OrderedItem",
    "ReceivedItem",
    "Item",
    "Inspector",
    "PoliceReport",
    "Device",
    "UserAccount",
    "Report",
    "PolicyClause",
}

# Valid domain bridge relationship types
DOMAIN_BRIDGE_VOCABULARY: Set[str] = {
    "HAS_SHIPMENT",
    "EXPECTS_ITEM",
    "RECEIVED_AS",
    "CONTAINS_ITEM",
    "HAS_POLICE_REPORT",
    "DUPLICATE_OF",
    "PURCHASED_FROM",
}

# ==========================================================
# LAYER SPECIFICATIONS
# ==========================================================

@dataclass(frozen=True)
class LayerSpec:
    layer_number: int
    layer_name: str
    labels: List[str]
    description: str


LAYERS: List[LayerSpec] = [
    LayerSpec(
        layer_number=1,
        layer_name="Case Anchor & Case-Bound Entities",
        labels=[
            "Case", "DisputeReason", "Entity",
            "Order", "Tracking", "Merchant", "Customer",
            "OrderedItem", "ReceivedItem", "Item",
            "Inspector", "PoliceReport", "Device", "UserAccount", "Report",
        ],
        description="Root namespace and case-bound shared business entities.",
    ),
    LayerSpec(
        layer_number=2,
        layer_name="Provenance Layer",
        labels=["Party", "Submission"],
        description="Records traceability for every document submission and party.",
    ),
    LayerSpec(
        layer_number=3,
        layer_name="Evidence Envelope Layer",
        labels=["Evidence"],
        description="Document-level evidence parent nodes anchoring extractions.",
    ),
    LayerSpec(
        layer_number=4,
        layer_name="Assertion & Fact Layer",
        labels=["Assertion", "FactNode"],
        description="Atomic claims made by parties and objective itemized facts.",
    ),
]

# Cypher constraints for uniqueness and MERGE efficiency
CONSTRAINTS: List[str] = [
    "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Case) REQUIRE c.case_id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Submission) REQUIRE s.document_id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Party) REQUIRE (p.name, p.case_id) IS NODE KEY",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Evidence) REQUIRE e.evidence_id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Assertion) REQUIRE a.assertion_id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (f:FactNode) REQUIRE f.fact_id IS UNIQUE",
    "CREATE CONSTRAINT IF NOT EXISTS FOR (ent:Entity) REQUIRE (ent.entity_id, ent.case_id) IS NODE KEY",
]

# Vector indexes for semantic similarity search on text-heavy nodes
VECTOR_INDEXES: List[str] = [
    # Assertion embeddings — for matching cardholder/merchant claims against evidence
    f"""CREATE VECTOR INDEX assertion_embeddings IF NOT EXISTS
FOR (a:Assertion) ON (a.embedding)
OPTIONS {{indexConfig: {{`vector.dimensions`: {EMBEDDING_DIMENSIONS}, `vector.similarity_function`: '{EMBEDDING_SIMILARITY}'}}}}""",
    # FactNode embeddings — for policy clauses, messages, and other text-heavy facts
    f"""CREATE VECTOR INDEX factnode_embeddings IF NOT EXISTS
FOR (f:FactNode) ON (f.embedding)
OPTIONS {{indexConfig: {{`vector.dimensions`: {EMBEDDING_DIMENSIONS}, `vector.similarity_function`: '{EMBEDDING_SIMILARITY}'}}}}""",
]


def get_schema() -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "layers": [asdict(l) for l in LAYERS],
        "constraints": CONSTRAINTS,
        "vector_indexes": VECTOR_INDEXES,
        "embedding_model": EMBEDDING_MODEL,
        "embedding_dimensions": EMBEDDING_DIMENSIONS,
        "assertion_subjects": sorted(list(ASSERTION_SUBJECT_VOCABULARY)),
        "fact_types": sorted(list(FACT_TYPE_VOCABULARY)),
        "relationships": sorted(list(RELATIONSHIP_VOCABULARY)),
        "hub_labels": sorted(list(HUB_LABEL_VOCABULARY)),
        "domain_bridges": sorted(list(DOMAIN_BRIDGE_VOCABULARY)),
    }

