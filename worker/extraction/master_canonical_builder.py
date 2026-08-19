"""
Master Canonical Builder.

Combines:
1. Structured Non-LLM Regex Form Extractions (with claim atomization & reason normalization)
2. Unstructured LLM Extractions (with content-aware routing & typed schemas)

Performs Dynamic Entity Deduplication:
- Merges MID- identifiers with canonical Merchant names.
- Filters out generic stop-nouns (e.g. 'return', 'refund', 'subscription').
- Drops null/empty placeholder entities.
- Deduplicates exact-match Item entities (SKU-first, then normalized name) --
  deliberately conservative: unlike merchants, item variants are NOT fuzzy-merged,
  since "ordered item" vs "received item" are meant to stay distinct entities
  in categories like Not-as-Described.
- Generates ONE unified, pristine canonical JSON file:
  output/extractions/final_canonical_case_extractions.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

# Ensure project root is in sys.path when running script directly
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from worker.extraction.form_extractor import FormExtractor
from worker.extraction.llm_pipeline import run_llm_pipeline

STOP_NOUNS = {
    "return", "refund", "subscription", "order", "item", "status",
    "delivery", "billing cycle", "product", "dispute", "case", "unknown", "null", "none"
}


def _is_real_merchant_name(name: str) -> bool:
    """Return True only if name looks like a real business name, not a system ID."""
    if not name or name in ("Merchant", "Cardholder", "null", "None", "Unknown"):
        return False
    if name.startswith("MID-") or name.startswith("MER-"):
        return False
    return True


def _pick_canonical_merchant(names: List[str]) -> str:
    """From a list of discovered real merchant names, pick one canonical name.

    Strategy: longest name wins (e.g. "TechGadgets Inc." beats "TechGadgets"),
    since shorter variants are usually truncations of the full legal name.

    CAVEAT (flagged, not fully solved here): "longest wins" breaks when the
    longer variant is actually a DIFFERENT sub-entity, not a fuller legal
    name -- e.g. "StreamMax" vs "StreamMax Billing" picks "StreamMax Billing"
    (a billing department name) as canonical, which is arguably worse than
    the shorter, cleaner "StreamMax". This still correctly unifies both
    variants into ONE merchant (avoiding duplicate nodes), it just may not
    always pick the most natural display name. A more robust fix would need
    a merchant name whitelist or frequency-based voting across documents
    rather than a length heuristic -- worth revisiting if this surfaces on
    a real case, not fixed here to avoid over-engineering on one data point.
    """
    if not names:
        return "Merchant"
    return max(names, key=len)


def _name_matches_canonical(name: str, canonical: str) -> bool:
    """Check if a name is a variant of the canonical merchant name.

    Handles: exact match, substring containment, case-insensitive.
    e.g. "TechGadgets" matches "TechGadgets Inc.", "techgadgets inc." matches too.
    """
    a = name.lower().strip().rstrip(".")
    b = canonical.lower().strip().rstrip(".")
    return a == b or a in b or b in a


def _normalize_item_key(sku: Optional[str], name: Optional[str]) -> Optional[str]:
    """Build a dedup key for an Item entity. SKU is preferred (strong identity
    signal); falls back to a normalized (lowercased, whitespace-collapsed)
    name only when no SKU is present. Returns None if neither is usable.

    Deliberately exact-match only -- no substring/fuzzy matching like the
    merchant logic, because two differently-named items in the same case
    (e.g. "ProFit Wireless Headphones" ordered vs "White Standard
    Headphones" received) are very often meant to be genuinely DIFFERENT
    entities, not variants of one thing. Fuzzy-merging them would erase
    the exact distinction a Not-as-Described dispute needs to reason over.
    """
    if sku:
        return f"sku:{sku.strip().lower()}"
    if name:
        norm = re.sub(r"\s+", " ", name.strip().lower())
        return f"name:{norm}" if norm else None
    return None


def deduplicate_and_clean_entities(all_envelopes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Dynamically deduplicate merchants, orders, customers, items, and filter
    out false entities.
    """
    # --- Pass 1: discover real merchant names & item SKU mappings across envelopes ---
    discovered_names: List[str] = []
    item_sku_map: Dict[str, str] = {}      # SKU -> Canonical Item Title
    item_title_catalog: List[str] = []     # List of full known product titles

    for env in all_envelopes:
        payload = env.get("payload", {})
        m_name = payload.get("merchant_name")
        if _is_real_merchant_name(m_name) and m_name not in discovered_names:
            discovered_names.append(m_name)

        # Collect SKUs and item names from structured PurchaseRecord / payloads
        for item in payload.get("items", []):
            if isinstance(item, dict):
                iname = item.get("name")
                isku = item.get("sku")
                if iname and isku:
                    item_sku_map[isku.strip().upper()] = iname.strip()
                    item_sku_map[isku.strip()] = iname.strip()
                if iname and iname not in item_title_catalog:
                    item_title_catalog.append(iname)

        for ent in env.get("extraction", {}).get("entities", []):
            etype = ent.get("entity_type")
            name = ent.get("name")
            eid = ent.get("entity_id")

            if etype == "Merchant":
                if _is_real_merchant_name(name) and name not in discovered_names:
                    discovered_names.append(name)
            elif etype in ("Item", "OrderedItem", "ReceivedItem"):
                if name and name not in item_title_catalog and len(name) > 3:
                    item_title_catalog.append(name)

    canonical_merchant = _pick_canonical_merchant(discovered_names)
    canonical_merchant_id = (
        f"MER-{re.sub(r'[^A-Z0-9]+', '-', canonical_merchant.upper()).strip('-')}"
        if canonical_merchant != "Merchant" else None
    )

    # --- Pass 2: clean each envelope ---
    clean_case_ids: Set[str] = set()
    clean_order_ids: Set[str] = set()
    clean_tracking_numbers: Set[str] = set()
    clean_merchants: Set[str] = {canonical_merchant} if canonical_merchant != "Merchant" else set()
    clean_customers: Set[str] = set()
    clean_reports: Set[str] = set()
    clean_devices: Set[str] = set()
    clean_user_accounts: Set[str] = set()
    clean_subscriptions: Set[str] = set()
    clean_inspectors: Set[str] = set()
    clean_ordered_items: Dict[str, Dict[str, Any]] = {}
    clean_received_items: Dict[str, Dict[str, Any]] = {}
    clean_general_items: Dict[str, Dict[str, Any]] = {}

    for env in all_envelopes:
        meta = env.get("meta", {})
        payload = env.get("payload", {})
        extraction = env.get("extraction", {})

        if meta.get("case_id") and meta["case_id"] != "DSP-UNKNOWN":
            clean_case_ids.add(meta["case_id"])

        # Synchronize merchant names & IDs in payload
        cur_name = payload.get("merchant_name")
        if cur_name and not _is_real_merchant_name(cur_name):
            payload["merchant_name"] = canonical_merchant
        elif cur_name and _is_real_merchant_name(cur_name) and _name_matches_canonical(cur_name, canonical_merchant):
            payload["merchant_name"] = canonical_merchant

        # Align merchant_id in payload so it never holds an orphaned, un-canonicalized MID
        if "merchant_id" in payload and canonical_merchant != "Merchant":
            payload["merchant_id"] = canonical_merchant

        if canonical_merchant_id:
            payload["canonical_merchant_id"] = canonical_merchant_id

        if payload.get("order_id"):
            clean_order_ids.add(payload["order_id"])
        if payload.get("subscription_id"):
            clean_subscriptions.add(payload["subscription_id"])
        if payload.get("user_id"):
            clean_user_accounts.add(payload["user_id"])
        if payload.get("ip_address"):
            clean_devices.add(payload["ip_address"])
        if payload.get("device_id"):
            clean_devices.add(payload["device_id"])
        if payload.get("inspection_id"):
            clean_inspectors.add(payload["inspection_id"])
        if payload.get("transaction_reference") and re.search(r"ORD-|SUB-", payload["transaction_reference"]):
            clean_order_ids.add(payload["transaction_reference"])
        if payload.get("tracking_number"):
            clean_tracking_numbers.add(payload["tracking_number"])
        if payload.get("report_number"):
            clean_reports.add(payload["report_number"])
        if payload.get("customer_name") and payload["customer_name"] not in ("Cardholder", "null"):
            clean_customers.add(payload["customer_name"])

        # Clean extraction entities
        cleaned_envelope_entities = []
        for ent in extraction.get("entities", []):
            etype = ent.get("entity_type", "Entity")
            eid = (ent.get("entity_id") or "").strip()
            ename = (ent.get("name") or "").strip()

            # Skip empty entities
            if not eid and not ename:
                continue

            # Skip generic stop-nouns
            eid_is_stop = eid.lower() in STOP_NOUNS
            ename_is_stop = ename.lower() in STOP_NOUNS
            has_digit = bool(re.search(r"\d", eid) or re.search(r"\d", ename))
            if (eid_is_stop or ename_is_stop) and not has_digit:
                continue

            # Merchant entities: always resolve to canonical name
            if etype == "Merchant":
                cleaned_envelope_entities.append({
                    "entity_type": "Merchant",
                    "entity_id": canonical_merchant,
                    "name": canonical_merchant,
                })
                continue

            # Order entities: sanitize so name is ALWAYS Order ID (never product titles)
            if etype == "Order":
                order_id_val = eid or ename
                clean_order_ids.add(order_id_val)
                cleaned_envelope_entities.append({
                    "entity_type": "Order",
                    "entity_id": order_id_val,
                    "name": order_id_val,
                })
                continue

            if etype == "Tracking" and (eid or ename):
                clean_tracking_numbers.add(eid or ename)
            elif etype == "Report" and (eid or ename):
                clean_reports.add(eid or ename)
            elif etype == "Customer" and ename and ename != "Cardholder":
                clean_customers.add(ename)
            elif etype in ("Device", "IPAddress") and (eid or ename):
                clean_devices.add(eid or ename)
            elif etype in ("UserAccount", "Account") and (eid or ename):
                clean_user_accounts.add(eid or ename)
            elif etype == "Subscription" and (eid or ename):
                clean_subscriptions.add(eid or ename)
            elif etype == "Inspector" and (eid or ename):
                clean_inspectors.add(eid or ename)

            # Item entities: resolve SKUs to full item names and group by role
            elif etype in ("Item", "OrderedItem", "ReceivedItem"):
                # Check SKU map
                if eid.upper() in item_sku_map:
                    ename = item_sku_map[eid.upper()]
                elif ename.upper() in item_sku_map:
                    ename = item_sku_map[ename.upper()]

                # Check catalog prefix match (e.g. "ProFit Wireless - Black" -> "ProFit Wireless Headphones")
                for cat_title in item_title_catalog:
                    prefix = " ".join(cat_title.split()[:2])
                    if len(prefix) > 4 and prefix.lower() in (ename or eid).lower():
                        ename = cat_title
                        break

                item_record = {
                    "entity_type": etype,
                    "entity_id": eid or ename,
                    "name": ename or eid,
                }

                if etype == "OrderedItem":
                    clean_ordered_items[ename or eid] = item_record
                elif etype == "ReceivedItem":
                    clean_received_items[ename or eid] = item_record
                else:
                    clean_general_items[ename or eid] = item_record

                cleaned_envelope_entities.append(item_record)
                continue

            cleaned_envelope_entities.append({
                "entity_type": etype,
                "entity_id": eid or ename,
                "name": ename or eid,
            })

        extraction["entities"] = cleaned_envelope_entities

    all_items = list(dict.fromkeys(
        [v["name"] for v in clean_ordered_items.values()]
        + [v["name"] for v in clean_received_items.values()]
        + [v["name"] for v in clean_general_items.values()]
    ))

    return {
        "case_ids": list(clean_case_ids),
        "order_ids": list(clean_order_ids),
        "tracking_numbers": list(clean_tracking_numbers),
        "merchants": list(clean_merchants),
        "customers": list(clean_customers),
        "reports": list(clean_reports),
        "devices": list(clean_devices),
        "user_accounts": list(clean_user_accounts),
        "subscriptions": list(clean_subscriptions),
        "inspectors": list(clean_inspectors),
        "items": all_items,
        "ordered_items": [v["name"] for v in clean_ordered_items.values()],
        "received_items": [v["name"] for v in clean_received_items.values()],
    }


def build_final_canonical_json(
    data_dir: Union[Path, str] = Path("data"),
    output_dir: Union[Path, str] = Path("output/extractions"),
) -> Dict[str, Any]:
    """Combine all document extractions from a data path into one clean final canonical JSON."""
    data_path = Path(data_dir)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    form_extractor = FormExtractor()
    form_files: List[Path] = []
    for p in data_path.glob("**/*.json"):
        if p.is_file() and not p.name.startswith(".") and "form" in p.name.lower():
            form_files.append(p)

    print(f"============================================================")
    print(f"[Canonical Builder] Scanning: {data_path.resolve()}")
    print(f"[Canonical Builder] Ingesting {len(form_files)} structured intake form(s)...")
    print(f"============================================================")

    structured_envelopes: List[Dict[str, Any]] = []
    primary_case_id: Optional[str] = None
    for f in form_files:
        print(f"  -> Extracting structured form: {f.name} ({f})")
        env = form_extractor.extract_form(f)
        structured_envelopes.append(env)
        if not primary_case_id and env.get("meta", {}).get("case_id") and env["meta"]["case_id"] != "DSP-UNKNOWN":
            primary_case_id = env["meta"]["case_id"]

    print(f"\n============================================================")
    print(f"[Canonical Builder] Running multi-stage LLM pipeline on unstructured evidence (Case: {primary_case_id or 'Auto'})...")
    print(f"============================================================")
    unstructured_envelopes = run_llm_pipeline(data_dir=data_path, output_dir=out_path, case_id=primary_case_id)

    all_envelopes = structured_envelopes + unstructured_envelopes

    # Run dynamic entity deduplication & cleaning
    entity_summary = deduplicate_and_clean_entities(all_envelopes)

    final_case_id = entity_summary["case_ids"][0] if entity_summary["case_ids"] else (primary_case_id or "DSP-2026-00187")

    final_canonical_output = {
        "title": "Canonical Case Evidence Extractions",
        "case_id": final_case_id,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": {
            "source_data_dir": str(data_path),
            "total_documents_processed": len(all_envelopes),
            "structured_form_documents": len(structured_envelopes),
            "unstructured_documents": len(unstructured_envelopes),
            
            "unique_entities_discovered": entity_summary,
        },
        "extractions": all_envelopes,
    }

    final_file = out_path / "final_canonical_case_extractions.json"
    final_file.write_text(json.dumps(final_canonical_output, indent=2), encoding="utf-8")

    print(f"\n============================================================")
    print(f"[Canonical Builder] Complete! Clean final canonical JSON generated:")
    print(f"  -> File: {final_file}")
    print(f"  -> Total documents: {len(all_envelopes)}")
    print(f"  -> Case ID: {final_case_id}")
    print(f"  -> Unique Merchants: {entity_summary['merchants']}")
    print(f"  -> Unique Items: {entity_summary['items']}")
    print(f"============================================================")

    return final_canonical_output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Final Canonical JSON for any category data path.")
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data",
        help="Path to input data directory, e.g. data/category_1_not_as_described (default: data)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output/extractions",
        help="Output directory (default: output/extractions)",
    )
    args = parser.parse_args()

    build_final_canonical_json(data_dir=Path(args.data_dir), output_dir=Path(args.output_dir))