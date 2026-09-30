"""
================================================================================
ClinSaarthi AI - PDF Layout, Table Extraction & Chunker Tests
================================================================================
What it tests:
    1. Sentence-aware splitting without breaking abbreviations or dosages.
    2. Spatial bounding box envelope calculation (min_x0, min_y0, max_x1, max_y1).
    3. Sliding window token chunking with ~15% overlap and boundary preservation.
    4. Column-aware reading order extraction on 2-column medical guideline PDFs.
    5. Table extraction and GitHub-Flavored Markdown conversion.
    6. End-to-end IngestionService pipeline (Document -> IngestJob -> Chunks).
    7. REST API endpoint retrieving chunks and spatial coordinates for react-pdf.
================================================================================
"""
from pathlib import Path
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.documents.models import Document, Chunk, IngestJob
from ingestion.chunker import ClinicalChunker
from ingestion.pdf_layout import PDFLayoutExtractor
from ingestion.tables import TableExtractor
from services.ingestion_service import IngestionService

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def clinician_user(db):
    return User.objects.create_user(
        username="dr_cardiologist",
        email="cardio@hospital.org",
        password="SecurePassword123!",
        role=User.Role.CLINICIAN,
        department="Cardiology"
    )

@pytest.fixture
def sample_pdf_path():
    p1 = Path(__file__).resolve().parent.parent.parent / "data" / "guidelines" / "sample_afib_guideline.pdf"
    if p1.exists():
        return str(p1)
    p2 = Path(__file__).resolve().parent.parent / "data" / "guidelines" / "sample_afib_guideline.pdf"
    return str(p2)

class TestClinicalChunkerUnit:
    def test_sentence_splitting_preserves_abbreviations_and_dosages(self):
        text = (
            "Patient was evaluated by Dr. Smith for atrial fibrillation. "
            "Administer Apixaban 2.5 mg twice daily e.g. at 8 AM and 8 PM. "
            "Rhythm control vs. rate control was discussed."
        )
        sentences = ClinicalChunker.split_sentences(text)
        assert len(sentences) == 3
        assert "Dr. Smith" in sentences[0]
        assert "Apixaban 2.5 mg twice daily e.g. at 8 AM and 8 PM" in sentences[1]
        assert "Rhythm control vs. rate control was discussed" in sentences[2]

    def test_bounding_box_merge_envelope(self):
        boxes = [
            {"x0": 40.0, "y0": 110.0, "x1": 280.0, "y1": 250.0},
            {"x0": 50.0, "y0": 260.0, "x1": 290.0, "y1": 400.0}
        ]
        envelope = ClinicalChunker.merge_bounding_boxes(boxes)
        assert envelope["x0"] == 40.0
        assert envelope["y0"] == 110.0
        assert envelope["x1"] == 290.0
        assert envelope["y1"] == 400.0

    def test_chunking_with_overlap(self):
        chunker = ClinicalChunker(target_tokens=30, overlap_tokens=10, min_chunk_tokens=15)
        blocks = [
            {
                "text": (
                    "Sentence one introduces the cardiology guideline recommendations. "
                    "Sentence two explains the pathophysiological mechanism of arrhythmia. "
                    "Sentence three details anticoagulation stroke prevention therapy. "
                    "Sentence four discusses renal clearance and dose adjustment criteria. "
                    "Sentence five concludes the clinical management recommendations."
                ),
                "page_number": 1,
                "section_title": "Recommendations",
                "bounding_box": {"x0": 40.0, "y0": 100.0, "x1": 280.0, "y1": 300.0}
            }
        ]
        chunks = chunker.chunk_page_blocks(blocks)
        assert len(chunks) >= 2
        # Verify chunks have index and section
        assert chunks[0].chunk_index == 0
        assert chunks[0].section_title == "Recommendations"
        assert chunks[0].bounding_box["x0"] == 40.0

class TestPDFLayoutAndTables:
    def test_column_aware_reading_order(self, sample_pdf_path):
        import pymupdf
        doc = pymupdf.open(sample_pdf_path)
        page1 = doc[0]

        blocks = PDFLayoutExtractor.extract_blocks_from_page(page1, page_number=1)
        doc.close()

        assert len(blocks) >= 2

        # Verify Column 1 (Introduction) appears BEFORE Column 2 (Stroke Risk)
        block_texts = [b.text for b in blocks]
        full_page_text = " ".join(block_texts)

        intro_pos = full_page_text.find("1. INTRODUCTION")
        stroke_pos = full_page_text.find("3. STROKE RISK")

        assert intro_pos != -1, "Introduction section heading should be present"
        assert stroke_pos != -1, "Stroke risk section heading should be present"
        assert intro_pos < stroke_pos, "Column 1 text must appear BEFORE Column 2 in reading order"

    def test_table_extraction_markdown_and_bbox(self, sample_pdf_path):
        import pymupdf
        doc = pymupdf.open(sample_pdf_path)
        page2 = doc[1]

        tables = TableExtractor.extract_tables_from_page(page2, page_number=2)
        doc.close()

        assert len(tables) >= 1
        table = tables[0]
        assert "Apixaban" in table.markdown_content
        assert "Rivaroxaban" in table.markdown_content
        assert table.page_number == 2
        assert "x0" in table.bounding_box
        assert table.row_count >= 3

@pytest.mark.django_db
class TestIngestionServiceIntegration:
    def test_end_to_end_document_ingestion(self, clinician_user, sample_pdf_path):
        doc = Document.objects.create(
            title="AHA Atrial Fibrillation Guideline 2026",
            file=sample_pdf_path,
            author_or_source="AHA/ACC/HRS",
            publication_year=2026,
            uploaded_by=clinician_user
        )

        job = IngestionService.process_document(str(doc.id))

        assert job.status == IngestJob.Status.COMPLETED
        assert job.chunks_created > 0
        assert job.progress_percentage == 100

        doc.refresh_from_db()
        assert doc.total_pages == 2
        assert doc.file_size_bytes > 0

        # Verify chunks saved in database
        chunks = doc.chunks.all().order_by('page_number', 'chunk_index')
        assert chunks.count() == job.chunks_created

        first_chunk = chunks.first()
        assert first_chunk.page_number == 1
        assert "x0" in first_chunk.bounding_box
        assert first_chunk.token_count > 0

    def test_document_chunks_api_endpoint(self, api_client, clinician_user, sample_pdf_path):
        api_client.force_authenticate(user=clinician_user)

        doc = Document.objects.create(
            title="Test Guideline",
            file=sample_pdf_path,
            uploaded_by=clinician_user
        )
        IngestionService.process_document(str(doc.id))

        # Query chunks API
        url = reverse('documents:document_chunks', kwargs={'document_id': doc.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        results = response.data.get('results', response.data)
        assert len(results) > 0
        assert "bounding_box" in results[0]
        assert "page_number" in results[0]
        assert "content" in results[0]
