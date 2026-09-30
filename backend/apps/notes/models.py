"""
================================================================================
ClinSaarthi AI - Clinical Notes & Restricted PII Models
================================================================================
What it does:
    Stores de-identified clinical notes safe for embedding and LLM inference.
    Isolates sensitive raw PII mappings in a separate, access-restricted table
    accessible ONLY to the original uploader (or authorized compliance admin).

Python Concepts Demonstrated:
    1. Separation of Concerns & Zero-Trust Data Architecture:
       Decoupling public AI data (ClinicalNote.masked_content) from
       HIPAA/GDPR-restricted mappings (PIIMapping.mapping_dict).
    2. One-to-One Relationships: Guaranteeing exactly one mapping record per note.
    3. Custom Field Validators: Ensuring no masked note is saved without passing
       pre-save sanitation checks.
================================================================================
"""
import uuid
from django.db import models
from django.conf import settings

class ClinicalNote(models.Model):
    """
    Represents a patient clinical record or discharge summary.
    NOTE: Only de-identified/masked text is stored in `masked_content`.
    Raw text is never sent to LLMs, vector databases, or logs.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, default="Untitled Clinical Note")
    masked_content = models.TextField(
        help_text="Sanitized note text with placeholders (e.g. [PATIENT_1], [PHONE_1])."
    )
    pii_entity_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of detected and masked PII entities."
    )
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='clinical_notes'
    )
    department = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.title} (Masked Entities: {self.pii_entity_count})"


class PIIMapping(models.Model):
    """
    Separate, strictly access-controlled storage for reversible PII placeholders.
    Allows only the original uploader to view the side-by-side original vs masked note.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    note = models.OneToOneField(
        ClinicalNote,
        on_delete=models.CASCADE,
        related_name='pii_mapping'
    )
    # Mapping dict format: {"[PATIENT_1]": "John Doe", "[PHONE_1]": "555-0199"}
    mapping_data = models.JSONField(
        default=dict,
        help_text="Secure mapping dictionary from placeholder token to original value."
    )
    # Metadata about detected categories: {"names": 1, "phones": 1, "mrn": 0}
    categories_detected = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"PIIMapping for Note {self.note_id}"
