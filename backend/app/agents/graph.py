"""LangGraph state graph assembling nodes 01 through 13."""

from typing import Literal

from langgraph.graph import END, StateGraph

from app.agents.nodes.node_01_planner import plan_workflow
from app.agents.nodes.node_02_intake import process_intake
from app.agents.nodes.node_03_context import gather_context
from app.agents.nodes.node_04_extractor import extract_from_photo
from app.agents.nodes.node_06_reconciler import reconcile_catalog
from app.agents.nodes.node_07_brief import create_brief
from app.agents.nodes.node_08_draft import draft_post
from app.agents.nodes.node_09_customer import process_customer_chat
from app.agents.nodes.node_10_verifier import verify_claims
from app.agents.nodes.node_11_critic import critique_consistency
from app.agents.nodes.node_12_repair import repair_or_escalate
from app.agents.nodes.node_13_policy import apply_policy_gate
from app.agents.state import GraphState


def route_by_kind(
    state: GraphState,
) -> Literal["extract_photo", "create_brief", "customer_chat", "end_failed"]:
    """Conditional routing based on workflow kind and intake validation."""
    if state.get("status") == "failed" or state.get("status") == "blocked":
        return "end_failed"

    kind = state["input_bundle"].kind
    if kind == "product_from_photo":
        return "extract_photo"
    elif kind == "post_generate":
        return "create_brief"
    elif kind == "customer_reply":
        return "customer_chat"
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
    workflow.add_node("reconcile", reconcile_catalog)
    workflow.add_node("create_brief", create_brief)
    workflow.add_node("draft_post", draft_post)
    workflow.add_node("customer_chat", process_customer_chat)
    workflow.add_node("verify_claims", verify_claims)
    workflow.add_node("critic", critique_consistency)
    workflow.add_node("repair", repair_or_escalate)
    workflow.add_node("policy_gate", apply_policy_gate)

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
            "create_brief": "create_brief",
            "customer_chat": "customer_chat",
            "end_failed": END,
        },
    )

    # Sub-workflow connections with failure guards
    workflow.add_conditional_edges(
        "extract_photo",
        check_extract_outcome,
        {"reconcile": "reconcile", "end": END},
    )
    workflow.add_edge("reconcile", END)

    # Customer chat workflow - simple response generation
    workflow.add_edge("customer_chat", END)

    # Post generation workflow
    workflow.add_edge("create_brief", "draft_post")
    workflow.add_edge("draft_post", "verify_claims")
    workflow.add_edge("verify_claims", "critic")
    workflow.add_edge("critic", "policy_gate")
    workflow.add_edge("policy_gate", END)

    return workflow.compile()
