"""
LLM Pipeline for Unstructured Documents & Evidence.

Processes evidence files (.pdf, .txt, .png, .jpg, .jpeg, .webp) through:
1. Router (EvidenceType & Owner classification)
2. Stage 1 Text/OCR Extraction (Vision VLM for images, fitz/pytesseract for PDF/TXT)
3. Stage 2 Final Text LLM Normalization into EvidenceEnvelopes
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from worker.extraction.llm_extractor import LLMExtractor


def run_llm_pipeline(
    data_dir: Path = Path("data"),
    output_dir: Path = Path("output/extractions"),
    case_id: Optional[str] = None,
    rate_limit_delay_seconds: float = 1.0,
) -> List[Dict[str, Any]]:
    """Run extraction pipeline on unstructured evidence documents."""
    extractor = LLMExtractor()
    output_dir.mkdir(parents=True, exist_ok=True)

    unstructured_files: List[Path] = []
    supported_extensions = {".pdf", ".txt", ".png", ".jpg", ".jpeg", ".webp"}

    for path in data_dir.glob("**/*"):
        if path.is_file() and not path.name.startswith(".") and "_pdf_images" not in path.parts:
            # Skip structured intake forms (handled by FormExtractor)
            if "form" in path.name.lower() and path.suffix.lower() == ".json":
                continue
            if path.suffix.lower() in supported_extensions:
                unstructured_files.append(path)

    print(f"============================================================")
    print(f"[LLM Pipeline] Found {len(unstructured_files)} unstructured evidence files.")
    print(f"============================================================")
    for idx, f in enumerate(unstructured_files, 1):
        print(f"  {idx}. {f} ({f.suffix})")
    print(f"============================================================\n")

    master_extractions: List[Dict[str, Any]] = []

    for idx, file_path in enumerate(unstructured_files, 1):
        print(f"[{idx}/{len(unstructured_files)}] Extracting: {file_path} ...")
        try:
            envelope = extractor.extract_canonical_envelope(file_path, case_id=case_id)

            ev_type = envelope["meta"]["evidence_type"]
            owner = envelope["meta"]["owner"]
            proc_by = envelope["meta"]["processed_by"]
            print(f"  -> SUCCESS | Type: {ev_type} | Owner: {owner} | Method: {proc_by}")

            master_extractions.append(envelope)

        except Exception as exc:
            print(f"  -> ERROR extracting {file_path}: {exc}")

        if idx < len(unstructured_files) and rate_limit_delay_seconds > 0:
            time.sleep(rate_limit_delay_seconds)

    print(f"\n============================================================")
    print(f"[LLM Pipeline] Complete! Processed {len(master_extractions)} unstructured document(s).")
    print(f"============================================================")

    return master_extractions


if __name__ == "__main__":
    run_llm_pipeline()
