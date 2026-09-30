"""
Serializers for Q&A, Citations, and Verifications
"""
from rest_framework import serializers
from .models import Conversation, Message, Citation, VerificationResult

class CitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Citation
        fields = [
            'id', 'citation_index', 'inline_tag', 'source_title',
            'page_number', 'section_title', 'highlight_text', 'bounding_box'
        ]

class VerificationResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationResult
        fields = [
            'id', 'drug_name', 'dosage', 'unit', 'route',
            'frequency', 'status', 'nli_score', 'explanation',
            'rxnorm_cui', 'openfda_match'
        ]

class MessageSerializer(serializers.ModelSerializer):
    citations = CitationSerializer(many=True, read_only=True)
    verifications = VerificationResultSerializer(many=True, read_only=True)

    class Meta:
        model = Message
        fields = [
            'id', 'role', 'content', 'confidence_score',
            'is_not_found', 'disclaimer', 'citations', 'verifications',
            'created_at'
        ]

class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'title', 'mode', 'messages', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class AskQuestionInputSerializer(serializers.Serializer):
    """Input payload for /ask endpoint."""
    question = serializers.CharField(required=True)
    conversation_id = serializers.UUIDField(required=False, allow_null=True)
    mode = serializers.ChoiceField(choices=Conversation.Mode.choices, default=Conversation.Mode.GUIDELINE_QA)
    document_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=list,
        help_text="Optional filter for specific documents"
    )
    note_id = serializers.UUIDField(required=False, allow_null=True)
