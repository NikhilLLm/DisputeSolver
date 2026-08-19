"""
Document Text Extractor module for PDF and TXT files.

Provides text extraction for digital PDF files using PyMuPDF (fitz),
OCR fallback via PyTesseract for scanned PDF images, and plain text reading for TXT files.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import pytesseract
    from PIL import Image
    import io
except ImportError:
    pytesseract = None
    Image = None


def extract_text_from_txt(file_path: Path) -> str:
    """Extract raw text from a .txt file using UTF-8 or latin-1 encoding fallback."""
    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return file_path.read_text(encoding="latin-1")


def extract_text_from_pdf(file_path: Path) -> str:
    """
    Extract raw text from a .pdf file using PyMuPDF (fitz).
    If text layer is missing or empty, fallback to PyTesseract OCR.
    """
    if fitz is None:
        raise ImportError("PyMuPDF (fitz) is not installed. Install via `pip install PyMuPDF`.")

    extracted_pages = []
    doc = fitz.open(file_path)

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text").strip()

        # Fallback to OCR if page text is empty / sparse
        if len(text) < 20 and pytesseract is not None and Image is not None:
            pix = page.get_pixmap(dpi=200)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            ocr_text = pytesseract.image_to_string(img).strip()
            if ocr_text:
                text = ocr_text

        if text:
            extracted_pages.append(f"--- PAGE {page_num + 1} ---\n{text}")

    doc.close()
    return "\n\n".join(extracted_pages)


def extract_text_from_image(file_path: Path) -> str:
    """Extract raw text from an image file using PyTesseract OCR."""
    if pytesseract is not None and Image is not None:
        try:
            img = Image.open(file_path)
            return pytesseract.image_to_string(img).strip()
        except Exception:
            return ""
    return ""


def extract_document_text(file_path: Path) -> str:
    """
    Unified function to extract raw text from PDF, TXT, or image files.
    """
    suffix = file_path.suffix.lower()
    if suffix == ".txt":
        return extract_text_from_txt(file_path)
    elif suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    elif suffix in [".png", ".jpg", ".jpeg", ".webp"]:
        return extract_text_from_image(file_path)
    else:
        raise ValueError(f"Unsupported file format for document text extractor: {suffix}")


if __name__ == "__main__":
    sample_pdf = Path("data/cardholder/cardholder_order_receipt.pdf")
    if sample_pdf.exists():
        print(f"--- Extracted text from {sample_pdf} ---")
        print(extract_document_text(sample_pdf))
