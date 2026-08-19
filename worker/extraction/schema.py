from datetime import datetime
from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel, Field


# ==========================================================
# ENUMS
# ==========================================================

class Owner(str, Enum):
    CARDHOLDER = "cardholder"
    MERCHANT = "merchant"
    ISSUER = "issuer"
    THIRD_PARTY = "third_party"


class EvidenceType(str, Enum):
    DISPUTE_FORM = "DISPUTE_FORM"
    PURCHASE_RECORD = "PURCHASE_RECORD"
    TRACKING_REPORT = "TRACKING_REPORT"
    DELIVERY_PROOF = "DELIVERY_PROOF"
    COMMUNICATION_LOG = "COMMUNICATION_LOG"
    MERCHANT_POLICY = "MERCHANT_POLICY"
    USAGE_LOG = "USAGE_LOG"
    PROCESSOR_LOG = "PROCESSOR_LOG"
    POLICE_REPORT = "POLICE_REPORT"
    ACCOUNT_STATEMENT = "ACCOUNT_STATEMENT"
    ORDER_STATUS_REPORT = "ORDER_STATUS_REPORT"
    TRANSACTION_COMPARISON = "TRANSACTION_COMPARISON"


# ==========================================================
# COMMON METADATA
# ==========================================================

class EvidenceMeta(BaseModel):
    case_id: str
    document_id: str
    file_name: str

    owner: Owner
    evidence_type: EvidenceType

    extracted_at: datetime
    confidence: Optional[float] = None
    processed_by: Optional[str] = None


# ==========================================================
# ES1 : DISPUTE FORM
# ==========================================================

class DisputeForm(BaseModel):
    merchant_name: Optional[str] = None
    merchant_id: Optional[str] = Field(
        None,
        description="System identifier for the merchant (e.g. 'MID-TECH-998'). Not a display name.",
    )
    customer_name: Optional[str] = None

    dispute_reason: Optional[str] = None
    canonical_dispute_reason: Optional[str] = None

    claim: str

    requested_resolution: Optional[str] = None

    disputed_amount: Optional[float] = None
    currency: Optional[str] = None

    # Canonical entity slots -- populated deterministically from the intake form
    # so downstream stages (graph builder, evidence agent) can converge on the
    # same item hubs without depending on free-text subject_entity labels.
    order_id: Optional[str] = Field(None, description="Primary order/transaction reference.")
    ordered_item_sku: Optional[str] = Field(None, description="SKU of the ordered item if known.")
    ordered_item_name: Optional[str] = Field(None, description="Display name of the ordered item.")
    received_item_name: Optional[str] = Field(None, description="Display name of the received item if different.")
    delivery_date: Optional[datetime] = Field(
        None,
        description="Date the item was actually delivered. Null when no delivery evidence exists in this document.",
    )


# ==========================================================
# ES2 : PURCHASE RECORD
# ==========================================================

class PurchaseItem(BaseModel):
    name: str
    sku: Optional[str] = None
    quantity: Optional[int] = None
    price: Optional[float] = None


class PurchaseRecord(BaseModel):
    merchant_name: Optional[str] = None
    order_id: Optional[str] = None
    purchase_date: Optional[datetime] = None
    total_amount: Optional[float] = None
    currency: Optional[str] = None
    shipping_address: Optional[str] = None
    billing_address: Optional[str] = None
    items: List[PurchaseItem] = []


# ==========================================================
# ES3 : TRACKING REPORT
# ==========================================================

class TrackingEvent(BaseModel):
    timestamp: Optional[datetime] = None
    status: str
    location: Optional[str] = None


class TrackingReport(BaseModel):
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    delivery_status: Optional[str] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    timeline: List[TrackingEvent] = []


# ==========================================================
# ES4 : DELIVERY PROOF
# ==========================================================

