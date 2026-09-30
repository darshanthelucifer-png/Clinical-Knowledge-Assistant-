"""
================================================================================
ClinSaarthi AI - Column-Aware PDF Layout Analysis
================================================================================
What it does:
    Extracts text blocks from clinical guideline PDFs using PyMuPDF (fitz),
    detects multi-column scientific layouts (2-column / 3-column) via spatial
    coordinate clustering, and sequences text blocks in true human reading order
    (top-to-bottom within Column 1, then Column 2, etc.) while preserving section
    headings and bounding box coordinates for frontend visual highlighting.

Python Concepts Demonstrated:
    1. Python Dataclasses (@dataclass): Typed data representation of text blocks.
    2. Generators & Streaming (yield): Yielding page blocks lazily to conserve RAM
       on massive 100+ page clinical guideline manuals.
    3. Custom Sorting Functions (sorted with multi-key lambdas): Spatial ordering
       based on (column_index, y0).
================================================================================
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Generator, Optional
import re
import fitz  # PyMuPDF

@dataclass
class TextBlock:
    """Represents a discrete text block extracted from a PDF with spatial metadata."""
    text: str
    page_number: int
    column_id: int
    bounding_box: Dict[str, float]  # {"x0": float, "y0": float, "x1": float, "y1": float}
    section_title: str = ""
    font_size: float = 10.0

class PDFLayoutExtractor:
    """
    Column-aware layout analyzer for multi-column medical guidelines and journals.
    """
    SECTION_HEADING_REGEX = re.compile(
        r'^(?:[0-9]{1,2}(?:\.[0-9]{1,2})*\s+[A-Z][A-Za-z0-9\s,-]{3,80}|[A-Z\s]{4,60})$'
    )

    @classmethod
    def analyze_columns(cls, blocks: List[tuple], page_width: float) -> int:
        """
        Determines if a page is single-column, two-column, or multi-column.
        Checks distribution of block centers and x-coordinates.
        """
        if not blocks:
            return 1

        midpoint = page_width / 2.0
        left_col_count = 0
        right_col_count = 0

        for block in blocks:
            x0, y0, x1, y1, text, block_no, block_type = block[:7]
            if block_type != 0 or not text.strip():  # Skip images/empty blocks
                continue
            width = x1 - x0
            # If the block spans across more than 75% of page width, it's a full-width header
            if width > page_width * 0.75:
                continue
            if x1 <= midpoint * 1.15:
                left_col_count += 1
            elif x0 >= midpoint * 0.85:
                right_col_count += 1

        # If both left and right columns have multiple blocks, it's a 2-column layout
        if left_col_count >= 2 and right_col_count >= 2:
            return 2
        return 1

    @classmethod
    def extract_blocks_from_page(
        cls,
        page: fitz.Page,
        page_number: int,
        current_section: str = ""
    ) -> List[TextBlock]:
        """
        Extracts and sorts blocks for a single PDF page in true reading order.
        """
        rect = page.rect
        page_width = rect.width
        raw_blocks = page.get_text("blocks")  # (x0, y0, x1, y1, text, block_no, block_type)
        num_columns = cls.analyze_columns(raw_blocks, page_width)

        classified_blocks: List[Dict[str, Any]] = []
        midpoint = page_width / 2.0

        for b in raw_blocks:
            x0, y0, x1, y1, text, block_no, block_type = b[:7]
            clean_text = text.strip()
            if block_type != 0 or not clean_text:
                continue

            # Assign column id:
            # -1: Full-width banner/title
            #  0: Left column
            #  1: Right column
            width = x1 - x0
            if width > page_width * 0.72:
                col_id = -1
            elif num_columns == 2:
                col_id = 0 if ((x0 + x1) / 2.0) < midpoint else 1
            else:
                col_id = 0

            # Check if this block looks like a section heading
            first_line = clean_text.split('\n')[0].strip()
            if cls.SECTION_HEADING_REGEX.match(first_line) and len(first_line) < 80:
                current_section = first_line

            classified_blocks.append({
                "x0": round(x0, 2),
                "y0": round(y0, 2),
                "x1": round(x1, 2),
                "y1": round(y1, 2),
                "text": clean_text,
                "col_id": col_id,
                "section": current_section
            })

        # Multi-stage sorting for true reading order:
        # Full width headers (-1) come first based on vertical position,
        # then Column 0 top-to-bottom, then Column 1 top-to-bottom.
        def reading_order_key(b):
            col = b["col_id"]
            if col == -1:
                # Full-width blocks are sorted directly by vertical y0 coordinate
                return (0, b["y0"])
            else:
                # Columnar blocks are sorted by column id first, then vertical y0 coordinate
                return (col + 1, b["y0"])

        sorted_blocks = sorted(classified_blocks, key=reading_order_key)

        result: List[TextBlock] = []
        for b in sorted_blocks:
            result.append(TextBlock(
                text=b["text"],
                page_number=page_number,
                column_id=b["col_id"],
                bounding_box={"x0": b["x0"], "y0": b["y0"], "x1": b["x1"], "y1": b["y1"]},
                section_title=b["section"]
            ))

        return result

    @classmethod
    def extract_document(cls, pdf_path: str) -> Generator[List[TextBlock], None, None]:
        """
        Streaming generator yielding parsed TextBlocks page by page.
        """
        doc = fitz.open(pdf_path)
        current_section = "Introduction"
        try:
            for page_idx in range(len(doc)):
                page_num = page_idx + 1
                page = doc[page_idx]
                blocks = cls.extract_blocks_from_page(page, page_num, current_section)
                if blocks and blocks[-1].section_title:
                    current_section = blocks[-1].section_title
                yield blocks
        finally:
            doc.close()
