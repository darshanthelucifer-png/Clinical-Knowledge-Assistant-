"""
================================================================================
ClinSaarthi AI - Clinical Document Ingestion Service
================================================================================
What it does:
    Coordinates the end-to-end PDF processing pipeline:
    1. Tracks asynchronous execution state via IngestJob.
    2. Opens guideline PDF via PyMuPDF.
    3. Detects multi-column layouts and orders text in true reading order.
    4. Extracts structured tables and formats them as Markdown.
    5. Falls back to OCR when scanned or rasterized pages are detected.
    6. Chunks text into sentence-aware segments (300-500 tokens, 15% overlap)
       with calculated spatial bounding box envelopes.
    7. Atomically saves chunks to database and updates document metadata.

Python Concepts Demonstrated:
    1. Pipeline / Orchestrator Pattern: Seamlessly coordinates multiple specialized
       modules (Layout, Tables, OCR, Chunker).
    2. Django Database Transactions (transaction.atomic): Ensures all chunks and
       status updates commit together or roll back on error.
    3. Bulk Database Operations (bulk_create): High-throughput ORM persistence
       minimizing database roundtrips.
================================================================================
"""
from typing import List, Dict, Any, Optional
import os
from django.db import transaction
from django.utils import timezone
import pymupdf

from apps.documents.models import Document, Chunk, IngestJob
from ingestion.pdf_layout import PDFLayoutExtractor, TextBlock
from ingestion.tables import TableExtractor
from ingestion.ocr import OCRProcessor
from ingestion.chunker import ClinicalChunker, ChunkPayload

class IngestionService:
    """
    Service orchestrating the complete PDF parsing and chunking workflow.
    """
    @classmethod
    def process_document(cls, document_id: str) -> IngestJob:
        """
        Executes the ingestion pipeline for a registered Document.
        """
        document = Document.objects.get(pk=document_id)

        job = IngestJob.objects.create(
            document=document,
            status=IngestJob.Status.PARSING,
            started_at=timezone.now(),
            progress_percentage=10
        )

        try:
            # Resolve actual filesystem path cleanly for both uploaded files and direct paths
            raw_name = document.file.name if hasattr(document.file, 'name') else str(document.file)
            if os.path.isabs(raw_name) and os.path.exists(raw_name):
                pdf_path = raw_name
            else:
                try:
                    pdf_path = document.file.path
                except Exception:
                    from django.conf import settings
                    pdf_path = str(settings.MEDIA_ROOT / raw_name)

            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found at path: {pdf_path}")

            # Update document file size
            document.file_size_bytes = os.path.getsize(pdf_path)

            doc = pymupdf.open(pdf_path)
            total_pages = len(doc)
            document.total_pages = total_pages
            document.save(update_fields=['total_pages', 'file_size_bytes'])

            all_page_blocks: List[Any] = []
            current_section = "Introduction"

            # ------------------------------------------------------------------
            # Stage 1: Layout Analysis, Table Extraction & OCR Fallback
            # ------------------------------------------------------------------
            for page_idx in range(total_pages):
                page_num = page_idx + 1
                page = doc[page_idx]

                # 1. Extract structured tables first
                tables = TableExtractor.extract_tables_from_page(page, page_num)
                for t in tables:
                    all_page_blocks.append(TextBlock(
                        text=t.markdown_content,
                        page_number=page_num,
                        column_id=-1,
                        bounding_box=t.bounding_box,
                        section_title=current_section
                    ))

                # 2. Extract columnar text blocks
                text_blocks = PDFLayoutExtractor.extract_blocks_from_page(
                    page=page,
                    page_number=page_num,
                    current_section=current_section
                )

                # Check if page is scanned/empty
                combined_text = "".join(b.text for b in text_blocks)
                if OCRProcessor.is_scanned_page(combined_text) and not tables:
                    ocr_text, ocr_bbox = OCRProcessor.run_ocr_on_page(page)
                    if ocr_text:
                        all_page_blocks.append(TextBlock(
                            text=ocr_text,
                            page_number=page_num,
                            column_id=0,
                            bounding_box=ocr_bbox,
                            section_title=current_section
                        ))
                else:
                    all_page_blocks.extend(text_blocks)
                    if text_blocks and text_blocks[-1].section_title:
                        current_section = text_blocks[-1].section_title

            doc.close()

            # ------------------------------------------------------------------
            # Stage 2: Sentence-Aware Chunking (300-500 tokens, 15% overlap)
            # ------------------------------------------------------------------
            job.status = IngestJob.Status.CHUNKING
            job.progress_percentage = 60
            job.save(update_fields=['status', 'progress_percentage'])

            chunker = ClinicalChunker(target_tokens=400, overlap_tokens=60)
            chunk_payloads: List[ChunkPayload] = chunker.chunk_page_blocks(all_page_blocks)

            # ------------------------------------------------------------------
            # Stage 3: Atomic Persistence in Database
            # ------------------------------------------------------------------
            with transaction.atomic():
                # Remove prior chunks if re-ingesting
                document.chunks.all().delete()

                chunk_instances = [
                    Chunk(
                        document=document,
                        chunk_index=cp.chunk_index,
                        page_number=cp.page_number,
                        section_title=cp.section_title,
                        content=cp.content,
                        token_count=cp.token_count,
                        bounding_box=cp.bounding_box,
                        metadata=cp.metadata
                    )
                    for cp in chunk_payloads
                ]

                Chunk.objects.bulk_create(chunk_instances)

            # ------------------------------------------------------------------
            # Stage 4: Dense Vector Indexing (ChromaDB / Swappable Vector Store)
            # ------------------------------------------------------------------
            job.status = IngestJob.Status.EMBEDDING
            job.progress_percentage = 85
            job.save(update_fields=['status', 'progress_percentage'])

            try:
                from ai.vectorstore import get_vector_store
                vstore = get_vector_store()
                vstore.delete_document_chunks(str(document.id))
                vstore.add_chunks(chunk_instances)
            except Exception as v_err:
                pass

            # Update Job to Completed
            job.status = IngestJob.Status.COMPLETED
            job.chunks_created = len(chunk_instances)
            job.progress_percentage = 100
            job.completed_at = timezone.now()
            job.save()

            return job

        except Exception as exc:
            job.status = IngestJob.Status.FAILED
            job.error_message = str(exc)
            job.completed_at = timezone.now()
            job.save()
            raise exc
