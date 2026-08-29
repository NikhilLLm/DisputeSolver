export type Evidence = {
  id: string
  name: string
  type: string
  detail: string
  tier?: 'TIER_1_TELEMETRY' | 'TIER_2_COMMUNICATION' | 'TIER_3_ASSERTION'
  selected?: boolean
}

export type Scenario = {
  id: string
  categoryFolder: string
  caseId: string
  label: string
  category: string
  reasonCode: string
  amount: string
  currency: string
  merchant: string
  merchantId: string
  customer: string
  date: string
  orderId: string
  claim: string
  merchantResponse: string
  merchantPrompt: string
  customerEvidence: Evidence[]
  merchantEvidence: Evidence[]
  resolutionTime: {
    cycleDays: number
    industryBaselineDays: number
    timeSavedDays: number
    reductionPct: string
    aiLatencySeconds: number
  }
  decision: {
    outcome: string
    confidence: string
    summary: string
    primaryReason?: string
    policyBasis?: string
    factors: string[]
  }
  reasoning: {
    question: string
    claims: string[]
    signals: string[]
    conclusion: string
  }
  graph: {
    nodes: { id: string; label: string; kind: string }[]
    edges: [string, string][]
  }
}

const ev = (id: string, name: string, type: string, detail: string, tier: 'TIER_1_TELEMETRY' | 'TIER_2_COMMUNICATION' | 'TIER_3_ASSERTION' = 'TIER_2_COMMUNICATION'): Evidence => ({
  id,
  name,
  type,
  detail,
  tier,
  selected: true,
})

