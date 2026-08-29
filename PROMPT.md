//Final Canaocial JSON FOR EACH CATEGORY

1.Not_as_described

{
  "title": "Canonical Case Evidence Extractions",
  "case_id": "DSP-2026-00201",
  "generated_at": "2026-08-16T12:19:29Z",
  "summary": {
    "source_data_dir": "data\\category_1_not_as_described",
    "total_documents_processed": 8,
    "structured_form_documents": 2,
    "unstructured_documents": 6,
    "unique_entities_discovered": {
      "case_ids": [
        "DSP-2026-00201"
      ],
      "order_ids": [
        "ORD-112233445"
      ],
      "tracking_numbers": [],
      "merchants": [
        "TechGadgets Inc."
      ]
    }
  },
  "extractions": [
    {
      "meta": {
        "case_id": "DSP-2026-00201",
        "document_id": "doc-form-cardholder_intake_fo-1786882737",
        "file_name": "cardholder_intake_form.json",
        "owner": "cardholder",
        "evidence_type": "DISPUTE_FORM",
        "extraction_method": "deterministic_regex_form_parser",
        "extracted_at": "2026-07-25T09:00:00Z",
        "confidence": 1.0
      },
      "payload": {
        "merchant_name": "TechGadgets Inc.",
        "customer_name": "Cardholder",
        "dispute_reason": "Not as Described",
        "claim": "I ordered the ProFit Wireless Headphones in Black, but I received a much cheaper 'Standard' model in White. The box was even mislabeled. I tried to contact the merchant but they told me all sales are final for 'electronics', which contradicts their website.",
        "requested_resolution": "Full refund",
        "disputed_amount": 199.99,
        "currency": "USD"
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "ast-form-882737-1",
            "assertion_text": "I ordered the ProFit Wireless Headphones in Black, but I received a much cheaper 'Standard' model in White. The box was even mislabeled. I tried to contact the merchant but they told me all sales are final for 'electronics', which contradicts their website.",
            "subject_entity": "ORD-112233445"
          }
        ],
        "entities": [
          {
            "entity_type": "Merchant",
            "entity_id": "MER-TECHGADGETS-INC.",
            "name": "TechGadgets Inc."
          },
          {
            "entity_type": "Order",
            "entity_id": "ORD-112233445",
            "name": "ORD-112233445"
          }
        ]
      }
    },
    {
      "meta": {
        "case_id": "DSP-2026-00201",
        "document_id": "doc-form-merchant_response_fo-1786882737",
        "file_name": "merchant_response_form.json",
        "owner": "merchant",
        "evidence_type": "DISPUTE_FORM",
        "extraction_method": "deterministic_regex_form_parser",
        "extracted_at": "2026-07-28T14:00:00Z",
        "confidence": 1.0
      },
      "payload": {
        "merchant_name": "TechGadgets Inc.",
        "customer_name": "Cardholder",
        "dispute_reason": "13.3",
        "claim": "The customer received the correct item as per our shipping records. Our quality check log confirms the Black Pro model was packed. Furthermore, the customer is outside our 5-day electronics return window.",
        "requested_resolution": "deny refund",
        "currency": "USD"
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "ast-form-882737-1",
            "assertion_text": "The customer received the correct item as per our shipping records. Our quality check log confirms the Black Pro model was packed. Furthermore, the customer is outside our 5-day electronics return window.",
            "subject_entity": null
          }
        ],
        "entities": []
      }
    },
    {
      "meta": {
        "case_id": "DSP-2026-00201",
        "document_id": "doc-cardholder_advertise-1786882737",
        "file_name": "cardholder_advertisement_screenshot.png",
        "owner": "cardholder",
        "evidence_type": "COMMUNICATION_LOG",
        "extracted_at": "2026-08-16T12:19:00Z",
        "confidence": 0.95,
        "processed_by": "groq_vision_vlm"
      },
      "payload": {
        "messages": []
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "claim-1",
            "assertion_text": "The product is ProFit Wireless Headphones.",
            "subject_entity": "product"
          },
          {
            "claim_id": "claim-2",
            "assertion_text": "The selected color is BLACK.",
            "subject_entity": "product"
          },
          {
            "claim_id": "claim-3",
            "assertion_text": "The price of the product is $199.99 USD.",
            "subject_entity": "product"
          },
          {
            "claim_id": "claim-4",
            "assertion_text": "The product features include Noise Cancelling and Metal Finish.",
            "subject_entity": "product"
          }
        ],
        "entities": [
          {
            "entity_type": "Merchant",
            "entity_id": "TechGadgets Inc.",
            "name": "TechGadgets Inc."
          },
          {
            "entity_type": "Item",
            "entity_id": "ProFit Wireless Headphones",
            "name": "ProFit Wireless Headphones"
          }
        ]
      }
    },
    {
      "meta": {
        "case_id": "DSP-2026-00201",
        "document_id": "doc-cardholder_communica-1786882741",
        "file_name": "cardholder_communication_log.pdf",
        "owner": "cardholder",
        "evidence_type": "COMMUNICATION_LOG",
        "extracted_at": "2026-08-16T12:19:02Z",
        "confidence": 0.95,
        "processed_by": "ocr_pdf_txt_extractor"
      },
      "payload": {
        "channel": "Email",
        "messages": [
          {
            "sender": "Alice Johnson",
            "recipient": "TechGadgets Inc. Support",
            "timestamp": "2026-07-22T00:00:00Z",
            "body": "Hi, I received order ORD-112233445 but it's the wrong model and color. I ordered the Black Pro model and got White Standard. Please help."
          },
          {
            "sender": "TechGadgets Inc. Support",
            "recipient": "Alice Johnson",
            "timestamp": "2026-07-23T00:00:00Z",
            "body": "Hi Alice, we have reviewed your order. Our policy states that all electronics are final sale. We cannot offer a return or exchange at this time."
          }
        ]
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "claim-1",
            "assertion_text": "I received order ORD-112233445 but it's the wrong model and color.",
            "subject_entity": "ORD-112233445"
          },
          {
            "claim_id": "claim-2",
            "assertion_text": "I ordered the Black Pro model and got White Standard.",
            "subject_entity": "ORD-112233445"
          },
          {
            "claim_id": "claim-3",
            "assertion_text": "Our policy states that all electronics are final sale.",
            "subject_entity": "TechGadgets Inc. Support"
          },
          {
            "claim_id": "claim-4",
            "assertion_text": "We cannot offer a return or exchange at this time.",
            "subject_entity": "TechGadgets Inc. Support"
          }
        ],
        "entities": [
          {
            "entity_type": "Order",
            "entity_id": "ORD-112233445",
            "name": "ORD-112233445"
          },
          {
            "entity_type": "Customer",
            "entity_id": "Alice Johnson",
            "name": "Alice Johnson"
          },
          {
            "entity_type": "Merchant",
            "entity_id": "TechGadgets Inc. Support",
            "name": "TechGadgets Inc. Support"
          },
          {
            "entity_type": "Item",
            "entity_id": "Black Pro model",
            "name": "Black Pro model"
          },
          {
            "entity_type": "Item",
            "entity_id": "White Standard",
            "name": "White Standard"
          }
        ]
      }
    },
    {
      "meta": {
        "case_id": "DSP-2026-00201",
        "document_id": "doc-cardholder_received_-1786882743",
        "file_name": "cardholder_received_item_photo.png",
        "owner": "cardholder",
        "evidence_type": "DELIVERY_PROOF",
        "extracted_at": "2026-08-16T12:19:23Z",
        "confidence": 0.95,
        "processed_by": "groq_vision_vlm"
      },
      "payload": {},
      "extraction": {
        "assertions": [
          {
            "claim_id": "claim-1",
            "assertion_text": "The item received is a White Standard Headphones.",
            "subject_entity": "Item"
          },
          {
            "claim_id": "claim-2",
            "assertion_text": "The condition of the item is Mismatched with order.",
            "subject_entity": "Item"
          },
          {
            "claim_id": "claim-3",
            "assertion_text": "The item received does not match the Black metal Pro model ordered.",
            "subject_entity": "Item"
          },
          {
            "claim_id": "claim-4",
            "assertion_text": "The case number for this dispute is DSP-2026-00201.",
            "subject_entity": "Case"
          }
        ],
        "entities": [
          {
            "entity_type": "Item",
            "entity_id": null,
            "name": "White Standard Headphones"
          },
          {
            "entity_type": "Case",
            "entity_id": "DSP-2026-00201",
            "name": null
          }
        ]
      }
    },
    {
      "meta": {
        "case_id": "DSP-2026-00201",
        "document_id": "doc-merchant_product_lis-1786882764",
        "file_name": "merchant_product_listing.pdf",
        "owner": "merchant",
        "evidence_type": "PURCHASE_RECORD",
        "extracted_at": "2026-08-16T12:19:25Z",
        "confidence": 0.95,
        "processed_by": "ocr_pdf_txt_extractor"
      },
      "payload": {
        "items": [
          {
            "name": "ProFit Wireless Headphones",
            "price": 199.99
          }
        ]
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "claim-1",
            "assertion_text": "The product name is ProFit Wireless Headphones.",
            "subject_entity": "Item"
          },
          {
            "claim_id": "claim-2",
            "assertion_text": "The product has a price of $199.99.",
            "subject_entity": "Item"
          },
          {
            "claim_id": "claim-3",
            "assertion_text": "The product has a description of High-end audio with noise cancellation.",
            "subject_entity": "Item"
          },
          {
            "claim_id": "claim-4",
            "assertion_text": "The product has a weight of 0.8 lbs.",
            "subject_entity": "Item"
          }
        ],
        "entities": [
          {
            "entity_type": "Item",
            "entity_id": "PF-WRLS-BLK",
            "name": "ProFit Wireless Headphones"
          }
        ]
      }
    },
    {
      "meta": {
        "case_id": "DSP-2026-00201",
        "document_id": "doc-merchant_quality_che-1786882766",
        "file_name": "merchant_quality_check_log.pdf",
        "owner": "merchant",
        "evidence_type": "PURCHASE_RECORD",
        "extracted_at": "2026-08-16T12:19:27Z",
        "confidence": 0.95,
        "processed_by": "ocr_pdf_txt_extractor"
      },
      "payload": {
        "order_id": "ORD-112233445",
        "items": [
          {
            "name": "ProFit Wireless - Black"
          }
        ]
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "claim-1",
            "assertion_text": "The order ID is ORD-112233445.",
            "subject_entity": "Order"
          },
          {
            "claim_id": "claim-2",
            "assertion_text": "The item verified is ProFit Wireless - Black.",
            "subject_entity": "Item"
          },
          {
            "claim_id": "claim-3",
            "assertion_text": "The status of the item is PASSED.",
            "subject_entity": "Item"
          },
          {
            "claim_id": "claim-4",
            "assertion_text": "The inspector ID is QC-88.",
            "subject_entity": "Inspector"
          },
          {
            "claim_id": "claim-5",
            "assertion_text": "The quality control log was processed at 2026-07-16T08:45:00Z.",
            "subject_entity": "Quality Control Log"
          }
        ],
        "entities": [
          {
            "entity_type": "Order",
            "entity_id": "ORD-112233445"
          },
          {
            "entity_type": "Item",
            "entity_id": "ProFit Wireless - Black"
          },
          {
            "entity_type": "Inspector",
            "entity_id": "QC-88"
          }
        ]
      }
    },
    {
      "meta": {
        "case_id": "DSP-2026-00201",
        "document_id": "doc-merchant_return_poli-1786882768",
        "file_name": "merchant_return_policy.pdf",
        "owner": "merchant",
        "evidence_type": "MERCHANT_POLICY",
        "extracted_at": "2026-08-16T12:19:29Z",
        "confidence": 0.95,
        "processed_by": "ocr_pdf_txt_extractor"
      },
      "payload": {
        "policy_name": "TechGadgets Return Policy",
        "refund_window_days": 30,
        "clauses": [
          {
            "clause_id": "1",
            "text": "Items can be returned within 30 days."
          },
          {
            "clause_id": "2",
            "text": "All high-value electronics (over $150) must be reported for discrepancies within 5 business days of delivery."
          },
          {
            "clause_id": "3",
            "text": "Clearance items are final sale."
          }
        ]
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "claim-1",
            "assertion_text": "Items can be returned within 30 days.",
            "subject_entity": null
          },
          {
            "claim_id": "claim-2",
            "assertion_text": "All high-value electronics (over $150) must be reported for discrepancies within 5 business days of delivery.",
            "subject_entity": null
          },
          {
            "claim_id": "claim-3",
            "assertion_text": "Clearance items are final sale.",
            "subject_entity": null
          }
        ],
        "entities": [
          {
            "entity_type": "Merchant",
            "entity_id": null,
            "name": "TechGadgets"
          }
        ]
      }
    }
  ]
}