class DeliveryProof(BaseModel):
    tracking_number: Optional[str] = None
    delivery_date: Optional[datetime] = None
    gps_coordinates: Optional[str] = None
    signature_collected: Optional[bool] = None
    recipient_name: Optional[str] = None
    image_timestamp: Optional[datetime] = None
    delivery_location_description: Optional[str] = None


# ==========================================================
# ES5 : COMMUNICATION LOG
# ==========================================================

class Message(BaseModel):
    sender: str
    recipient: str
    timestamp: Optional[datetime] = None
    body: str


class CommunicationLog(BaseModel):
    channel: Optional[str] = None
    messages: List[Message] = []


# ==========================================================
# ES6 : MERCHANT POLICY
# ==========================================================

class PolicyClause(BaseModel):
    clause_id: Optional[str] = None
    text: str


class MerchantPolicy(BaseModel):
    policy_name: Optional[str] = None
    refund_window_days: Optional[int] = None
    cancellation_window_days: Optional[int] = None
    clauses: List[PolicyClause] = []


# ==========================================================
# ES7 : USAGE LOG
# ==========================================================

class UsageEvent(BaseModel):
    timestamp: Optional[datetime] = None
    event_type: str
    device: Optional[str] = None
    ip_address: Optional[str] = None
    details: Optional[str] = None


class UsageLog(BaseModel):
    user_id: Optional[str] = None
    account_name: Optional[str] = None
    events: List[UsageEvent] = []


# ==========================================================
# ES8 : PROCESSOR LOG & SECURITY METADATA
# ==========================================================

class ProcessorLog(BaseModel):
    transaction_reference: Optional[str] = None
    order_id: Optional[str] = None
    payment_status: Optional[str] = None
    gateway_name: Optional[str] = None
    auth_code: Optional[str] = None
    avs_result: Optional[str] = None
    cvv_result: Optional[str] = None
    three_ds_status: Optional[str] = None
    three_ds_authenticated: Optional[bool] = None
    device_fingerprint: Optional[str] = None
    ip_address: Optional[str] = None
    ip_state_or_country: Optional[str] = None
    arn: Optional[str] = None
    fraud_risk_score: Optional[float] = None
    fraud_risk_level: Optional[str] = None
    authorization_timestamp: Optional[datetime] = None
    refund_timestamp: Optional[datetime] = None


# ==========================================================
# ES9 : POLICE REPORT / GOVERNMENT RECORD
# ==========================================================

class PoliceReport(BaseModel):
    report_number: Optional[str] = None
    agency_name: Optional[str] = None
    filing_date: Optional[datetime] = None
    incident_date: Optional[datetime] = None
    incident_type: Optional[str] = None
    status: Optional[str] = None
    investigating_officer: Optional[str] = None
    incident_details: Optional[str] = None
    items_stolen: List[str] = []


# ==========================================================
# ES10 : ACCOUNT / BANK STATEMENT
# ==========================================================

class StatementLineItem(BaseModel):
    post_date: Optional[datetime] = None
    description: str
    amount: float
    transaction_type: Optional[str] = None
    reference_id: Optional[str] = None


class AccountStatement(BaseModel):
    bank_name: Optional[str] = None
    account_holder: Optional[str] = None
    account_ending_digits: Optional[str] = None
    statement_period: Optional[str] = None
    currency: Optional[str] = "USD"
    ending_balance: Optional[float] = None
    line_items: List[StatementLineItem] = []


# ==========================================================
# ES11 : ORDER STATUS & INTERNAL FULFILLMENT REPORT
# ==========================================================

class OrderStatusReport(BaseModel):
    order_id: Optional[str] = None
    fulfillment_status: Optional[str] = None
    carrier_name: Optional[str] = None
    is_tracked: Optional[bool] = None
    shipped_date: Optional[datetime] = None
    tracking_number: Optional[str] = None
    inspection_id: Optional[str] = None
    notes: Optional[str] = None


# ==========================================================
# ES12 : TRANSACTION & ORDER COMPARISON
# ==========================================================

