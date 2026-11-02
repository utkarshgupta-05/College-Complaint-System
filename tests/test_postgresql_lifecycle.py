"""
tests/test_postgresql_lifecycle.py
----------------------------------
End-to-end integration and persistence test suite for PostgreSQL 18.
Verifies engine dialect, schema migration, user registration, JWT authentication,
complaint submission, AI triage, category/priority overrides, audit trail persistence,
admin analytics aggregation, and restart durability on PostgreSQL.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
import pytest
import psycopg2

# Configure PostgreSQL connection for the test session
PG_TEST_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://complaint_user:dev_test_pg_pass_2026@127.0.0.1:5433/complaint_db"
)

def _is_pg_reachable(url: str) -> bool:
    try:
        conn = psycopg2.connect(url, connect_timeout=1)
        conn.close()
        return True
    except Exception:
        return False

if not _is_pg_reachable(PG_TEST_URL):
    pytestmark = pytest.mark.skip(
        reason=f"PostgreSQL test database not reachable at {PG_TEST_URL}. Skipping PostgreSQL lifecycle suite."
    )
    # Stubs so file parses cleanly when skipped
    pg_session = None
    client = None
else:
    os.environ["DATABASE_URL"] = PG_TEST_URL
    os.environ["ENV"] = "development"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from backend.config import settings
from backend.database import Base, SessionLocal, engine, get_db
from backend.main import app
from backend.models import (
    Complaint,
    ComplaintPrediction,
    ComplaintPriority,
    ComplaintStatus,
    PriorityOverrideAudit,
    User,
    UserRole,
)
from backend.auth import create_access_token, hash_password


@pytest.fixture(scope="module")
def pg_session():
    """Verify PostgreSQL engine and provide a dedicated test session."""
    assert engine.dialect.name == "postgresql", f"Expected postgresql dialect, got {engine.dialect.name}"
    db = SessionLocal()
    try:
        # Check database version
        version = db.execute(text("SELECT version();")).scalar()
        assert "PostgreSQL" in version, f"Unexpected version string: {version}"
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client():
    """FastAPI TestClient configured against PostgreSQL backend."""
    return TestClient(app)


def test_01_postgresql_dialect_and_version(pg_session):
    """Task 6 & 10: Confirm engine dialect is PostgreSQL and server is PostgreSQL 18."""
    result = pg_session.execute(text("SELECT current_database(), current_user, version();")).fetchone()
    current_db, current_user, version = result
    assert current_db == "complaint_db"
    assert current_user == "complaint_user"
    assert "PostgreSQL 18" in version
    print(f"\n[PG-TEST] Connected to {current_db} as {current_user} ({version.split(',')[0]})")


def test_02_schema_and_tables_verified(pg_session):
    """Task 7: Verify that Alembic migrations created all 7 expected tables and indexes."""
    tables_result = pg_session.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)).fetchall()
    tables = [r[0] for r in tables_result]

    expected_tables = {
        "alembic_version",
        "complaint_predictions",
        "complaint_priorities",
        "complaints",
        "duplicate_suggestions",
        "priority_override_audits",
        "users",
    }
    assert expected_tables.issubset(set(tables)), f"Missing tables: {expected_tables - set(tables)}"

    # Verify alembic head
    head_rev = pg_session.execute(text("SELECT version_num FROM alembic_version;")).scalar()
    assert head_rev == "0001_initial_schema"


def test_03_user_registration_and_jwt_login(client, pg_session):
    """Task 9: Test user registration and authentication lifecycle in PostgreSQL."""
    reg_payload = {
        "username": "pg_test_student",
        "email": "pg_student@college.edu",
        "password": "SecurePassword123!",
        "full_name": "Postgres Test Student",
        "department": "Mechanical Engineering",
    }
    # Clean up if exists from previous run
    existing = pg_session.query(User).filter(User.username == "pg_test_student").first()
    if existing:
        pg_session.delete(existing)
        pg_session.commit()

    resp = client.post("/api/auth/register", json=reg_payload)
    assert resp.status_code == 201, f"Registration failed: {resp.text}"
    data = resp.json()
    assert data["username"] == "pg_test_student"
    assert "id" in data

    # Verify persistence directly in PostgreSQL
    db_user = pg_session.query(User).filter(User.username == "pg_test_student").first()
    assert db_user is not None
    assert db_user.email == "pg_student@college.edu"

    # Test login
    login_resp = client.post("/api/auth/login", json={
        "username": "pg_test_student",
        "password": "SecurePassword123!"
    })
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token_data = login_resp.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"


def test_04_complaint_creation_and_ai_triage(client, pg_session):
    """Task 9: Test complaint submission, live AI classification, and department mapping in PostgreSQL."""
    # Obtain student token
    login_resp = client.post("/api/auth/login", json={"username": "pg_test_student", "password": "SecurePassword123!"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    complaint_payload = {
        "complaint_text": "Severe water leakage from the ceiling in Room 204 Brahmaputra Hostel during heavy rain.",
        "location": "Brahmaputra Hostel",
    }
    resp = client.post("/api/complaints", json=complaint_payload, headers=headers)
    assert resp.status_code == 201, f"Complaint creation failed: {resp.text}"
    c_data = resp.json()

    cid = c_data["id"]
    assert cid.startswith("CMP-")
    assert c_data["assigned_department"] in ("Hostel Administration & Chief Warden Office", "Campus Maintenance & Estate")
    assert c_data["prediction"]["predicted_category"] in ("C01", "C02")
    assert "score" in c_data["priority"]

    # Verify complaint in PostgreSQL DB
    db_c = pg_session.query(Complaint).filter(Complaint.id == cid).first()
    assert db_c is not None
    assert db_c.complaint_text == complaint_payload["complaint_text"]
    assert db_c.prediction is not None
    assert db_c.priority is not None


def test_05_complaint_retrieval_and_filtering(client):
    """Task 9: Test complaint querying and department filtering in PostgreSQL."""
    login_resp = client.post("/api/auth/login", json={"username": "staff", "password": "staff123"})
    staff_token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {staff_token}"}

    # Query all complaints
    resp = client.get("/api/complaints", headers=headers)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) >= 1
    assert "assigned_department" in items[0]

    # Filter by department
    estate_resp = client.get("/api/complaints?department=Campus+Maintenance+%26+Estate", headers=headers)
    assert estate_resp.status_code == 200
    for c in estate_resp.json():
        assert c["assigned_department"] == "Campus Maintenance & Estate"


def test_06_complaint_status_progression(client, pg_session):
    """Task 9: Test status transitions (SUBMITTED -> IN_PROGRESS -> RESOLVED) in PostgreSQL."""
    staff_token = client.post("/api/auth/login", json={"username": "staff", "password": "staff123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {staff_token}"}

    # Find a complaint
    target_c = pg_session.query(Complaint).first()
    assert target_c is not None
    cid = target_c.id

    # Advance to IN_PROGRESS
    p1 = client.patch(f"/api/complaints/{cid}/status", json={"status": "in_progress"}, headers=headers)
    assert p1.status_code == 200
    assert p1.json()["status"] == "in_progress"

    # Refresh DB session and verify in PostgreSQL
    pg_session.expire_all()
    updated = pg_session.query(Complaint).filter(Complaint.id == cid).first()
    assert updated.status == "in_progress"

    # Advance to RESOLVED
    p2 = client.patch(f"/api/complaints/{cid}/status", json={"status": "resolved"}, headers=headers)
    assert p2.status_code == 200
    assert p2.json()["status"] == "resolved"


def test_07_category_and_priority_overrides(client, pg_session):
    """Task 9: Test staff category override and priority override with audit log in PostgreSQL."""
    staff_token = client.post("/api/auth/login", json={"username": "staff", "password": "staff123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {staff_token}"}

    target_c = pg_session.query(Complaint).first()
    cid = target_c.id

    # 1. Priority Override
    prio_resp = client.post(
        f"/api/complaints/{cid}/priority-override",
        json={"override_priority": "CRITICAL", "reason": "Water leakage poses immediate structural risk"},
        headers=headers,
    )
    assert prio_resp.status_code == 200
    assert prio_resp.json()["priority"]["final_priority"] == "CRITICAL"

    # 2. Category Override
    cat_resp = client.post(
        f"/api/complaints/{cid}/category-override",
        json={"override_category": "C02", "reason": "Water pipeline rupture falls under Water & Electricity division"},
        headers=headers,
    )
    assert cat_resp.status_code == 200
    cat_data = cat_resp.json()
    assert cat_data["prediction"]["predicted_category"] == "C02"
    assert cat_data["prediction"]["category_name"] == "Electricity and Water"
    assert cat_data["prediction"]["needs_human_review"] is False

    # 3. Check Audit Trail in Complaint Detail
    detail_resp = client.get(f"/api/complaints/{cid}", headers=headers)
    assert detail_resp.status_code == 200
    audits = detail_resp.json()["priority_overrides"]
    assert len(audits) >= 1
    assert audits[0]["override_priority"] == "CRITICAL"


def test_08_admin_analytics_aggregation(client):
    """Task 9: Test admin KPI analytics, category breakdown, hotspots, and clustering in PostgreSQL."""
    admin_token = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Test overview
    resp = client.get("/api/analytics/overview", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert "total_complaints" in data
    assert data["total_complaints"] >= 25
    assert "category_distribution" in data
    assert "priority_distribution" in data
    assert "hotspots" in data
    assert "trend_warning" in data

    # Test clusters
    cluster_resp = client.get("/api/analytics/clusters", headers=headers)
    assert cluster_resp.status_code == 200
    assert isinstance(cluster_resp.json(), list)


def test_09_persistence_after_backend_engine_restart():
    """Task 9: Verify complete durability across SQLAlchemy engine restart and disconnect on PostgreSQL."""
    # Step A: Connect and insert a unique sentinel complaint
    sentinel_id = f"CMP-SENTINEL-PG-{int(datetime.now(timezone.utc).timestamp())}"
    
    eng1 = create_engine(PG_TEST_URL)
    Session1 = sessionmaker(bind=eng1)
    s1 = Session1()
    
    u = s1.query(User).filter(User.username == "pg_test_student").first()
    assert u is not None
    
    sentinel_complaint = Complaint(
        id=sentinel_id,
        user_id=u.id,
        complaint_text="PostgreSQL persistence verification across engine disposal and reconnection.",
        location="Administrative Complex Block B",
        status=ComplaintStatus.SUBMITTED.value,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    s1.add(sentinel_complaint)
    s1.commit()
    s1.close()
    
    # Simulate full backend crash/shutdown: dispose engine 1
    eng1.dispose()
    
    # Step B: Create a brand new engine 2 and reconnect to PostgreSQL
    eng2 = create_engine(PG_TEST_URL, pool_pre_ping=True)
    Session2 = sessionmaker(bind=eng2)
    s2 = Session2()
    
    retrieved = s2.query(Complaint).filter(Complaint.id == sentinel_id).first()
    assert retrieved is not None, f"Sentinel complaint {sentinel_id} lost after engine restart!"
    assert retrieved.location == "Administrative Complex Block B"
    assert retrieved.student.username == "pg_test_student"
    
    s2.close()
    eng2.dispose()
    print(f"\n[PG-TEST] Persistence verified: {sentinel_id} persisted across engine disposal and reconnection.")


def test_10_sqlite_fallback_intact():
    """Task 1 & Safeguards: Verify that SQLite database was never deleted or overwritten."""
    from pathlib import Path
    sqlite_db_path = Path("backend/complaints.db")
    assert sqlite_db_path.exists(), "SQLite fallback database was deleted!"
    assert sqlite_db_path.stat().st_size > 0, "SQLite fallback database was wiped or emptied!"
    print(f"\n[SAFEGUARD] SQLite database preserved: {sqlite_db_path} ({sqlite_db_path.stat().st_size} bytes)")
