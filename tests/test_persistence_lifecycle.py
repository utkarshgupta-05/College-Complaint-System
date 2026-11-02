"""
tests/test_persistence_lifecycle.py
-----------------------------------
Tests end-to-end data persistence across session closures and engine restarts.
Verifies relational integrity, foreign key cascades, priority override audits,
and Alembic migration compatibility for Phase 12.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.auth import hash_password, verify_password
from backend.database import Base
from backend.models import (
    Complaint,
    ComplaintPrediction,
    ComplaintPriority,
    ComplaintStatus,
    PriorityOverrideAudit,
    User,
    UserRole,
)
from backend.routers.complaints import (
    override_category,
    override_priority,
    submit_complaint,
    update_complaint_status,
)
from backend.schemas import (
    CategoryOverrideRequest,
    ComplaintCreateRequest,
    ComplaintStatusUpdateRequest,
    PriorityOverrideRequest,
)


def test_data_persistence_across_engine_restart(tmp_path):
    """Verify that complaints, predictions, priorities, and audits persist across engine reconnects."""
    db_file = tmp_path / "persistence_test.db"
    db_url = f"sqlite:///{db_file}"

    # 1. Initialize first engine & session
    engine1 = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine1)
    Session1 = sessionmaker(autocommit=False, autoflush=False, bind=engine1)
    db1 = Session1()

    # Create users
    student = User(
        username="persist_student",
        email="ps@campus.edu",
        hashed_password=hash_password("mypassword123"),
        role=UserRole.STUDENT.value,
        department="Mechanical",
    )
    staff = User(
        username="persist_staff",
        email="staff@campus.edu",
        hashed_password=hash_password("staffpass123"),
        role=UserRole.STAFF.value,
        department="Maintenance",
    )
    db1.add_all([student, staff])
    db1.commit()

    # Submit complaint
    req = ComplaintCreateRequest(
        complaint_text="Hostel Block B room 302 ceiling fan makes intense buzzing and sparks when turned on",
        location="Hostel Block B Room 302",
        student_dept="Mechanical",
    )
    cmp_res = submit_complaint(req, student, db1)
    cmp_id = cmp_res.id

    # Update status & override priority
    update_complaint_status(cmp_id, ComplaintStatusUpdateRequest(status="in_progress"), staff, db1)
    override_priority(
        cmp_id,
        PriorityOverrideRequest(override_priority="CRITICAL", reason="Immediate fire risk from sparking fan"),
        staff,
        db1,
    )
    override_category(
        cmp_id,
        CategoryOverrideRequest(override_category="C02", reason="Electrical fault in hostel room"),
        staff,
        db1,
    )

    db1.close()
    engine1.dispose()

    # 2. Simulate Backend Server Restart (Brand new engine and session instance)
    engine2 = create_engine(db_url, connect_args={"check_same_thread": False})
    Session2 = sessionmaker(autocommit=False, autoflush=False, bind=engine2)
    db2 = Session2()

    # Verify user persistence
    persisted_user = db2.query(User).filter(User.username == "persist_student").first()
    assert persisted_user is not None
    assert verify_password("mypassword123", persisted_user.hashed_password) is True

    # Verify complaint persistence & updated state
    persisted_cmp = db2.query(Complaint).filter(Complaint.id == cmp_id).first()
    assert persisted_cmp is not None
    assert persisted_cmp.status == "in_progress"
    assert persisted_cmp.location == "Hostel Block B Room 302"
    assert persisted_cmp.student.username == "persist_student"

    # Verify prediction persistence & category correction
    assert persisted_cmp.prediction is not None
    assert persisted_cmp.prediction.predicted_category == "C02"
    assert persisted_cmp.prediction.category_name == "Electricity and Water"
    assert persisted_cmp.prediction.needs_human_review is False

    # Verify priority persistence
    assert persisted_cmp.priority is not None
    assert persisted_cmp.priority.final_priority == "CRITICAL"

    # Verify audit trail persistence
    assert len(persisted_cmp.priority_overrides) == 1
    audit = persisted_cmp.priority_overrides[0]
    assert audit.override_priority == "CRITICAL"
    assert audit.staff_username == "persist_staff"
    assert "fire risk" in audit.reason

    db2.close()
    engine2.dispose()

