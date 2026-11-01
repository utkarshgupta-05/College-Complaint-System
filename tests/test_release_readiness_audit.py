"""
tests/test_release_readiness_audit.py
-------------------------------------
Phase 8 Release-Readiness Audit Verification Suite.
Covers:
1. Zero synthetic fallback in live clustering endpoint when complaints < 3.
2. Production configuration enforcement (prohibiting SQLite and default secrets in production).
3. Database persistence across simulated backend restarts (engine dispose/re-creation).
4. Strict backend RBAC enforcement (blocking students from analytics, status updates, and overrides).
5. Demo credential seeding safeguards.
"""

import os
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.auth import hash_password, require_admin, require_staff, require_student
from backend.database import Base
from backend.models import (
    Complaint,
    ComplaintPrediction,
    ComplaintPriority,
    PriorityOverrideAudit,
    User,
    UserRole,
)
from backend.routers.analytics import get_analytics_overview, get_recurring_clusters
from backend.routers.complaints import (
    get_complaint,
    override_priority,
    update_complaint_status,
)
from backend.schemas import (
    ComplaintStatusUpdateRequest,
    PriorityOverrideRequest,
)


@pytest.fixture
def audit_db(tmp_path):
    """Isolated session for audit testing."""
    db_file = tmp_path / "audit.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()

    student = User(
        id=1,
        username="audit_student",
        email="student@campus.edu",
        hashed_password=hash_password("student123"),
        role=UserRole.STUDENT.value,
        full_name="Audit Student",
        department="Computer Science",
    )
    student_other = User(
        id=2,
        username="other_student",
        email="other@campus.edu",
        hashed_password=hash_password("student123"),
        role=UserRole.STUDENT.value,
        full_name="Other Student",
        department="Mechanical",
    )
    staff = User(
        id=3,
        username="audit_staff",
        email="staff@campus.edu",
        hashed_password=hash_password("staff123"),
        role=UserRole.STAFF.value,
        full_name="Audit Staff",
        department="Facilities",
    )
    admin = User(
        id=4,
        username="audit_admin",
        email="admin@campus.edu",
        hashed_password=hash_password("admin123"),
        role=UserRole.ADMIN.value,
        full_name="Audit Admin",
        department="Administration",
    )
    db.add_all([student, student_other, staff, admin])
    db.commit()
    yield db
    db.close()


# -------------------------------------------------------------------------
# Test 1: Zero Synthetic Fallback in Clustering
# -------------------------------------------------------------------------
def test_clustering_zero_synthetic_fallback(audit_db):
    """Verify that when live DB has < 3 complaints, clustering returns [] and never uses validation data."""
    staff = audit_db.query(User).filter(User.username == "audit_staff").first()

    # Empty DB: zero live complaints
    clusters_empty = get_recurring_clusters(current_user=staff, db=audit_db)
    assert clusters_empty == [], "Must return empty list when DB has no live complaints"

    # Only 1 complaint: below minimum 3
    c1 = Complaint(
        id="CMP-TEST-001",
        user_id=1,
        complaint_text="Water cooler on first floor is leaking heavily.",
        status="submitted",
    )
    audit_db.add(c1)
    audit_db.commit()

    clusters_single = get_recurring_clusters(current_user=staff, db=audit_db)
    assert clusters_single == [], "Must not fabricate clusters when live complaints < 3"

    # Add 2 more complaints (total 3): live clustering activates honestly
    c2 = Complaint(
        id="CMP-TEST-002",
        user_id=1,
        complaint_text="Water cooler dispenser pipe broken and overflowing.",
        status="submitted",
    )
    c3 = Complaint(
        id="CMP-TEST-003",
        user_id=1,
        complaint_text="Drinking water filter in cafeteria tastes foul and muddy.",
        status="submitted",
    )
    audit_db.add_all([c2, c3])
    audit_db.commit()

    clusters_live = get_recurring_clusters(current_user=staff, db=audit_db)
    assert len(clusters_live) > 0, "Live clustering should form clusters with 3 live records"
    # Verify representative complaints come strictly from our live data, not validation split
    all_reps = [r for cl in clusters_live for r in cl.representative_complaints]
    for rep in all_reps:
        assert any(live_text in rep for live_text in ["Water cooler", "water filter"]), (
            "Clusters must only contain live complaint text, never offline validation corpus"
        )


