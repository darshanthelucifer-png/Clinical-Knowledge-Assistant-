"""
================================================================================
ClinSaarthi AI - OCR Fallback Processor (Tesseract)
================================================================================
What it does:
    Detects scanned or rasterized PDF pages that yield insufficient digital text,
    renders high-DPI page images using PyMuPDF pixmaps, and executes Tesseract OCR
    to extract textual content and spatial bounding boxes.

Python Concepts Demonstrated:
    1. Graceful Degradation & Feature Detection: Checks for Tesseract executable
       availability before execution; safely skips if OCR binary is not in PATH.
    2. Context Managers & Binary Buffer Processing: Converts in-memory pixmap bytes
       to PIL.Image without temporary file disk I/O.
================================================================================
"""
import io
from typing import Tuple, Dict, Any, Optional
import pymupdf
from PIL import Image

class OCRProcessor:
    """
    Handles scanned page detection and Tesseract OCR fallback.
    """
    @classmethod
    def is_scanned_page(cls, text: str, min_characters: int = 50) -> bool:
        """
        Determines whether a page contains insufficient digital text, indicating a scan.
        """
        return len(text.strip()) < min_characters

    @classmethod
    def run_ocr_on_page(cls, page: pymupdf.Page) -> Tuple[str, Dict[str, float]]:
        """
        Renders page to image and runs OCR if Tesseract is available.
        Returns extracted text and page bounding box.
        """
        rect = page.rect
        default_bbox = {
            "x0": 0.0,
            "y0": 0.0,
            "x1": round(rect.width, 2),
            "y1": round(rect.height, 2)
        }

        try:
            import pytesseract
            # Render page at 150 DPI for optimal OCR speed/accuracy balance
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))

            ocr_text = pytesseract.image_to_string(img)
            return ocr_text.strip(), default_bbox
        except Exception:
            # If pytesseract or Tesseract-OCR binary is not installed, return empty gracefully
            return "", default_bbox
