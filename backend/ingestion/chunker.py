"""
================================================================================
ClinSaarthi AI - Sentence-Aware Clinical Text Chunker
================================================================================
What it does:
    Partitions continuous medical guideline text into semantically complete,
    sentence-bounded chunks of 300-500 tokens with approximately 15% overlap (~60 tokens).
    Calculates spatial bounding box envelopes (min_x0, min_y0, max_x1, max_y1)
    and preserves page numbers and section headers for accurate citation linking
    and react-pdf visual passage highlighting.

Python Concepts Demonstrated:
    1. Python Dataclasses (@dataclass): Strongly-typed chunk DTOs.
    2. Regular Expressions & Lookbehind Assertions: Splitting sentences accurately
       without breaking abbreviations (e.g., "vs.", "e.g.", "Dr.") or dosages ("2.5 mg").
    3. Sliding Window / Token Overlap Algorithm: Maintaining context continuity
       without mid-sentence truncation.
================================================================================
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import re

@dataclass
class ChunkPayload:
    """Standardized chunk data ready for database persistence and vector indexing."""
    content: str
    chunk_index: int
    page_number: int
    section_title: str
    token_count: int
    bounding_box: Dict[str, float]
    metadata: Dict[str, Any] = field(default_factory=dict)

class ClinicalChunker:
    """
    Sentence-aware chunker tailored for medical guidelines, clinical trials, and drug labels.
    """
    # Medical and standard abbreviations that should not trigger sentence splits
    ABBREVIATIONS = {
        "e.g.", "i.e.", "dr.", "mr.", "mrs.", "ms.", "vs.", "fig.", "tab.",
        "no.", "vol.", "p.", "pp.", "approx.", "dept.", "prof.", "al.", "etc."
    }

    def __init__(
        self,
        target_tokens: int = 400,
        overlap_tokens: int = 60,
        min_chunk_tokens: int = 100
    ):
        self.target_tokens = target_tokens
        self.overlap_tokens = overlap_tokens
        self.min_chunk_tokens = min_chunk_tokens

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Estimates token count for English clinical text.
        Averages approximately 1.3 tokens per word.
        """
        words = text.split()
        return max(1, int(len(words) * 1.3))

    @classmethod
    def split_sentences(cls, text: str) -> List[str]:
        """
        Splits paragraph into sentences respecting abbreviations, decimals, and dosages.
        """
        clean = text.strip()
        if not clean:
            return []

        # Split on candidate sentence terminators (period, exclamation, question mark followed by whitespace)
        # or double newlines
        parts = re.split(r'(\. |\? |\! |\n\n+)', clean)

        sentences: List[str] = []
        current_sentence = ""

        i = 0
        while i < len(parts):
            segment = parts[i]
            current_sentence += segment

            # If the segment was a delimiter
            if i + 1 < len(parts) and parts[i + 1] in ('. ', '? ', '! ') or (segment in ('. ', '? ', '! ')):
                pass

            # Check if current_sentence ends with a period delimiter
            if current_sentence.endswith(('. ', '.\n', '? ', '! ', '\n\n')):
                stripped = current_sentence.rstrip()
                last_word = stripped.split()[-1].lower() if stripped.split() else ""

                # If the last word is an abbreviation or single letter, do not split!
                if last_word in cls.ABBREVIATIONS or (len(last_word) == 2 and last_word.endswith('.')):
                    # Continue accumulating into current sentence
                    pass
                else:
                    sentences.append(stripped)
                    current_sentence = ""
            i += 1

        if current_sentence.strip():
            sentences.append(current_sentence.strip())

        return sentences

    @staticmethod
    def merge_bounding_boxes(boxes: List[Dict[str, float]]) -> Dict[str, float]:
        """
        Computes the outer bounding box envelope containing all provided boxes.
        Format: {"x0": min_x, "y0": min_y, "x1": max_x, "y1": max_y}
        """
        valid_boxes = [b for b in boxes if b and "x0" in b and "y0" in b]
        if not valid_boxes:
            return {"x0": 0.0, "y0": 0.0, "x1": 0.0, "y1": 0.0}

        min_x0 = min(b["x0"] for b in valid_boxes)
        min_y0 = min(b["y0"] for b in valid_boxes)
        max_x1 = max(b["x1"] for b in valid_boxes)
        max_y1 = max(b["y1"] for b in valid_boxes)

        return {
            "x0": round(min_x0, 2),
            "y0": round(min_y0, 2),
            "x1": round(max_x1, 2),
            "y1": round(max_y1, 2)
        }

    def chunk_page_blocks(
        self,
        blocks: List[Any],  # List of TextBlock or dicts
        start_chunk_index: int = 0
    ) -> List[ChunkPayload]:
        """
        Converts ordered page blocks into sentence-aware overlapping chunks.
        """
        chunks: List[ChunkPayload] = []
        current_sentences: List[Dict[str, Any]] = []
        current_token_count = 0
        chunk_idx = start_chunk_index

        for b in blocks:
            # Handle TextBlock dataclass or dict
            text = b.text if hasattr(b, 'text') else b.get('text', '')
            page_num = b.page_number if hasattr(b, 'page_number') else b.get('page_number', 1)
            section = b.section_title if hasattr(b, 'section_title') else b.get('section_title', '')
            bbox = b.bounding_box if hasattr(b, 'bounding_box') else b.get('bounding_box', {})

            sentences = self.split_sentences(text)
            for s in sentences:
                s_tokens = self.estimate_tokens(s)
                sentence_obj = {
                    "text": s,
                    "tokens": s_tokens,
                    "page_number": page_num,
                    "section": section,
                    "bbox": bbox
                }

                # If adding this sentence exceeds target_tokens and we already have sufficient tokens
                if current_token_count + s_tokens > self.target_tokens and current_token_count >= self.min_chunk_tokens:
                    # Form chunk
                    chunk_text = " ".join(item["text"] for item in current_sentences)
                    if not chunk_text.endswith('.'):
                        chunk_text += '.'
                    chunk_bbox = self.merge_bounding_boxes([item["bbox"] for item in current_sentences])
                    primary_page = current_sentences[0]["page_number"]
                    primary_section = current_sentences[0]["section"]

                    chunks.append(ChunkPayload(
                        content=chunk_text,
                        chunk_index=chunk_idx,
                        page_number=primary_page,
                        section_title=primary_section,
                        token_count=current_token_count,
                        bounding_box=chunk_bbox,
                        metadata={
                            "sentence_count": len(current_sentences),
                            "section": primary_section
                        }
                    ))
                    chunk_idx += 1

                    # Slide window with overlap: keep the trailing sentences amounting to overlap_tokens
                    overlap_sentences: List[Dict[str, Any]] = []
                    overlap_tokens_accum = 0
                    for item in reversed(current_sentences):
                        overlap_sentences.insert(0, item)
                        overlap_tokens_accum += item["tokens"]
                        if overlap_tokens_accum >= self.overlap_tokens:
                            break

                    current_sentences = overlap_sentences
                    current_token_count = sum(item["tokens"] for item in current_sentences)

                current_sentences.append(sentence_obj)
                current_token_count += s_tokens

        # Flush remaining sentences as the final chunk
        if current_sentences:
            chunk_text = " ".join(item["text"] for item in current_sentences)
            if not chunk_text.endswith('.'):
                chunk_text += '.'
            chunk_bbox = self.merge_bounding_boxes([item["bbox"] for item in current_sentences])
            primary_page = current_sentences[0]["page_number"]
            primary_section = current_sentences[0]["section"]

            chunks.append(ChunkPayload(
                content=chunk_text,
                chunk_index=chunk_idx,
                page_number=primary_page,
                section_title=primary_section,
                token_count=current_token_count,
                bounding_box=chunk_bbox,
                metadata={
                    "sentence_count": len(current_sentences),
                    "section": primary_section
                }
            ))

        return chunks
