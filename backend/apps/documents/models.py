"""
================================================================================
ClinSaarthi AI - Documents & Chunk Models
================================================================================
What it does:
    Stores medical guidelines, books, and policy documents alongside their
    column-parsed chunks, spatial bounding boxes, and vector index references.

Python Concepts Demonstrated:
    1. Relational Modeling: Documents have a one-to-many relationship with Chunks
       and IngestionJobs.
    2. JSONField for Semi-Structured Data: Bounding boxes and layout coordinates
       are stored as JSON without requiring rigid schema tables.
    3. Custom QuerySets / Model Managers: Adding domain methods for filtering
       ingested vs processing documents.
================================================================================
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Document(models.Model):
    """
    Represents an uploaded clinical guideline PDF or reference manual.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='guidelines/')
    description = models.TextField(blank=True)
    author_or_source = models.CharField(max_length=255, blank=True, help_text="e.g. WHO, AHA, ESC, NICE")
    publication_year = models.PositiveIntegerField(null=True, blank=True)
    total_pages = models.PositiveIntegerField(default=0)
    file_size_bytes = models.PositiveBigIntegerField(default=0)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_documents'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.title


class IngestJob(models.Model):
    """
    Tracks the asynchronous pipeline of parsing, OCR, chunking, and embedding.
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        PARSING = 'PARSING', _('Extracting Layout & Columns')
        CHUNKING = 'CHUNKING', _('Sentence-Aware Chunking')
        EMBEDDING = 'EMBEDDING', _('Generating Embeddings & Storing')
        COMPLETED = 'COMPLETED', _('Ingestion Completed')
        FAILED = 'FAILED', _('Ingestion Failed')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='ingest_jobs')
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    progress_percentage = models.PositiveSmallIntegerField(default=0)
    error_message = models.TextField(blank=True)
    chunks_created = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"IngestJob for {self.document.title} [{self.status}]"


class Chunk(models.Model):
    """
    An individual segment of a guideline text, anchored to a specific page and
    column-aware reading order coordinates.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    chunk_index = models.PositiveIntegerField(db_index=True)
    page_number = models.PositiveIntegerField(db_index=True, help_text="1-based PDF page number")
    section_title = models.CharField(max_length=255, blank=True)
    content = models.TextField(help_text="Exact text segment used for retrieval")
    token_count = models.PositiveIntegerField(default=0)
    
    # Spatial metadata for react-pdf source viewer highlighting:
    # bounding_box format: {"x0": float, "y0": float, "x1": float, "y1": float}
    bounding_box = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    # Reference ID inside ChromaDB or FAISS
    vector_id = models.CharField(max_length=128, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['document', 'page_number', 'chunk_index']

    def __str__(self) -> str:
        return f"{self.document.title} - p.{self.page_number} (Chunk #{self.chunk_index})"
