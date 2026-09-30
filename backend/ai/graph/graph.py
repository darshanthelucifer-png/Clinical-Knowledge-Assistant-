"""
================================================================================
ClinSaarthi AI - LangGraph Multi-Node Verification Agent Workflow
================================================================================
What it does:
    Compiles and executes the state machine connecting all 8 clinical pipeline nodes:
    Understand -> Retrieve -> Confidence Gate -> (Pass -> Generate | Fail -> Respond)
    -> Extract -> Verify -> (Conflict & repairs < 2 -> Repair -> Generate | Else -> Respond)
    -> Respond -> END.

Python Concepts Demonstrated:
    1. Directed Acyclic Graph (DAG) with Controlled Cyclic Self-Correction Loops:
       Demonstrates how agentic loops iteratively repair contradictions before final output.
    2. Decoupled State Machine Architecture: Compatible with LangGraph semantics
       with zero heavy external binary/DLL dependencies.
================================================================================
"""
import logging
from typing import Dict, Any, Callable, Optional, List
from .state import AgentState
from .nodes import (
    understand_node,
    retrieve_node,
    confidence_gate_node,
    generate_node,
    extract_facts_node,
    verify_node,
    repair_node,
    respond_node
)

logger = logging.getLogger(__name__)

END = "__END__"


class StateGraph:
    """
    StateGraph engine implementing node registration, edge traversal,
    and conditional branching with recursion guardrails.
    """
    def __init__(self):
        self.nodes: Dict[str, Callable[[AgentState], Dict[str, Any]]] = {}
        self.edges: Dict[str, str] = {}
        self.conditional_edges: Dict[str, Tuple[Callable[[AgentState], str], Dict[str, str]]] = {}
        self.entry_point: Optional[str] = None

    def add_node(self, name: str, fn: Callable[[AgentState], Dict[str, Any]]):
        self.nodes[name] = fn

    def set_entry_point(self, name: str):
        self.entry_point = name

    def add_edge(self, start: str, end: str):
        self.edges[start] = end

    def add_conditional_edges(
        self,
        start: str,
        condition_fn: Callable[[AgentState], str],
        mapping: Dict[str, str]
    ):
        self.conditional_edges[start] = (condition_fn, mapping)

    def compile(self) -> 'CompiledStateGraph':
        return CompiledStateGraph(self)


class CompiledStateGraph:
    """
    Executable compiled agent graph.
    """
    def __init__(self, graph: StateGraph, max_iterations: int = 15):
        self.graph = graph
        self.max_iterations = max_iterations

    def invoke(self, initial_state: AgentState) -> AgentState:
        """
        Executes the state machine synchronously until reaching END or max_iterations.
        """
        state: AgentState = dict(initial_state)  # type: ignore
        current_node = self.graph.entry_point
        iteration = 0

        while current_node and current_node != END and iteration < self.max_iterations:
            iteration += 1
            node_fn = self.graph.nodes.get(current_node)
            if not node_fn:
                logger.warning("Node '%s' not registered. Halting graph.", current_node)
                break

            logger.debug("[Graph Agent] Running node: %s (iter %d)", current_node, iteration)
            updates = node_fn(state)
            if updates and isinstance(updates, dict):
                state.update(updates)

            # Determine next node
            if current_node in self.graph.conditional_edges:
                condition_fn, mapping = self.graph.conditional_edges[current_node]
                decision_key = condition_fn(state)
                next_node = mapping.get(decision_key, END)
            elif current_node in self.graph.edges:
                next_node = self.graph.edges[current_node]
            else:
                next_node = END

            current_node = next_node

        return state


def route_confidence_gate(state: AgentState) -> str:
    """Routes to 'refuse' if confidence gate failed; otherwise 'generate'."""
    if state.get("is_refusal", False) or not state.get("confidence_passed", False):
        return "refuse"
    return "pass"


def route_verification(state: AgentState) -> str:
    """Routes to 'repair' if conflicts exist and repair_count < 2; otherwise 'respond'."""
    has_conflicts = state.get("has_conflicts", False)
    repair_count = state.get("repair_count", 0)

    if has_conflicts and repair_count < 2:
        return "repair"
    return "respond"


def build_graph() -> CompiledStateGraph:
    """
    Assembles the 8-node LangGraph verification pipeline:
    1. understand -> 2. retrieve -> 3. gate ->
       - (refuse) -> 8. respond -> END
       - (pass) -> 4. generate -> 5. extract -> 6. verify ->
         - (repair) -> 7. repair -> 4. generate (self-correction loop!)
         - (respond) -> 8. respond -> END
    """
    workflow = StateGraph()

    # Register all 8 nodes
    workflow.add_node("understand", understand_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("gate", confidence_gate_node)
    workflow.add_node("generate", generate_node)
    workflow.add_node("extract", extract_facts_node)
    workflow.add_node("verify", verify_node)
    workflow.add_node("repair", repair_node)
    workflow.add_node("respond", respond_node)

    # Set Entry Point
    workflow.set_entry_point("understand")

    # Add Linear Transitions
    workflow.add_edge("understand", "retrieve")
    workflow.add_edge("retrieve", "gate")

    # Conditional Branch: Gate
    workflow.add_conditional_edges(
        "gate",
        route_confidence_gate,
        {
            "pass": "generate",
            "refuse": "respond"
        }
    )

    # Linear Transitions after Generation
    workflow.add_edge("generate", "extract")
    workflow.add_edge("extract", "verify")

    # Conditional Branch: Verify (Self-Correction Loop)
    workflow.add_conditional_edges(
        "verify",
        route_verification,
        {
            "repair": "repair",
            "respond": "respond"
        }
    )

    # Loop back from repair to generate
    workflow.add_edge("repair", "generate")

    # Final transition
    workflow.add_edge("respond", END)

    return workflow.compile()