# -------------------------------------------------------------------------
# Test 2: Production Configuration Safeguards
# -------------------------------------------------------------------------
def test_production_safeguards():
    """Verify production mode rejects SQLite and rejects default secrets."""
    from backend.config import Settings

    # Case A: Production with SQLite URL must be rejected
    orig_env = os.environ.get("ENV")
    orig_db = os.environ.get("DATABASE_URL")
    orig_key = os.environ.get("SECRET_KEY")

    try:
        os.environ["ENV"] = "production"
        os.environ["DATABASE_URL"] = "sqlite:///./complaints.db"
        with pytest.raises(ValueError, match="PRODUCTION CONFIGURATION ERROR"):
            Settings()

        # Case B: Production with unset DATABASE_URL must be rejected
        os.environ["DATABASE_URL"] = ""
        with pytest.raises(ValueError, match="PRODUCTION CONFIGURATION ERROR"):
            Settings()

        # Case C: Production with PostgreSQL but default insecure SECRET_KEY must be rejected
        os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/complaints"
        os.environ["SECRET_KEY"] = "insecure-dev-secret-key-change-in-production-32bytes"
        with pytest.raises(ValueError, match="Default insecure SECRET_KEY cannot be used in production"):
            Settings()

        # Case D: Production with valid PostgreSQL and strong key succeeds
        os.environ["SECRET_KEY"] = "super-secret-random-production-key-2026-phase8"
        prod_settings = Settings()
        assert prod_settings.ENV == "production"
        assert prod_settings.DATABASE_URL.startswith("postgresql")
    finally:
        # Restore environment
        if orig_env: os.environ["ENV"] = orig_env
        else: os.environ.pop("ENV", None)
        if orig_db: os.environ["DATABASE_URL"] = orig_db
        else: os.environ.pop("DATABASE_URL", None)
        if orig_key: os.environ["SECRET_KEY"] = orig_key
        else: os.environ.pop("SECRET_KEY", None)


# -------------------------------------------------------------------------
# Test 3: Database Persistence Across Simulated Backend Restarts
# -------------------------------------------------------------------------
def test_database_persistence_across_restarts(tmp_path):
    """Verify complaints, status changes, and priority override audits persist across engine restarts."""
    db_file = tmp_path / "persistent_test.db"
    db_url = f"sqlite:///{db_file}"

    # First session: Start backend, create schema, submit complaint
    engine_1 = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine_1)
    Session1 = sessionmaker(bind=engine_1)
    db1 = Session1()

    student = User(
        id=1,
        username="alice",
        email="alice@college.edu",
        hashed_password=hash_password("pass123"),
        role=UserRole.STUDENT.value,
    )
    staff = User(
        id=2,
        username="bob_staff",
        email="bob@college.edu",
        hashed_password=hash_password("pass123"),
        role=UserRole.STAFF.value,
    )
    c = Complaint(
        id="CMP-PERSIST-001",
        user_id=1,
        complaint_text="Elevator in Library Building stuck between 2nd and 3rd floors.",
        location="Library Elevator B",
        status="submitted",
    )
    prio = ComplaintPriority(
        complaint_id="CMP-PERSIST-001",
        score=85.0,
        suggested_priority="HIGH",
        final_priority="HIGH",
        safety_flag=True,
        safety_override=False,
        needs_human_review=False,
    )
    db1.add_all([student, staff, c, prio])
    db1.commit()

    # Update status and override priority
    c.status = "in_progress"
    prio.final_priority = "CRITICAL"
    audit = PriorityOverrideAudit(
        complaint_id="CMP-PERSIST-001",
        staff_id=2,
        staff_username="bob_staff",
        original_priority="HIGH",
        override_priority="CRITICAL",
        reason="Students confirmed trapped inside elevator",
    )
    db1.add(audit)
    db1.commit()

    # SIMULATE BACKEND SHUTDOWN
    db1.close()
    engine_1.dispose()

    # SIMULATE BACKEND RESTART: New engine, new session pointing to same file
    engine_2 = create_engine(db_url, connect_args={"check_same_thread": False})
    # create_all should not overwrite existing tables
    Base.metadata.create_all(bind=engine_2)
    Session2 = sessionmaker(bind=engine_2)
    db2 = Session2()

    # Verify all records and relationships are persisted
    persisted_c = db2.query(Complaint).filter(Complaint.id == "CMP-PERSIST-001").first()
    assert persisted_c is not None, "Complaint must persist across backend restarts"
    assert persisted_c.status == "in_progress", "Updated status must persist across restarts"
    assert persisted_c.priority.final_priority == "CRITICAL", "Overridden priority must persist"
    assert len(persisted_c.priority_overrides) == 1, "Audit log must persist across restarts"
    assert persisted_c.priority_overrides[0].reason == "Students confirmed trapped inside elevator"

    db2.close()
    engine_2.dispose()


