"""
================================================================================
ClinSaarthi AI - Clinical Q&A & Streaming Service
================================================================================
What it does:
    Orchestrates the complete Question-Answering workflow:
    1. Intent Routing (first pipeline step):
       - GREETING: Short, natural plain text with no citations or verification table.
       - OFF_TOPIC: Short, natural plain text explaining clinical scope.
       - UNSAFE: Defends against prompt injection and adversarial manipulation.
       - MEDICAL / NOTE_QUERY: Triggers evidence-based RAG pipeline.
    2. Hybrid retrieval (Dense + BM25 + RRF + Reranker) for clinical evidence.
    3. Strict Confidence Gating: Real rerank score threshold. Rejects unsupported queries with
       "I'm not sure — this information is not found in the provided documents" + rephrase tip.
    4. Grounded Generation: Addresses ONLY the asked question with inline citations [1][2].
    5. Fact Verification: Audits ONLY the drugs and dosages present in the generated answer.
    6. Server-Sent Events (SSE) streaming with live status updates, chunk payloads, and tokens.
    7. Extracts spatial coordinates (bounding_box) for react-pdf viewer highlighting.
    8. Persists Conversation, Message, and Citation records to PostgreSQL/SQLite.

Python Concepts Demonstrated:
    1. Generators (def ... yield): Yielding SSE data payloads for streaming HTTP.
    2. Intent Routing & Pipeline Dispatch: Directing execution before expensive retrieval.
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
from ai.intent_router import IntentRouter
from services.verification_service import VerificationService


class QAService:
    """
    Coordinates question answering, intent routing, confidence gating, streaming responses, and citations.
    """
    NOT_FOUND_MESSAGE = (
        "I'm not sure — this information is not found in the provided documents. "
        "Please consider rephrasing your clinical question with specific drug names, clinical conditions, "
        "or guideline topics, or consult authoritative medical reference literature."
    )

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

        # ----------------------------------------------------------------------
        # Step 0: Intent Routing (greeting / medical / note_query / off_topic / unsafe)
        # ----------------------------------------------------------------------
        intent_res = IntentRouter.route(query=query, note_id=note_id)

        # Handle UNSAFE Intent
        if intent_res.intent == IntentRouter.UNSAFE:
            yield format_sse({
                "type": "status",
                "stage": "safety_guard",
                "message": "Adversarial or unsupported prompt pattern detected by safety guardrails."
            })
            rejection_text = intent_res.suggested_reply or PromptGuard.DEFAULT_REJECTION_MESSAGE
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
                "intent": "unsafe",
                "is_not_found": True,
                "confidence_score": 0.0,
                "citations": [],
                "verifications": [],
                "disclaimer": settings.DISCLAIMER_TEXT
            })
            return

        # Handle GREETING Intent: Short, natural plain text with NO citations, confidence, or verification
        if intent_res.intent == IntentRouter.GREETING:
            yield format_sse({
                "type": "status",
                "stage": "greeting",
                "message": "Recognized greeting. Formulating clinical assistant greeting..."
            })
            llm = LLMClient()
            token_stream = llm.stream_plain_response(
                prompt=query,
                system_prompt=(
                    "You are ClinSaarthi AI, a polite and professional clinical decision-support assistant. "
                    "Greet the clinician warmly and concisely in 1-2 natural sentences, asking how you can "
                    "assist with clinical guidelines or patient queries today."
                )
            )
            accumulated: List[str] = []
            for token in token_stream:
                accumulated.append(token)
                yield format_sse({"type": "token", "content": token})

            full_greeting = "".join(accumulated).strip()
            if not full_greeting:
                full_greeting = IntentRouter.get_natural_response(intent=IntentRouter.GREETING, query=query)
                yield format_sse({"type": "token", "content": full_greeting})

            with transaction.atomic():
                conversation = None
                if conversation_id:
                    conversation = Conversation.objects.filter(id=conversation_id, user=user).first()
                if not conversation:
                    conversation = Conversation.objects.create(user=user, title=query[:60], mode=mode)

                Message.objects.create(conversation=conversation, role=Message.Role.USER, content=query)
                asst_msg = Message.objects.create(
                    conversation=conversation,
                    role=Message.Role.ASSISTANT,
                    content=full_greeting,
                    confidence_score=None,
                    is_not_found=False,
                    disclaimer=settings.DISCLAIMER_TEXT
                )

            yield format_sse({
                "type": "done",
                "conversation_id": str(conversation.id),
                "message_id": str(asst_msg.id),
                "intent": "greeting",
                "is_not_found": False,
                "confidence_score": None,
                "citations": [],
                "verifications": [],
                "disclaimer": settings.DISCLAIMER_TEXT
            })
            return

        # Handle OFF_TOPIC Intent: Short, natural plain text with NO citations, confidence, or verification
        if intent_res.intent == IntentRouter.OFF_TOPIC:
            yield format_sse({
                "type": "status",
                "stage": "off_topic",
                "message": "Recognized non-clinical query. Explaining clinical decision-support scope..."
            })
            llm = LLMClient()
            token_stream = llm.stream_plain_response(
                prompt=query,
                intent=intent_res.intent,
                system_prompt=(
                    "You are ClinSaarthi AI, a clinical decision-support assistant designed strictly for "
                    "certified medical practice guidelines and patient notes. Politely explain in 1-2 concise sentences "
                    "that you cannot assist with general trivia, sports, or non-medical topics, and invite clinical questions."
                )
            )
            accumulated: List[str] = []
            for token in token_stream:
                accumulated.append(token)
                yield format_sse({"type": "token", "content": token})

            full_reply = "".join(accumulated).strip()
            if not full_reply:
                full_reply = IntentRouter.get_natural_response(intent=IntentRouter.OFF_TOPIC, query=query)
                yield format_sse({"type": "token", "content": full_reply})

            with transaction.atomic():
                conversation = None
                if conversation_id:
                    conversation = Conversation.objects.filter(id=conversation_id, user=user).first()
                if not conversation:
                    conversation = Conversation.objects.create(user=user, title=query[:60], mode=mode)

                Message.objects.create(conversation=conversation, role=Message.Role.USER, content=query)
                asst_msg = Message.objects.create(
                    conversation=conversation,
                    role=Message.Role.ASSISTANT,
                    content=full_reply,
                    confidence_score=None,
                    is_not_found=False,
                    disclaimer=settings.DISCLAIMER_TEXT
                )

            yield format_sse({
                "type": "done",
                "conversation_id": str(conversation.id),
                "message_id": str(asst_msg.id),
                "intent": "off_topic",
                "is_not_found": False,
                "confidence_score": None,
                "citations": [],
                "verifications": [],
                "disclaimer": settings.DISCLAIMER_TEXT
            })
            return

        # ----------------------------------------------------------------------
        # Medical & Note Queries: Evidence-Based RAG Pipeline
        # ----------------------------------------------------------------------
        sanitized_query = query.strip()

        # Step 1: Query Understanding & Expansion
        yield format_sse({
            "type": "status",
            "stage": "understanding",
            "message": "Analyzing clinical query and expanding medical terminology..."
        })

        # Step 2: Evidence Retrieval
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
            query=sanitized_query,
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

        # Step 3: Confidence Gating Check (Real Rerank Score)
        if not retrieval_res.confidence_passed or not top_chunks:
            yield format_sse({
                "type": "status",
                "stage": "confidence_gate",
                "message": "Confidence threshold not met. Generating grounded refusal notice..."
            })

            not_found_msg = cls.NOT_FOUND_MESSAGE
            yield format_sse({"type": "token", "content": not_found_msg})

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
                "intent": intent_res.intent,
                "is_not_found": True,
                "confidence_score": retrieval_res.best_score,
                "citations": [],
                "verifications": [],
                "disclaimer": settings.DISCLAIMER_TEXT
            })
            return

        # Step 4: Grounded Generation (Addresses ONLY the asked question)
        yield format_sse({
            "type": "status",
            "stage": "generating",
            "message": "Synthesizing response grounded strictly in retrieved guideline chunks..."
        })

        context_str = cls.format_context_for_prompt(top_chunks)
        llm = LLMClient()
        token_stream = llm.stream_generate(query=sanitized_query, context=context_str)

        accumulated_answer: List[str] = []
        for token in token_stream:
            accumulated_answer.append(token)
            yield format_sse({
                "type": "token",
                "content": token
            })

        full_answer = "".join(accumulated_answer).strip()

        # Step 5: Citation Extraction & Bounding Box Linking
        citations = cls.extract_citations_from_text(full_answer, top_chunks)
        yield format_sse({
            "type": "citations",
            "citations": citations
        })

        # Step 6: Multi-Node Fact Verification (Verifies ONLY drugs/doses in the generated answer)
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

        # Step 7: Atomic Database Persistence
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

        # Step 8: Done Event
        yield format_sse({
            "type": "done",
            "conversation_id": str(conversation.id),
            "message_id": str(asst_msg.id),
            "intent": intent_res.intent,
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
        # Step 0: Intent Routing
        intent_res = IntentRouter.route(query=query, note_id=note_id)

        # Unsafe
        if intent_res.intent == IntentRouter.UNSAFE:
            rejection_text = intent_res.suggested_reply or PromptGuard.DEFAULT_REJECTION_MESSAGE
            with transaction.atomic():
                conversation = None
                if conversation_id:
                    conversation = Conversation.objects.filter(id=conversation_id, user=user).first()
                if not conversation:
                    conversation = Conversation.objects.create(user=user, title=query[:60], mode=mode)

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
                "intent": "unsafe",
                "answer": rejection_text,
                "is_not_found": True,
                "confidence_score": 0.0,
                "citations": [],
                "verifications": [],
                "disclaimer": settings.DISCLAIMER_TEXT
            }

        # Greeting
        if intent_res.intent == IntentRouter.GREETING:
            llm = LLMClient()
            answer = llm.generate_plain_response(
                prompt=query,
                intent=intent_res.intent,
                system_prompt=(
                    "You are ClinSaarthi AI, a polite and professional clinical decision-support assistant. "
                    "Greet the clinician warmly and concisely in 1-2 natural sentences, asking how you can "
                    "assist with clinical guidelines or patient queries today."
                )
            )
            with transaction.atomic():
                conversation = None
                if conversation_id:
                    conversation = Conversation.objects.filter(id=conversation_id, user=user).first()
                if not conversation:
                    conversation = Conversation.objects.create(user=user, title=query[:60], mode=mode)

                Message.objects.create(conversation=conversation, role=Message.Role.USER, content=query)
                asst_msg = Message.objects.create(
                    conversation=conversation,
                    role=Message.Role.ASSISTANT,
                    content=answer,
                    confidence_score=None,
                    is_not_found=False,
                    disclaimer=settings.DISCLAIMER_TEXT
                )

            return {
                "conversation_id": str(conversation.id),
                "message_id": str(asst_msg.id),
                "intent": "greeting",
                "answer": answer,
                "confidence_score": None,
                "is_not_found": False,
                "citations": [],
                "verifications": [],
                "disclaimer": settings.DISCLAIMER_TEXT
            }

        # Off-Topic
        if intent_res.intent == IntentRouter.OFF_TOPIC:
            llm = LLMClient()
            answer = llm.generate_plain_response(
                prompt=query,
                intent=intent_res.intent,
                system_prompt=(
                    "You are ClinSaarthi AI, a clinical decision-support assistant designed strictly for "
                    "certified medical practice guidelines and patient notes. Politely explain in 1-2 concise sentences "
                    "that you cannot assist with general trivia, sports, or non-medical topics, and invite clinical questions."
                )
            )
            with transaction.atomic():
                conversation = None
                if conversation_id:
                    conversation = Conversation.objects.filter(id=conversation_id, user=user).first()
                if not conversation:
                    conversation = Conversation.objects.create(user=user, title=query[:60], mode=mode)

                Message.objects.create(conversation=conversation, role=Message.Role.USER, content=query)
                asst_msg = Message.objects.create(
                    conversation=conversation,
                    role=Message.Role.ASSISTANT,
                    content=answer,
                    confidence_score=None,
                    is_not_found=False,
                    disclaimer=settings.DISCLAIMER_TEXT
                )

            return {
                "conversation_id": str(conversation.id),
                "message_id": str(asst_msg.id),
                "intent": "off_topic",
                "answer": answer,
                "confidence_score": None,
                "is_not_found": False,
                "citations": [],
                "verifications": [],
                "disclaimer": settings.DISCLAIMER_TEXT
            }

        # Medical & Note Queries
        sanitized_query = query.strip()
        doc_filter = [str(d) for d in (document_ids or [])]
        if note_id:
            nid = str(note_id)
            if nid not in doc_filter:
                doc_filter.append(nid)

        retriever = HybridRetriever()
        retrieval_res = retriever.retrieve(
            query=sanitized_query,
            document_filter=doc_filter if doc_filter else None,
            debug=True
        )
        top_chunks = retrieval_res.chunks[:5]

        # Confidence gate check
        if not retrieval_res.confidence_passed or not top_chunks:
            answer = cls.NOT_FOUND_MESSAGE
            is_not_found = True
            citations = []
            verifications = []
        else:
            context_str = cls.format_context_for_prompt(top_chunks)
            llm = LLMClient()
            answer = llm.generate(query=sanitized_query, context=context_str)
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
            "intent": intent_res.intent,
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
        intent_res = IntentRouter.route(query=query, note_id=note_id)

        if intent_res.intent == IntentRouter.UNSAFE:
            rejection_text = intent_res.suggested_reply or PromptGuard.DEFAULT_REJECTION_MESSAGE
            with transaction.atomic():
                conversation = None
                if conversation_id:
                    conversation = Conversation.objects.filter(id=conversation_id, user=user).first()
                if not conversation:
                    conversation = Conversation.objects.create(user=user, title=query[:60], mode=mode)
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
                "intent": "unsafe",
                "answer": rejection_text,
                "is_not_found": True,
                "confidence_score": 0.0,
                "citations": [],
                "verifications": [],
                "disclaimer": settings.DISCLAIMER_TEXT
            }

        if intent_res.intent == IntentRouter.GREETING:
            llm = LLMClient()
            answer = llm.generate_plain_response(prompt=query)
            with transaction.atomic():
                conversation = None
                if conversation_id:
                    conversation = Conversation.objects.filter(id=conversation_id, user=user).first()
                if not conversation:
                    conversation = Conversation.objects.create(user=user, title=query[:60], mode=mode)
                Message.objects.create(conversation=conversation, role=Message.Role.USER, content=query)
                asst_msg = Message.objects.create(
                    conversation=conversation,
                    role=Message.Role.ASSISTANT,
                    content=answer,
                    confidence_score=None,
                    is_not_found=False,
                    disclaimer=settings.DISCLAIMER_TEXT
                )
            return {
                "conversation_id": str(conversation.id),
                "message_id": str(asst_msg.id),
                "intent": "greeting",
                "answer": answer,
                "confidence_score": None,
                "is_not_found": False,
                "citations": [],
                "verifications": [],
                "disclaimer": settings.DISCLAIMER_TEXT
            }

        if intent_res.intent == IntentRouter.OFF_TOPIC:
            llm = LLMClient()
            answer = llm.generate_plain_response(
                prompt=query,
                system_prompt="Politely explain in 1-2 sentences that ClinSaarthi AI is for medical guidelines only."
            )
            with transaction.atomic():
                conversation = None
                if conversation_id:
                    conversation = Conversation.objects.filter(id=conversation_id, user=user).first()
                if not conversation:
                    conversation = Conversation.objects.create(user=user, title=query[:60], mode=mode)
                Message.objects.create(conversation=conversation, role=Message.Role.USER, content=query)
                asst_msg = Message.objects.create(
                    conversation=conversation,
                    role=Message.Role.ASSISTANT,
                    content=answer,
                    confidence_score=None,
                    is_not_found=False,
                    disclaimer=settings.DISCLAIMER_TEXT
                )
            return {
                "conversation_id": str(conversation.id),
                "message_id": str(asst_msg.id),
                "intent": "off_topic",
                "answer": answer,
                "confidence_score": None,
                "is_not_found": False,
                "citations": [],
                "verifications": [],
                "disclaimer": settings.DISCLAIMER_TEXT
            }

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
            "intent": intent_res.intent,
            "answer": final_answer,
            "confidence_score": best_score,
            "is_not_found": is_refusal,
            "citations": citations,
            "verifications": verifications,
            "repair_count": state.get("repair_count", 0),
            "clinical_intent": state.get("clinical_intent", ""),
            "disclaimer": settings.DISCLAIMER_TEXT
        }