GAPS for NOT AS DESCRIBED
Not as Described" doesn't have one Order/Tracking hub the way Not-Received did — it needs two comparable item-hubs: the ordered item vs. the received item. Right now the extraction is creating loosely-named Item entities per document with no consistent scheme ("ProFit Wireless Headphones", "Black Pro model", "White Standard", "PF-WRLS-BLK" all appear as separate entity_ids for what are really just two real-world items — what was ordered, and what arrived). This category's entire reasoning question — does received match ordered — depends on cleanly converging "everything asserted about the ordered item" and "everything asserted about the received item" onto two distinct hubs, the same way Order/Tracking did for delivery disputes. This is genuinely new schema work, not a bug fix — worth explicit OrderedItem/ReceivedItem entity types with canonical IDs (SKU where available), rather than reusing the generic Item label freely per document.

One evidentiary gap worth flagging as a finding, not silently missing

Clause 2 (the decisive one — "must be reported within 5 business days of delivery") requires a delivery date to evaluate. This case has purchase date (July 15) and a QC-pack timestamp (July 16), but no shipping or delivery date document at all — makes sense, since "Not as Described" doesn't need proof-of-delivery evidence the way Not-Received does, but it means the merchant's "outside the 5-day window" claim can't actually be verified against real data, only estimated from purchase/pack dates as loose proxies. Your Evidence Agent/Policy Agent should surface this explicitly as an insufficient_evidence finding ("delivery date unavailable, window compliance cannot be verified, estimated from purchase date only") rather than either agent silently picking a proxy date and treating clause 2's evaluation as settled fact — this is the same "false confidence from an unstated assumption" risk we caught with the complaint-timing anchor ambiguity a few turns back, just showing up in a new category.

Also worth normalizing again: dispute_reason stores "Not as Described" on the cardholder side and the raw code "13.3" on the merchant side — same category-name-vs-code inconsistency flagged for Item Not Received, confirm


2.Fraudalent
{
  "title": "Canonical Case Evidence Extractions",
  "case_id": "DSP-2026-00302",
  "generated_at": "2026-08-16T12:32:52Z",
  "summary": {
    "source_data_dir": "data\\category_2_fraudulent",
    "total_documents_processed": 7,
    "structured_form_documents": 2,
    "unstructured_documents": 5,
    "unique_entities_discovered": {
      "case_ids": [
        "DSP-2026-00302"
      ],
      "order_ids": [
        "ORD-998877665"
      ],
      "tracking_numbers": [],
      "merchants": [
        "MID-FASHION-442",
        "FashionHub Online"
      ]
    }
  },
  "extractions": [
    {
      "meta": {
        "case_id": "DSP-2026-00302",
        "document_id": "doc-form-cardholder_intake_fo-1786883560",
        "file_name": "cardholder_intake_form.json",
        "owner": "cardholder",
        "evidence_type": "DISPUTE_FORM",
        "extraction_method": "deterministic_regex_form_parser",
        "extracted_at": "2026-08-03T10:00:00Z",
        "confidence": 1.0
      },
      "payload": {
        "merchant_name": "FashionHub Online",
        "customer_name": "Cardholder",
        "dispute_reason": "Fraudulent",
        "claim": "I did not authorize this charge of $850. My physical wallet was stolen on July 31, and I reported my cards as compromised on August 2 when I saw the pending transactions. This purchase was made in a city I have not visited.",
        "requested_resolution": "Full refund",
        "disputed_amount": 850.0,
        "currency": "USD"
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "ast-form-883560-1",
            "assertion_text": "I did not authorize this charge of $850. My physical wallet was stolen on July 31, and I reported my cards as compromised on August 2 when I saw the pending transactions. This purchase was made in a city I have not visited.",
            "subject_entity": "ORD-998877665"
          }
        ],
        "entities": [
          {
            "entity_type": "Merchant",
            "entity_id": "MER-FASHIONHUB-ONLINE",
            "name": "FashionHub Online"
          },
          {
            "entity_type": "Order",
            "entity_id": "ORD-998877665",
            "name": "ORD-998877665"
          }
        ]
      }
    },
    {
      "meta": {
        "case_id": "DSP-2026-00302",
        "document_id": "doc-form-merchant_response_fo-1786883560",
        "file_name": "merchant_response_form.json",
        "owner": "merchant",
        "evidence_type": "DISPUTE_FORM",
        "extraction_method": "deterministic_regex_form_parser",
        "extracted_at": "2026-08-05T16:00:00Z",
        "confidence": 1.0
      },
      "payload": {
        "merchant_name": "MID-FASHION-442",
        "customer_name": "Cardholder",
        "dispute_reason": "10.4",
        "claim": "The transaction was processed with full security verification. AVS matched the billing address, CVV was verified, and 3D Secure was successfully completed by the user. The IP address used is consistent with the customer's billing state.",
        "requested_resolution": "deny refund",
        "currency": "USD"
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "ast-form-883560-1",
            "assertion_text": "The transaction was processed with full security verification. AVS matched the billing address, CVV was verified, and 3D Secure was successfully completed by the user. The IP address used is consistent with the customer's billing state.",
            "subject_entity": null
          }
        ],
        "entities": []
      }
    },
    {
      "meta": {
        "case_id": "DSP-2026-00302",
        "document_id": "doc-cardholder_police_re-1786883560",
        "file_name": "cardholder_police_report_excerpt.pdf",
        "owner": "cardholder",
        "evidence_type": "PURCHASE_RECORD",
        "extracted_at": "2026-08-16T12:32:44Z",
        "confidence": 0.95,
        "processed_by": "ocr_pdf_txt_extractor"
      },
      "payload": {
        "items": []
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "claim-1",
            "assertion_text": "Theft of wallet containing multiple credit cards.",
            "subject_entity": null
          },
          {
            "claim_id": "claim-2",
            "assertion_text": "Police report filed with report number PR-2026-9901.",
            "subject_entity": null
          },
          {
            "claim_id": "claim-3",
            "assertion_text": "The report was filed on 2026-08-01.",
            "subject_entity": null
          },
          {
            "claim_id": "claim-4",
            "assertion_text": "The status of the investigation is open.",
            "subject_entity": null
          }
        ],
        "entities": [
          {
            "entity_type": "Report",
            "entity_id": "PR-2026-9901",
            "name": "Police Report"
          },
          {
            "entity_type": "Customer",
            "entity_id": null,
            "name": null
          }
        ]
      }
    },
    {
      "meta": {
        "case_id": "DSP-2026-00302",
        "document_id": "doc-cardholder_unauthori-1786883565",
        "file_name": "cardholder_unauthorized_statement.pdf",
        "owner": "cardholder",
        "evidence_type": "PURCHASE_RECORD",
        "extracted_at": "2026-08-16T12:32:46Z",
        "confidence": 0.95,
        "processed_by": "ocr_pdf_txt_extractor"
      },
      "payload": {
        "merchant_name": "FashionHub Online",
        "total_amount": 850.0,
        "items": []
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "claim-1",
            "assertion_text": "The transaction for $850.00 at FashionHub Online was not made by me",
            "subject_entity": "FashionHub Online"
          },
          {
            "claim_id": "claim-2",
            "assertion_text": "I did not authorize anyone else to make it",
            "subject_entity": null
          },
          {
            "claim_id": "claim-3",
            "assertion_text": "My card ending in 7788 was stolen on 2026-07-31",
            "subject_entity": null
          }
        ],
        "entities": [
          {
            "entity_type": "Merchant",
            "entity_id": null,
            "name": "FashionHub Online"
          },
          {
            "entity_type": "Customer",
            "entity_id": null,
            "name": "Robert Smith"
          }
        ]
      }
    },
    {
      "meta": {
        "case_id": "DSP-2026-00302",
        "document_id": "doc-merchant_device_fing-1786883567",
        "file_name": "merchant_device_fingerprint.pdf",
        "owner": "merchant",
        "evidence_type": "PURCHASE_RECORD",
        "extracted_at": "2026-08-16T12:32:48Z",
        "confidence": 0.95,
        "processed_by": "ocr_pdf_txt_extractor"
      },
      "payload": {
        "items": []
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "claim-1",
            "assertion_text": "The device type is Mobile Safari / iOS.",
            "subject_entity": null
          },
          {
            "claim_id": "claim-2",
            "assertion_text": "The IP address is 192.168.10.55.",
            "subject_entity": null
          },
          {
            "claim_id": "claim-3",
            "assertion_text": "The location of the IP address is Springfield, IL.",
            "subject_entity": null
          },
          {
            "claim_id": "claim-4",
            "assertion_text": "The browser language is en-US.",
            "subject_entity": null
          },
          {
            "claim_id": "claim-5",
            "assertion_text": "The screen resolution is 1170x2532.",
            "subject_entity": null
          }
        ],
        "entities": [
          {
            "entity_type": "Device",
            "entity_id": null,
            "name": "Mobile Safari / iOS"
          },
          {
            "entity_type": "IP Address",
            "entity_id": "192.168.10.55",
            "name": "192.168.10.55"
          },
          {
            "entity_type": "Location",
            "entity_id": null,
            "name": "Springfield, IL"
          }
        ]
      }
    },
    {
      "meta": {
        "case_id": "DSP-2026-00302",
        "document_id": "doc-merchant_fraud_risk_-1786883569",
        "file_name": "merchant_fraud_risk_score.pdf",
        "owner": "merchant",
        "evidence_type": "PURCHASE_RECORD",
        "extracted_at": "2026-08-16T12:32:50Z",
        "confidence": 0.95,
        "processed_by": "ocr_pdf_txt_extractor"
      },
      "payload": {
        "items": []
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "claim-1",
            "assertion_text": "IP Address (IL) matches Billing State.",
            "subject_entity": null
          },
          {
            "claim_id": "claim-2",
            "assertion_text": "Email age > 2 years.",
            "subject_entity": null
          },
          {
            "claim_id": "claim-3",
            "assertion_text": "Device has prior successful orders.",
            "subject_entity": null
          },
          {
            "claim_id": "claim-4",
            "assertion_text": "Risk Score: 12 / 100",
            "subject_entity": null
          },
          {
            "claim_id": "claim-5",
            "assertion_text": "Risk Level: LOW",
            "subject_entity": null
          }
        ],
        "entities": [
          {
            "entity_type": "Merchant",
            "entity_id": null,
            "name": null
          },
          {
            "entity_type": "Customer",
            "entity_id": null,
            "name": null
          },
          {
            "entity_type": "Device",
            "entity_id": null,
            "name": null
          },
          {
            "entity_type": "Email",
            "entity_id": null,
            "name": null
          },
          {
            "entity_type": "IP Address",
            "entity_id": "IL",
            "name": null
          }
        ]
      }
    },
    {
      "meta": {
        "case_id": "DSP-2026-00302",
        "document_id": "doc-merchant_transaction-1786883571",
        "file_name": "merchant_transaction_metadata.pdf",
        "owner": "merchant",
        "evidence_type": "PURCHASE_RECORD",
        "extracted_at": "2026-08-16T12:32:52Z",
        "confidence": 0.95,
        "processed_by": "ocr_pdf_txt_extractor"
      },
      "payload": {
        "order_id": "ORD-998877665",
        "items": []
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "claim-1",
            "assertion_text": "The transaction has a security metadata.",
            "subject_entity": null
          },
          {
            "claim_id": "claim-2",
            "assertion_text": "The AVS result is Y, indicating a full match of address and zip.",
            "subject_entity": "ORD-998877665"
          },
          {
            "claim_id": "claim-3",
            "assertion_text": "The CVV result is M, indicating a match.",
            "subject_entity": "ORD-998877665"
          },
          {
            "claim_id": "claim-4",
            "assertion_text": "The 3D secure status is successful and authenticated.",
            "subject_entity": "ORD-998877665"
          },
          {
            "claim_id": "claim-5",
            "assertion_text": "The auth code is 099281.",
            "subject_entity": "ORD-998877665"
          }
        ],
        "entities": [
          {
            "entity_type": "Order",
            "entity_id": "ORD-998877665",
            "name": null
          }
        ]
      }
    }
  ]
}


