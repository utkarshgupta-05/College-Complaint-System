"""
backend/models.py
-----------------
SQLAlchemy ORM models for complaint management, AI predictions, priority assessment,
duplicate suggestions, and staff override auditing.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from backend.database import Base


class UserRole(str, Enum):
    STUDENT = "student"
    STAFF = "staff"
    ADMIN = "admin"


class ComplaintStatus(str, Enum):
    SUBMITTED = "submitted"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    email = Column(String(128), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    full_name = Column(String(128), nullable=True)
    role = Column(String(32), default=UserRole.STUDENT.value, nullable=False)
    department = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    complaints = relationship("Complaint", back_populates="student", cascade="all, delete-orphan")


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    complaint_text = Column(Text, nullable=False)
    location = Column(String(128), nullable=True, default="<Unspecified Location>")
    student_dept = Column(String(64), nullable=True)
    status = Column(String(32), default=ComplaintStatus.SUBMITTED.value, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    student = relationship("User", back_populates="complaints")
    prediction = relationship("ComplaintPrediction", back_populates="complaint", uselist=False, cascade="all, delete-orphan")
    priority = relationship("ComplaintPriority", back_populates="complaint", uselist=False, cascade="all, delete-orphan")
    duplicate_suggestions = relationship("DuplicateSuggestion", back_populates="complaint", cascade="all, delete-orphan")
    priority_overrides = relationship("PriorityOverrideAudit", back_populates="complaint", cascade="all, delete-orphan")


class ComplaintPrediction(Base):
    __tablename__ = "complaint_predictions"

    complaint_id = Column(String(64), ForeignKey("complaints.id"), primary_key=True)
    predicted_category = Column(String(16), nullable=False)
    category_name = Column(String(64), nullable=False)
    confidence = Column(Float, nullable=False)
    low_confidence = Column(Boolean, default=False, nullable=False)
    needs_human_review = Column(Boolean, default=False, nullable=False)
    all_scores_json = Column(Text, nullable=True)

    complaint = relationship("Complaint", back_populates="prediction")

    @property
    def all_scores(self) -> dict[str, float]:
        if not self.all_scores_json:
            return {}
        try:
            return json.loads(self.all_scores_json)
        except Exception:
            return {}

    @all_scores.setter
    def all_scores(self, scores: dict[str, float]) -> None:
        self.all_scores_json = json.dumps(scores)


class ComplaintPriority(Base):
    __tablename__ = "complaint_priorities"

    complaint_id = Column(String(64), ForeignKey("complaints.id"), primary_key=True)
    score = Column(Float, nullable=False)  # 0.0 - 100.0
    suggested_priority = Column(String(32), nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    final_priority = Column(String(32), nullable=False)
    safety_flag = Column(Boolean, default=False, nullable=False)
    safety_override = Column(Boolean, default=False, nullable=False)
    needs_human_review = Column(Boolean, default=False, nullable=False)
    signals_json = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)

    complaint = relationship("Complaint", back_populates="priority")

    @property
    def signals(self) -> dict[str, float]:
        if not self.signals_json:
            return {}
        try:
            return json.loads(self.signals_json)
        except Exception:
            return {}

    @signals.setter
    def signals(self, sigs: dict[str, float]) -> None:
        self.signals_json = json.dumps(sigs)


class DuplicateSuggestion(Base):
    __tablename__ = "duplicate_suggestions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    complaint_id = Column(String(64), ForeignKey("complaints.id"), nullable=False, index=True)
    candidate_id = Column(String(64), nullable=False)
    similarity_score = Column(Float, nullable=False)
    similarity_level = Column(String(32), nullable=False)
    candidate_text = Column(Text, nullable=False)
    candidate_category = Column(String(64), nullable=True)
    candidate_location = Column(String(128), nullable=True)

    complaint = relationship("Complaint", back_populates="duplicate_suggestions")


class PriorityOverrideAudit(Base):
    __tablename__ = "priority_override_audits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    complaint_id = Column(String(64), ForeignKey("complaints.id"), nullable=False, index=True)
    staff_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    staff_username = Column(String(64), nullable=False)
    original_priority = Column(String(32), nullable=False)
    override_priority = Column(String(32), nullable=False)
    reason = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    complaint = relationship("Complaint", back_populates="priority_overrides")

