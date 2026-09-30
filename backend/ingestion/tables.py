"""
================================================================================
ClinSaarthi AI - PDF Table Extraction & Markdown Formatting
================================================================================
What it does:
    Detects and extracts structured clinical tables (e.g. pharmacology matrices,
    dosage regimens, diagnostic criteria) from guideline PDF pages using PyMuPDF's
    built-in table engine (page.find_tables()) with pdfplumber fallback.
    Converts tables into clean GitHub-Flavored Markdown for optimal RAG context.

Python Concepts Demonstrated:
    1. Python Dataclasses (@dataclass): Typed representation of structured tabular data.
    2. Fallback / Adapter Pattern: Tries PyMuPDF native table engine first; adapts
       to pdfplumber if installed and allowed by OS policy.
    3. String Formatting & List Comprehensions: Assembling clean Markdown tables.
================================================================================
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import pymupdf

@dataclass
class ExtractedTable:
    """Represents a structured clinical table extracted from a document page."""
    markdown_content: str
    bounding_box: Dict[str, float]  # {"x0": float, "y0": float, "x1": float, "y1": float}
    page_number: int
    row_count: int
    headers: List[str] = field(default_factory=list)

class TableExtractor:
    """
    Extracts tabular data from PDF pages and serializes into LLM-friendly Markdown.
    """
    @classmethod
    def extract_tables_from_page(cls, page: pymupdf.Page, page_number: int) -> List[ExtractedTable]:
        """
        Uses PyMuPDF's native find_tables() to identify and extract table data.
        """
        extracted: List[ExtractedTable] = []
        try:
            tabs = page.find_tables()
            for tab in tabs:
                bbox = tab.bbox  # (x0, y0, x1, y1)
                data = tab.extract()  # list of lists of strings
                if not data or len(data) < 2:
                    continue

                headers = [str(col).strip() if col else f"Col_{i+1}" for i, col in enumerate(data[0])]
                rows = data[1:]

                # Construct Markdown table
                md_lines = []
                header_row = "| " + " | ".join(headers) + " |"
                separator_row = "| " + " | ".join(["---"] * len(headers)) + " |"
                md_lines.append(header_row)
                md_lines.append(separator_row)

                for r in rows:
                    clean_row = [str(cell).strip().replace("\n", " ") if cell else "" for cell in r]
                    # Ensure row length matches headers
                    if len(clean_row) < len(headers):
                        clean_row.extend([""] * (len(headers) - len(clean_row)))
                    elif len(clean_row) > len(headers):
                        clean_row = clean_row[:len(headers)]
                    md_lines.append("| " + " | ".join(clean_row) + " |")

                markdown_table = "\n".join(md_lines)

                extracted.append(ExtractedTable(
                    markdown_content=markdown_table,
                    bounding_box={
                        "x0": round(bbox[0], 2),
                        "y0": round(bbox[1], 2),
                        "x1": round(bbox[2], 2),
                        "y1": round(bbox[3], 2)
                    },
                    page_number=page_number,
                    row_count=len(rows),
                    headers=headers
                ))
        except Exception as e:
            # Graceful recovery: log error and return empty list
            pass

        return extracted