GAPS FOR FRAUDALENT
Incorrect/inconsistent findings in the Fraud category JSON, for your notes:

evidence_type wrong for 5 of 7 documents — police report, unauthorized statement, device fingerprint, fraud risk score, and transaction metadata are all tagged PURCHASE_RECORD, none of which are purchase records.
DISPUTE_FORM claims not atomized — both cardholder's and merchant's compound statements extracted as one single assertion each, not split by subject.
Merchant name field holds an ID, not a name — merchant_response_form.json's merchant_name field contains "MID-FASHION-442" instead of "FashionHub Online".
Merchant appears as two different entities in the same case — "FashionHub Online" and "MID-FASHION-442" both listed in unique_entities_discovered.merchants, caused by finding 3.
dispute_reason inconsistent between parties — cardholder stores "Fraudulent" (category name), merchant stores "10.4" (raw code).
Same IP-address signal keyed two different ways, un-mergeable — device_fingerprint.pdf creates an IP entity with entity_id: "192.168.10.55"; fraud_risk_score.pdf creates a separate IP entity with entity_id: "IL" (the state, not the IP).
Multiple null-null placeholder entities with no identifying data — e.g., fraud_risk_score.pdf emits Merchant{id:null,name:null}, Customer{id:null,name:null}, Device{id:null,name:null}, Email{id:null,name:null}.
No canonical Customer/Cardholder entity across the case — appears with null id/name in the police report; only gets a real name ("Robert Smith") in one other document, never reconciled.
Two merchant documents (device_fingerprint.pdf, fraud_risk_score.pdf) never reference the Order entity at all — no Order/ORD-998877665 entry in either document's entities list, unlike transaction_metadata.pdf which correctly includes it.



3.DUPLICATE"

