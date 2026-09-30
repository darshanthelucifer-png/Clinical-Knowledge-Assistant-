"""
Document Views
Thin API views for listing, uploading, and retrieving medical guidelines and their chunks.
"""
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Document, Chunk, IngestJob
from .serializers import DocumentSerializer, ChunkSerializer, IngestJobSerializer
from services.ingestion_service import IngestionService

class DocumentListCreateView(generics.ListCreateAPIView):
    queryset = Document.objects.filter(is_active=True)
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        document = serializer.save(uploaded_by=self.request.user)
        # Automatically process document ingestion
        try:
            IngestionService.process_document(document.id)
        except Exception as e:
            # Document created; job will reflect failure status
            pass


class DocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]


class DocumentChunksListView(generics.ListAPIView):
    serializer_class = ChunkSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        document_id = self.kwargs.get('document_id')
        return Chunk.objects.filter(document_id=document_id).order_by('page_number', 'chunk_index')


class DocumentIngestTriggerView(APIView):
    """
    POST /api/v1/documents/<id>/ingest/
    Manually triggers or re-runs ingestion pipeline for a document.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        try:
            document = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            return Response({"error": "Document not found."}, status=status.HTTP_404_NOT_FOUND)

        job = IngestionService.process_document(document.id)
        return Response(IngestJobSerializer(job).data, status=status.HTTP_200_OK)


class IngestJobDetailView(generics.RetrieveAPIView):
    queryset = IngestJob.objects.all()
    serializer_class = IngestJobSerializer
    permission_classes = [permissions.IsAuthenticated]
