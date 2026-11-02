"""
backend/routers/complaints.py
-----------------------------
API routes for complaint creation, retrieval, AI analysis, status progression,
and staff priority overrides with audit logging.
"""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from backend.auth import get_current_user, require_staff
from backend.database import get_db
from backend.models import (
    Complaint,
    ComplaintPrediction,
    ComplaintPriority,
    ComplaintStatus,
    DuplicateSuggestion,
    PriorityOverrideAudit,
    User,
    UserRole,
)
from backend.schemas import (
    CategoryOverrideRequest,
    ComplaintAnalyzeRequest,
    ComplaintAnalyzeResponse,
    ComplaintCreateRequest,
    ComplaintDetailResponse,
    ComplaintListItem,
    ComplaintStatusUpdateRequest,
    DuplicateCandidateResponse,
    PredictionResponse,
    PriorityOverrideRequest,
    PriorityResponse,
    StaffOverrideRecordResponse,
)
from backend.services.ai_service import ai_service
from src.taxonomy import get_category_name, get_department_for_category


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/complaints", tags=["Complaints"])


def _generate_complaint_id() -> str:
    today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    random_hex = secrets.token_hex(2).upper()
    return f"CMP-{today_str}-{random_hex}"


def _format_complaint_detail(complaint: Complaint) -> ComplaintDetailResponse:
    pred_res = None
    if complaint.prediction:
        pred_res = PredictionResponse(
            predicted_category=complaint.prediction.predicted_category,
            category_name=complaint.prediction.category_name,
            confidence=complaint.prediction.confidence,
            low_confidence=complaint.prediction.low_confidence,
            needs_human_review=complaint.prediction.needs_human_review,
            all_scores=complaint.prediction.all_scores,
        )

    prio_res = None
    if complaint.priority:
        prio_res = PriorityResponse(
            score=complaint.priority.score,
            suggested_priority=complaint.priority.suggested_priority,
            final_priority=complaint.priority.final_priority,
            safety_flag=complaint.priority.safety_flag,
            safety_override=complaint.priority.safety_override,
            needs_human_review=complaint.priority.needs_human_review,
            signals=complaint.priority.signals,
            explanation=complaint.priority.explanation or "",
        )

    dup_list = [
        DuplicateCandidateResponse(
            candidate_id=d.candidate_id,
            candidate_text=d.candidate_text,
            similarity_score=d.similarity_score,
            similarity_level=d.similarity_level,
            candidate_category=d.candidate_category,
            candidate_location=d.candidate_location,
        )
        for d in complaint.duplicate_suggestions
    ]

    override_list = [
        StaffOverrideRecordResponse(
            id=o.id,
            complaint_id=o.complaint_id,
            staff_id=o.staff_id,
            staff_username=o.staff_username,
            original_priority=o.original_priority,
            override_priority=o.override_priority,
            reason=o.reason,
            timestamp=o.timestamp,
        )
        for o in sorted(complaint.priority_overrides, key=lambda x: x.timestamp)
    ]

    assigned_dept = None
    if complaint.prediction and complaint.prediction.predicted_category:
        assigned_dept = get_department_for_category(complaint.prediction.predicted_category)

    return ComplaintDetailResponse(
        id=complaint.id,
        user_id=complaint.user_id,
        student_username=complaint.student.username if complaint.student else None,
        complaint_text=complaint.complaint_text,
        location=complaint.location,
        student_dept=complaint.student_dept,
        status=complaint.status,
        created_at=complaint.created_at,
        updated_at=complaint.updated_at,
        assigned_department=assigned_dept,
        prediction=pred_res,
        priority=prio_res,
        duplicate_suggestions=dup_list,
        priority_overrides=override_list,
    )


