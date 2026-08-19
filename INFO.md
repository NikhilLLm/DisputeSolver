# Dispute Reason Code & Evidence Matrix

A reference table mapping dispute **categories** across the four major US card networks (Visa, Mastercard, American Express, Discover) to their reason codes, and the evidence typically required from **both** the cardholder and the merchant side.

> **How to read this:** Reason codes describe the cardholder's *claim*, not a verified fact — treat every row as a starting classification, not a verdict. Evidence lists are non-exhaustive guidance published by networks/processors, not hard pass/fail checklists — sufficiency is ultimately judged case-by-case. Where a cell says "not publicly standardized," that network doesn't publish a granular structured requirement the way Visa/Stripe do — treat it as lower-confidence and confirm against current network documentation before hardcoding it into your rule engine.

---

## 1. Product / Service Not Received

**Definition:** Cardholder claims goods or services paid for were never delivered/rendered.

| Network | Reason Code | Code Meaning |
|---|---|---|
| Visa | 13.1 | Merchandise/Services Not Received |
| Mastercard | 4855 | Goods or Services Not Provided |
| American Express | C08 | Goods/Services Not Received or Only Partially Received |
| Discover | RG | Non-Receipt of Goods, Services, or Cash |

**Cardholder evidence typically submitted:**
- Written statement describing non-receipt
- Order confirmation (to prove the purchase occurred)
- Any communication attempts with the merchant about the missing item
- Screenshot of order/account status showing no delivery confirmation

**Merchant evidence typically required (physical goods):**
- Terms of service covering delivery confirmation and disputes
- Carrier tracking history with delivery date, carrier, and status
- Proof of delivery: signature capture or delivery photo
- Email notifications sent before/during/after delivery
- Address match between shipping and billing/order address

**Merchant evidence (digital goods):**
- Terms of service covering delivery/activation
- Delivery/access notification emails
- Customer account activity log (download, activation, access)
- Usage data: activation date, login sessions

**Merchant evidence (services):**
- Terms of service covering service delivery
- Scheduling/completion communication with customer
- Confirmation receipt of service completion
- Session logs (scheduling, reminders, session notes)

---

## 2. Product / Service Not as Described (Unacceptable Quality)

**Definition:** Cardholder claims what they received doesn't match what was advertised or expected.

| Network | Reason Code | Code Meaning |
|---|---|---|
| Visa | 13.3 | Not as Described or Defective Merchandise/Services |
| Mastercard | 4853 | Cardholder Dispute — Defective/Not as Described |
| American Express | C31 | Goods/Services Not as Described |
| Discover | RM | Quality Discrepancy |

**Cardholder evidence typically submitted:**
- Description of the discrepancy between advertised and received item
- Photos of the received product (if defective/different)
- Copy of the original listing/advertisement they relied on
- Any merchant response to their complaint (or lack thereof)

**Merchant evidence typically required:**
- Full product listing as it appeared at time of purchase
- Evidence the product functioned/matched as advertised
- Pre-shipment quality/specification documentation
- Feature verification summary showing advertised features were functional and used
- Support ticket logs showing no functionality complaints, or resolution notes if a complaint was resolved
- Refund/return policy the customer agreed to

---

## 3. Fraudulent / Unauthorized Transaction

**Definition:** Cardholder claims they did not authorize or make the transaction (card-not-present or lost/stolen card scenarios).

| Network | Reason Code | Code Meaning |
|---|---|---|
| Visa | 10.4 | Other Fraud — Card-Absent Environment |
| Mastercard | 4837 | No Cardholder Authorization |
| American Express | F29 | Card Not Present — Fraud |
| Discover | UA** | Unauthorized (series, e.g. UA01–UA05 by sub-type) |

**Cardholder evidence typically submitted:**
- Statement that they did not make or authorize the transaction
- Confirmation the card was lost/stolen, or account/credentials compromised (if applicable)
- List of other unrecognized transactions, if part of a pattern

**Merchant evidence typically required:**
- Investigation summary concluding the transaction was legitimate
- IP/geolocation data consistent with billing address or prior order history
- Fraud risk score assigned to the transaction (if available), noting it was low-risk
- Proof of AVS (Address Verification System) match, CVV verification, and 3D Secure (3DS) completion
- Customer verification details (account history, device fingerprint, prior legitimate orders)

---

## 4. Duplicate Processing / Duplicate Charge

**Definition:** Cardholder claims they were charged more than once for the same transaction.

| Network | Reason Code | Code Meaning |
|---|---|---|
| Visa | 12.6.1 | Duplicate Processing |
| Mastercard | 4834 | Duplicate Processing |
| American Express | P05 | Duplicate Charge |
| Discover | DP | Duplicate Processing |

**Cardholder evidence typically submitted:**
- Bank/card statement showing the two (or more) charges
- Statement that only one purchase was intended

**Merchant evidence typically required (if charges were legitimately separate):**
- Investigation summary
- Side-by-side comparison of both transactions, highlighting differentiators (different order/session IDs)
- Time-gap analysis showing the charges are inconsistent with a system duplication error
- Evidence the customer explicitly completed two separate purchase actions (e.g., two distinct "Complete Purchase" clicks/sessions)

**Merchant evidence (if it was genuinely a duplicate, i.e., conceding):**
- Investigation summary acknowledging the duplicate
- Proof one of the two transactions was refunded (refund confirmation, processor log, bank statement record)

---

## 5. Credit / Refund Not Processed

**Definition:** Cardholder claims they were promised or are entitled to a refund/credit that was never issued.

