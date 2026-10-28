"""Node 01: Planner (deterministic router).

Inspects the job kind and prepares the structured task plan.
"""

from typing import Any

from app.agents.models import TaskPlan
from app.agents.state import GraphState


def plan_workflow(state: GraphState) -> dict[str, Any]:
    """Determine steps and assigned nodes based on input bundle."""
    input_bundle = state["input_bundle"]
    kind = input_bundle.kind

    if kind == "product_from_photo":
        plan = TaskPlan(
            goal="Extract product draft from photos with uncertainty flags and conflict detection",
            steps=["validate_intake", "gather_context", "extract_photo_features", "reconcile_catalog"],
            assigned_nodes=[
                "node_01_planner",
                "node_02_intake",
                "node_03_context",
                "node_04_extractor",
                "node_06_reconciler",
            ],
        )
    elif kind == "product_from_voice":
        plan = TaskPlan(
            goal="Transcribe voice recording and extract product attributes",
            steps=["validate_intake", "gather_context", "transcribe_and_extract", "reconcile_catalog"],
            assigned_nodes=[
                "node_01_planner",
                "node_02_intake",
                "node_03_context",
                "node_05_voice",
                "node_06_reconciler",
            ],
        )
    elif kind == "post_generate":
        plan = TaskPlan(
            goal="Generate channel-specific post draft with explicit evidence claims",
            steps=["validate_intake", "gather_context", "create_brief", "draft_post_with_claims"],
            assigned_nodes=["node_01_planner", "node_02_intake", "node_03_context", "node_07_brief", "node_08_draft"],
        )
    else:
        plan = TaskPlan(
            goal=f"Process generic workflow {kind}",
            steps=["validate_intake", "gather_context"],
            assigned_nodes=["node_01_planner", "node_02_intake", "node_03_context"],
        )

    return {
        "task_plan": plan,
        "status": "running",
    }