{
  "title": "Canonical Case Evidence Extractions",
  "case_id": "DSP-2026-00403",
  "generated_at": "2026-08-16T13:07:51Z",
  "summary": {
    "source_data_dir": "data\\category_3_duplicate",
    "total_documents_processed": 5,
    "structured_form_documents": 2,
    "unstructured_documents": 3,
    "unique_entities_discovered": {
      "case_ids": [
        "DSP-2026-00403"
      ],
      "order_ids": [
        "ORD-554433221"
      ],
      "tracking_numbers": [],
      "merchants": [
        "MID-COFFEE-112",
        "CoffeeExpress"
      ]
    }
  },
  "extractions": [
    {
      "meta": {
        "case_id": "DSP-2026-00403",
        "document_id": "doc-form-cardholder_intake_fo-1786885635",
        "file_name": "cardholder_intake_form.json",
        "owner": "cardholder",
        "evidence_type": "DISPUTE_FORM",
        "extraction_method": "deterministic_regex_form_parser",
        "extracted_at": "2026-08-12T11:00:00Z",
        "confidence": 1.0
      },
      "payload": {
        "merchant_name": "CoffeeExpress",
        "customer_name": "Cardholder",
        "dispute_reason": "Duplicate Charge",
        "claim": "I was charged twice for the same order of coffee beans. I only intended to buy one bag. I see two charges of $45 on my statement on the same day.",
        "requested_resolution": "Full refund of the second charge",
        "disputed_amount": 45.0,
        "currency": "USD"
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "ast-form-885635-1",
            "assertion_text": "I was charged twice for the same order of coffee beans. I only intended to buy one bag. I see two charges of $45 on my statement on the same day.",
            "subject_entity": "ORD-554433222"
          }
        ],
        "entities": [
          {
            "entity_type": "Merchant",
            "entity_id": "MER-COFFEEEXPRESS",
            "name": "CoffeeExpress"
          },
          {
            "entity_type": "Order",
            "entity_id": "ORD-554433222",
            "name": "ORD-554433222"
          }
        ]
      }
    },
    {
      "meta": {
        "case_id": "DSP-2026-00403",
        "document_id": "doc-form-merchant_response_fo-1786885635",
        "file_name": "merchant_response_form.json",
        "owner": "merchant",
        "evidence_type": "DISPUTE_FORM",
        "extraction_method": "deterministic_regex_form_parser",
        "extracted_at": "2026-08-14T15:00:00Z",
        "confidence": 1.0
      },
      "payload": {
        "merchant_name": "MID-COFFEE-112",
        "customer_name": "Cardholder",
        "dispute_reason": "12.6.1",
        "claim": "These are two distinct transactions. The customer placed two separate orders 45 minutes apart. Each order has a unique session ID and unique item fulfillment record. This was not a system error.",
        "requested_resolution": "deny refund",
        "currency": "USD"
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "ast-form-885635-1",
            "assertion_text": "These are two distinct transactions. The customer placed two separate orders 45 minutes apart. Each order has a unique session ID and unique item fulfillment record. This was not a system error.",
            "subject_entity": null
          }
        ],
        "entities": []
      }
    },
    {
      "meta": {
        "case_id": "DSP-2026-00403",
        "document_id": "doc-cardholder_bank_stat-1786885635",
        "file_name": "cardholder_bank_statement.pdf",
        "owner": "cardholder",
        "evidence_type": "PURCHASE_RECORD",
        "extracted_at": "2026-08-16T13:07:47Z",
        "confidence": 0.95,
        "processed_by": "ocr_pdf_txt_extractor"
      },
      "payload": {
        "merchant_name": "CoffeeExpress",
        "order_id": "ORD-554433221",
        "purchase_date": "2026-08-10T00:00:00",
        "total_amount": 90.0,
        "currency": "USD",
        "items": [
          {
            "name": "Unknown",
            "quantity": 2,
            "price": 45.0
          }
        ]
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "claim-1",
            "assertion_text": "Two transactions of $45.00 were made at CoffeeExpress on 2026-08-10.",
            "subject_entity": "CoffeeExpress"
          },
          {
            "claim_id": "claim-2",
            "assertion_text": "The balance after the transactions was $1,240.00.",
            "subject_entity": "Michael Brown"
          }
        ],
        "entities": [
          {
            "entity_type": "Merchant",
            "entity_id": "CoffeeExpress",
            "name": "CoffeeExpress"
          },
          {
            "entity_type": "Customer",
            "entity_id": "Michael Brown",
            "name": "Michael Brown"
          },
          {
            "entity_type": "Order",
            "entity_id": "ORD-554433221",
            "name": "ORD-554433221"
          },
          {
            "entity_type": "Order",
            "entity_id": "ORD-554433222",
            "name": "ORD-554433222"
          }
        ]
      }
    },
    {
      "meta": {
        "case_id": "DSP-2026-00403",
        "document_id": "doc-merchant_session_log-1786885668",
        "file_name": "merchant_session_logs.pdf",
        "owner": "merchant",
        "evidence_type": "PURCHASE_RECORD",
        "extracted_at": "2026-08-16T13:07:49Z",
        "confidence": 0.95,
        "processed_by": "ocr_pdf_txt_extractor"
      },
      "payload": {
        "items": []
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "claim-1",
            "assertion_text": "Session A (ID: sess_abc123) started at 08:55 AM.",
            "subject_entity": "Session A"
          },
          {
            "claim_id": "claim-2",
            "assertion_text": "Session A (ID: sess_abc123) checked out at 2026-08-10T09:00:00Z.",
            "subject_entity": "Session A"
          },
          {
            "claim_id": "claim-3",
            "assertion_text": "Session B (ID: sess_xyz789) started at 09:40 AM.",
            "subject_entity": "Session B"
          },
          {
            "claim_id": "claim-4",
            "assertion_text": "Session B (ID: sess_xyz789) checked out at 2026-08-10T09:45:00Z.",
            "subject_entity": "Session B"
          },
          {
            "claim_id": "claim-5",
            "assertion_text": "Both sessions originated from the same IP, but involved distinct navigation paths and item selections.",
            "subject_entity": null
          }
        ],
        "entities": [
          {
            "entity_type": "Session",
            "entity_id": "sess_abc123",
            "name": "Session A"
          },
          {
            "entity_type": "Session",
            "entity_id": "sess_xyz789",
            "name": "Session B"
          }
        ]
      }
    },
    {
      "meta": {
        "case_id": "DSP-2026-00403",
        "document_id": "doc-merchant_transaction-1786885670",
        "file_name": "merchant_transaction_comparison.pdf",
        "owner": "merchant",
        "evidence_type": "PURCHASE_RECORD",
        "extracted_at": "2026-08-16T13:07:51Z",
        "confidence": 0.95,
        "processed_by": "ocr_pdf_txt_extractor"
      },
      "payload": {
        "order_id": "ORD-554433221",
        "purchase_date": "2026-08-10T09:00:00Z",
        "items": [
          {
            "name": "Premium Beans (Sumatra)"
          },
          {
            "name": "Premium Beans (Ethiopia)"
          }
        ]
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "claim-1",
            "assertion_text": "Order 1 has an ID of ORD-554433221.",
            "subject_entity": "ORD-554433221"
          },
          {
            "claim_id": "claim-2",
            "assertion_text": "Order 1 was placed at 2026-08-10T09:00:00Z.",
            "subject_entity": "ORD-554433221"
          },
          {
            "claim_id": "claim-3",
            "assertion_text": "Order 1 item is Premium Beans (Sumatra).",
            "subject_entity": "ORD-554433221"
          },
          {
            "claim_id": "claim-4",
            "assertion_text": "Order 1 status is Shipped.",
            "subject_entity": "ORD-554433221"
          },
          {
            "claim_id": "claim-5",
            "assertion_text": "Order 2 has an ID of ORD-554433222.",
            "subject_entity": "ORD-554433222"
          },
          {
            "claim_id": "claim-6",
            "assertion_text": "Order 2 was placed at 2026-08-10T09:45:00Z.",
            "subject_entity": "ORD-554433222"
          },
          {
            "claim_id": "claim-7",
            "assertion_text": "Order 2 item is Premium Beans (Ethiopia).",
            "subject_entity": "ORD-554433222"
          },
          {
            "claim_id": "claim-8",
            "assertion_text": "Order 2 status is Shipped.",
            "subject_entity": "ORD-554433222"
          }
        ],
        "entities": [
          {
            "entity_type": "Order",
            "entity_id": "ORD-554433221",
            "name": "Order 1"
          },
          {
            "entity_type": "Order",
            "entity_id": "ORD-554433222",
            "name": "Order 2"
          },
          {
            "entity_type": "Item",
            "entity_id": "Premium Beans (Sumatra)",
            "name": "Premium Beans (Sumatra)"
          },
          {
            "entity_type": "Item",
            "entity_id": "Premium Beans (Ethiopia)",
            "name": "Premium Beans (Ethiopia)"
          }
        ]
      }
    }
  ]
}

evidence_type wrong for the bank statement, session logs, and transaction comparison — all tagged PURCHASE_RECORD; the session logs and transaction comparison aren't purchase records at all (same pattern as Fraud's category-2 misclassification).
DISPUTE_FORM claims not atomized — both cardholder and merchant compound statements are one blob each, same recurring bug.
Merchant name field holds an ID again — merchant_response_form.json's merchant_name is "MID-COFFEE-112", not "CoffeeExpress". Same bug as Fraud category, confirming this is systemic to the form parser itself, not per-category.
Merchant appears as two entities — "CoffeeExpress" and "MID-COFFEE-112" both in unique_entities_discovered.merchants, direct consequence of #3.
dispute_reason inconsistent — cardholder: "Duplicate Charge", merchant: "12.6.1". Third category in a row with this exact pattern.
A real, case-corrupting extraction error — the cardholder's intake form has the wrong order ID(THIS IS DATA PROBLEM DO NOT CONSIDER PIPELINE ISSUE ). transaction_reference: "ORD-554433222" in the cardholder's form — but per the bank statement, ORD-554433221 is the first charge (9:00 AM) and ORD-554433222 is the second (9:45 AM). The cardholder's stated complaint is "I only intended to buy one bag" and wants "full refund of the second charge" — meaning their form should reference the first, legitimate order as their transaction reference, not the second one they're disputing. As extracted, the cardholder's own form is pointing at the wrong transaction relative to their stated intent — this isn't a formatting inconsistency like the others, it's a genuine "which order is this form even about" error.
Item identity per order is completely disconnected — worse than category 1's item-splitting problem. The bank statement extracts item name as "Unknown" for a $45 charge; the transaction comparison document (a different file) is what actually reveals Order 1 = Sumatra beans, Order 2 = Ethiopia beans. Nothing in the extraction connects "the item on this specific charge" to "the item this specific order actually contained" — for a Duplicate Charge case, whether the two orders contained the same item (supporting "this was one mistaken double-charge") or different items (supporting the merchant's "two distinct purchases" defense) is the single most decisive fact in the whole case, and it's currently split across two unlinked documents with no entity connecting a charge to its item.
Merchant's own evidence, read literally, undermines their own claim, and nothing surfaces this. The merchant's assertion says the two orders are unrelated distinct purchases — but merchant_session_logs.pdf states both sessions originated from the same IP, and both orders are for "Premium Beans," 45 minutes apart, same day, same amount. This pattern (same IP, same product category, extremely close in time) is at least as consistent with "customer accidentally double-submitted" as it is with "two genuinely separate purchases" — yet this is buried as one throwaway assertion (claim-5, subject_entity: null) with no connection drawn to the merchant's own "not a system error" claim it's sitting right next to.



4.REFUND