class ComparisonEntry(BaseModel):
    order_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    item_name: Optional[str] = None
    amount: Optional[float] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    status: Optional[str] = None


class TransactionComparison(BaseModel):
    orders: List[ComparisonEntry] = []
    comparison_summary: Optional[str] = None
    is_identical_item: Optional[bool] = None
    time_delta_minutes: Optional[float] = None


# ==========================================================
# NEUTRAL EXTRACTION LAYER
# ==========================================================

class AtomicAssertion(BaseModel):
    """Represents a single, discrete factual claim made by a party."""
    claim_id: str = Field(description="Unique ID for this claim (e.g. 'claim-1')")
    assertion_text: str = Field(description="Single atomic claim text")
    subject_entity: Optional[str] = Field(None, description="Entity identifier this claim refers to")


class EntityType(str, Enum):
    """Fixed vocabulary for extracted entities. Anything not in this list
    should not be minted as an entity -- either map it to the closest valid
    type or omit it entirely.

    CHANGED: this was previously a free-text `str` field on ExtractedEntity,
    with the valid list only documented in a description string. Nothing
    enforced it, which is why hallucinated/invalid entity types slipped
    through across every category tested (e.g. entity_type="Report" for a
    "Discrepancy Report" that doesn't appear in the source text at all,
    entity_type="Policy", entity_type="Electronics" -- none of these are in
    the intended vocabulary, but plain str accepted them silently). Making
    this a real Enum means Pydantic will reject any value outside this list
    at parse time instead of passing it through.
    """
    ORDER = "Order"
    TRACKING = "Tracking"
    MERCHANT = "Merchant"
    CUSTOMER = "Customer"
    ITEM = "Item"
    ORDERED_ITEM = "OrderedItem"
    RECEIVED_ITEM = "ReceivedItem"
    REPORT = "Report"
    SESSION = "Session"
    DEVICE = "Device"
    CARRIER = "Carrier"
    GATEWAY = "Gateway"
    NETWORK = "Network"
    IP_ADDRESS = "IPAddress"
    LOCATION = "Location"
    EMAIL = "Email"
    REFUND = "Refund"
    INSPECTOR = "Inspector"
    POLICY_CLAUSE = "PolicyClause"


class ExtractedEntity(BaseModel):
    """System identifier or business entity discovered in text."""
    entity_type: EntityType = Field(
        description=(
            "Must be one of the fixed EntityType values. Do NOT invent an "
            "entity for a generic noun that's really just a topic label "
            "(e.g. 'refund', 'subscription', 'billing cycle') -- those "
            "belong in AtomicAssertion.subject_entity as free text, not as "
            "a minted ExtractedEntity with a fabricated entity_type."
        )
    )
    entity_id: str = Field(
        description=(
            "A real, unique identifying value, e.g. 'ORD-987654321', "
            "'MER-NOVAMART', 'PR-2026-9901'. Do not populate with an empty "
            "string or a placeholder -- if no genuine identifying value was "
            "found in this document, omit the entity from the list "
            "entirely rather than emitting one with a null/empty entity_id."
        )
    )
    name: Optional[str] = None


class NeutralExtraction(BaseModel):
    """Standardized extraction block for atomic assertions and discovered entities."""
    assertions: List[AtomicAssertion] = Field(default_factory=list)
    entities: List[ExtractedEntity] = Field(default_factory=list)


# ==========================================================
# GENERIC ENVELOPE
# ==========================================================

class EvidenceEnvelope(BaseModel):
    meta: EvidenceMeta

    payload: Union[
        DisputeForm,
        PurchaseRecord,
        TrackingReport,
        DeliveryProof,
        CommunicationLog,
        MerchantPolicy,
        UsageLog,
        ProcessorLog,
        PoliceReport,
        AccountStatement,
        OrderStatusReport,
        TransactionComparison,
    ]

    extraction: Optional[NeutralExtraction] = Field(default_factory=NeutralExtraction)