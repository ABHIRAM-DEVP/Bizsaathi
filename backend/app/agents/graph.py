"""LangGraph state graph assembling nodes 01 through 08."""

from typing import Literal

from langgraph.graph import END, StateGraph

from app.agents.nodes.node_01_planner import plan_workflow
from app.agents.nodes.node_02_intake import process_intake
from app.agents.nodes.node_03_context import gather_context
from app.agents.nodes.node_04_extractor import extract_from_photo
from app.agents.nodes.node_05_voice import process_voice
from app.agents.nodes.node_06_reconciler import reconcile_catalog
from app.agents.nodes.node_07_brief import create_brief
from app.agents.nodes.node_08_draft import draft_post
from app.agents.state import GraphState


def route_by_kind(state: GraphState) -> Literal["extract_photo", "process_voice", "create_brief", "end_failed"]:
    """Conditional routing based on workflow kind and intake validation."""
    if state.get("status") == "failed" or state.get("status") == "blocked":
        return "end_failed"

    kind = state["input_bundle"].kind
    if kind == "product_from_photo":
        return "extract_photo"
    elif kind == "product_from_voice":
        return "process_voice"
    elif kind == "post_generate":
        return "create_brief"
    return "end_failed"


def check_extract_outcome(state: GraphState) -> Literal["reconcile", "end"]:
    """Stop graph execution if extraction failed or was blocked."""
    if state.get("status") in ("blocked", "failed"):
        return "end"
    return "reconcile"


def build_bizsaathi_graph():
    """Build and compile the unified BizSaathi LangGraph state graph."""
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("planner", plan_workflow)
    workflow.add_node("intake", process_intake)
    workflow.add_node("context", gather_context)
    workflow.add_node("extract_photo", extract_from_photo)
    workflow.add_node("process_voice", process_voice)
    workflow.add_node("reconcile", reconcile_catalog)
    workflow.add_node("create_brief", create_brief)
    workflow.add_node("draft_post", draft_post)

    # Fixed base pipeline
    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "intake")
    workflow.add_edge("intake", "context")

    # Conditional dispatch
    workflow.add_conditional_edges(
        "context",
        route_by_kind,
        {
            "extract_photo": "extract_photo",
            "process_voice": "process_voice",
            "create_brief": "create_brief",
            "end_failed": END,
        },
    )

    # Sub-workflow connections with failure guards
    workflow.add_conditional_edges(
        "extract_photo",
        check_extract_outcome,
        {"reconcile": "reconcile", "end": END},
    )
    workflow.add_conditional_edges(
        "process_voice",
        check_extract_outcome,
        {"reconcile": "reconcile", "end": END},
    )
    workflow.add_edge("reconcile", END)

    workflow.add_edge("create_brief", "draft_post")
    workflow.add_edge("draft_post", END)

    return workflow.compile()
