"""
================================================================================
ClinSaarthi AI - Clinical Q&A & Streaming Service
================================================================================
What it does:
    Orchestrates the complete Question-Answering workflow:
    1. Hybrid retrieval (Dense + BM25 + RRF + Reranker) for clinical evidence.
    2. Strict Confidence Gating: Rejects out-of-domain/unsupported queries with
       "I'm not sure — this information is not found in the provided clinical guidelines."
    3. Server-Sent Events (SSE) streaming with live status updates, chunk payloads,
       token-by-token generation, and inline citations [1][2].
    4. Extracts spatial coordinates (bounding_box) for react-pdf viewer highlighting.
    5. Persists Conversation, Message, and Citation records to PostgreSQL/SQLite.

Python Concepts Demonstrated:
    1. Generators (def ... yield): Yielding SSE data payloads for streaming HTTP.
    2. Regular Expression Extraction: Parsing inline citation tags ([1], [2]).
    3. Transactional Database Persistence: Atomic commits of messages and citations.
================================================================================
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Generator, Optional
import json
import re
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.documents.models import Document, Chunk
from apps.qa.models import Conversation, Message, Citation, VerificationResult
from ai.retriever import HybridRetriever
from ai.llm import LLMClient
from ai.prompt_guard import PromptGuard
from services.verification_service import VerificationService

class QAService:
    """
    Coordinates question answering, confidence gating, streaming responses, and citations.
    """
    @classmethod
    def format_context_for_prompt(cls, chunks: List[Dict[str, Any]]) -> str:
        """
        Formats retrieved chunks with strict index delimiters [Chunk 1], [Chunk 2].
        """
        formatted = []
        for i, chk in enumerate(chunks, start=1):
            sec = chk.get("section_title") or "General"
            pg = chk.get("page_number", 1)
            content = chk.get("content", "").strip()
            formatted.append(f"[Chunk {i}] (Page {pg} - Section: {sec})\n{content}")
        return "\n\n".join(formatted)

    @classmethod
    def extract_citations_from_text(
        cls,
        text: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extracts [1], [2] tags from text and binds them to retrieved chunk metadata,
        page numbers, and spatial bounding boxes for the frontend source viewer.
        """
        citation_tags = sorted(list(set(re.findall(r'\[(\d+)\]', text))), key=int)
        citations_data: List[Dict[str, Any]] = []

        for tag in citation_tags:
            idx = int(tag)
            if 1 <= idx <= len(retrieved_chunks):
                chunk = retrieved_chunks[idx - 1]
                # Look up document title
                doc_title = "Clinical Guideline"
                doc_id = chunk.get("document_id")
                if doc_id:
                    try:
                        d = Document.objects.filter(id=doc_id).first()
                        if d:
                            doc_title = d.title
                        else:
                            from apps.notes.models import ClinicalNote
                            n = ClinicalNote.objects.filter(id=doc_id).first()
                            if n:
                                doc_title = f"Patient Note: {n.title}"
                    except Exception:
                        pass

                citations_data.append({
                    "citation_index": idx,
                    "inline_tag": f"[{idx}]",
                    "chunk_id": chunk.get("chunk_id"),
                    "source_title": doc_title,
                    "page_number": chunk.get("page_number", 1),
                    "section_title": chunk.get("section_title", ""),
                    "highlight_text": chunk.get("content", "")[:300],
                    "bounding_box": chunk.get("bounding_box", {})
                })

        return citations_data

    @classmethod
    def ask_stream(
        cls,
        query: str,
        user: Any,
        conversation_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        mode: str = Conversation.Mode.GUIDELINE_QA,
        note_id: Optional[str] = None,
        debug: bool = False
    ) -> Generator[str, None, None]:
        """
        Main SSE streaming generator yielding formatted data frames:
        data: {"type": ..., ...}\n\n
        """
        def format_sse(payload: Dict[str, Any]) -> str:
            return f"data: {json.dumps(payload)}\n\n"

        # Security: Prompt Guardrail Inspection
        guard_res = PromptGuard.inspect(query)
        if not guard_res.is_safe:
            yield format_sse({
                "type": "status",
                "stage": "safety_guard",
                "message": "Adversarial or unsupported prompt pattern detected by safety guardrails."
            })
            rejection_text = guard_res.rejection_message or PromptGuard.DEFAULT_REJECTION_MESSAGE
            yield format_sse({"type": "token", "content": rejection_text})

            with transaction.atomic():
                conversation = None
                if conversation_id:
                    conversation = Conversation.objects.filter(id=conversation_id, user=user).first()
                if not conversation:
                    conversation = Conversation.objects.create(
                        user=user,
                        title=query[:60],
                        mode=mode
                    )

                Message.objects.create(conversation=conversation, role=Message.Role.USER, content=query)
                asst_msg = Message.objects.create(
                    conversation=conversation,
                    role=Message.Role.ASSISTANT,
                    content=rejection_text,
                    confidence_score=0.0,
                    is_not_found=True,
                    disclaimer=settings.DISCLAIMER_TEXT
                )

            yield format_sse({
                "type": "done",
                "conversation_id": str(conversation.id),
                "message_id": str(asst_msg.id),
                "is_not_found": True,
                "confidence_score": 0.0,
                "citations": [],
                "disclaimer": settings.DISCLAIMER_TEXT
            })
            return

        query = guard_res.sanitized_text

        # 1. Step 1: Query Understanding & Expansion
        yield format_sse({
            "type": "status",
            "stage": "understanding",
            "message": "Analyzing clinical query and expanding medical terminology..."
        })

        # 2. Step 2: Evidence Retrieval
        yield format_sse({
            "type": "status",
            "stage": "retrieving",
            "message": "Executing hybrid retrieval (Dense + BM25 + RRF) across guidelines..."
        })

        doc_filter = [str(d) for d in (document_ids or [])]
        if note_id:
            nid = str(note_id)
            if nid not in doc_filter:
                doc_filter.append(nid)

        retriever = HybridRetriever()
        retrieval_res = retriever.retrieve(
            query=query,
            document_filter=doc_filter if doc_filter else None,
            debug=True
        )
        top_chunks = retrieval_res.chunks[:5]

        # Emit retrieved chunks to client immediately for split-pane live display
        yield format_sse({
            "type": "retrieval",
            "chunks": top_chunks,
            "best_score": retrieval_res.best_score,
            "confidence_passed": retrieval_res.confidence_passed,
            "debug_info": retrieval_res.debug_info
        })

        # 3. Step 3: Confidence Gating Check
        # If best rerank score is below threshold, trigger strict refusal
        if not retrieval_res.confidence_passed or not top_chunks:
            yield format_sse({
                "type": "status",
                "stage": "confidence_gate",
                "message": "Confidence threshold not met. Generating grounded refusal notice..."
            })

            not_found_msg = (
                "I'm not sure — this information is not found in the provided clinical guidelines. "
                "Please verify your clinical query or consult other authoritative medical reference sources."
            )

            # Stream refusal text
            yield format_sse({"type": "token", "content": not_found_msg})

            # Persist refusal to database
            with transaction.atomic():
                conversation = None
                if conversation_id:
                    conversation = Conversation.objects.filter(id=conversation_id, user=user).first()
                if not conversation:
                    conversation = Conversation.objects.create(
                        user=user,
                        title=query[:60],
                        mode=mode
                    )

                Message.objects.create(
                    conversation=conversation,
                    role=Message.Role.USER,
                    content=query
                )
                asst_msg = Message.objects.create(
                    conversation=conversation,
                    role=Message.Role.ASSISTANT,
                    content=not_found_msg,
                    confidence_score=retrieval_res.best_score,
                    is_not_found=True,
                    disclaimer=settings.DISCLAIMER_TEXT
                )

            yield format_sse({
                "type": "done",
                "conversation_id": str(conversation.id),
                "message_id": str(asst_msg.id),
                "is_not_found": True,
                "confidence_score": retrieval_res.best_score,
                "citations": [],
                "disclaimer": settings.DISCLAIMER_TEXT
            })
            return

        # 4. Step 4: Grounded Generation with Inline Citations
        yield format_sse({
            "type": "status",
            "stage": "generating",
            "message": "Synthesizing response grounded strictly in retrieved guideline chunks..."
        })

        context_str = cls.format_context_for_prompt(top_chunks)
        llm = LLMClient()
        token_stream = llm.stream_generate(query=query, context=context_str)

        accumulated_answer: List[str] = []
        for token in token_stream:
            accumulated_answer.append(token)
            yield format_sse({
                "type": "token",
                "content": token
            })

        full_answer = "".join(accumulated_answer).strip()

        # 5. Step 5: Citation Extraction & Bounding Box Linking
        citations = cls.extract_citations_from_text(full_answer, top_chunks)
        yield format_sse({
            "type": "citations",
            "citations": citations
        })

        # 6. Step 6: Multi-Node Fact Verification (RxNorm + openFDA + NLI)
        yield format_sse({
            "type": "status",
            "stage": "verifying",
            "message": "Auditing pharmacological claims against cited sources and RxNorm/openFDA..."
        })
        verifications = VerificationService.verify_answer(full_answer, top_chunks)
        yield format_sse({
            "type": "verifications",
            "verifications": verifications
        })

        # 7. Step 7: Atomic Database Persistence
        with transaction.atomic():
            conversation = None
            if conversation_id:
                conversation = Conversation.objects.filter(id=conversation_id, user=user).first()
            if not conversation:
                conversation = Conversation.objects.create(
                    user=user,
                    title=query[:60],
                    mode=mode
                )

            Message.objects.create(
                conversation=conversation,
                role=Message.Role.USER,
                content=query
            )
            asst_msg = Message.objects.create(
                conversation=conversation,
                role=Message.Role.ASSISTANT,
                content=full_answer,
                confidence_score=retrieval_res.best_score,
                is_not_found=False,
                disclaimer=settings.DISCLAIMER_TEXT
            )

            # Persist Citation records
            for cit in citations:
                chunk_obj = None
                chk_id = cit.get("chunk_id")
                if chk_id:
                    try:
                        chunk_obj = Chunk.objects.filter(id=chk_id).first()
                    except Exception:
                        pass

                Citation.objects.create(
                    message=asst_msg,
                    chunk=chunk_obj,
                    citation_index=cit["citation_index"],
                    inline_tag=cit["inline_tag"],
                    source_title=cit["source_title"],
                    page_number=cit["page_number"],
                    section_title=cit.get("section_title", ""),
                    highlight_text=cit.get("highlight_text", ""),
                    bounding_box=cit.get("bounding_box", {})
                )

            # Persist VerificationResult records
            for ver in verifications:
                VerificationResult.objects.create(
                    message=asst_msg,
                    drug_name=ver["drug_name"],
                    dosage=ver.get("dosage", ""),
                    unit=ver.get("unit", ""),
                    route=ver.get("route", ""),
                    frequency=ver.get("frequency", ""),
                    status=ver["status"],
                    nli_score=ver.get("nli_score"),
                    explanation=ver.get("explanation", ""),
                    rxnorm_cui=ver.get("rxnorm_cui", ""),
                    openfda_match=ver.get("openfda_match", False)
                )

        # 8. Step 8: Done Event
        yield format_sse({
            "type": "done",
            "conversation_id": str(conversation.id),
            "message_id": str(asst_msg.id),
            "is_not_found": False,
            "confidence_score": retrieval_res.best_score,
            "citations": citations,
            "verifications": verifications,
            "disclaimer": settings.DISCLAIMER_TEXT
        })

    @classmethod
    def ask_sync(
        cls,
        query: str,
        user: Any,
        conversation_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        mode: str = Conversation.Mode.GUIDELINE_QA,
        note_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Synchronous Q&A execution for REST API consumers.
        """
        guard_res = PromptGuard.inspect(query)
        if not guard_res.is_safe:
            rejection_text = guard_res.rejection_message or PromptGuard.DEFAULT_REJECTION_MESSAGE
            with transaction.atomic():
                conversation = None
                if conversation_id:
                    conversation = Conversation.objects.filter(id=conversation_id, user=user).first()
                if not conversation:
                    conversation = Conversation.objects.create(
                        user=user,
                        title=query[:60],
                        mode=mode
                    )

                Message.objects.create(conversation=conversation, role=Message.Role.USER, content=query)
                asst_msg = Message.objects.create(
                    conversation=conversation,
                    role=Message.Role.ASSISTANT,
                    content=rejection_text,
                    confidence_score=0.0,
                    is_not_found=True,
                    disclaimer=settings.DISCLAIMER_TEXT
                )

            return {
                "conversation_id": str(conversation.id),
                "message_id": str(asst_msg.id),
                "answer": rejection_text,
                "is_not_found": True,
                "confidence_score": 0.0,
                "citations": [],
                "verifications": [],
                "disclaimer": settings.DISCLAIMER_TEXT
            }

        query = guard_res.sanitized_text

        doc_filter = [str(d) for d in (document_ids or [])]
        if note_id:
            nid = str(note_id)
            if nid not in doc_filter:
                doc_filter.append(nid)

        retriever = HybridRetriever()
        retrieval_res = retriever.retrieve(
            query=query,
            document_filter=doc_filter if doc_filter else None,
            debug=True
        )
        top_chunks = retrieval_res.chunks[:5]

        # Confidence gate check
        if not retrieval_res.confidence_passed or not top_chunks:
            answer = (
                "I'm not sure — this information is not found in the provided clinical guidelines. "
                "Please verify your clinical query or consult other authoritative medical reference sources."
            )
            is_not_found = True
            citations = []
            verifications = []
        else:
            context_str = cls.format_context_for_prompt(top_chunks)
            llm = LLMClient()
            answer = llm.generate(query=query, context=context_str)
            is_not_found = False
            citations = cls.extract_citations_from_text(answer, top_chunks)
            verifications = VerificationService.verify_answer(answer, top_chunks)

        # Persist to database
        with transaction.atomic():
            conversation = None
            if conversation_id:
                conversation = Conversation.objects.filter(id=conversation_id, user=user).first()
            if not conversation:
                conversation = Conversation.objects.create(
                    user=user,
                    title=query[:60],
                    mode=mode
                )

            Message.objects.create(conversation=conversation, role=Message.Role.USER, content=query)
            asst_msg = Message.objects.create(
                conversation=conversation,
                role=Message.Role.ASSISTANT,
                content=answer,
                confidence_score=retrieval_res.best_score,
                is_not_found=is_not_found,
                disclaimer=settings.DISCLAIMER_TEXT
            )

            for cit in citations:
                chunk_obj = None
                chk_id = cit.get("chunk_id")
                if chk_id:
                    try:
                        chunk_obj = Chunk.objects.filter(id=chk_id).first()
                    except Exception:
                        chunk_obj = None
                Citation.objects.create(
                    message=asst_msg,
                    chunk=chunk_obj,
                    citation_index=cit["citation_index"],
                    inline_tag=cit["inline_tag"],
                    source_title=cit["source_title"],
                    page_number=cit["page_number"],
                    section_title=cit.get("section_title", ""),
                    highlight_text=cit.get("highlight_text", ""),
                    bounding_box=cit.get("bounding_box", {})
                )

            for ver in verifications:
                VerificationResult.objects.create(
                    message=asst_msg,
                    drug_name=ver["drug_name"],
                    dosage=ver.get("dosage", ""),
                    unit=ver.get("unit", ""),
                    route=ver.get("route", ""),
                    frequency=ver.get("frequency", ""),
                    status=ver["status"],
                    nli_score=ver.get("nli_score"),
                    explanation=ver.get("explanation", ""),
                    rxnorm_cui=ver.get("rxnorm_cui", ""),
                    openfda_match=ver.get("openfda_match", False)
                )

        return {
            "conversation_id": str(conversation.id),
            "message_id": str(asst_msg.id),
            "answer": answer,
            "confidence_score": retrieval_res.best_score,
            "is_not_found": is_not_found,
            "citations": citations,
            "verifications": verifications,
            "disclaimer": settings.DISCLAIMER_TEXT
        }

    @classmethod
    def ask_agentic(
        cls,
        query: str,
        user: Any,
        conversation_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        mode: str = Conversation.Mode.GUIDELINE_QA,
        note_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes the LangGraph 8-node multi-step verification agent.
        """
        guard_res = PromptGuard.inspect(query)
        if not guard_res.is_safe:
            rejection_text = guard_res.rejection_message or PromptGuard.DEFAULT_REJECTION_MESSAGE
            with transaction.atomic():
                conversation = None
                if conversation_id:
                    conversation = Conversation.objects.filter(id=conversation_id, user=user).first()
                if not conversation:
                    conversation = Conversation.objects.create(
                        user=user,
                        title=query[:60],
                        mode=mode
                    )

                Message.objects.create(conversation=conversation, role=Message.Role.USER, content=query)
                asst_msg = Message.objects.create(
                    conversation=conversation,
                    role=Message.Role.ASSISTANT,
                    content=rejection_text,
                    confidence_score=0.0,
                    is_not_found=True,
                    disclaimer=settings.DISCLAIMER_TEXT
                )

            return {
                "conversation_id": str(conversation.id),
                "message_id": str(asst_msg.id),
                "answer": rejection_text,
                "is_not_found": True,
                "confidence_score": 0.0,
                "citations": [],
                "verifications": [],
                "disclaimer": settings.DISCLAIMER_TEXT
            }

        query = guard_res.sanitized_text

        from ai.graph.graph import build_graph

        doc_filter = [str(d) for d in (document_ids or [])]
        if note_id:
            nid = str(note_id)
            if nid not in doc_filter:
                doc_filter.append(nid)

        graph = build_graph()
        state = graph.invoke({
            "raw_query": query,
            "document_ids": doc_filter if doc_filter else None
        })

        final_answer = state.get("final_answer") or state.get("draft_answer", "")
        citations = state.get("citations", [])
        verifications = state.get("verification_results", [])
        is_refusal = state.get("is_refusal", False)
        best_score = state.get("best_rerank_score", 0.0)

        # Atomic persistence
        with transaction.atomic():
            conversation = None
            if conversation_id:
                conversation = Conversation.objects.filter(id=conversation_id, user=user).first()
            if not conversation:
                conversation = Conversation.objects.create(
                    user=user,
                    title=query[:60],
                    mode=mode
                )

            Message.objects.create(conversation=conversation, role=Message.Role.USER, content=query)
            asst_msg = Message.objects.create(
                conversation=conversation,
                role=Message.Role.ASSISTANT,
                content=final_answer,
                confidence_score=best_score,
                is_not_found=is_refusal,
                disclaimer=settings.DISCLAIMER_TEXT,
                metadata={
                    "clinical_intent": state.get("clinical_intent", ""),
                    "repair_count": state.get("repair_count", 0),
                    "expanded_query": state.get("expanded_query", "")
                }
            )

            for cit in citations:
                chunk_obj = None
                chk_id = cit.get("chunk_id")
                if chk_id:
                    try:
                        chunk_obj = Chunk.objects.filter(id=chk_id).first()
                    except Exception:
                        chunk_obj = None
                Citation.objects.create(
                    message=asst_msg,
                    chunk=chunk_obj,
                    citation_index=cit["citation_index"],
                    inline_tag=cit["inline_tag"],
                    source_title=cit["source_title"],
                    page_number=cit["page_number"],
                    section_title=cit.get("section_title", ""),
                    highlight_text=cit.get("highlight_text", ""),
                    bounding_box=cit.get("bounding_box", {})
                )

            for ver in verifications:
                VerificationResult.objects.create(
                    message=asst_msg,
                    drug_name=ver["drug_name"],
                    dosage=ver.get("dosage", ""),
                    unit=ver.get("unit", ""),
                    route=ver.get("route", ""),
                    frequency=ver.get("frequency", ""),
                    status=ver["status"],
                    nli_score=ver.get("nli_score"),
                    explanation=ver.get("explanation", ""),
                    rxnorm_cui=ver.get("rxnorm_cui", ""),
                    openfda_match=ver.get("openfda_match", False)
                )

        return {
            "conversation_id": str(conversation.id),
            "message_id": str(asst_msg.id),
            "answer": final_answer,
            "confidence_score": best_score,
            "is_not_found": is_refusal,
            "citations": citations,
            "verifications": verifications,
            "repair_count": state.get("repair_count", 0),
            "clinical_intent": state.get("clinical_intent", ""),
            "disclaimer": settings.DISCLAIMER_TEXT
        }
