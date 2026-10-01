"""
Clinical Note Views
Thin views for listing, uploading, and viewing masked notes and side-by-side diffs.
"""
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from .models import ClinicalNote, PIIMapping
from .serializers import (
    ClinicalNoteSerializer,
    ClinicalNoteUploadSerializer,
    PIIMappingSerializer
)
from services.pii_service import PIIMasker

class ClinicalNoteListView(generics.ListAPIView):
    """
    GET /api/v1/notes/
    Lists masked clinical notes visible to the user.
    """
    serializer_class = ClinicalNoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin_role:
            return ClinicalNote.objects.all()
        return ClinicalNote.objects.filter(uploader=user)


class ClinicalNoteUploadView(APIView):
    """
    POST /api/v1/notes/
    Thin view: Parses payload, passes raw text to PIIMasker service,
    saves sanitized note and isolated mapping, and returns masked note.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = 'notes'

    def post(self, request, *args, **kwargs):
        serializer = ClinicalNoteUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        title = serializer.validated_data.get('title', 'Clinical Note')
        department = serializer.validated_data.get('department', '')

        raw_text = serializer.validated_data.get('raw_content')
        uploaded_file = serializer.validated_data.get('file')
        if uploaded_file:
            raw_text = uploaded_file.read().decode('utf-8', errors='replace')
            if not title or title == 'Clinical Note':
                title = uploaded_file.name

        # Delegate business logic strictly to service layer
        mask_result = PIIMasker.mask(raw_text)

        # Security check: assert zero raw PII values leak into the masked text
        raw_values = [v for v in mask_result.mapping.values() if len(v.strip()) >= 3]
        PIIMasker.assert_no_pii_leak(mask_result.masked_text, raw_values)

        note = ClinicalNote.objects.create(
            title=title,
            masked_content=mask_result.masked_text,
            pii_entity_count=len(mask_result.mapping),
            uploader=request.user,
            department=department
        )

        PIIMapping.objects.create(
            note=note,
            mapping_data=mask_result.mapping,
            categories_detected=mask_result.categories_detected
        )

        # Index de-identified note chunks into vector store
        try:
            from ai.vectorstore import get_vector_store
            from dataclasses import dataclass, field

            @dataclass
            class NoteChunkItem:
                id: str
                content: str
                document_id: str
                page_number: int = 1
                section_title: str = "Clinical Note"
                token_count: int = 0
                bounding_box: dict = field(default_factory=dict)

            vstore = get_vector_store()
            paragraphs = [p.strip() for p in mask_result.masked_text.split('\n\n') if p.strip()]
            if not paragraphs:
                paragraphs = [mask_result.masked_text]

            note_chunks = [
                NoteChunkItem(
                    id=f"note_{note.id}_{i}",
                    content=p,
                    document_id=str(note.id),
                    page_number=1,
                    section_title=f"Clinical Note: {title}",
                    token_count=len(p.split())
                )
                for i, p in enumerate(paragraphs, start=1)
            ]
            vstore.add_chunks(note_chunks)
        except Exception:
            pass

        return Response(ClinicalNoteSerializer(note).data, status=status.HTTP_201_CREATED)


class ClinicalNoteDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/notes/<id>/
    Retrieves masked clinical note.
    Access restricted to note uploader or system administrators.
    """
    serializer_class = ClinicalNoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin_role:
            return ClinicalNote.objects.all()
        return ClinicalNote.objects.filter(uploader=user)


class ClinicalNoteDiffView(APIView):
    """
    GET /api/v1/notes/<id>/diff/
    Restricted to note uploader. Returns side-by-side original vs masked
    with highlighted redactions.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        try:
            note = ClinicalNote.objects.get(pk=pk)
        except ClinicalNote.DoesNotExist:
            return Response({"error": "Note not found."}, status=status.HTTP_404_NOT_FOUND)

        if note.uploader != request.user and not request.user.is_admin_role:
            raise PermissionDenied("Only the original uploader or an administrator can access note PII.")

        try:
            mapping = note.pii_mapping
            mapping_data = mapping.mapping_data
            categories = mapping.categories_detected
        except PIIMapping.DoesNotExist:
            mapping_data = {}
            categories = {}

        # Reconstruct original text using unmasking service
        original_text = PIIMasker.unmask(note.masked_content, mapping_data)

        return Response({
            "id": str(note.id),
            "title": note.title,
            "masked_content": note.masked_content,
            "original_content": original_text,
            "mapping": mapping_data,
            "categories_detected": categories,
            "pii_entity_count": note.pii_entity_count
        })