@router.post("/analyze", response_model=ComplaintAnalyzeResponse)
def analyze_complaint_preview(
    req: ComplaintAnalyzeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Preview AI triage (classification, priority, duplicates) in real-time before submission."""
    triage = ai_service.analyze_full(
        text=req.complaint_text,
        location=req.location,
        recurrence_count=req.recurrence_count,
    )

    pred = PredictionResponse(**triage["prediction"])
    prio = PriorityResponse(**triage["priority"])
    dups = [DuplicateCandidateResponse(**d) for d in triage["duplicate_suggestions"]]

    return ComplaintAnalyzeResponse(
        prediction=pred,
        priority=prio,
        duplicate_suggestions=dups,
    )


@router.post("", response_model=ComplaintDetailResponse, status_code=status.HTTP_201_CREATED)
def submit_complaint(
    req: ComplaintCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Submit an identified student complaint, trigger automated AI triage, and persist records."""
    complaint_id = _generate_complaint_id()
    now_utc = datetime.now(timezone.utc)

    # 1. Run AI Triage
    triage = ai_service.analyze_full(text=req.complaint_text, location=req.location)
    pred_data = triage["prediction"]
    prio_data = triage["priority"]
    dup_data = triage["duplicate_suggestions"]

    # 2. Create Complaint Record
    complaint = Complaint(
        id=complaint_id,
        user_id=current_user.id,
        complaint_text=req.complaint_text,
        location=req.location or "<Unspecified Location>",
        student_dept=req.student_dept or current_user.department,
        status=ComplaintStatus.SUBMITTED.value,
        created_at=now_utc,
        updated_at=now_utc,
    )
    db.add(complaint)
    db.flush()

    # 3. Create Prediction Record
    pred_rec = ComplaintPrediction(
        complaint_id=complaint_id,
        predicted_category=pred_data["predicted_category"],
        category_name=pred_data["category_name"],
        confidence=pred_data["confidence"],
        low_confidence=pred_data["low_confidence"],
        needs_human_review=pred_data["needs_human_review"],
    )
    pred_rec.all_scores = pred_data.get("all_scores", {})
    db.add(pred_rec)

    # 4. Create Priority Record
    prio_rec = ComplaintPriority(
        complaint_id=complaint_id,
        score=prio_data["score"],
        suggested_priority=prio_data["suggested_priority"],
        final_priority=prio_data["final_priority"],
        safety_flag=prio_data["safety_flag"],
        safety_override=prio_data["safety_override"],
        needs_human_review=prio_data["needs_human_review"],
        explanation=prio_data.get("explanation", ""),
    )
    prio_rec.signals = prio_data.get("signals", {})
    db.add(prio_rec)

    # 5. Create Duplicate Suggestion Records
    for d in dup_data:
        dup_rec = DuplicateSuggestion(
            complaint_id=complaint_id,
            candidate_id=d["candidate_id"],
            similarity_score=d["similarity_score"],
            similarity_level=d["similarity_level"],
            candidate_text=d["candidate_text"],
            candidate_category=d.get("candidate_category"),
            candidate_location=d.get("candidate_location"),
        )
        db.add(dup_rec)

    db.commit()
    db.refresh(complaint)

    # 6. Dynamically index new complaint into runtime retriever
    ai_service.index_complaint(
        complaint_id=complaint.id,
        text=complaint.complaint_text,
        category=pred_data["category_name"],
        location=complaint.location,
        created_at=now_utc.isoformat(),
    )

    logger.info("Complaint %s successfully created and triaged for user %s", complaint.id, current_user.username)
    return _format_complaint_detail(complaint)


@router.get("", response_model=list[ComplaintListItem])
def list_complaints(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    status: Annotated[str | None, Query(description="Filter by status")] = None,
    category: Annotated[str | None, Query(description="Filter by category code (C01-C11)")] = None,
    priority: Annotated[str | None, Query(description="Filter by final priority (CRITICAL/HIGH/MEDIUM/LOW)")] = None,
    needs_review: Annotated[bool | None, Query(description="Filter complaints requiring human review")] = None,
    department: Annotated[str | None, Query(description="Filter by assigned department or student department")] = None,
):
    """Retrieve list of complaints with role-based visibility and filters."""
    query = db.query(Complaint).options(
        joinedload(Complaint.student),
        joinedload(Complaint.prediction),
        joinedload(Complaint.priority),
        joinedload(Complaint.duplicate_suggestions),
    )

    # Role enforcement: Students only see their own complaints
    if current_user.role == UserRole.STUDENT.value:
        query = query.filter(Complaint.user_id == current_user.id)

    # Filters
    if status:
        query = query.filter(Complaint.status == status)

    if category:
        query = query.join(Complaint.prediction).filter(ComplaintPrediction.predicted_category == category)

    if priority:
        query = query.join(Complaint.priority).filter(ComplaintPriority.final_priority == priority)

    if needs_review is not None:
        query = query.join(Complaint.priority).filter(ComplaintPriority.needs_human_review == needs_review)

    complaints = query.order_by(Complaint.created_at.desc()).all()

    items = []
    for c in complaints:
        assigned_dept = (
            get_department_for_category(c.prediction.predicted_category)
            if c.prediction and c.prediction.predicted_category
            else None
        )

        # Department filter check if requested
        if department:
            dept_lower = department.lower().strip()
            matches_assigned = assigned_dept and dept_lower in assigned_dept.lower()
            matches_student = c.student_dept and dept_lower in c.student_dept.lower()
            if not (matches_assigned or matches_student):
                continue

        items.append(
            ComplaintListItem(
                id=c.id,
                user_id=c.user_id,
                student_username=c.student.username if c.student else None,
                complaint_text=c.complaint_text,
                location=c.location,
                student_dept=c.student_dept,
                status=c.status,
                created_at=c.created_at,
                updated_at=c.updated_at,
                predicted_category=c.prediction.predicted_category if c.prediction else None,
                category_name=c.prediction.category_name if c.prediction else None,
                assigned_department=assigned_dept,
                confidence=c.prediction.confidence if c.prediction else None,
                final_priority=c.priority.final_priority if c.priority else None,
                safety_flag=c.priority.safety_flag if c.priority else False,
                needs_human_review=(
                    (c.prediction.needs_human_review if c.prediction else False)
                    or (c.priority.needs_human_review if c.priority else False)
                ),
                duplicate_count=len(c.duplicate_suggestions),
            )
        )
    return items


@router.get("/{complaint_id}", response_model=ComplaintDetailResponse)
def get_complaint(
    complaint_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Retrieve complete complaint record including AI explainability and audit trail."""
    complaint = db.query(Complaint).options(
        joinedload(Complaint.student),
        joinedload(Complaint.prediction),
        joinedload(Complaint.priority),
        joinedload(Complaint.duplicate_suggestions),
        joinedload(Complaint.priority_overrides),
    ).filter(Complaint.id == complaint_id).first()

    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint '{complaint_id}' not found.",
        )

    # Permission check: Student can only view own complaint
    if current_user.role == UserRole.STUDENT.value and complaint.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Students can only inspect their own complaints.",
        )

    return _format_complaint_detail(complaint)


@router.patch("/{complaint_id}/status", response_model=ComplaintDetailResponse)
def update_complaint_status(
    complaint_id: str,
    req: ComplaintStatusUpdateRequest,
    current_user: Annotated[User, Depends(require_staff)],
    db: Annotated[Session, Depends(get_db)],
):
    """Update complaint status (staff and admin only)."""
    if current_user.role not in [UserRole.STAFF.value, UserRole.ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied. Staff or Administrator role required, but your role is '{current_user.role}'.",
        )

    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint '{complaint_id}' not found.",
        )

    old_status = complaint.status
    complaint.status = req.status
    complaint.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(complaint)

    logger.info("Staff %s updated status of %s: %s -> %s", current_user.username, complaint.id, old_status, req.status)
    return _format_complaint_detail(complaint)


@router.post("/{complaint_id}/priority-override", response_model=ComplaintDetailResponse)
def override_priority(
    complaint_id: str,
    req: PriorityOverrideRequest,
    current_user: Annotated[User, Depends(require_staff)],
    db: Annotated[Session, Depends(get_db)],
):
    """Override complaint priority with mandatory audit reason (staff and admin only)."""
    if current_user.role not in [UserRole.STAFF.value, UserRole.ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied. Staff or Administrator role required, but your role is '{current_user.role}'.",
        )

    complaint = db.query(Complaint).options(
        joinedload(Complaint.priority),
    ).filter(Complaint.id == complaint_id).first()

    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint '{complaint_id}' not found.",
        )

    if not complaint.priority:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complaint priority record does not exist.",
        )

    original_prio = complaint.priority.final_priority

    # Record audit log
    audit_record = PriorityOverrideAudit(
        complaint_id=complaint.id,
        staff_id=current_user.id,
        staff_username=current_user.username,
        original_priority=original_prio,
        override_priority=req.override_priority,
        reason=req.reason.strip(),
        timestamp=datetime.now(timezone.utc),
    )
    db.add(audit_record)

    # Update active priority
    complaint.priority.final_priority = req.override_priority
    complaint.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(complaint)

    logger.info(
        "Priority override applied on %s by %s: %s -> %s (Reason: %s)",
        complaint.id, current_user.username, original_prio, req.override_priority, req.reason
    )
    return _format_complaint_detail(complaint)


@router.post("/{complaint_id}/category-override", response_model=ComplaintDetailResponse)
def override_category(
    complaint_id: str,
    req: CategoryOverrideRequest,
    current_user: Annotated[User, Depends(require_staff)],
    db: Annotated[Session, Depends(get_db)],
):
    """Override or confirm complaint category (staff and admin only).
    Corrects the predicted category, updates the category name, clears human review flag,
    and updates complaint timestamp.
    """
    if current_user.role not in [UserRole.STAFF.value, UserRole.ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied. Staff or Administrator role required, but your role is '{current_user.role}'.",
        )

    complaint = db.query(Complaint).options(
        joinedload(Complaint.prediction),
        joinedload(Complaint.priority),
        joinedload(Complaint.student),
        joinedload(Complaint.duplicate_suggestions),
        joinedload(Complaint.priority_overrides),
    ).filter(Complaint.id == complaint_id).first()

    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint '{complaint_id}' not found.",
        )

    if not complaint.prediction:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complaint prediction record does not exist.",
        )

    old_cat = complaint.prediction.predicted_category
    new_cat_name = get_category_name(req.override_category)

    complaint.prediction.predicted_category = req.override_category
    complaint.prediction.category_name = new_cat_name
    complaint.prediction.needs_human_review = False
    complaint.prediction.low_confidence = False
    complaint.updated_at = datetime.now(timezone.utc)

    # If priority review flag was due to classification ambiguity, clear it as well
    if complaint.priority and not complaint.priority.safety_override:
        complaint.priority.needs_human_review = False

    db.commit()
    db.refresh(complaint)

    # Re-index complaint in dynamic retriever with corrected category
    ai_service.index_complaint(
        complaint_id=complaint.id,
        text=complaint.complaint_text,
        category=new_cat_name,
        location=complaint.location,
        created_at=complaint.created_at.isoformat() if complaint.created_at else "",
    )

    logger.info(
        "Category override applied on %s by %s: %s -> %s (Reason: %s)",
        complaint.id, current_user.username, old_cat, req.override_category, req.reason
    )
    return _format_complaint_detail(complaint)

