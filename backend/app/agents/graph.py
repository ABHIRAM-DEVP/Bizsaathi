"""LangGraph state graph assembling nodes 01 through 13."""

import inspect
import time
from collections.abc import Callable
from typing import Any, Literal

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


class _InstrumentedNode:
    def __init__(
        self,
        name: str,
        node: Callable[[GraphState], Any],
        node_events: list[dict[str, Any]],
    ) -> None:
        self._name = name
        self._node = node
        self._node_events = node_events

    async def __call__(self, state: GraphState) -> dict[str, Any]:
        started = time.perf_counter()
        calls_before = state.get("model_calls", 0)
        try:
            result = self._node(state)
            if inspect.isawaitable(result):
                result = await result
            if not isinstance(result, dict):
                raise TypeError(f"Node {self._name} did not return a state update.")
            calls_after = result.get("model_calls", calls_before)
            calls_made = max(0, calls_after - calls_before) if isinstance(calls_after, int) else 0
        except Exception:
            self._node_events.append(
                {
                    "node": self._name,
                    "event": "error",
                    "duration_ms": int((time.perf_counter() - started) * 1000),
                    "model_calls": 0,
                    "error_code": "node.failed",
                }
            )
            raise

        self._node_events.append(
            {
                "node": self._name,
                "event": "step_finished",
                "duration_ms": int((time.perf_counter() - started) * 1000),
                "model_calls": calls_made,
            }
        )
        return result


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


def build_bizsaathi_graph(node_events: list[dict[str, Any]] | None = None):
    """Build and compile the unified BizSaathi LangGraph state graph."""
    events = node_events if node_events is not None else []
    workflow = StateGraph(GraphState)

    # Add nodes
    nodes: dict[str, Callable[[GraphState], Any]] = {
        "planner": plan_workflow,
        "intake": process_intake,
        "context": gather_context,
        "extract_photo": extract_from_photo,
        "reconcile": reconcile_catalog,
        "create_brief": create_brief,
        "draft_post": draft_post,
        "customer_chat": process_customer_chat,
        "verify_claims": verify_claims,
        "critic": critique_consistency,
        "repair": repair_or_escalate,
        "policy_gate": apply_policy_gate,
    }
    for name, node in nodes.items():
        workflow.add_node(name, _InstrumentedNode(name, node, events))

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
