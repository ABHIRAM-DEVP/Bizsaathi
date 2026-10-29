"""Dashboard response schemas."""
from pydantic import BaseModel, Field
from typing import Optional


class NextStep(BaseModel):
    """Suggested next action for the seller."""
    label: str = Field(..., description="Human-readable action label")
    route: str = Field(..., description="Frontend route path")


class DashboardResponse(BaseModel):
    """Dashboard aggregated metrics (EP-I01)."""
    pending_approvals: int = Field(..., description="Count of pending approval items")
    open_escalations: int = Field(..., description="Count of escalated conversations")
    recent_jobs: list[dict] = Field(default_factory=list, description="Recent background jobs")
    low_stock: list[dict] = Field(default_factory=list, description="Products with low stock")
    next_step: Optional[NextStep] = Field(None, description="Suggested next action")
    
    model_config = {"from_attributes": True}