| Network | Reason Code | Code Meaning |
|---|---|---|
| Visa | 13.6 | Credit Not Processed |
| Mastercard | 4860 | Credit Not Processed |
| American Express | C05 | Credit Not Processed |
| Discover | RN | Credit Not Processed |

**Cardholder evidence typically submitted:**
- Communication showing merchant agreed to issue a refund/credit
- Return confirmation (if a physical item was returned)
- Statement/date by which the refund was expected but not received

**Merchant evidence typically required (to deny — refund not owed):**
- Reason for denial (e.g., return policy not met, window expired)
- Communication history showing the customer was informed of the policy before the dispute
- Terms of sale presented at checkout, with contact information provided

**Merchant evidence (to concede — refund was in fact processed or is owed):**
- Proof of the original transaction
- Refund confirmation, payment processor log, and merchant account statement showing the credit was issued

---

## 6. Subscription Canceled / Recurring Billing Dispute

**Definition:** Cardholder claims they were billed for a subscription after they canceled it.

| Network | Reason Code | Code Meaning |
|---|---|---|
| Visa | 13.2 | Cancelled Recurring Transaction |
| Mastercard | 4841 | Cancelled Recurring Transaction |
| American Express | C28 | Cancelled Recurring Billing |
| Discover | RM3** | Cancelled Recurring Transaction (sub-code) |

**Cardholder evidence typically submitted:**
- Cancellation confirmation (email, screenshot, or reference number) if they have one
- Date they attempted to cancel
- Statement that no further service was used after the claimed cancellation date

**Merchant evidence typically required:**
- Subscription terms agreed to at signup, including renewal/cancellation/refund policy
- Evidence the customer received and agreed to these terms
- Cancellation-confirmation email process (proof one is auto-sent on cancellation)
- Available cancellation methods (self-service + support channel)
- Evidence the subscription was active and billed without any cancellation request on file
- Usage logs showing continued use after the claimed cancellation date (undermines the claim)
- Renewal reminder emails sent before the billing date

---

## 7. Processing Errors (Incorrect Amount / Currency)

**Definition:** Cardholder claims they were billed the wrong amount, wrong currency, or the transaction was processed incorrectly.

| Network | Reason Code | Code Meaning |
|---|---|---|
| Visa | 12.2 / 12.5 | Incorrect Transaction Amount / Incorrect Currency |
| Mastercard | 4831 | Transaction Amount Differs |
| American Express | P04 | Incorrect Amount |
| Discover | AT | Altered Amount |

**Cardholder evidence typically submitted:**
- Receipt or order confirmation showing the expected amount
- Statement/card record showing the actual amount charged

**Merchant evidence typically required:**
- POS data / system logs showing the transaction amount at time of sale
- Pricing and tax breakdown as displayed to the customer
- Proof the total amount was clearly presented before payment
- Transaction ID, date, and authorization code for verification

---

## Notes on Network-Specific Formatting

| Network | Code Format | Structural Logic |
|---|---|---|
| Visa | Decimal (e.g., 13.1, 10.4) | Grouped under 10.x = Fraud, 11.x = Authorization, 12.x = Processing Errors, 13.x = Consumer Disputes |
| Mastercard | 4-digit numeric (e.g., 4855, 4837) | Grouped by Fraud, Authorization, Point-of-Interaction Errors, Cardholder Disputes |
| American Express | Alphanumeric, letter + number (e.g., C08, F29, P05) | Letter prefix = category: A (Authorization), C (Consumer Dispute), F (Fraud), P (Processing Error) |
| Discover | Mostly 2-letter codes, fraud sub-codes numeric (e.g., RG, UA01) | Grouped by Cardholder Disputes and Authorization Errors; fraud codes generally start with UA |

---

## How This Maps to Your Pipeline

- **Intake/classification agent** → uses this table's left columns (network + code) to route an incoming dispute into the correct **category** row.
- **Evidence checklist agent** → uses the category's evidence columns as the *required-category* checklist (deterministic gate — Layer 1 in our earlier discussion), not as weighted scores yet.
- **Trust/confidence scoring** → applied *within* each submitted evidence item (e.g., is the tracking data legitimate, is the complaint narrative internally consistent) — this table only tells you *what* to check for, not *how strong* any given submission is.
- **Cross-network normalization** → since your system likely won't know the issuer's exact network in advance, classify by **category** first (this table's section headers), then map to the specific network code only if/when you need to cite it back to the issuer.

---

## Sources & Confidence Notes

- Stripe's merchant-side evidence guidance (categories, evidence types, and visual examples) is pulled from Stripe's official docs: `docs.stripe.com/disputes/reason-codes-defense-requirements` and `docs.stripe.com/disputes/visual-evidence` — high confidence, current as of your session.
- Network reason code numbers/letters (Visa 13.1/10.4, Mastercard 4855/4837, Amex C08/F29, Discover RG/UA) are corroborated across multiple independent chargeback-management sources (Chargebacks911, Chargeflow, MidMetrics) — moderate-high confidence, but **networks do revise codes periodically** (e.g., Visa's 2018 VCR consolidation), so verify current codes against Visa/Mastercard/Amex's own published guides before hardcoding into production.
- Cardholder-side evidence columns are **inferred symmetrically** from merchant-side requirements (since networks document evidence requirements merchant-first) — treat these as reasonable defaults for your MVP, not verbatim from an issuer policy document.
- Discover and Amex evidence specifics are less granularly documented publicly than Visa/Mastercard/Stripe — flagged above where applicable.