{
  "title": "Canonical Case Evidence Extractions",
  "case_id": "DSP-2026-00504",
  "generated_at": "2026-08-16T13:21:07Z",
  "summary": {
    "source_data_dir": "data\\category_4_refund",
    "total_documents_processed": 6,
    "structured_form_documents": 2,
    "unstructured_documents": 4,
    "unique_entities_discovered": {
      "case_ids": [
        "DSP-2026-00504"
      ],
      "order_ids": [
        "ORD-123456789"
      ],
      "tracking_numbers": [],
      "merchants": [
        "MID-URBAN-771",
        "UrbanWear"
      ]
    }
  },
  "extractions": [
    {
      "meta": {
        "case_id": "DSP-2026-00504",
        "document_id": "doc-form-cardholder_intake_fo-1786886458",
        "file_name": "cardholder_intake_form.json",
        "owner": "cardholder",
        "evidence_type": "DISPUTE_FORM",
        "extraction_method": "deterministic_regex_form_parser",
        "extracted_at": "2026-08-01T09:00:00Z",
        "confidence": 1.0
      },
      "payload": {
        "merchant_name": "UrbanWear",
        "customer_name": "Cardholder",
        "dispute_reason": "Credit Not Processed",
        "claim": "I returned the dress on July 20 and the merchant agreed via email to refund me. It has been over 10 days and I still don't see the credit on my card.",
        "requested_resolution": "Full refund",
        "disputed_amount": 65.0,
        "currency": "USD"
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "ast-form-886458-1",
            "assertion_text": "I returned the dress on July 20 and the merchant agreed via email to refund me. It has been over 10 days and I still don't see the credit on my card.",
            "subject_entity": "ORD-123456789"
          }
        ],
        "entities": [
          {
            "entity_type": "Merchant",
            "entity_id": "MER-URBANWEAR",
            "name": "UrbanWear"
          },
          {
            "entity_type": "Order",
            "entity_id": "ORD-123456789",
            "name": "ORD-123456789"
          }
        ]
      }
    },
    {
      "meta": {
        "case_id": "DSP-2026-00504",
        "document_id": "doc-form-merchant_response_fo-1786886458",
        "file_name": "merchant_response_form.json",
        "owner": "merchant",
        "evidence_type": "DISPUTE_FORM",
        "extraction_method": "deterministic_regex_form_parser",
        "extracted_at": "2026-08-03T11:00:00Z",
        "confidence": 1.0
      },
      "payload": {
        "merchant_name": "MID-URBAN-771",
        "customer_name": "Cardholder",
        "dispute_reason": "13.6",
        "claim": "We acknowledge the refund is owed. Our records show the refund was successfully processed on July 25. The customer should see it on their statement shortly.",
        "requested_resolution": "accept dispute / refund processed",
        "currency": "USD"
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "ast-form-886458-1",
            "assertion_text": "We acknowledge the refund is owed. Our records show the refund was successfully processed on July 25. The customer should see it on their statement shortly.",
            "subject_entity": null
          }
        ],
        "entities": []
      }
    },
    {
      "meta": {
        "case_id": "DSP-2026-00504",
        "document_id": "doc-cardholder_refund_ag-1786886459",
        "file_name": "cardholder_refund_agreement_email.pdf",
        "owner": "cardholder",
        "evidence_type": "COMMUNICATION_LOG",
        "extracted_at": "2026-08-16T13:21:01Z",
        "confidence": 0.95,
        "processed_by": "ocr_pdf_txt_extractor"
      },
      "payload": {
        "channel": "email",
        "messages": [
          {
            "sender": "UrbanWear Support",
            "recipient": "Sarah Wilson",
            "timestamp": "2026-07-22T00:00:00Z",
            "body": "Hi Sarah, we have received your return. We have initiated a refund of $65.00 to your original payment method. Please allow 3-5 business days for it to appear."
          }
        ]
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "claim-1",
            "assertion_text": "We have received your return.",
            "subject_entity": "return"
          },
          {
            "claim_id": "claim-2",
            "assertion_text": "We have initiated a refund of $65.00 to your original payment method.",
            "subject_entity": "refund"
          },
          {
            "claim_id": "claim-3",
            "assertion_text": "Please allow 3-5 business days for it to appear.",
            "subject_entity": "refund"
          }
        ],
        "entities": [
          {
            "entity_type": "Merchant",
            "entity_id": "UrbanWear",
            "name": "UrbanWear"
          },
          {
            "entity_type": "Customer",
            "entity_id": "Sarah Wilson",
            "name": "Sarah Wilson"
          },
          {
            "entity_type": "Item",
            "entity_id": "return",
            "name": "return"
          },
          {
            "entity_type": "Order",
            "entity_id": "refund",
            "name": "refund"
          }
        ]
      }
    },
    {
      "meta": {
        "case_id": "DSP-2026-00504",
        "document_id": "doc-cardholder_return_re-1786886462",
        "file_name": "cardholder_return_receipt.pdf",
        "owner": "cardholder",
        "evidence_type": "PURCHASE_RECORD",
        "extracted_at": "2026-08-16T13:21:03Z",
        "confidence": 0.95,
        "processed_by": "ocr_pdf_txt_extractor"
      },
      "payload": {
        "items": []
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "claim-1",
            "assertion_text": "The return shipping carrier is QuickShip.",
            "subject_entity": "Carrier"
          },
          {
            "claim_id": "claim-2",
            "assertion_text": "The tracking number is QS-998811.",
            "subject_entity": "Tracking"
          },
          {
            "claim_id": "claim-3",
            "assertion_text": "The return shipping date is 2026-07-20.",
            "subject_entity": "Return Shipping"
          },
          {
            "claim_id": "claim-4",
            "assertion_text": "The status is Delivered to Merchant Warehouse.",
            "subject_entity": "Status"
          }
        ],
        "entities": [
          {
            "entity_type": "Tracking",
            "entity_id": "QS-998811",
            "name": "QuickShip Tracking Number"
          },
          {
            "entity_type": "Carrier",
            "entity_id": "QuickShip",
            "name": "QuickShip"
          }
        ]
      }
    },
    {
      "meta": {
        "case_id": "DSP-2026-00504",
        "document_id": "doc-merchant_processor_l-1786886464",
        "file_name": "merchant_processor_log.pdf",
        "owner": "merchant",
        "evidence_type": "PROCESSOR_LOG",
        "extracted_at": "2026-08-16T13:21:05Z",
        "confidence": 0.95,
        "processed_by": "ocr_pdf_txt_extractor"
      },
      "payload": {
        "transaction_reference": "ORD-123456789",
        "payment_status": "APPROVED",
        "refund_timestamp": "2026-07-25T14:00:05Z"
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "claim-1",
            "assertion_text": "A refund was approved for Order ORD-123456789.",
            "subject_entity": "ORD-123456789"
          },
          {
            "claim_id": "claim-2",
            "assertion_text": "The refund amount was 65.00.",
            "subject_entity": "ORD-123456789"
          },
          {
            "claim_id": "claim-3",
            "assertion_text": "The payment gateway used was Stripe.",
            "subject_entity": null
          },
          {
            "claim_id": "claim-4",
            "assertion_text": "The network used was Visa.",
            "subject_entity": null
          },
          {
            "claim_id": "claim-5",
            "assertion_text": "The ARN for the transaction was 74512345678901234567890.",
            "subject_entity": null
          }
        ],
        "entities": [
          {
            "entity_type": "Order",
            "entity_id": "ORD-123456789",
            "name": null
          },
          {
            "entity_type": "Gateway",
            "entity_id": "Stripe",
            "name": "Stripe"
          },
          {
            "entity_type": "Network",
            "entity_id": "Visa",
            "name": "Visa"
          }
        ]
      }
    },
    {
      "meta": {
        "case_id": "DSP-2026-00504",
        "document_id": "doc-merchant_refund_conf-1786886466",
        "file_name": "merchant_refund_confirmation.pdf",
        "owner": "merchant",
        "evidence_type": "PURCHASE_RECORD",
        "extracted_at": "2026-08-16T13:21:07Z",
        "confidence": 0.95,
        "processed_by": "ocr_pdf_txt_extractor"
      },
      "payload": {
        "order_id": "ORD-123456789",
        "purchase_date": "2026-07-25T14:00:00Z",
        "total_amount": 65.0,
        "currency": "USD",
        "items": []
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "claim-1",
            "assertion_text": "A refund was issued with Refund ID REF-992288.",
            "subject_entity": "REF-992288"
          },
          {
            "claim_id": "claim-2",
            "assertion_text": "The original order was ORD-123456789.",
            "subject_entity": "ORD-123456789"
          },
          {
            "claim_id": "claim-3",
            "assertion_text": "The refund amount was $65.0.",
            "subject_entity": null
          },
          {
            "claim_id": "claim-4",
            "assertion_text": "The refund was processed on 2026-07-25T14:00:00Z.",
            "subject_entity": null
          },
          {
            "claim_id": "claim-5",
            "assertion_text": "The refund status is SUCCESS.",
            "subject_entity": null
          }
        ],
        "entities": [
          {
            "entity_type": "Order",
            "entity_id": "ORD-123456789",
            "name": null
          },
          {
            "entity_type": "Refund",
            "entity_id": "REF-992288",
            "name": null
          }
        ]
      }
    }
  ]
}


