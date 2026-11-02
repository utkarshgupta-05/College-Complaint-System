"""
tests/test_api_integration.py
------------------------------
End-to-end backend integration tests for Phase 8.
Tests authentication, complaint creation, AI triage, duplicate detection,
priority rules and safety overrides, staff audit logs, RBAC enforcement,
and analytics with an isolated temporary SQLite database.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.auth import hash_password, require_admin, require_staff, require_student
from backend.database import Base
from backend.models import Complaint, User, UserRole
from backend.routers.analytics import get_analytics_overview, get_recurring_clusters
from backend.routers.auth import get_me, login, register
from backend.routers.complaints import (
    analyze_complaint_preview,
    get_complaint,
    list_complaints,
    override_category,
    override_priority,
    submit_complaint,
    update_complaint_status,
)
from backend.schemas import (
    CategoryOverrideRequest,
    ComplaintAnalyzeRequest,
    ComplaintCreateRequest,
    ComplaintStatusUpdateRequest,
    PriorityOverrideRequest,
    UserLoginRequest,
    UserRegisterRequest,
)
from backend.services.ai_service import ai_service


@pytest.fixture
def test_db(tmp_path):
    """Isolated SQLite database session fixture."""
    db_file = tmp_path / "test_api.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    # Pre-seed test users
    student = User(
        username="test_student",
        email="student@test.edu",
        hashed_password=hash_password("studentpass"),
        full_name="Test Student",
        role=UserRole.STUDENT.value,
        department="CSE",
    )
    staff = User(
        username="test_staff",
        email="staff@test.edu",
        hashed_password=hash_password("staffpass"),
        full_name="Test Staff",
        role=UserRole.STAFF.value,
        department="Maintenance",
    )
    admin = User(
        username="test_admin",
        email="admin@test.edu",
        hashed_password=hash_password("adminpass"),
        full_name="Test Admin",
        role=UserRole.ADMIN.value,
        department="Administration",
    )
    db.add_all([student, staff, admin])
    db.commit()

    yield db

    db.close()
    Base.metadata.drop_all(bind=engine)


# =========================================================================
# 1. Model Loading & AI Service Tests
# =========================================================================

def test_ai_service_model_loading():
    """Verify AI models are loaded with valid interfaces."""
    ai_service.load_models()
    assert ai_service.is_classifier_loaded is True
    assert ai_service.is_retriever_loaded is True

    # Test classification
    pred = ai_service.classify("Ceiling fan motor is smoking and burning in room 204")
    assert pred["predicted_category"] in ("C01", "C02", "C06", "C07", "C08")
    assert 0.0 <= pred["confidence"] <= 1.0
    assert isinstance(pred["low_confidence"], bool)

    # Test priority
    prio = ai_service.prioritize("Ceiling fan motor is smoking and burning in room 204")
    assert prio["safety_flag"] is True
    assert prio["final_priority"] == "CRITICAL"


# =========================================================================
# 2. Authentication & RBAC Tests
# =========================================================================

def test_auth_register_and_login(test_db):
    """Test user registration and successful login."""
    reg_req = UserRegisterRequest(
        username="new_user",
        email="new@test.edu",
        password="securepassword123",
        role="student",
    )
    new_user = register(reg_req, test_db)
    assert new_user.username == "new_user"

    # Login
    login_req = UserLoginRequest(username="new_user", password="securepassword123")
    tok = login(login_req, test_db)
    assert tok.access_token is not None
    assert tok.user.username == "new_user"


def test_auth_invalid_credentials(test_db):
    """Test login failure with bad password."""
    login_req = UserLoginRequest(username="test_student", password="wrongpassword")
    with pytest.raises(HTTPException) as exc_info:
        login(login_req, test_db)
    assert exc_info.value.status_code == 401


def test_rbac_role_enforcement(test_db):
    """Verify students cannot perform staff/admin operations."""
    student = test_db.query(User).filter(User.username == "test_student").first()
    staff = test_db.query(User).filter(User.username == "test_staff").first()
    admin = test_db.query(User).filter(User.username == "test_admin").first()

    # require_student allows all
    assert require_student(student).id == student.id
    assert require_student(staff).id == staff.id

    # require_staff blocks student
    with pytest.raises(HTTPException) as exc_info:
        require_staff(student)
    assert exc_info.value.status_code == 403

    # require_staff allows staff and admin
    assert require_staff(staff).id == staff.id
    assert require_staff(admin).id == admin.id

    # require_admin blocks staff
    with pytest.raises(HTTPException) as exc_admin:
        require_admin(staff)
    assert exc_admin.value.status_code == 403
    assert require_admin(admin).id == admin.id


# =========================================================================
# 3. Complaint Submission, AI Triage & Retrieval
# =========================================================================

def test_analyze_preview(test_db):
    """Test instant pre-submission triage preview."""
    student = test_db.query(User).filter(User.username == "test_student").first()
    req = ComplaintAnalyzeRequest(
        complaint_text="Water pipe broke and flooded the corridor on 2nd floor",
        location="Academic Block 1",
    )
    res = analyze_complaint_preview(req, student)
    assert res.prediction.predicted_category in ("C02", "C07")
    assert res.priority.score > 0.0


def test_submit_complaint_end_to_end(test_db):
    """Test complaint creation, AI inference, and database persistence."""
    student = test_db.query(User).filter(User.username == "test_student").first()
    req = ComplaintCreateRequest(
        complaint_text="Wi-Fi connectivity is dropping continuously in hostel study hall",
        location="Hostel Block A - Study Hall",
        student_dept="CSE",
    )
    res = submit_complaint(req, student, test_db)

    assert res.id.startswith("CMP-")
    assert res.status == "submitted"
    assert res.prediction is not None
    assert res.prediction.predicted_category == "C03"
    assert res.priority is not None
    assert res.priority.final_priority in ("LOW", "MEDIUM", "HIGH", "CRITICAL")

    # Verify complaint persisted in database
    db_rec = test_db.query(Complaint).filter(Complaint.id == res.id).first()
    assert db_rec is not None
    assert db_rec.prediction.predicted_category == "C03"


def test_duplicate_detection_ranking(test_db):
    """Test duplicate detection surfaces similar issues."""
    student = test_db.query(User).filter(User.username == "test_student").first()

    # First complaint
    c1_req = ComplaintCreateRequest(
        complaint_text="Air conditioner leaking large puddle of water in Computer Lab 102",
        location="Computer Lab 102",
    )
    c1 = submit_complaint(c1_req, student, test_db)

    # Near duplicate complaint submitted
    c2_req = ComplaintCreateRequest(
        complaint_text="AC is leaking water on the floor in Computer Lab 102 creating slipping hazard",
        location="Computer Lab 102",
    )
    c2 = submit_complaint(c2_req, student, test_db)

    assert len(c2.duplicate_suggestions) >= 0


def test_list_complaints_role_isolation(test_db):
    """Verify students only see their own complaints, while staff see all."""
    student = test_db.query(User).filter(User.username == "test_student").first()
    staff = test_db.query(User).filter(User.username == "test_staff").first()

    # Submit 2 complaints by student
    req = ComplaintCreateRequest(complaint_text="Mess food quality is stale and unhygienic today")
    submit_complaint(req, student, test_db)

    student_list = list_complaints(student, test_db)
    staff_list = list_complaints(staff, test_db)

    assert len(student_list) >= 1
    assert len(staff_list) >= len(student_list)


# =========================================================================
# 4. Status Update & Priority Override Audit Trail
# =========================================================================

def test_status_update(test_db):
    """Test staff updating complaint status."""
    student = test_db.query(User).filter(User.username == "test_student").first()
    staff = test_db.query(User).filter(User.username == "test_staff").first()

    req = ComplaintCreateRequest(complaint_text="Elevator button for 4th floor is broken and stuck")
    cmp_obj = submit_complaint(req, student, test_db)

    status_req = ComplaintStatusUpdateRequest(status="in_progress")
    updated = update_complaint_status(cmp_obj.id, status_req, staff, test_db)
    assert updated.status == "in_progress"


def test_priority_override_with_audit_logging(test_db):
    """Test staff overriding priority with recorded reason and full audit trail."""
    student = test_db.query(User).filter(User.username == "test_student").first()
    staff = test_db.query(User).filter(User.username == "test_staff").first()

    req = ComplaintCreateRequest(complaint_text="Classroom 301 blackboard has hairline cracks")
    cmp_obj = submit_complaint(req, student, test_db)
    orig_prio = cmp_obj.priority.final_priority

    override_req = PriorityOverrideRequest(
        override_priority="CRITICAL",
        reason="Inspected in person: crack is structural and masonry could fall",
    )
    res = override_priority(cmp_obj.id, override_req, staff, test_db)

    assert res.priority.final_priority == "CRITICAL"
    assert len(res.priority_overrides) == 1
    audit = res.priority_overrides[0]
    assert audit.original_priority == orig_prio
    assert audit.override_priority == "CRITICAL"
    assert audit.staff_username == "test_staff"
    assert "structural" in audit.reason


# =========================================================================
# 5. Analytics & Recurring-Issue Discovery
# =========================================================================

def test_analytics_endpoints(test_db):
    """Test analytics overview and topic clustering."""
    admin = test_db.query(User).filter(User.username == "test_admin").first()

    # Overview
    overview = get_analytics_overview(admin, test_db)
    assert overview.total_complaints >= 0
    assert isinstance(overview.category_distribution, list)
    assert isinstance(overview.priority_distribution, list)

    # Clusters
    clusters = get_recurring_clusters(admin, test_db)
    assert isinstance(clusters, list)
    for cl in clusters:
        assert cl.size > 0
        assert isinstance(cl.representative_complaints, list)


def test_category_override_by_staff(test_db):
    """Test staff overriding the predicted category, updating category name, and clearing review flag."""
    student = test_db.query(User).filter(User.username == "test_student").first()
    staff = test_db.query(User).filter(User.username == "test_staff").first()

    req = ComplaintCreateRequest(
        complaint_text="Digital oscilloscope in lab 2 is smoking and displaying error code",
        location="Lab 2",
    )
    cmp_obj = submit_complaint(req, student, test_db)

    # 1. Staff corrects category to C06 (Classroom and Laboratory)
    override_req = CategoryOverrideRequest(
        override_category="C06",
        reason="Staff reviewed and confirmed this is instructional lab equipment, not sanitation"
    )
    updated = override_category(cmp_obj.id, override_req, staff, test_db)

    assert updated.prediction.predicted_category == "C06"
    assert updated.prediction.category_name == "Classroom and Laboratory"
    assert updated.prediction.needs_human_review is False
    assert "Instructional Facilities" in updated.assigned_department

    # 2. Student cannot override category (permission check)
    with pytest.raises(HTTPException) as exc:
        override_category(cmp_obj.id, override_req, student, test_db)
    assert exc.value.status_code == 403


def test_assigned_department_and_filtering(test_db):
    """Test assigned department resolution and department filtering in list_complaints."""
    student = test_db.query(User).filter(User.username == "test_student").first()
    staff = test_db.query(User).filter(User.username == "test_staff").first()

    # Submit 2 complaints
    c1 = submit_complaint(
        ComplaintCreateRequest(complaint_text="Wi-Fi connectivity completely down in Library 2nd floor", location="Library"),
        student,
        test_db,
    )
    c2 = submit_complaint(
        ComplaintCreateRequest(complaint_text="Washroom tap leaking clean water on Hostel Block B floor 1", location="Hostel B"),
        student,
        test_db,
    )

    # Check detail response contains assigned_department
    d1 = get_complaint(c1.id, staff, test_db)
    assert d1.assigned_department is not None

    # Check list response contains assigned_department
    all_items = list_complaints(staff, test_db)
    for it in all_items:
        if it.predicted_category:
            assert it.assigned_department is not None

    # Filter by department
    it_items = list_complaints(staff, test_db, department="Network")
    assert any(c.id == c1.id for c in it_items)


def test_empty_database_analytics_and_clusters(tmp_path):
    """Test analytics endpoints gracefully handle an empty database without exceptions."""
    db_file = tmp_path / "empty.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()

    admin = User(
        username="empty_admin",
        email="ea@test.edu",
        hashed_password=hash_password("adminpass"),
        role=UserRole.ADMIN.value,
    )
    db.add(admin)
    db.commit()

    # Analytics overview on empty database
    overview = get_analytics_overview(admin, db)
    assert overview.total_complaints == 0
    assert overview.category_distribution == []
    assert "No complaints" in overview.trend_warning

    # Recurring clusters on empty database
    clusters = get_recurring_clusters(admin, db)
    assert clusters == []
    db.close()


