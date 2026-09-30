"""
================================================================================
ClinSaarthi AI - Agent State Definition
================================================================================
What it does:
    Defines the typed graph state object passed across nodes in the LangGraph
    verification pipeline. Every node consumes this immutable/typed dictionary,
    computes localized transitions, and yields state updates.

Python Concepts Demonstrated:
    1. Typing.TypedDict: Enforces compile-time schema correctness for complex
       dictionary state dictionaries passed between pipeline stages.
================================================================================
"""
from typing import TypedDict, List, Dict, Any, Optional


class AgentState(TypedDict, total=False):
    # Inputs
    raw_query: str
    document_ids: Optional[List[str]]

    # Step 1: Understand
    expanded_query: str
    clinical_intent: str

    # Step 2: Retrieve
    retrieved_chunks: List[Dict[str, Any]]
    best_rerank_score: float

    # Step 3: Confidence Gate
    confidence_passed: bool
    is_refusal: bool

    # Step 4: Generate
    draft_answer: str

    # Step 5: Extract Facts
    extracted_facts: List[Dict[str, Any]]

    # Step 6: Verify
    verification_results: List[Dict[str, Any]]
    has_conflicts: bool

    # Step 7: Repair
    repair_count: int
    repair_instruction: str

    # Step 8: Respond
    final_answer: str
    citations: List[Dict[str, Any]]
    disclaimer: str
