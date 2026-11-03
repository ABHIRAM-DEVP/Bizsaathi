"""Tenant-scoped dashboard aggregates backed by confirmed database records."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.domain import Approval, Conversation, Job, Product, ProductVariant
from app.schemas.dashboard import DashboardResponse, NextStep


def get_dashboard_summary(db: Session, *, business_id: UUID) -> DashboardResponse:
    pending_approvals = (
        db.scalar(
            select(func.count(Approval.id)).where(
                Approval.business_id == business_id,
                Approval.status == "pending",
            )
        )
        or 0
    )
    open_escalations = (
        db.scalar(
            select(func.count(Conversation.id)).where(
                Conversation.business_id == business_id,
                Conversation.status == "escalated",
            )
        )
        or 0
    )

    low_stock_rows = db.execute(
        select(Product, func.coalesce(func.sum(ProductVariant.stock), 0).label("stock_total"))
        .join(
            ProductVariant,
            (ProductVariant.product_id == Product.id) & (ProductVariant.business_id == Product.business_id),
        )
        .where(Product.business_id == business_id, Product.status == "active")
        .group_by(Product.id)
        .having(func.coalesce(func.sum(ProductVariant.stock), 0) < settings.LOW_STOCK_THRESHOLD)
        .order_by(func.sum(ProductVariant.stock), Product.name)
        .limit(10)
    ).all()
    low_stock = [
        {
            "id": product.id,
            "sku": product.sku,
            "name": product.name,
            "price_inr": product.price_inr,
            "status": product.status,
            "stock_total": int(stock_total),
            "thumbnail_url": None,
        }
        for product, stock_total in low_stock_rows
    ]

    jobs = (
        db.execute(select(Job).where(Job.business_id == business_id).order_by(Job.created_at.desc()).limit(10))
        .scalars()
        .all()
    )
    recent_jobs = [
        {
            "id": job.id,
            "business_id": job.business_id,
            "kind": job.kind,
            "status": job.status,
            "progress_step": job.progress_step,
            "progress_total": job.progress_total,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "finished_at": job.finished_at,
        }
        for job in jobs
    ]

    next_step = None
    if pending_approvals:
        next_step = NextStep(label="Review pending approvals", route="/approvals")
    elif low_stock:
        next_step = NextStep(label="Review low-stock products", route="/products")

    return DashboardResponse(
        pending_approvals=pending_approvals,
        open_escalations=open_escalations,
        recent_jobs=recent_jobs,
        low_stock=low_stock,
        next_step=next_step,
    )
