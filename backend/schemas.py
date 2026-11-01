"""
backend/schemas.py
------------------
Pydantic V2 schemas for request validation and response serialization.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


# =========================================================================
# Auth & User Schemas
# =========================================================================

class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(..., min_length=6, max_length=100)
    full_name: str | None = None
    role: str = Field(default="student", pattern="^(student|staff|admin)$")
    department: str | None = None


class UserLoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    full_name: str | None = None
    role: str
    department: str | None = None
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# =========================================================================
# AI Analysis & Prediction Schemas
# =========================================================================

class PredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    predicted_category: str
    category_name: str
    confidence: float
    low_confidence: bool
    needs_human_review: bool
    all_scores: dict[str, float] = Field(default_factory=dict)


class PriorityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    score: float
    suggested_priority: str
    final_priority: str
    safety_flag: bool
    safety_override: bool
    needs_human_review: bool
    signals: dict[str, float] = Field(default_factory=dict)
    explanation: str = ""


class DuplicateCandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    candidate_id: str
    candidate_text: str
    similarity_score: float
    similarity_level: str
    candidate_category: str | None = None
    candidate_location: str | None = None


class StaffOverrideRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    complaint_id: str
    staff_id: int
    staff_username: str
    original_priority: str
    override_priority: str
    reason: str
    timestamp: datetime


# =========================================================================
# Complaint Schemas
# =========================================================================

class ComplaintAnalyzeRequest(BaseModel):
    """Request to preview AI triage without saving."""
    complaint_text: str = Field(..., min_length=5, max_length=4000)
    location: str | None = None
    recurrence_count: int = 0


class ComplaintAnalyzeResponse(BaseModel):
    """Real-time preview of AI triage outputs."""
    prediction: PredictionResponse
    priority: PriorityResponse
    duplicate_suggestions: list[DuplicateCandidateResponse] = Field(default_factory=list)


class ComplaintCreateRequest(BaseModel):
    complaint_text: str = Field(..., min_length=10, max_length=4000)
    location: str | None = None
    student_dept: str | None = None


class ComplaintListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: int
    student_username: str | None = None
    complaint_text: str
    location: str | None = None
    student_dept: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime
    predicted_category: str | None = None
    category_name: str | None = None
    confidence: float | None = None
    final_priority: str | None = None
    safety_flag: bool = False
    needs_human_review: bool = False
    duplicate_count: int = 0


class ComplaintDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: int
    student_username: str | None = None
    complaint_text: str
    location: str | None = None
    student_dept: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    prediction: PredictionResponse | None = None
    priority: PriorityResponse | None = None
    duplicate_suggestions: list[DuplicateCandidateResponse] = Field(default_factory=list)
    priority_overrides: list[StaffOverrideRecordResponse] = Field(default_factory=list)


class ComplaintStatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(submitted|in_progress|resolved|rejected)$")


class PriorityOverrideRequest(BaseModel):
    override_priority: str = Field(..., pattern="^(CRITICAL|HIGH|MEDIUM|LOW)$")
    reason: str = Field(..., min_length=5, max_length=500)


# =========================================================================
# Analytics Schemas
# =========================================================================

class HotspotItem(BaseModel):
    location: str
    category: str
    category_name: str | None = None
    count: int
    percentage: float


class CategoryCountItem(BaseModel):
    category: str
    category_name: str
    count: int
    percentage: float


class PriorityCountItem(BaseModel):
    priority: str
    count: int
    percentage: float


class ClusterSummaryResponse(BaseModel):
    cluster_id: int
    size: int
    representative_complaints: list[str]
    top_terms: list[str]
    is_weakly_supported: bool
    warning: str | None = None
    label: str


class AnalyticsOverviewResponse(BaseModel):
    total_complaints: int
    pending_review_count: int
    critical_high_count: int
    resolved_count: int
    in_progress_count: int
    category_distribution: list[CategoryCountItem]
    priority_distribution: list[PriorityCountItem]
    hotspots: list[HotspotItem]
    trend_warning: str | None = None