export const scenarios: Scenario[] = [
  {
    id: 'category_0_item_not_recieved',
    categoryFolder: 'category_0_item_not recieved',
    caseId: 'DSP-2026-00187',
    label: 'Item Not Received (Category 0)',
    category: 'Item Not Received',
    reasonCode: '13.1 / 4853',
    amount: '$149.99',
    currency: 'USD',
    merchant: 'TechGadgets Inc.',
    merchantId: 'MID-TECH-889',
    customer: 'Sarah Jenkins',
    date: 'Jul 15, 2026',
    orderId: 'ORD-987654321',
    claim: 'I ordered a premium wireless headset on July 15. The tracking says delivered on July 18, but I never received the package. I checked with neighbors and my building management. No package was found. The merchant refused to refund or reship.',
    merchantResponse: 'The order was shipped via FedEx with tracking number 789456123012. Carrier tracking confirms delivery on July 18 at 2:15 PM to the customer\'s front porch. A delivery photo was captured. According to our Terms of Service (Section 4.2), carrier delivery confirmation constitutes completed fulfillment.',
    merchantPrompt: 'Provide carrier scan logs, proof of delivery photo, and applicable Terms of Service.',
    customerEvidence: [
      ev('c1', 'cardholder_order_receipt.pdf', 'PDF', 'Order #987654321 receipt for $149.99', 'TIER_2_COMMUNICATION'),
      ev('c2', 'cardholder_email_screenshot.png', 'PNG', 'Customer inquiry asking for delivery status', 'TIER_2_COMMUNICATION'),
    ],
    merchantEvidence: [
      ev('m1', 'merchant_tracking_report.pdf', 'PDF', 'FedEx Tracking #789456123012 showing delivered Jul 18', 'TIER_1_TELEMETRY'),
      ev('m2', 'merchant_delivery_photo.png', 'PNG', 'Carrier photo of package at front porch', 'TIER_1_TELEMETRY'),
      ev('m3', 'merchant_terms_of_service.pdf', 'PDF', 'Terms of Service Section 4.2 fulfillment clause', 'TIER_2_COMMUNICATION'),
    ],
    resolutionTime: {
      cycleDays: 4,
      industryBaselineDays: 45,
      timeSavedDays: 41,
      reductionPct: '91%',
      aiLatencySeconds: 12,
    },
    decision: {
      outcome: 'Merchant Defense Upheld (Proof of Delivery)',
      confidence: '89%',
      summary: 'Carrier tracking telemetry and delivery photo verify fulfillment to the cardholder address on July 18. Cardholder non-receipt claim is outweighed by Tier-1 carrier telemetry.',
      primaryReason: 'Carrier GPS delivery scan and front porch photo corroborate completed fulfillment under Visa Rule 13.1.',
      policyBasis: 'Visa Core Rule 13.1 & Merchant Terms of Service Section 4.2.',
      factors: [
        'Carrier tracking confirms delivery timestamp Jul 18 2:15 PM',
        'Visual proof of delivery photo matches recipient premises',
        'Transaction amount ($149.99) matches original order receipt',
      ],
    },
    reasoning: {
      question: 'Did the merchant provide conclusive carrier proof of delivery to the cardholder address?',
      claims: [
        'Cardholder states parcel was not received despite delivered status.',
        'Merchant states package was delivered by FedEx with photo proof.',
      ],
      signals: [
        'FedEx tracking scan records successful drop-off on Jul 18.',
        'Delivery photo provides contemporaneous physical evidence.',
        'No carrier exception or return-to-sender event was logged.',
      ],
      conclusion: 'Objective carrier telemetry substantiates fulfillment. Resolution supports the merchant.',
    },
    graph: {
      nodes: [
        { id: 'customer', label: 'Sarah Jenkins', kind: 'person' },
        { id: 'order', label: 'Order #ORD-987654321', kind: 'order' },
        { id: 'carrier', label: 'FedEx #789456123012', kind: 'delivery' },
        { id: 'photo', label: 'Porch Photo Proof', kind: 'evidence' },
        { id: 'policy', label: 'Terms Clause 4.2', kind: 'policy' },
      ],
      edges: [
        ['customer', 'order'],
        ['order', 'carrier'],
        ['carrier', 'photo'],
        ['order', 'policy'],
      ],
    },
  },
  {
    id: 'category_1_not_as_described',
    categoryFolder: 'category_1_not_as_described',
    caseId: 'DSP-2026-00201',
    label: 'Not as Described (Category 1)',
    category: 'Not as Described',
    reasonCode: '13.3 / 4855',
    amount: '$89.99',
    currency: 'USD',
    merchant: 'SoundWave Audio',
    merchantId: 'MID-SOUND-551',
    customer: 'David Miller',
    date: 'Aug 01, 2026',
    orderId: 'ORD-112233445',
    claim: 'I ordered the \'ProFit Wireless Headphones - Black Edition\' as advertised on the merchant\'s website with active noise cancellation. What I received was a generic unbranded white headset with no ANC feature and poor sound quality. I contacted the merchant for a return/exchange, but they claimed the item sent was correct.',
    merchantResponse: 'The customer received the correct product SKU (SKU-HP-BLK-01). Our quality check log confirms the item inspected and packed matched the order specifications. The customer\'s photos appear to show a different product not sold by us. Our return policy requires items to be in original condition.',
    merchantPrompt: 'Submit product catalog listing, warehouse quality inspection logs, and return policy.',
    customerEvidence: [
      ev('c1', 'cardholder_received_item_photo.png', 'PNG', 'Photo showing white unbranded headset received', 'TIER_1_TELEMETRY'),
      ev('c2', 'cardholder_advertisement_screenshot.png', 'PNG', 'Website listing displaying black ANC headphones', 'TIER_2_COMMUNICATION'),
      ev('c3', 'cardholder_communication_log.pdf', 'PDF', 'Support emails requesting return/replacement', 'TIER_2_COMMUNICATION'),
    ],
    merchantEvidence: [
      ev('m1', 'merchant_product_listing.pdf', 'PDF', 'Product catalog specifications for ProFit Headphones', 'TIER_2_COMMUNICATION'),
      ev('m2', 'merchant_quality_check_log.pdf', 'PDF', 'Quality inspection packing log for SKU-HP-BLK-01', 'TIER_1_TELEMETRY'),
      ev('m3', 'merchant_return_policy.pdf', 'PDF', 'Standard 30-day merchant return policy', 'TIER_2_COMMUNICATION'),
    ],
    resolutionTime: {
      cycleDays: 5,
      industryBaselineDays: 45,
      timeSavedDays: 40,
      reductionPct: '89%',
      aiLatencySeconds: 15,
    },
    decision: {
      outcome: 'Cardholder Refund Recommended (Material Discrepancy)',
      confidence: '91%',
      summary: 'Cardholder photographic proof shows received white unbranded unit differs materially from the advertised black ANC model on order #112233445. Cardholder attempted return within policy window.',
      primaryReason: 'Item received does not match advertised specifications in color, branding, and noise cancellation features.',
      policyBasis: 'Card Scheme Rule 13.3 (Not as Described) & Merchant 30-day Return Clause.',
      factors: [
        'Photographic evidence reveals non-matching color and unbranded hardware',
        'Website advertisement shows Black Edition with ANC specifications',
        'Cardholder initiated communication within 48 hours of receipt',
      ],
    },
    reasoning: {
      question: 'Did the goods delivered match the advertised description and purchase agreement?',
      claims: [
        'Cardholder claims received item was generic white model lacking ANC.',
        'Merchant claims warehouse QC passed SKU-HP-BLK-01.',
      ],
      signals: [
        'Photographic evidence depicts white unbranded headphones.',
        'Ad screenshot specifies black headphones with ANC.',
        'Customer communication log documents timely notification.',
      ],
      conclusion: 'Objective evidence supports material difference between ordered and received goods.',
    },
    graph: {
      nodes: [
        { id: 'customer', label: 'David Miller', kind: 'person' },
        { id: 'order', label: 'Order #ORD-112233445', kind: 'order' },
        { id: 'expected', label: 'ProFit Black ANC (Ordered)', kind: 'item' },
        { id: 'received', label: 'Generic White (Received)', kind: 'evidence' },
        { id: 'policy', label: 'Return Policy 30d', kind: 'policy' },
      ],
      edges: [
        ['customer', 'order'],
        ['order', 'expected'],
        ['order', 'received'],
        ['order', 'policy'],
      ],
    },
  },
  {
    id: 'category_2_fraudulent',
    categoryFolder: 'category_2_fraudulent',
    caseId: 'DSP-2026-00302',
    label: 'Fraudulent Transaction (Category 2)',
    category: 'Fraudulent Transaction',
    reasonCode: '10.4 / 4837',
    amount: '$320.00',
    currency: 'USD',
    merchant: 'FashionHub',
    merchantId: 'MID-FASHION-442',
    customer: 'Elena Rostova',
    date: 'Aug 11, 2026',
    orderId: 'ORD-998877665',
    claim: 'I did not make or authorize this transaction of $320.00 at FashionHub. I was asleep at 3:22 AM when the charge occurred. My card was in my possession. I have filed a police report.',
    merchantResponse: 'The transaction was processed with full security verification. AVS matched the billing address, CVV was verified, and 3D Secure was successfully completed by the user. The IP address used is consistent with the customer\'s billing state.',
    merchantPrompt: 'Provide 3D Secure authentication tokens, transaction metadata, AVS/CVV matching, and fraud score logs.',
    customerEvidence: [
      ev('c1', 'cardholder_unauthorized_statement.pdf', 'PDF', 'Signed non-authorization declaration', 'TIER_3_ASSERTION'),
      ev('c2', 'cardholder_police_report_excerpt.pdf', 'PDF', 'Police report excerpt for identity theft', 'TIER_2_COMMUNICATION'),
    ],
    merchantEvidence: [
      ev('m1', 'merchant_transaction_metadata.pdf', 'PDF', 'Gateway auth metadata showing AVS Match & CVV Match', 'TIER_1_TELEMETRY'),
      ev('m2', 'merchant_fraud_risk_score.pdf', 'PDF', 'Fraud engine risk score (Low Risk / 3DS Verified)', 'TIER_1_TELEMETRY'),
      ev('m3', 'merchant_device_fingerprint.pdf', 'PDF', 'Device fingerprint and IP geolocation log', 'TIER_1_TELEMETRY'),
    ],
    resolutionTime: {
      cycleDays: 3,
      industryBaselineDays: 45,
      timeSavedDays: 42,
      reductionPct: '93%',
      aiLatencySeconds: 8,
    },
    decision: {
      outcome: 'Merchant Defense Upheld (3DS Liability Shift)',
      confidence: '93%',
      summary: 'Merchant presented verified 3D Secure cryptographic authentication along with full AVS and CVV matching. Payment network liability shift rules assign responsibility to the card issuer.',
      primaryReason: '3D Secure 2.2 authentication and matching billing metadata shift fraud chargeback liability away from the merchant.',
      policyBasis: 'Card Scheme Fraud Rule 10.4 & EMV 3-D Secure Liability Shift Framework.',
      factors: [
        '3DS OTP authentication successfully completed at checkout',
        'AVS address verification and CVV returned exact matches',
        'Risk telemetry confirms low fraud probability score',
      ],
    },
    reasoning: {
      question: 'Do transaction authentication logs establish 3D Secure liability shift?',
      claims: [
        'Cardholder asserts card was used without permission while asleep.',
        'Merchant proves transaction was authenticated with 3DS, CVV, and AVS.',
      ],
      signals: [
        '3D Secure authentication status is fully validated.',
        'AVS and CVV both returned verified match codes.',
        'Device telemetry aligns with cardholder geographic region.',
      ],
      conclusion: 'Technical telemetry satisfies card scheme rules for merchant liability shift.',
    },
    graph: {
      nodes: [
        { id: 'customer', label: 'Elena Rostova', kind: 'person' },
        { id: 'order', label: 'Order #ORD-998877665', kind: 'order' },
        { id: 'auth', label: '3DS OTP Verified', kind: 'authentication' },
        { id: 'avs', label: 'AVS & CVV Match', kind: 'signal' },
        { id: 'policy', label: 'Fraud Rule 10.4', kind: 'policy' },
      ],
      edges: [
        ['customer', 'order'],
        ['order', 'auth'],
        ['auth', 'avs'],
        ['order', 'policy'],
      ],
    },
  },
  {
    id: 'category_3_duplicate',
    categoryFolder: 'category_3_duplicate',
    caseId: 'DSP-2026-00403',
    label: 'Duplicate Charge (Category 3)',
    category: 'Duplicate Processing',
    reasonCode: '12.6.1 / 4834',
    amount: '$45.00',
    currency: 'USD',
    merchant: 'CoffeeExpress',
    merchantId: 'MID-COFFEE-112',
    customer: 'Marcus Vance',
    date: 'Aug 10, 2026',
    orderId: 'ORD-554433222',
    claim: 'I was charged twice for the same order of coffee beans. I only intended to buy one bag. I see two charges of $45 on my statement on the same day.',
    merchantResponse: 'These are two distinct transactions. The customer placed two separate orders 45 minutes apart. Each order has a unique session ID and unique item fulfillment record. This was not a system error.',
    merchantPrompt: 'Provide transaction comparison, session logs, and distinct order fulfillment records.',
    customerEvidence: [
      ev('c1', 'cardholder_bank_statement.pdf', 'PDF', 'Bank statement with two $45.00 entries on Aug 10', 'TIER_1_TELEMETRY'),
    ],
    merchantEvidence: [
      ev('m1', 'merchant_transaction_comparison.pdf', 'PDF', 'Comparison showing ORD-554433221 and ORD-554433222', 'TIER_1_TELEMETRY'),
      ev('m2', 'merchant_session_logs.pdf', 'PDF', 'Distinct browser session IDs (09:00 vs 09:45)', 'TIER_1_TELEMETRY'),
    ],
    resolutionTime: {
      cycleDays: 2,
      industryBaselineDays: 30,
      timeSavedDays: 28,
      reductionPct: '93%',
      aiLatencySeconds: 5,
    },
    decision: {
      outcome: 'Merchant Defense Upheld (Two Distinct Orders)',
      confidence: '95%',
      summary: 'Telemetry confirms two separate checkout sessions (sess_abc123 at 09:00 and sess_xyz789 at 09:45) generating distinct orders for different bean varieties. Not a duplicate processing collision.',
      primaryReason: 'Distinct session IDs, order numbers, and 45-minute timestamp separation refute the duplicate charge claim.',
      policyBasis: 'Card Scheme Duplicate Processing Rule 12.6.1.',
      factors: [
        'Two separate checkout sessions 45 minutes apart',
        'Distinct order IDs (ORD-554433221 & ORD-554433222)',
        'Different products fulfilled (Sumatra vs Ethiopia beans)',
      ],
    },
    reasoning: {
      question: 'Were the two transactions a system duplicate or two separate intentional purchases?',
      claims: [
        'Cardholder believes two $45 charges represent accidental double billing.',
        'Merchant proves cardholder placed two separate orders 45 min apart.',
      ],
      signals: [
        'Timestamp gap is 45 minutes (exceeds duplicate threshold <5 min).',
        'Two distinct order IDs and fulfillment manifests exist in graph.',
        'Both checkouts completed independently with separate session IDs.',
      ],
      conclusion: 'Telemetry objectively disproves duplicate processing error. Merchant defense stands.',
    },
    graph: {
      nodes: [
        { id: 'customer', label: 'Marcus Vance', kind: 'person' },
        { id: 'order1', label: 'Order #ORD-554433221 (09:00)', kind: 'order' },
        { id: 'order2', label: 'Order #ORD-554433222 (09:45)', kind: 'order' },
        { id: 'sess1', label: 'Session A (Sumatra)', kind: 'payment' },
        { id: 'sess2', label: 'Session B (Ethiopia)', kind: 'payment' },
      ],
      edges: [
        ['customer', 'order1'],
        ['customer', 'order2'],
        ['order1', 'sess1'],
        ['order2', 'sess2'],
      ],
    },
  },
  {
    id: 'category_4_refund',
    categoryFolder: 'category_4_refund',
    caseId: 'DSP-2026-00504',
    label: 'Credit Not Processed (Category 4)',
    category: 'Credit Not Processed',
    reasonCode: '13.6 / 4860',
    amount: '$65.00',
    currency: 'USD',
    merchant: 'UrbanWear',
    merchantId: 'MID-URBAN-771',
    customer: 'Jessica Taylor',
    date: 'Jul 10, 2026',
    orderId: 'ORD-123456789',
    claim: 'I returned the dress on July 20 and the merchant agreed via email to refund me. It has been over 10 days and I still don\'t see the credit on my card.',
    merchantResponse: 'We acknowledge the refund is owed. Our records show the refund was successfully processed on July 25. The customer should see it on their statement shortly.',
    merchantPrompt: 'Provide processor settlement log, refund confirmation reference ARN, and refund agreement.',
    customerEvidence: [
      ev('c1', 'cardholder_refund_agreement_email.pdf', 'PDF', 'Email confirmation agreeing to $65.00 refund', 'TIER_2_COMMUNICATION'),
      ev('c2', 'cardholder_return_receipt.pdf', 'PDF', 'Physical return receipt dated July 20', 'TIER_1_TELEMETRY'),
    ],
    merchantEvidence: [
      ev('m1', 'merchant_refund_confirmation.pdf', 'PDF', 'Merchant internal refund confirmation receipt', 'TIER_2_COMMUNICATION'),
      ev('m2', 'merchant_processor_log.pdf', 'PDF', 'Payment gateway processor log showing credit issued Jul 25', 'TIER_1_TELEMETRY'),
    ],
    resolutionTime: {
      cycleDays: 3,
      industryBaselineDays: 45,
      timeSavedDays: 42,
      reductionPct: '93%',
      aiLatencySeconds: 10,
    },
    decision: {
      outcome: 'Dispute Resolved — Merchant Refund Confirmed',
      confidence: '96%',
      summary: 'Both parties agree the refund is valid. Merchant processor logs verify credit of $65.00 was dispatched on July 25 (ARN: 745892100234). Dispute closed as settled.',
      primaryReason: 'Merchant processor logs prove refund was issued to cardholder account on July 25.',
      policyBasis: 'Card Scheme Credit Processing Rule 13.6.',
      factors: [
        'Agreed return acknowledged by both cardholder and merchant',
        'Gateway processor log confirms $65.00 credit issued Jul 25',
        'Acquirer reference number (ARN) available for bank tracking',
      ],
    },
    reasoning: {
      question: 'Did the merchant process the agreed credit within the required timeframe?',
      claims: [
        'Cardholder states credit was not received 10 days post-return.',
        'Merchant states refund was executed on July 25 via gateway.',
      ],
      signals: [
        'Return receipt and merchant email agree on $65 refund amount.',
        'Processor ledger contains matching credit authorization entry.',
        'Timestamp confirms merchant acted 5 days after physical return.',
      ],
      conclusion: 'Credit was properly transmitted by merchant. Case marked as fulfilled refund.',
    },
    graph: {
      nodes: [
        { id: 'customer', label: 'Jessica Taylor', kind: 'person' },
        { id: 'order', label: 'Order #ORD-123456789', kind: 'order' },
        { id: 'return', label: 'Return Receipt (Jul 20)', kind: 'evidence' },
        { id: 'refund', label: 'Credit Auth $65 (Jul 25)', kind: 'payment' },
      ],
      edges: [
        ['customer', 'order'],
        ['order', 'return'],
        ['return', 'refund'],
      ],
    },
  },
  {
    id: 'category_5_subscription',
    categoryFolder: 'category_5_subscription',
    caseId: 'DSP-2026-00605',
    label: 'Cancelled Subscription (Category 5)',
    category: 'Cancelled Recurring Transaction',
    reasonCode: '13.2 / 4841',
    amount: '$19.99',
    currency: 'USD',
    merchant: 'StreamMax',
    merchantId: 'MID-STREAM-009',
    customer: 'Alexander Wright',
    date: 'Aug 01, 2026',
    orderId: 'SUB-887766',
    claim: 'I cancelled my StreamMax subscription on July 28. I received a confirmation email. However, I was still charged $19.99 on August 1. I have not used the service since I cancelled.',
    merchantResponse: 'The customer did initiate a cancellation, but our logs show continued usage of the service on August 2nd and 3rd. According to our terms, usage after the billing date constitutes a renewal of the subscription for the next month.',
    merchantPrompt: 'Provide subscription terms, access logs post-cancellation, and billing event records.',
    customerEvidence: [
      ev('c1', 'cardholder_cancellation_confirmation.pdf', 'PDF', 'Cancellation email received July 28', 'TIER_2_COMMUNICATION'),
    ],
    merchantEvidence: [
      ev('m1', 'merchant_subscription_terms.pdf', 'PDF', 'Subscription Terms Section 5 (Post-cancellation usage)', 'TIER_2_COMMUNICATION'),
      ev('m2', 'merchant_usage_logs.pdf', 'PDF', 'Active video streaming sessions logged Aug 2 & Aug 3', 'TIER_1_TELEMETRY'),
    ],
    resolutionTime: {
      cycleDays: 5,
      industryBaselineDays: 45,
      timeSavedDays: 40,
      reductionPct: '89%',
      aiLatencySeconds: 14,
    },
    decision: {
      outcome: 'Contested — Post-Cancellation Usage Conflict',
      confidence: '79%',
      summary: 'Cardholder holds valid cancellation notice from July 28, but merchant server logs reflect active streaming on August 2-3. Partial refund or terms review recommended.',
      primaryReason: 'Timely cancellation on July 28 conflicts with subsequent active usage logs under Terms Section 5.',
      policyBasis: 'Card Scheme Recurring Billing Rule 13.2 & StreamMax Terms Section 5.',
      factors: [
        'Valid cancellation confirmation timestamped July 28',
        'Server logs show 3.5 hours of streaming on August 2-3',
        'Terms specify continued usage voids immediate billing stop',
      ],
    },
    reasoning: {
      question: 'Does post-cancellation platform usage invalidate the July 28 cancellation confirmation?',
      claims: [
        'Cardholder proves cancellation was confirmed on July 28 before billing.',
        'Merchant proves customer streamed media on August 2 and 3.',
      ],
      signals: [
        'Cancellation email timestamp is July 28 (prior to August 1 charge).',
        'Device and IP telemetry confirm active streaming sessions post-billing.',
        'Terms of Service clause contains post-cancellation renewal trigger.',
      ],
      conclusion: 'Submissions are mutually contradictory regarding intent. Requires policy interpretation.',
    },
    graph: {
      nodes: [
        { id: 'customer', label: 'Alexander Wright', kind: 'person' },
        { id: 'sub', label: 'Subscription #SUB-887766', kind: 'subscription' },
        { id: 'cancel', label: 'Cancel Notice (Jul 28)', kind: 'signal' },
        { id: 'usage', label: 'Active Stream Logs (Aug 2)', kind: 'evidence' },
        { id: 'policy', label: 'Terms Clause 5', kind: 'policy' },
      ],
      edges: [
        ['customer', 'sub'],
        ['sub', 'cancel'],
        ['sub', 'usage'],
        ['sub', 'policy'],
      ],
    },
  },
  {
    id: 'category_6_error',
    categoryFolder: 'category_6_error',
    caseId: 'DSP-2026-00706',
    label: 'Incorrect Amount / Surcharge (Category 6)',
    category: 'Incorrect Transaction Amount',
    reasonCode: '12.2 / 4831',
    amount: '$85.00',
    currency: 'USD',
    merchant: 'GourmetBistro',
    merchantId: 'MID-GOURMET-883',
    customer: 'Rachel Adams',
    date: 'Aug 12, 2026',
    orderId: 'ORD-332211',
    claim: 'I was charged $85 for a dinner that cost $55. My receipt clearly shows $55. The merchant seems to have added an unauthorized $30 charge.',
    merchantResponse: 'The $85 charge is correct. It includes the base price of $55 plus a mandatory $30 \'Chef\'s Table\' service fee that is applied to all weekend bookings.',
    merchantPrompt: 'Submit POS receipt, pricing schedule, and customer booking consent for additional fees.',
    customerEvidence: [
      ev('c1', 'cardholder_order_receipt.pdf', 'PDF', 'Itemized receipt showing $55.00 total paid', 'TIER_1_TELEMETRY'),
    ],
    merchantEvidence: [
      ev('m1', 'merchant_pricing_breakdown.pdf', 'PDF', 'Weekend Chef\'s Table pricing schedule with $30 fee', 'TIER_2_COMMUNICATION'),
      ev('m2', 'merchant_pos_system_log.pdf', 'PDF', 'POS system terminal log recording $85.00 settlement', 'TIER_1_TELEMETRY'),
    ],
    resolutionTime: {
      cycleDays: 3,
      industryBaselineDays: 30,
      timeSavedDays: 27,
      reductionPct: '90%',
      aiLatencySeconds: 7,
    },
    decision: {
      outcome: 'Partial Refund of $30 Discrepancy Recommended',
      confidence: '92%',
      summary: 'Cardholder itemized receipt reflects $55.00 agreed payment at time of signing. Undisclosed $30 surcharge added at settlement violates transaction amount integrity rules.',
      primaryReason: 'Receipt signed by customer specifies $55.00 total; merchant failed to prove cardholder consent for $30 fee at point of sale.',
      policyBasis: 'Card Scheme Rule 12.2 (Incorrect Transaction Amount).',
      factors: [
        'Customer signed receipt totals $55.00',
        'Settled amount was altered to $85.00 without cardholder authorization',
        'Card scheme rules require explicit disclosure before authorization',
      ],
    },
    reasoning: {
      question: 'Was the $30 service surcharge explicitly disclosed and authorized at checkout?',
      claims: [
        'Cardholder shows physical receipt for $55.00.',
        'Merchant claims mandatory $30 fee applies to weekend bookings.',
      ],
      signals: [
        'Receipt provided by cardholder lacks the $30 surcharge item.',
        'Math difference between receipt ($55) and charge ($85) equals exactly $30.',
        'No cardholder signature exists approving the $85.00 total.',
      ],
      conclusion: 'Cardholder authorized only $55.00. Refund of $30.00 delta is warranted.',
    },
    graph: {
      nodes: [
        { id: 'customer', label: 'Rachel Adams', kind: 'person' },
        { id: 'order', label: 'Dining Order #ORD-332211', kind: 'order' },
        { id: 'receipt', label: 'Receipt ($55.00)', kind: 'evidence' },
        { id: 'settled', label: 'Settled Charge ($85.00)', kind: 'payment' },
        { id: 'delta', label: 'Discrepancy ($30.00)', kind: 'signal' },
      ],
      edges: [
        ['customer', 'order'],
        ['order', 'receipt'],
        ['order', 'settled'],
        ['settled', 'delta'],
      ],
    },
  },
  {
    id: 'category_7_weak',
    categoryFolder: 'category_7_weak',
    caseId: 'DSP-2026-00807',
    label: 'Weak Telemetry / Missing Tracking (Category 7)',
    category: 'Item Not Received',
    reasonCode: '13.1 / 4853',
    amount: '$25.00',
    currency: 'USD',
    merchant: 'GadgetWorld',
    merchantId: 'MID-GADGET-221',
    customer: 'Timothy Clark',
    date: 'Aug 05, 2026',
    orderId: 'ORD-445566',
    claim: 'I ordered a wireless mouse 10 days ago and I have not received it. The merchant has not provided any tracking information despite multiple requests.',
    merchantResponse: 'We shipped the item as per our internal records. We do not have a tracking number available for this low-value shipment.',
    merchantPrompt: 'Provide carrier tracking number, shipping manifest, or delivery confirmation.',
    customerEvidence: [
      ev('c1', 'cardholder_order_confirmation.pdf', 'PDF', 'Order confirmation for $25.00 wireless mouse', 'TIER_2_COMMUNICATION'),
    ],
    merchantEvidence: [
      ev('m1', 'merchant_internal_order_status.pdf', 'PDF', 'Internal software status marked as \'Dispatched\'', 'TIER_3_ASSERTION'),
    ],
    resolutionTime: {
      cycleDays: 2,
      industryBaselineDays: 45,
      timeSavedDays: 43,
      reductionPct: '96%',
      aiLatencySeconds: 4,
    },
    decision: {
      outcome: 'Cardholder Refund Recommended (Insufficient Merchant Proof)',
      confidence: '95%',
      summary: 'Merchant admitted no carrier tracking number exists. Internal status notes are Tier-3 assertions and cannot overcome missing carrier delivery proof under Rule 13.1.',
      primaryReason: 'Merchant failed to submit verifiable carrier tracking or proof of delivery.',
      policyBasis: 'Card Scheme Delivery Rule 13.1 (Mandatory Carrier Tracking Standard).',
      factors: [
        'No carrier tracking number provided by merchant',
        'Internal order status is an unverified assertion',
        'Non-delivery claim stands unrebutted by objective telemetry',
      ],
    },
    reasoning: {
      question: 'Did merchant satisfy mandatory delivery proof requirements without carrier tracking?',
      claims: [
        'Cardholder states item never arrived and no tracking was given.',
        'Merchant states item was dispatched internally without tracking.',
      ],
      signals: [
        'Merchant submission lacks any carrier scan or tracking identifier.',
        'Internal notes are self-reported with low evidential weight (Tier 3).',
        'Card scheme rules require independent carrier delivery proof.',
      ],
      conclusion: 'Absence of carrier telemetry compels resolution in favor of cardholder.',
    },
    graph: {
      nodes: [
        { id: 'customer', label: 'Timothy Clark', kind: 'person' },
        { id: 'order', label: 'Order #ORD-445566', kind: 'order' },
        { id: 'receipt', label: 'Confirmation ($25)', kind: 'evidence' },
        { id: 'missing_track', label: 'No Carrier Tracking', kind: 'signal' },
        { id: 'policy', label: 'Rule 13.1 Mandate', kind: 'policy' },
      ],
      edges: [
        ['customer', 'order'],
        ['order', 'receipt'],
        ['order', 'missing_track'],
        ['missing_track', 'policy'],
      ],
    },
  },
]

export const getScenario = (id: string) => scenarios.find((scenario) => scenario.id === id || scenario.caseId === id) ?? scenarios[0]

export type TimelineEvent = { label: string; detail: string; status: 'complete' | 'current' | 'pending' }
export const initialTimeline = (): TimelineEvent[] => [
  { label: 'Case created', detail: 'Cardholder dispute intake ingested from data repository', status: 'current' },
  { label: 'Merchant notified', detail: 'Waiting for merchant defense representment', status: 'pending' },
  { label: 'Merchant response', detail: 'Merchant telemetry & counter-evidence submitted', status: 'pending' },
  { label: 'AI investigation', detail: 'Deterministic rules & evidence tiers cross-checked', status: 'pending' },
  { label: 'Decision ready', detail: 'Explainable resolution & graph synthesized', status: 'pending' },
]
