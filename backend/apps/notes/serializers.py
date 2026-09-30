"""
Serializers for Clinical Notes & PII De-identification
"""
from rest_framework import serializers
from .models import ClinicalNote, PIIMapping

class ClinicalNoteSerializer(serializers.ModelSerializer):
    """Safe serializer exposing only de-identified content."""
    uploader_name = serializers.CharField(source='uploader.username', read_only=True)

    class Meta:
        model = ClinicalNote
        fields = [
            'id', 'title', 'masked_content', 'pii_entity_count',
            'department', 'uploader_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'masked_content', 'pii_entity_count', 'uploader_name', 'created_at', 'updated_at']

class ClinicalNoteUploadSerializer(serializers.Serializer):
    """
    Accepts raw clinical note text or text file on upload.
    The service layer masks PII before persisting to database or vector store.
    """
    title = serializers.CharField(max_length=255, default="Clinical Note")
    raw_content = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text="Raw clinical note with patient data. Will be masked immediately before database save."
    )
    file = serializers.FileField(
        write_only=True,
        required=False,
        help_text="Raw clinical note .txt file."
    )
    department = serializers.CharField(max_length=120, required=False, allow_blank=True)

    def validate(self, data):
        if not data.get('raw_content') and not data.get('file'):
            raise serializers.ValidationError("Either raw_content or file must be provided.")
        return data

class PIIMappingSerializer(serializers.ModelSerializer):
    """Exposes PII mapping only to the authorized note owner."""
    class Meta:
        model = PIIMapping
        fields = ['id', 'note', 'mapping_data', 'categories_detected', 'created_at']
        read_only_fields = ['id', 'created_at']