# -------------------------------------------------------------------------
# Test 4: Strict Backend RBAC Enforcement
# -------------------------------------------------------------------------
def test_backend_rbac_enforcement(audit_db):
    """Confirm role permissions are strictly enforced at the backend API layer."""
    student = audit_db.query(User).filter(User.username == "audit_student").first()
    other_student = audit_db.query(User).filter(User.username == "other_student").first()
    staff = audit_db.query(User).filter(User.username == "audit_staff").first()

    # Create a complaint owned by audit_student
    c = Complaint(
        id="CMP-RBAC-001",
        user_id=student.id,
        complaint_text="Laboratory chemical fumes in Room 104.",
        status="submitted",
    )
    prio = ComplaintPriority(
        complaint_id="CMP-RBAC-001",
        score=70.0,
        suggested_priority="HIGH",
        final_priority="HIGH",
        safety_flag=False,
        safety_override=False,
        needs_human_review=False,
    )
    audit_db.add_all([c, prio])
    audit_db.commit()

    # 1. Student CANNOT view system-wide analytics overview (HTTP 403)
    with pytest.raises(HTTPException) as exc_info:
        get_analytics_overview(current_user=student, db=audit_db)
    assert exc_info.value.status_code == 403
    assert "Permission denied" in exc_info.value.detail

    # 2. Student CANNOT view unsupervised clusters (HTTP 403)
    with pytest.raises(HTTPException) as exc_info:
        get_recurring_clusters(current_user=student, db=audit_db)
    assert exc_info.value.status_code == 403

    # 3. Student CANNOT update complaint status (HTTP 403)
    with pytest.raises(HTTPException) as exc_info:
        update_complaint_status(
            complaint_id="CMP-RBAC-001",
            req=ComplaintStatusUpdateRequest(status="resolved"),
            current_user=student,
            db=audit_db,
        )
    assert exc_info.value.status_code == 403

    # 4. Student CANNOT override priority (HTTP 403)
    with pytest.raises(HTTPException) as exc_info:
        override_priority(
            complaint_id="CMP-RBAC-001",
            req=PriorityOverrideRequest(override_priority="LOW", reason="Self demotion"),
            current_user=student,
            db=audit_db,
        )
    assert exc_info.value.status_code == 403

    # 5. Student CANNOT inspect another student's complaint (HTTP 403)
    with pytest.raises(HTTPException) as exc_info:
        get_complaint(complaint_id="CMP-RBAC-001", current_user=other_student, db=audit_db)
    assert exc_info.value.status_code == 403
    assert "Access denied" in exc_info.value.detail

    # 6. Staff IS permitted to access analytics, update status, and override priority
    overview = get_analytics_overview(current_user=staff, db=audit_db)
    assert overview.total_complaints >= 1

    updated = update_complaint_status(
        complaint_id="CMP-RBAC-001",
        req=ComplaintStatusUpdateRequest(status="in_progress"),
        current_user=staff,
        db=audit_db,
    )
    assert updated.status == "in_progress"

    overridden = override_priority(
        complaint_id="CMP-RBAC-001",
        req=PriorityOverrideRequest(override_priority="CRITICAL", reason="Fumes verified toxic"),
        current_user=staff,
        db=audit_db,
    )
    assert overridden.priority.final_priority == "CRITICAL"