evidence_type correct this time for PROCESSOR_LOG — worth noting as a genuine positive: the classifier correctly tagged merchant_processor_log.pdf as PROCESSOR_LOG, not the usual PURCHASE_RECORD fallback. First correct non-default classification seen across all 4 categories so far — likely because "processor log" as a filename/content phrase happens to hit an existing keyword rule. merchant_refund_confirmation.pdf, though, is still wrongly tagged PURCHASE_RECORD (it's a refund receipt, not a purchase record) — so the classifier fix is partial, not general.
DISPUTE_FORM claims not atomized — same recurring bug, both forms one blob each. Fourth category in a row.
Merchant name field holds an ID again — "MID-URBAN-771" vs "UrbanWear". Fourth category in a row, now unambiguously confirmed as a pipeline-level parsing bug in the merchant form handler, not a per-case data quirk.
Merchant duplicated as two entities — same consequence of #3.
dispute_reason inconsistent — "Credit Not Processed" vs "13.6". Fourth category in a row.
A genuinely bad entity-extraction error — nonsensical entity types from the refund-agreement email. This one's new and worth flagging clearly: the extractor created {"entity_type": "Item", "entity_id": "return", "name": "return"} and {"entity_type": "Order", "entity_id": "refund", "name": "refund"} — the common nouns "return" and "refund" got promoted into typed entities with themselves as both ID and name, and "refund" was mislabeled as an Order entity type entirely. These aren't real entities; they're the extractor mistaking subject_entity: "return" / "refund" (which look like they were meant as topic tags, similar to the subject field on Assertions elsewhere in your schema) for actual named things worth minting nodes for. This is a distinct bug from anything found in categories 1-3 — it suggests whatever logic promotes subject_entity values into Entity records isn't filtering out generic/topic-like strings before doing so.
This is the cleanest, most internally consistent case of the four so far — worth noting as a positive baseline. Every date, amount, and reference ID matches exactly across all 5 documents (refund initiated July 22, shipped back July 20, processed July 25, $65 throughout, ORD-123456789 consistent everywhere) — no equivalent to category 3's wrong-order-ID data bug. This is a good category to use as your "clean merchant-concedes" reference case precisely because the underlying facts are trustworthy; the bugs here are purely in extraction/entity-typing, not in the source data.


//SUBSCRIPTION


{
  "title": "Canonical Case Evidence Extractions",
  "case_id": "DSP-2026-00605",
  "generated_at": "2026-08-16T13:27:20Z",
  "summary": {
    "source_data_dir": "data\\category_5_subscription",
    "total_documents_processed": 5,
    "structured_form_documents": 2,
    "unstructured_documents": 3,
    "unique_entities_discovered": {
      "case_ids": [
        "DSP-2026-00605"
      ],
      "order_ids": [],
      "tracking_numbers": [],
      "merchants": [
        "MID-STREAM-009",
        "StreamMax",
        "StreamMax Billing"
      ]
    }
  },
  "extractions": [
    {
      "meta": {
        "case_id": "DSP-2026-00605",
        "document_id": "doc-form-cardholder_intake_fo-1786886834",
        "file_name": "cardholder_intake_form.json",
        "owner": "cardholder",
        "evidence_type": "DISPUTE_FORM",
        "extraction_method": "deterministic_regex_form_parser",
        "extracted_at": "2026-08-05T10:00:00Z",
        "confidence": 1.0
      },
      "payload": {
        "merchant_name": "StreamMax",
        "customer_name": "Cardholder",
        "dispute_reason": "Cancelled Recurring Transaction",
        "claim": "I cancelled my StreamMax subscription on July 28. I received a confirmation email. However, I was still charged $19.99 on August 1. I have not used the service since I cancelled.",
        "requested_resolution": "Full refund",
        "disputed_amount": 19.99,
        "currency": "USD"
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "ast-form-886834-1",
            "assertion_text": "I cancelled my StreamMax subscription on July 28. I received a confirmation email. However, I was still charged $19.99 on August 1. I have not used the service since I cancelled.",
            "subject_entity": "SUB-887766"
          }
        ],
        "entities": [
          {
            "entity_type": "Merchant",
            "entity_id": "MER-STREAMMAX",
            "name": "StreamMax"
          },
          {
            "entity_type": "Order",
            "entity_id": "SUB-887766",
            "name": "SUB-887766"
          }
        ]
      }
    },
    {
      "meta": {
        "case_id": "DSP-2026-00605",
        "document_id": "doc-form-merchant_response_fo-1786886834",
        "file_name": "merchant_response_form.json",
        "owner": "merchant",
        "evidence_type": "DISPUTE_FORM",
        "extraction_method": "deterministic_regex_form_parser",
        "extracted_at": "2026-08-07T14:00:00Z",
        "confidence": 1.0
      },
      "payload": {
        "merchant_name": "MID-STREAM-009",
        "customer_name": "Cardholder",
        "dispute_reason": "13.2",
        "claim": "The customer did initiate a cancellation, but our logs show continued usage of the service on August 2nd and 3rd. According to our terms, usage after the billing date constitutes a renewal of the subscription for the next month.",
        "requested_resolution": "deny refund",
        "currency": "USD"
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "ast-form-886834-1",
            "assertion_text": "The customer did initiate a cancellation, but our logs show continued usage of the service on August 2nd and 3rd. According to our terms, usage after the billing date constitutes a renewal of the subscription for the next month.",
            "subject_entity": null
          }
        ],
        "entities": []
      }
    },
    {
      "meta": {
        "case_id": "DSP-2026-00605",
        "document_id": "doc-cardholder_cancellat-1786886835",
        "file_name": "cardholder_cancellation_confirmation.pdf",
        "owner": "cardholder",
        "evidence_type": "PURCHASE_RECORD",
        "extracted_at": "2026-08-16T13:27:16Z",
        "confidence": 0.95,
        "processed_by": "ocr_pdf_txt_extractor"
      },
      "payload": {
        "merchant_name": "StreamMax Billing",
        "items": []
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "claim-1",
            "assertion_text": "Your subscription has been successfully cancelled.",
            "subject_entity": "subscription"
          },
          {
            "claim_id": "claim-2",
            "assertion_text": "You will continue to have access until the end of your current billing cycle (July 31).",
            "subject_entity": "billing cycle"
          },
          {
            "claim_id": "claim-3",
            "assertion_text": "No further charges will be made.",
            "subject_entity": null
          }
        ],
        "entities": [
          {
            "entity_type": "Customer",
            "entity_id": null,
            "name": "David Lee"
          },
          {
            "entity_type": "Merchant",
            "entity_id": null,
            "name": "StreamMax Billing"
          }
        ]
      }
    },
    {
      "meta": {
        "case_id": "DSP-2026-00605",
        "document_id": "doc-merchant_subscriptio-1786886837",
        "file_name": "merchant_subscription_terms.pdf",
        "owner": "merchant",
        "evidence_type": "MERCHANT_POLICY",
        "extracted_at": "2026-08-16T13:27:18Z",
        "confidence": 0.95,
        "processed_by": "ocr_pdf_txt_extractor"
      },
      "payload": {
        "policy_name": "StreamMax Terms of Service",
        "cancellation_window_days": 2,
        "clauses": [
          {
            "clause_id": "4.1",
            "text": "Cancellation must be made 48 hours before the renewal date."
          },
          {
            "clause_id": "4.2",
            "text": "Access to Premium content after the renewal date, regardless of cancellation status, will be treated as an authorization for the next month's billing."
          }
        ]
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "claim-1",
            "assertion_text": "Cancellation must be made 48 hours before the renewal date.",
            "subject_entity": null
          },
          {
            "claim_id": "claim-2",
            "assertion_text": "Access to Premium content after the renewal date, regardless of cancellation status, will be treated as an authorization for the next month's billing.",
            "subject_entity": null
          }
        ],
        "entities": [
          {
            "entity_type": "Merchant",
            "entity_id": null,
            "name": "StreamMax"
          }
        ]
      }
    },
    {
      "meta": {
        "case_id": "DSP-2026-00605",
        "document_id": "doc-merchant_usage_logs-1786886839",
        "file_name": "merchant_usage_logs.pdf",
        "owner": "merchant",
        "evidence_type": "USAGE_LOG",
        "extracted_at": "2026-08-16T13:27:20Z",
        "confidence": 0.95,
        "processed_by": "ocr_pdf_txt_extractor"
      },
      "payload": {
        "user_id": "user-8822",
        "events": [
          {
            "timestamp": "2026-08-02T20:15:00Z",
            "event_type": "Login",
            "device": "Apple TV",
            "ip_address": "1.2.3.4"
          },
          {
            "timestamp": "2026-08-02T20:16:00Z",
            "event_type": "Stream Started"
          },
          {
            "timestamp": "2026-08-03T18:00:00Z",
            "event_type": "Login",
            "device": "Web Browser",
            "ip_address": "1.2.3.4"
          }
        ]
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "claim-1",
            "assertion_text": "User David Lee with ID user-8822 had activity post-cancellation.",
            "subject_entity": "user-8822"
          },
          {
            "claim_id": "claim-2",
            "assertion_text": "On 2026-08-02 at 20:15:00, the user logged in from an Apple TV device with IP 1.2.3.4.",
            "subject_entity": "user-8822"
          },
          {
            "claim_id": "claim-3",
            "assertion_text": "On 2026-08-02 at 20:16:00, the user started streaming 'The Last Agent' S1E1.",
            "subject_entity": "user-8822"
          },
          {
            "claim_id": "claim-4",
            "assertion_text": "On 2026-08-03 at 18:00:00, the user logged in from a web browser with IP 1.2.3.4.",
            "subject_entity": "user-8822"
          }
        ],
        "entities": [
          {
            "entity_type": "Customer",
            "entity_id": "user-8822",
            "name": "David Lee"
          }
        ]
      }
    }
  ]
}

GAPS

