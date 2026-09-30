"""
Serializers for Documents & Chunks
"""
from rest_framework import serializers
from .models import Document, Chunk, IngestJob

class ChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chunk
        fields = [
            'id', 'chunk_index', 'page_number', 'section_title',
            'content', 'token_count', 'bounding_box', 'metadata'
        ]

class DocumentSerializer(serializers.ModelSerializer):
    chunks_count = serializers.IntegerField(source='chunks.count', read_only=True)

    class Meta:
        model = Document
        fields = [
            'id', 'title', 'file', 'description', 'author_or_source',
            'publication_year', 'total_pages', 'file_size_bytes',
            'is_active', 'chunks_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'chunks_count', 'created_at', 'updated_at']

class IngestJobSerializer(serializers.ModelSerializer):
    document_title = serializers.CharField(source='document.title', read_only=True)

    class Meta:
        model = IngestJob
        fields = [
            'id', 'document', 'document_title', 'status',
            'progress_percentage', 'error_message', 'chunks_created',
            'started_at', 'completed_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
