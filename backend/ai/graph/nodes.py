"""
================================================================================
ClinSaarthi AI - LangGraph Pipeline Nodes
================================================================================
What it does:
    Contains the 8 independently testable node functions for the LangGraph agent:
    1. understand_node: Acronym expansion and clinical intent classification.
    2. retrieve_node: Executes hybrid dense + sparse retrieval over guideline chunks.
    3. confidence_gate_node: Checks retrieval score threshold; rejects unsupported queries.
    4. generate_node: Grounded LLM generation with prompt-injection defense and repair instructions.
    5. extract_facts_node: Extracts (drug, dose, frequency, route) claim tuples.
    6. verify_node: Cross-checks claims against source text & RxNorm/openFDA.
    7. repair_node: Constructs self-correction instructions or annotates warning banner.
    8. respond_node: Assembles final answer, citations, and disclaimer.

Python Concepts Demonstrated:
    1. Pure Functional Architecture: Each node function accepts a state dictionary
       and returns a dictionary of state updates, ensuring full testability and determinism.
================================================================================
"""
import logging
from typing import Dict, Any, List
from django.conf import settings

from .state import AgentState
from ai.nlp import MedicalNLPExtractor
from ai.retriever import HybridRetriever
from ai.llm import LLMClient
from services.verification_service import VerificationService

logger = logging.getLogger(__name__)


def understand_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 1: Understand
    Expands clinical acronyms and classifies query intent.
    """
    raw_query = state.get("raw_query", "")
    expanded = MedicalNLPExtractor.expand_medical_acronyms(raw_query)
    intent = MedicalNLPExtractor.classify_clinical_intent(raw_query)
    return {
        "expanded_query": expanded,
        "clinical_intent": intent
    }


def retrieve_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 2: Retrieve
    Executes hybrid retrieval (Dense Chroma + BM25 + Cross-Encoder Reranker).
    """
    query = state.get("expanded_query") or state.get("raw_query", "")
    doc_filter = state.get("document_ids", None)

    retriever = HybridRetriever()
    result = retriever.retrieve(query=query, document_filter=doc_filter, debug=True)

    return {
        "retrieved_chunks": result.chunks[:5],
        "best_rerank_score": result.best_score,
        "confidence_passed": result.confidence_passed
    }


def confidence_gate_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 3: Confidence Gate
    Checks if retrieval confidence score meets minimum threshold.
    Routes to refusal if sources lack sufficient evidence.
    """
    passed = state.get("confidence_passed", False)
    chunks = state.get("retrieved_chunks", [])

    if not passed or not chunks:
        refusal_msg = (
            "I'm not sure — this information is not found in the provided clinical guidelines. "
            "Please verify your clinical query or consult other authoritative medical reference sources."
        )
        return {
            "confidence_passed": False,
            "is_refusal": True,
            "draft_answer": refusal_msg,
            "final_answer": refusal_msg
        }

    return {
        "confidence_passed": True,
        "is_refusal": False
    }


def generate_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 4: Generate
    Generates draft answer with inline citation tags [1][2].
    Injects repair instructions if re-routed from repair_node.
    """
    # If already marked as refusal, skip generation
    if state.get("is_refusal"):
        return {"draft_answer": state.get("draft_answer", "")}

    raw_query = state.get("raw_query", "")
    chunks = state.get("retrieved_chunks", [])
    repair_instruction = state.get("repair_instruction", "")

    # Format context passages
    context_lines = []
    for idx, chk in enumerate(chunks, start=1):
        context_lines.append(f"[{idx}] {chk.get('content', '')}")
    context_str = "\n\n".join(context_lines)

    # Inject repair instructions if this is a self-correction pass
    effective_query = raw_query
    if repair_instruction:
        effective_query = (
            f"{raw_query}\n\n"
            f"[MANDATORY SELF-CORRECTION DIRECTIVE]:\n"
            f"The previous draft contained factual discrepancies: {repair_instruction}\n"
            f"Carefully correct these statements strictly according to the guideline text."
        )

    llm = LLMClient()
    answer = llm.generate(query=effective_query, context=context_str)

    return {"draft_answer": answer}


def extract_facts_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 5: Extract Facts
    Extracts structured pharmaceutical claims from the draft answer.
    """
    if state.get("is_refusal"):
        return {"extracted_facts": []}

    draft_answer = state.get("draft_answer", "")
    facts = MedicalNLPExtractor.extract_clinical_claims(draft_answer)
    return {"extracted_facts": facts}


def verify_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 6: Verify
    Cross-checks claims against source chunks and RxNorm / openFDA ontologies.
    Determines if any claim has direct conflicts.
    """
    if state.get("is_refusal"):
        return {"verification_results": [], "has_conflicts": False}

    draft_answer = state.get("draft_answer", "")
    chunks = state.get("retrieved_chunks", [])

    results = VerificationService.verify_answer(draft_answer, chunks)
    has_conflicts = any(r.get("status") == "CONFLICT" for r in results)

    return {
        "verification_results": results,
        "has_conflicts": has_conflicts
    }


def repair_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 7: Repair
    Builds self-correction prompt if conflicts detected and repair_count < 2.
    If repair limit reached (>= 2), appends a prominent clinical warning banner.
    """
    repair_count = state.get("repair_count", 0) + 1
    verification_results = state.get("verification_results", [])

    conflicts = [v for v in verification_results if v.get("status") == "CONFLICT"]

    if repair_count < 2 and conflicts:
        explanations = [c.get("explanation", "") for c in conflicts]
        instruction = " ".join(explanations)
        return {
            "repair_count": repair_count,
            "repair_instruction": instruction
        }

    # Repair limit reached: append safety banner
    banner = (
        "\n\n> [!WARNING]\n"
        "> **CLINICAL AUDIT WARNING**: One or more pharmaceutical claims could not be verified "
        "against the cited reference guideline. Please consult the verification panel below."
    )
    current_answer = state.get("draft_answer", "")
    if banner not in current_answer:
        current_answer = current_answer + banner

    return {
        "repair_count": repair_count,
        "repair_instruction": "",
        "draft_answer": current_answer
    }


def respond_node(state: AgentState) -> Dict[str, Any]:
    """
    Node 8: Respond
    Finalizes response payload, resolves spatial citations, and attaches disclaimer.
    """
    from services.qa_service import QAService

    final_answer = state.get("draft_answer", "")
    chunks = state.get("retrieved_chunks", [])
    is_refusal = state.get("is_refusal", False)

    if is_refusal:
        citations = []
    else:
        citations = QAService.extract_citations_from_text(final_answer, chunks)

    return {
        "final_answer": final_answer,
        "citations": citations,
        "disclaimer": getattr(settings, 'DISCLAIMER_TEXT', 'Mandatory clinical disclaimer.')
    }