evidence_type correct for both MERCHANT_POLICY and USAGE_LOG — second positive data point after category 4's PROCESSOR_LOG. Worth confirming exactly which keyword/content signal made these classify correctly, so it can be generalized rather than staying accidental.
DISPUTE_FORM claims not atomized — same recurring bug, fifth category in a row.
Merchant name field holds an ID again — "MID-STREAM-009" vs "StreamMax". Fifth category in a row.
Merchant fragmented into THREE separate strings this time, worse than usual — unique_entities_discovered.merchants lists "MID-STREAM-009", "StreamMax", AND "StreamMax Billing". The third one is new: the cancellation confirmation email is genuinely from a sub-brand/billing-department name, which is realistic real-world messiness — but nothing in extraction treats these three strings as referring to one merchant entity.
dispute_reason inconsistent — "Cancelled Recurring Transaction" vs "13.2". Fifth category in a row.
The decisive fact in this entire case — "no service use before the charge, but use after cancellation" — is split across three documents with zero connecting entity. The cardholder claims "I have not used the service since I cancelled" (in the DISPUTE_FORM's unatomized blob). The merchant's usage log shows activity on Aug 2-3, correctly linked to Customer{entity_id:"user-8822", name:"David Lee"}. But the cardholder's own intake form never creates or references a Customer/user_id entity at all — so there is no shared node connecting "the cardholder who says they didn't use it" to "the user_id whose logs show they did." This is the Contradiction Agent's single most important comparison for this entire category, and right now it's structurally unreachable — not because the facts disagree ambiguously, but because nothing in the extraction gives them a common identity to be compared on.
Same generic-noun-as-entity bug as category 4 — {"entity_type": "Order", "entity_id": "subscription", "name": "subscription"}-style pattern recurs here too: subject_entity: "subscription" and "billing cycle" in the cancellation confirmation's assertions look like topic tags being promoted the same way "return"/"refund" were in category 4. Confirms this is a general extractor bug, not a one-off.
A real, subtle policy-application question worth flagging for your reasoning design, not just extraction — clause 4.2's actual text is "access... after the renewal date... will be treated as authorization for the next month's billing," but the cardholder's confirmation email explicitly promised "access until the end of your current billing cycle (July 31)" with no further charges. The merchant is applying clause 4.2 to activity on Aug 2-3, which is genuinely after the July 31 cutoff their own cancellation email promised — meaning the merchant's own two documents (the confirmation email and their policy clause) may be in tension with each other, not just with the cardholder's claim. That's a merchant-self-contradiction pattern, structurally similar to the "9 days" issue from Item Not Received, and it's currently invisible because nothing connects the confirmation email's promised end-date to the usage log's activity dates


//CATEGORY ERROR
{
  "title": "Canonical Case Evidence Extractions",
  "case_id": "DSP-2026-00706",
  "generated_at": "2026-08-16T13:37:59Z",
  "summary": {
    "source_data_dir": "data\\category_6_error",
    "total_documents_processed": 5,
    "structured_form_documents": 2,
    "unstructured_documents": 3,
    "unique_entities_discovered": {
      "case_ids": [
        "DSP-2026-00706"
      ],
      "order_ids": [
        "ORD-332211"
      ],
      "tracking_numbers": [],
      "merchants": [
        "MID-GOURMET-883",
        "GourmetBistro"
      ]
    }
  },
  "extractions": [
    {
      "meta": {
        "case_id": "DSP-2026-00706",
        "document_id": "doc-form-cardholder_intake_fo-1786887472",
        "file_name": "cardholder_intake_form.json",
        "owner": "cardholder",
        "evidence_type": "DISPUTE_FORM",
        "extraction_method": "deterministic_regex_form_parser",
        "extracted_at": "2026-08-14T09:00:00Z",
        "confidence": 1.0
      },
      "payload": {
        "merchant_name": "GourmetBistro",
        "customer_name": "Cardholder",
        "dispute_reason": "Incorrect Transaction Amount",
        "claim": "I was charged $85 for a dinner that cost $55. My receipt clearly shows $55. The merchant seems to have added an unauthorized $30 charge.",
        "requested_resolution": "Refund of $30 discrepancy",
        "disputed_amount": 85.0,
        "currency": "USD"
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "ast-form-887472-1",
            "assertion_text": "I was charged $85 for a dinner that cost $55. My receipt clearly shows $55. The merchant seems to have added an unauthorized $30 charge.",
            "subject_entity": "ORD-332211"
          }
        ],
        "entities": [
          {
            "entity_type": "Merchant",
            "entity_id": "MER-GOURMETBISTRO",
            "name": "GourmetBistro"
          },
          {
            "entity_type": "Order",
            "entity_id": "ORD-332211",
            "name": "ORD-332211"
          }
        ]
      }
    },
    {
      "meta": {
        "case_id": "DSP-2026-00706",
        "document_id": "doc-form-merchant_response_fo-1786887472",
        "file_name": "merchant_response_form.json",
        "owner": "merchant",
        "evidence_type": "DISPUTE_FORM",
        "extraction_method": "deterministic_regex_form_parser",
        "extracted_at": "2026-08-16T11:00:00Z",
        "confidence": 1.0
      },
      "payload": {
        "merchant_name": "MID-GOURMET-883",
        "customer_name": "Cardholder",
        "dispute_reason": "12.2",
        "claim": "The $85 charge is correct. It includes the base price of $55 plus a mandatory $30 'Chef's Table' service fee that is applied to all weekend bookings.",
        "requested_resolution": "deny refund",
        "currency": "USD"
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "ast-form-887472-1",
            "assertion_text": "The $85 charge is correct. It includes the base price of $55 plus a mandatory $30 'Chef's Table' service fee that is applied to all weekend bookings.",
            "subject_entity": null
          }
        ],
        "entities": []
      }
    },
    {
      "meta": {
        "case_id": "DSP-2026-00706",
        "document_id": "doc-cardholder_order_rec-1786887473",
        "file_name": "cardholder_order_receipt.pdf",
        "owner": "cardholder",
        "evidence_type": "PURCHASE_RECORD",
        "extracted_at": "2026-08-16T13:37:55Z",
        "confidence": 0.95,
        "processed_by": "ocr_pdf_txt_extractor"
      },
      "payload": {
        "merchant_name": "GourmetBistro",
        "order_id": "ORD-332211",
        "purchase_date": "2026-08-12T19:30:00Z",
        "total_amount": 55.0,
        "items": [
          {
            "name": "Tasting Menu",
            "quantity": 1,
            "price": 45.0
          },
          {
            "name": "Glass of Wine",
            "quantity": 1,
            "price": 10.0
          }
        ]
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "claim-1",
            "assertion_text": "The order was placed at GourmetBistro.",
            "subject_entity": "GourmetBistro"
          },
          {
            "claim_id": "claim-2",
            "assertion_text": "The order ID is ORD-332211.",
            "subject_entity": "ORD-332211"
          },
          {
            "claim_id": "claim-3",
            "assertion_text": "The order was placed on 2026-08-12T19:30:00Z.",
            "subject_entity": null
          },
          {
            "claim_id": "claim-4",
            "assertion_text": "The total amount of the order is $55.0.",
            "subject_entity": null
          },
          {
            "claim_id": "claim-5",
            "assertion_text": "The order includes 1 Tasting Menu for $45.0.",
            "subject_entity": "Tasting Menu"
          },
          {
            "claim_id": "claim-6",
            "assertion_text": "The order includes 1 Glass of Wine for $10.0.",
            "subject_entity": "Glass of Wine"
          }
        ],
        "entities": [
          {
            "entity_type": "Merchant",
            "entity_id": null,
            "name": "GourmetBistro"
          },
          {
            "entity_type": "Order",
            "entity_id": "ORD-332211",
            "name": null
          },
          {
            "entity_type": "Item",
            "entity_id": null,
            "name": "Tasting Menu"
          },
          {
            "entity_type": "Item",
            "entity_id": null,
            "name": "Glass of Wine"
          }
        ]
      }
    },
    {
      "meta": {
        "case_id": "DSP-2026-00706",
        "document_id": "doc-merchant_pos_system_-1786887476",
        "file_name": "merchant_pos_system_log.pdf",
        "owner": "merchant",
        "evidence_type": "PURCHASE_RECORD",
        "extracted_at": "2026-08-16T13:37:57Z",
        "confidence": 0.95,
        "processed_by": "ocr_pdf_txt_extractor"
      },
      "payload": {
        "order_id": "ORD-332211",
        "total_amount": 85.0,
        "items": []
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "claim-1",
            "assertion_text": "The order ID is ORD-332211.",
            "subject_entity": "Order"
          },
          {
            "claim_id": "claim-2",
            "assertion_text": "The transaction amount is $85.00.",
            "subject_entity": "Order"
          },
          {
            "claim_id": "claim-3",
            "assertion_text": "The transaction status is AUTH_SUCCESS.",
            "subject_entity": "Order"
          }
        ],
        "entities": [
          {
            "entity_type": "Order",
            "entity_id": "ORD-332211",
            "name": null
          }
        ]
      }
    },
    {
      "meta": {
        "case_id": "DSP-2026-00706",
        "document_id": "doc-merchant_pricing_bre-1786887478",
        "file_name": "merchant_pricing_breakdown.pdf",
        "owner": "merchant",
        "evidence_type": "PURCHASE_RECORD",
        "extracted_at": "2026-08-16T13:37:59Z",
        "confidence": 0.95,
        "processed_by": "ocr_pdf_txt_extractor"
      },
      "payload": {
        "total_amount": 85.0,
        "currency": "USD",
        "items": [
          {
            "name": "Standard Menu",
            "price": 55.0
          },
          {
            "name": "Chef's Table Fee",
            "price": 30.0
          }
        ]
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "claim-1",
            "assertion_text": "The Standard Menu costs $55.00.",
            "subject_entity": null
          },
          {
            "claim_id": "claim-2",
            "assertion_text": "The Chef's Table Fee is $30.00 and is mandatory for Saturday and Sunday.",
            "subject_entity": null
          },
          {
            "claim_id": "claim-3",
            "assertion_text": "The Total Charge is $85.00.",
            "subject_entity": null
          }
        ],
        "entities": [
          {
            "entity_type": "Item",
            "entity_id": "standard-menu",
            "name": "Standard Menu"
          },
          {
            "entity_type": "Item",
            "entity_id": "chefs-table-fee",
            "name": "Chef's Table Fee"
          }
        ]
      }
    }
  ]
}

GAP
Verified against source — text accuracy solid again. This is actually the cleanest, most decidable case of the six so far (real receipt shows $55, real weekend policy adds a $30 fee, real POS log confirms $85 charged — no factual ambiguity at all, the whole question is whether the fee was disclosed, which the evidence doesn't settle either way). Notes:

evidence_type wrong for all 3 PDF documents — the receipt, POS log, and pricing breakdown are all tagged PURCHASE_RECORD, and this time it's arguably correct for the receipt but wrong for the other two (a POS transaction log and a pricing policy sheet aren't purchase records). Back to the default-fallback pattern after two categories of partial improvement — confirms the classifier fix isn't systematic yet.
DISPUTE_FORM claims not atomized — sixth category in a row.
Merchant name field holds an ID again — "MID-GOURMET-883" vs "GourmetBistro". Sixth category in a row, now fully unambiguous as a core pipeline bug.
Merchant duplicated as two entities — consequence of #3, sixth time.
dispute_reason inconsistent — "Incorrect Transaction Amount" vs "12.2". Sixth category in a row.
The single most decision-relevant fact in this case has no connecting entity at all — this is this category's version of category 5's finding 6. The cardholder's receipt lists Tasting Menu ($45) + Glass of Wine ($10) = $55. The merchant's pricing breakdown lists Standard Menu ($55) + Chef's Table Fee ($30) = $85. "Tasting Menu" and "Standard Menu" are almost certainly meant to be the same line item, priced differently by each party's own document ($45 vs $55) — and on top of that, the merchant's $55 "Standard Menu" coincidentally equals the cardholder's entire $55 total, meaning it's ambiguous whether the merchant's breakdown even represents the same order composition at all. None of this is connected: Tasting Menu and Standard Menu are extracted as two entirely separate Item entities with no shared identifier, so there's no structural way to compare them side by side — the exact comparison that would actually resolve this dispute.
The merchant's core defense — the $30 fee being "mandatory for Saturday/Sunday" — depends on the purchase date, and nothing connects the two. The cardholder's receipt shows the purchase happened 2026-08-12T19:30:00Z. Whether that date was actually a Saturday or Sunday is the load-bearing fact for the merchant's whole justification, and it's never checked against the pricing policy's "Sat/Sun" condition anywhere in the extraction — the date sits on the receipt, the day-of-week condition sits on the pricing breakdown, and nothing connects them. (For reference: August 12, 2026 is a Wednesday — meaning if this fact were actually checked, the merchant's stated justification for the fee wouldn't even apply to this transaction. That's a significant, currently-undetected finding.)

