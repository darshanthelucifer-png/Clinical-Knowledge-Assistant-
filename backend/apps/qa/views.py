"""
Q&A Views
Provides streaming SSE endpoints, conversation history, and consultation export.
"""
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import StreamingHttpResponse, HttpResponse
from django.conf import settings

from .models import Conversation, Message
from .serializers import ConversationSerializer, AskQuestionInputSerializer
from services.qa_service import QAService
from ai.retriever import HybridRetriever

class ConversationListView(generics.ListCreateAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ConversationDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)


class RetrieveDebugView(APIView):
    """
    POST /api/v1/qa/retrieve/
    Executes hybrid retrieval (Dense + BM25 + RRF + Reranker) and returns
    top-5 chunks with comprehensive score and latency telemetry when DEBUG_RAG=true.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = 'ask'

    def post(self, request, *args, **kwargs):
        query = request.data.get('query', '')
        if not query:
            return Response({"error": "Query field is required."}, status=status.HTTP_400_BAD_REQUEST)

        document_ids = request.data.get('document_ids', None)
        debug_param = request.data.get('debug', None)

        retriever = HybridRetriever()
        result = retriever.retrieve(query=query, document_filter=document_ids, debug=debug_param)

        return Response({
            "query": result.query,
            "best_score": result.best_score,
            "confidence_passed": result.confidence_passed,
            "total_candidates_analyzed": result.total_candidates_analyzed,
            "chunks": result.chunks,
            "debug_info": result.debug_info
        }, status=status.HTTP_200_OK)


class AskQuestionView(APIView):
    """
    POST /api/v1/qa/ask/
    Primary Question Answering endpoint.
    Supports Server-Sent Events (SSE) streaming (default) or synchronous JSON.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = 'ask'

    def post(self, request, *args, **kwargs):
        serializer = AskQuestionInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        query = serializer.validated_data['question']
        conversation_id = serializer.validated_data.get('conversation_id', None)
        document_ids = serializer.validated_data.get('document_ids', None)
        mode = serializer.validated_data.get('mode', Conversation.Mode.GUIDELINE_QA)
        note_id = serializer.validated_data.get('note_id', None)

        use_agent = request.data.get('agentic', False)
        if str(use_agent).lower() in ['true', '1']:
            result = QAService.ask_agentic(
                query=query,
                user=request.user,
                conversation_id=conversation_id,
                document_ids=document_ids,
                mode=mode,
                note_id=note_id
            )
            return Response(result, status=status.HTTP_200_OK)

        is_stream = request.data.get('stream', True)
        if str(is_stream).lower() == 'false':
            result = QAService.ask_sync(
                query=query,
                user=request.user,
                conversation_id=conversation_id,
                document_ids=document_ids,
                mode=mode,
                note_id=note_id
            )
            return Response(result, status=status.HTTP_200_OK)

        # SSE Streaming response
        stream_generator = QAService.ask_stream(
            query=query,
            user=request.user,
            conversation_id=conversation_id,
            document_ids=document_ids,
            mode=mode,
            note_id=note_id
        )

        response = StreamingHttpResponse(
            streaming_content=stream_generator,
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response


from rest_framework.renderers import JSONRenderer, BaseRenderer

class MarkdownRenderer(BaseRenderer):
    media_type = 'text/markdown'
    format = 'markdown'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if isinstance(data, str):
            return data.encode('utf-8')
        return str(data).encode('utf-8')


class ConversationExportView(APIView):
    """
    GET /api/v1/qa/conversations/<id>/export/?format=markdown|json
    Exports a consultation with questions, answers, citations, and medical disclaimer.
    """
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [JSONRenderer, MarkdownRenderer]

    def get(self, request, pk, *args, **kwargs):
        try:
            conv = Conversation.objects.get(pk=pk, user=request.user)
        except Conversation.DoesNotExist:
            return Response({"error": "Conversation not found."}, status=status.HTTP_404_NOT_FOUND)

        export_format = request.query_params.get('format', 'markdown').lower()
        messages = conv.messages.all().order_by('created_at')

        if export_format == 'json':
            return Response(ConversationSerializer(conv).data, status=status.HTTP_200_OK)

        # Generate clean Markdown export
        lines = [
            f"# ClinSaarthi AI Consultation Export",
            f"**Consultation ID**: `{conv.id}`",
            f"**Date**: {conv.created_at.strftime('%Y-%m-%d %H:%M UTC')}",
            f"**Clinical Mode**: {conv.get_mode_display()}",
            "\n---\n"
        ]

        for msg in messages:
            role_header = "### 🧑‍⚕️ Clinician Query" if msg.role == Message.Role.USER else "### 🤖 ClinSaarthi AI Guidance"
            lines.append(f"{role_header}:\n{msg.content}\n")

            if msg.role == Message.Role.ASSISTANT and msg.citations.exists():
                lines.append("#### 📚 Verified Guideline Citations:")
                for cit in msg.citations.all():
                    lines.append(
                        f"- **{cit.inline_tag}**: *{cit.source_title}* (Page {cit.page_number}) - Section: {cit.section_title or 'General'}\n"
                        f"  > \"{cit.highlight_text}\""
                    )
                lines.append("")

        lines.append("\n---\n")
        lines.append(f"> **MANDATORY MEDICAL DISCLAIMER**:\n> {settings.DISCLAIMER_TEXT}\n")

        markdown_text = "\n".join(lines)
        response = HttpResponse(markdown_text, content_type='text/markdown; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="consultation_{conv.id}.md"'
        return response
