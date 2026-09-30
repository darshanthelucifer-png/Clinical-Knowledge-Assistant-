"""
================================================================================
ClinSaarthi AI - Clinical Q&A, Citation & Verification Models
================================================================================
What it does:
    Persists conversational threads, RAG generated answers, fine-grained inline
    citations [1][2] tied to source pages/bounding boxes, and drug verification
    cross-check audits (VERIFIED / UNSUPPORTED / CONFLICT).

Python Concepts Demonstrated:
    1. Rich Relational Structures: Deeply linked database models (Conversation ->
       Message -> Citations & VerificationResults).
    2. Django Model Choices: Clean status enums for verification claims and conversation modes.
    3. Nullable ForeignKeys: Citations can reference a guideline Chunk or fallback to source metadata.
================================================================================
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.documents.models import Chunk

class Conversation(models.Model):
    """
    Groups a sequence of user questions and agentic responses.
    """
    class Mode(models.TextChoices):
        GUIDELINE_QA = 'guideline_qa', _('Guideline Q&A')
        CLINICAL_NOTE_QA = 'clinical_note_qa', _('Clinical Note Q&A')
        STUDY_MODE = 'study_mode', _('Study & Quiz Mode')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversations'
    )
    title = models.CharField(max_length=255, default="New Consultation")
    mode = models.CharField(max_length=30, choices=Mode.choices, default=Mode.GUIDELINE_QA)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self) -> str:
        return f"{self.title} ({self.get_mode_display()})"


class Message(models.Model):
    """
    An individual question or answer inside a conversation.
    """
    class Role(models.TextChoices):
        USER = 'user', _('User')
        ASSISTANT = 'assistant', _('Assistant')
        SYSTEM = 'system', _('System')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=Role.choices)
    content = models.TextField()
    confidence_score = models.FloatField(null=True, blank=True, help_text="Aggregated rerank/faithfulness score (0.0 to 1.0)")
    is_not_found = models.BooleanField(
        default=False,
        help_text="True if confidence gate triggered 'not found in sources'."
    )
    disclaimer = models.TextField(
        default=settings.DISCLAIMER_TEXT,
        help_text="Mandatory clinical disclaimer displayed on every answer."
    )
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self) -> str:
        return f"{self.role.capitalize()}: {self.content[:40]}..."


class Citation(models.Model):
    """
    An inline citation anchor (e.g. [1]) linking an answer passage to an
    exact page, section, and spatial coordinate in a medical document.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='citations')
    chunk = models.ForeignKey(Chunk, on_delete=models.SET_NULL, null=True, blank=True, related_name='citations')
    citation_index = models.PositiveSmallIntegerField(help_text="Citation index number: 1, 2, 3")
    inline_tag = models.CharField(max_length=10, help_text="e.g. [1], [2]")
    source_title = models.CharField(max_length=255)
    page_number = models.PositiveIntegerField()
    section_title = models.CharField(max_length=255, blank=True)
    highlight_text = models.TextField(help_text="Exact sentence or passage cited from source")
    bounding_box = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['citation_index']

    def __str__(self) -> str:
        return f"Citation {self.inline_tag} -> {self.source_title} p.{self.page_number}"


class VerificationResult(models.Model):
    """
    Audited verification check for a single clinical entity (drug, dosage, unit, frequency)
    extracted from the generated answer and checked against cited source text.
    """
    class Status(models.TextChoices):
        VERIFIED = 'VERIFIED', _('Verified in Source')
        UNSUPPORTED = 'UNSUPPORTED', _('Unsupported by Source')
        CONFLICT = 'CONFLICT', _('Direct Conflict / Contradiction')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='verifications')
    drug_name = models.CharField(max_length=120)
    dosage = models.CharField(max_length=80, blank=True)
    unit = models.CharField(max_length=40, blank=True)
    route = models.CharField(max_length=80, blank=True)
    frequency = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices)
    nli_score = models.FloatField(null=True, blank=True, help_text="NLI entailment confidence score")
    explanation = models.TextField(blank=True)
    rxnorm_cui = models.CharField(max_length=64, blank=True, help_text="RxNorm Concept Unique Identifier")
    openfda_match = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self) -> str:
        return f"{self.drug_name} {self.dosage} [{self.status}]"