Running tally, 6 categories in: items 2, 3, 4, 5 are unbroken across all six categories — these four are your highest-confidence, must-fix-first list. Item 1's classifier accuracy is inconsistent, not improving monotonically — worth a dedicated look at what differs between the cases where it worked (categories 4, 5) and where it didn't (this one, categories 1-3), since right now it looks more like coincidental keyword hits than a real fix. Item 6 in this case is a genuinely strong finding — the actual undetected fact (August 12, 2026 was a Wednesday, not a weekend) would flip the merchant's stated justification if checked, and it's sitting unexamined only because nothing connects a purchase date to a day-of-week policy condition.



//eark category

{
  "title": "Canonical Case Evidence Extractions",
  "case_id": "DSP-2026-00807",
  "generated_at": "2026-08-16T13:46:24Z",
  "summary": {
    "source_data_dir": "data\\category_7_weak",
    "total_documents_processed": 4,
    "structured_form_documents": 2,
    "unstructured_documents": 2,
    "unique_entities_discovered": {
      "case_ids": [
        "DSP-2026-00807"
      ],
      "order_ids": [
        "ORD-445566"
      ],
      "tracking_numbers": [],
      "merchants": [
        "MID-GADGET-221",
        "GadgetWorld"
      ]
    }
  },
  "extractions": [
    {
      "meta": {
        "case_id": "DSP-2026-00807",
        "document_id": "doc-form-cardholder_intake_fo-1786887980",
        "file_name": "cardholder_intake_form.json",
        "owner": "cardholder",
        "evidence_type": "DISPUTE_FORM",
        "extraction_method": "deterministic_regex_form_parser",
        "extracted_at": "2026-08-15T10:00:00Z",
        "confidence": 1.0
      },
      "payload": {
        "merchant_name": "GadgetWorld",
        "customer_name": "Cardholder",
        "dispute_reason": "Item Not Received",
        "claim": "I ordered a wireless mouse 10 days ago and I have not received it. The merchant has not provided any tracking information despite multiple requests.",
        "requested_resolution": "Full refund",
        "disputed_amount": 25.0,
        "currency": "USD"
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "ast-form-887980-1",
            "assertion_text": "I ordered a wireless mouse 10 days ago and I have not received it. The merchant has not provided any tracking information despite multiple requests.",
            "subject_entity": "ORD-445566"
          }
        ],
        "entities": [
          {
            "entity_type": "Merchant",
            "entity_id": "MER-GADGETWORLD",
            "name": "GadgetWorld"
          },
          {
            "entity_type": "Order",
            "entity_id": "ORD-445566",
            "name": "ORD-445566"
          }
        ]
      }
    },
    {
      "meta": {
        "case_id": "DSP-2026-00807",
        "document_id": "doc-form-merchant_response_fo-1786887980",
        "file_name": "merchant_response_form.json",
        "owner": "merchant",
        "evidence_type": "DISPUTE_FORM",
        "extraction_method": "deterministic_regex_form_parser",
        "extracted_at": "2026-08-18T14:00:00Z",
        "confidence": 1.0
      },
      "payload": {
        "merchant_name": "MID-GADGET-221",
        "customer_name": "Cardholder",
        "dispute_reason": "13.1",
        "claim": "We shipped the item as per our internal records. We do not have a tracking number available for this low-value shipment.",
        "requested_resolution": "deny refund",
        "currency": "USD"
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "ast-form-887980-1",
            "assertion_text": "We shipped the item as per our internal records. We do not have a tracking number available for this low-value shipment.",
            "subject_entity": null
          }
        ],
        "entities": []
      }
    },
    {
      "meta": {
        "case_id": "DSP-2026-00807",
        "document_id": "doc-cardholder_order_con-1786887980",
        "file_name": "cardholder_order_confirmation.pdf",
        "owner": "cardholder",
        "evidence_type": "PURCHASE_RECORD",
        "extracted_at": "2026-08-16T13:46:22Z",
        "confidence": 0.95,
        "processed_by": "ocr_pdf_txt_extractor"
      },
      "payload": {
        "order_id": "ORD-445566",
        "purchase_date": "2026-08-05T14:00:00Z",
        "total_amount": 25.0,
        "currency": "USD",
        "items": [
          {
            "name": "Wireless Mouse",
            "price": 25.0
          }
        ]
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "claim-1",
            "assertion_text": "The order number is ORD-445566.",
            "subject_entity": "Order"
          },
          {
            "claim_id": "claim-2",
            "assertion_text": "The order date is 2026-08-05T14:00:00Z.",
            "subject_entity": "Order"
          },
          {
            "claim_id": "claim-3",
            "assertion_text": "The item purchased is a Wireless Mouse.",
            "subject_entity": "Item"
          },
          {
            "claim_id": "claim-4",
            "assertion_text": "The total amount paid is $25.00.",
            "subject_entity": "Order"
          },
          {
            "claim_id": "claim-5",
            "assertion_text": "The shipping method is Standard Ground.",
            "subject_entity": "Order"
          }
        ],
        "entities": [
          {
            "entity_type": "Order",
            "entity_id": "ORD-445566",
            "name": "Order ORD-445566"
          },
          {
            "entity_type": "Item",
            "entity_id": "Wireless Mouse",
            "name": "Wireless Mouse"
          }
        ]
      }
    },
    {
      "meta": {
        "case_id": "DSP-2026-00807",
        "document_id": "doc-merchant_internal_or-1786887983",
        "file_name": "merchant_internal_order_status.pdf",
        "owner": "merchant",
        "evidence_type": "PURCHASE_RECORD",
        "extracted_at": "2026-08-16T13:46:24Z",
        "confidence": 0.95,
        "processed_by": "ocr_pdf_txt_extractor"
      },
      "payload": {
        "order_id": "ORD-445566",
        "items": []
      },
      "extraction": {
        "assertions": [
          {
            "claim_id": "claim-1",
            "assertion_text": "The order has been shipped.",
            "subject_entity": "Order"
          },
          {
            "claim_id": "claim-2",
            "assertion_text": "The order ID is ORD-445566.",
            "subject_entity": "Order"
          },
          {
            "claim_id": "claim-3",
            "assertion_text": "The ship date is 2026-08-06.",
            "subject_entity": "Order"
          },
          {
            "claim_id": "claim-4",
            "assertion_text": "The carrier is USPS (Untracked).",
            "subject_entity": "Order"
          }
        ],
        "entities": [
          {
            "entity_type": "Order",
            "entity_id": "ORD-445566",
            "name": "Order"
          },
          {
            "entity_type": "Carrier",
            "entity_id": "USPS",
            "name": "USPS"
          }
        ]
      }
    }
  ]
}

Verified — accurate text extraction, last one confirmed clean. This is the last of your seven, designed to test Evidence Agent's gap detection specifically, so the analysis is shorter and more targeted:

DISPUTE_FORM claims not atomized — seventh category in a row, unbroken.
Merchant name field holds an ID again — "MID-GADGET-221" vs "GadgetWorld". Seventh in a row, unbroken.
Merchant duplicated as two entities — consequence of #2, seventh in a row.
dispute_reason inconsistent — "Item Not Received" vs "13.1". Seventh in a row, unbroken. (Note: this case reuses category 1's reason code and text exactly, which is fine and expected — it's a weak-evidence Item Not Received variant, same category, different evidence completeness, per your original design intent.)
evidence_type wrong for both PDFs — both tagged PURCHASE_RECORD; the internal order status document is a fulfillment/shipping status report, not a purchase record.
The case's design intent — genuinely weak merchant evidence — did come through correctly in the raw content, and it's the cleanest confirmation yet that Evidence Agent's checklist logic itself works. No tracking number, no delivery confirmation, no signature, no TOS excerpt, no proof-of-delivery of any kind — just an unverifiable internal claim of "shipped, but untracked." Checked against REQUIRED_EVIDENCE_MATRIX["13.1"]["merchant"] = {MERCHANT_POLICY, TRACKING_REPORT, DELIVERY_PROOF} — all three required categories are genuinely missing here, so this case should trigger real, correctly-identified evidence gaps once run through Evidence Agent, exactly as designed. Good test case, functioning as intended at the data level.
One thing worth checking once you run this through the pipeline, not an extraction bug per se: the merchant's claim states "we do not have a tracking number for this low-value shipment" — framing untracked shipping as a normal business practice tied to item value ($25 mouse), not negligence. Whether your Evidence Agent/Decision Agent treats "merchant explains why evidence is missing" any differently from "merchant simply failed to provide required evidence" is a real design question worth deciding deliberately — right now nothing in your pipeline distinguishes an excused gap from an unexcused one, and for this case specifically, that distinction could reasonably matter to a real-world decision (network rules about compelling evidence generally don't accept "low value" as an excuse, but it's worth confirming that's actually how your Evidence Agent treats it, rather than assuming).
Final tally across all 7 categories
Bug	Categories hit	Verdict
DISPUTE_FORM not atomized	7/7	Fix first — universal
Merchant name field = ID	7/7	Fix first — universal
Merchant duplicated as entity	7/7	Direct consequence of above
dispute_reason inconsistent	7/7	Fix first — universal
evidence_type misclassified	5-6/7, improving unevenly	Needs a real rewrite, not incremental keyword patching
Generic-noun entities (e.g. "refund", "subscription")	2/7 (cat 4, 5)	Worth fixing, lower priority
Cross-document fact linkage missing on the case's decisive fact	7/7, different fact each time (delivery ambiguity, complaint gap, item-per-order, usage-after-cancel, item-name mismatch, weekend-fee date check)	This is the most important finding across the whole set — every single case has its actual outcome-determining comparison sitting unconnected across two+ documents

The last row is the real headline: it's not that any one category is missing a feature — it's that the specific fact each dispute actually turns on is, every single time, the one thing your extraction fails to connect. That's not coincidence; it's a structural gap in how entities get identified and merged across documents, and it'll keep recurring on every new case you generate until the canonicalization/entity-resolution layer is fixed generically — which is exactly the pipeline-first priority you already decided on two turns ago, now backed by seven-for-seven evidence.








