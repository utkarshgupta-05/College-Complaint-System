"""
backend/routers/analytics.py
----------------------------
Analytics and recurring-issue pattern discovery endpoints.
Serves category trends, priority distribution, spatiotemporal hotspots, and
unsupervised topic clusters with statistical sufficiency warnings.
"""

from __future__ import annotations

import logging
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from backend.auth import get_current_user, require_staff
from backend.database import get_db
from backend.models import Complaint, ComplaintPrediction, ComplaintPriority, User, UserRole
from backend.schemas import (
    AnalyticsOverviewResponse,
    CategoryCountItem,
    ClusterSummaryResponse,
    HotspotItem,
    PriorityCountItem,
)
from backend.services.ai_service import CATEGORY_NAMES
from src.clustering.discover import run_kmeans
from src.clustering.frequency import (
    aggregate_by_category,
    aggregate_by_location,
    assess_trend_sufficiency,
    find_hotspots,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview", response_model=AnalyticsOverviewResponse)
def get_analytics_overview(
    current_user: Annotated[User, Depends(require_staff)],
    db: Annotated[Session, Depends(get_db)],
):
    """Retrieve real-time summary statistics, priority breakdown, category distribution, and hotspots.
    Restricted to staff and administrator roles.
    """
    if current_user.role not in [UserRole.STAFF.value, UserRole.ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied. Staff or Administrator role required, but your role is '{current_user.role}'.",
        )

    complaints = db.query(Complaint).options(
        joinedload(Complaint.prediction),
        joinedload(Complaint.priority),
    ).all()

    total = len(complaints)
    if total == 0:
        return AnalyticsOverviewResponse(
            total_complaints=0,
            pending_review_count=0,
            critical_high_count=0,
            resolved_count=0,
            in_progress_count=0,
            category_distribution=[],
            priority_distribution=[],
            hotspots=[],
            trend_warning="No complaints in database yet.",
        )

    # Convert to DataFrame for robust frequency analysis
    rows = []
    for c in complaints:
        rows.append({
            "complaint_id": c.id,
            "complaint_text": c.complaint_text,
            "category": c.prediction.predicted_category if c.prediction else "C11",
            "category_name": c.prediction.category_name if c.prediction else "Other / Unclassified",
            "location": c.location or "<Unspecified Location>",
            "status": c.status,
            "priority": c.priority.final_priority if c.priority else "LOW",
            "needs_review": (
                (c.prediction.needs_human_review if c.prediction else False)
                or (c.priority.needs_human_review if c.priority else False)
            ),
            "created_at": c.created_at.isoformat(),
        })
    df = pd.DataFrame(rows)

    # Counts
    resolved_count = int((df["status"] == "resolved").sum())
    in_progress_count = int((df["status"] == "in_progress").sum())
    pending_review_count = int(df["needs_review"].sum())
    critical_high_count = int(df["priority"].isin(["CRITICAL", "HIGH"]).sum())

    # Category distribution
    cat_agg = aggregate_by_category(df, category_col="category")
    cat_items = []
    for _, r in cat_agg.iterrows():
        code = str(r["category"])
        name = CATEGORY_NAMES.get(code, code)
        cat_items.append(
            CategoryCountItem(
                category=code,
                category_name=name,
                count=int(r["count"]),
                percentage=float(r["percentage"]),
            )
        )

    # Priority distribution
    prio_counts = df["priority"].value_counts()
    prio_items = [
        PriorityCountItem(
            priority=p,
            count=int(prio_counts.get(p, 0)),
            percentage=round(float(prio_counts.get(p, 0) / total * 100.0), 2),
        )
        for p in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    ]

    # Recurring Hotspots
    hotspot_df = find_hotspots(df, min_count=2)
    hotspot_items = []
    for _, h in hotspot_df.head(10).iterrows():
        code = str(h["category"])
        name = CATEGORY_NAMES.get(code, code)
        hotspot_items.append(
            HotspotItem(
                location=str(h["location"]),
                category=code,
                category_name=name,
                count=int(h["count"]),
                percentage=float(h["percentage"]),
            )
        )

    # Trend Sufficiency Report
    trend_report = assess_trend_sufficiency(df)

    return AnalyticsOverviewResponse(
        total_complaints=total,
        pending_review_count=pending_review_count,
        critical_high_count=critical_high_count,
        resolved_count=resolved_count,
        in_progress_count=in_progress_count,
        category_distribution=cat_items,
        priority_distribution=prio_items,
        hotspots=hotspot_items,
        trend_warning=trend_report.warning,
    )


@router.get("/clusters", response_model=list[ClusterSummaryResponse])
def get_recurring_clusters(
    current_user: Annotated[User, Depends(require_staff)],
    db: Annotated[Session, Depends(get_db)],
):
    """Discover recurring complaint themes using unsupervised K-Means clustering.
    Restricted to staff and administrator roles.

    Important Invariants:
    1. Discovered clusters represent lexical themes, NOT confirmed real-world incidents.
    2. Zero synthetic or validation-corpus data is ever disguised as live clusters.
       If live complaints are fewer than 3, returns an empty set indicating insufficient data.
    """
    if current_user.role not in [UserRole.STAFF.value, UserRole.ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied. Staff or Administrator role required, but your role is '{current_user.role}'.",
        )

    complaints = db.query(Complaint).all()
    texts = [c.complaint_text for c in complaints if c.complaint_text and len(c.complaint_text.strip()) >= 10]

    # Honest data state: If fewer than 3 live complaints, do not fabricate clusters
    if len(texts) < 3:
        logger.info(
            "Insufficient live complaints for clustering (found %d, minimum required is 3). Returning empty set.",
            len(texts),
        )
        return []

    # Choose k proportional to data size (between 2 and 8)
    k = max(2, min(8, len(texts) // 3))
    res = run_kmeans(texts, k=k, random_seed=42, min_cluster_size=3)

    out = []
    for c in res.clusters:
        label = f"Theme {c.cluster_id}: {', '.join(c.top_terms[:3])}" if c.top_terms else f"Cluster {c.cluster_id}"
        out.append(
            ClusterSummaryResponse(
                cluster_id=c.cluster_id,
                size=c.size,
                representative_complaints=c.representative_complaints[:3],
                top_terms=c.top_terms[:6],
                is_weakly_supported=c.is_weakly_supported,
                warning=c.warning,
                label=label,
            )
        )
    return out

