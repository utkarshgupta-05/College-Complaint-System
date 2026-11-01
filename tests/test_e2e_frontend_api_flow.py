"""
tests/test_e2e_frontend_api_flow.py
------------------------------------
Simulates the exact frontend HTTP interactions, user typing flows,
and role transitions across Student, Staff, and Admin portals.
Verifies the exact JSON payloads and data structures consumed by React components.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import User, UserRole, ComplaintStatus
from backend.auth import create_access_token, hash_password
from backend.routers.auth import login
from backend.routers.complaints import (
    analyze_complaint_preview,
    submit_complaint,
    list_complaints,
    get_complaint,
    update_complaint_status,
    override_priority,
)
from backend.routers.analytics import get_analytics_overview, get_recurring_clusters
from backend.schemas import (
    UserLoginRequest,
    ComplaintAnalyzeRequest,
    ComplaintCreateRequest,
    ComplaintStatusUpdateRequest,
    PriorityOverrideRequest,
)

@pytest.fixture
def isolated_db(tmp_path):
    db_file = tmp_path / "e2e_test.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()

    # Seed 3 users
    student = User(
        username="student",
        email="student@campus.edu",
        hashed_password=hash_password("student123"),
        role=UserRole.STUDENT.value,
        full_name="Alice Student",
        department="Computer Science"
    )
    staff = User(
        username="staff",
        email="staff@campus.edu",
        hashed_password=hash_password("staff123"),
        role=UserRole.STAFF.value,
        full_name="Bob Staff",
        department="Facilities"
    )
    admin = User(
        username="admin",
        email="admin@campus.edu",
        hashed_password=hash_password("admin123"),
        role=UserRole.ADMIN.value,
        full_name="Carol Admin",
        department="Administration"
    )
    db.add_all([student, staff, admin])
    db.commit()
    yield db
    db.close()


def test_full_student_typing_and_submission_workflow(isolated_db):
    student = isolated_db.query(User).filter(User.username == "student").first()

    # 1. Typing flow: Live AI pre-triage preview
    text = "Exposed electrical wire in Hostel Block C Room 204 is sparking dangerously near the fan switch."
    analyze_req = ComplaintAnalyzeRequest(complaint_text=text, location="Hostel Block C Room 204")
    preview = analyze_complaint_preview(analyze_req, current_user=student)

    # Verify frontend contract fields
    assert preview.prediction.predicted_category in ["C02", "C08", "C01"]
    assert isinstance(preview.prediction.confidence, float)
    assert preview.prediction.confidence >= 0.0 and preview.prediction.confidence <= 1.0
    assert isinstance(preview.priority.score, float)
    assert preview.priority.score >= 0.0 and preview.priority.score <= 100.0
    assert preview.priority.final_priority in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    assert isinstance(preview.duplicate_suggestions, list)

    # 2. Student Submits Complaint
    submit_req = ComplaintCreateRequest(
        complaint_text=text,
        location="Hostel Block C Room 204",
        student_dept="Computer Science"
    )
    created = submit_complaint(submit_req, current_user=student, db=isolated_db)
    assert created.id.startswith("CMP-")
    assert created.status == "submitted"

    # 3. Student views "My Submitted Complaints"
    student_complaints = list_complaints(current_user=student, db=isolated_db)
    assert len(student_complaints) == 1
    item = student_complaints[0]
    assert item.id == created.id
    assert item.final_priority is not None
    assert item.predicted_category is not None


def test_staff_queue_inspection_status_update_and_override_workflow(isolated_db):
    student = isolated_db.query(User).filter(User.username == "student").first()
    staff = isolated_db.query(User).filter(User.username == "staff").first()

    # Pre-submit a complaint
    submit_req = ComplaintCreateRequest(
        complaint_text="Wi-Fi connectivity in Library 3rd floor reading room keeps dropping every 5 minutes.",
        location="Library 3rd floor",
        student_dept="Computer Science"
    )
    created = submit_complaint(submit_req, current_user=student, db=isolated_db)

    # 1. Staff lists queue
    queue = list_complaints(current_user=staff, db=isolated_db)
    assert len(queue) >= 1
    assert any(c.id == created.id for c in queue)

    # 2. Staff inspects full details
    detail = get_complaint(complaint_id=created.id, current_user=staff, db=isolated_db)
    assert detail.id == created.id
    assert detail.prediction is not None
    assert detail.priority is not None
    assert isinstance(detail.prediction.all_scores, dict)
    assert isinstance(detail.priority.signals, dict)

    # 3. Staff updates status to in_progress
    status_req = ComplaintStatusUpdateRequest(status="in_progress")
    updated = update_complaint_status(complaint_id=created.id, req=status_req, current_user=staff, db=isolated_db)
    assert updated.status == "in_progress"

    # 4. Staff executes Priority Override with mandatory reason
    override_req = PriorityOverrideRequest(
        override_priority="CRITICAL",
        reason="Exam week in progress; Wi-Fi disruption in library severely impairs student study"
    )
    overridden = override_priority(complaint_id=created.id, req=override_req, current_user=staff, db=isolated_db)
    assert overridden.priority.final_priority == "CRITICAL"
    assert len(overridden.priority_overrides) == 1
    audit = overridden.priority_overrides[0]
    assert audit.override_priority == "CRITICAL"
    assert audit.staff_username == "staff"
    assert "Exam week" in audit.reason


def test_admin_analytics_and_unsupervised_clusters(isolated_db):
    admin = isolated_db.query(User).filter(User.username == "admin").first()
    student = isolated_db.query(User).filter(User.username == "student").first()

    # Submit 3 diverse complaints to populate analytics
    samples = [
        ("Hostel room ceiling leaking water violently near bed", "Hostel Block A Room 101"),
        ("Lab computers have broken power cables with exposed copper", "CS Lab 1"),
        ("Mess food contains foreign contaminants and sour milk served", "Central Mess Hall"),
    ]
    for text, loc in samples:
        submit_complaint(ComplaintCreateRequest(complaint_text=text, location=loc), current_user=student, db=isolated_db)

    # 1. Admin Overview
    overview = get_analytics_overview(current_user=admin, db=isolated_db)
    assert overview.total_complaints >= 3
    assert isinstance(overview.category_distribution, list)
    for cat_item in overview.category_distribution:
        assert hasattr(cat_item, "category")
        assert hasattr(cat_item, "category_name")
        assert hasattr(cat_item, "count")
        assert hasattr(cat_item, "percentage")
        assert isinstance(cat_item.count, int)
        assert isinstance(cat_item.percentage, float)

    # 2. Admin Clusters
    clusters = get_recurring_clusters(current_user=admin, db=isolated_db)
    assert isinstance(clusters, list)
    for cl in clusters:
        assert hasattr(cl, "cluster_id")
        assert hasattr(cl, "size")
        assert hasattr(cl, "top_terms")
        assert hasattr(cl, "is_weakly_supported")

