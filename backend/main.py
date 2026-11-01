"""
backend/main.py
---------------
FastAPI application entry point for the College Complaint Intelligence System.
Initializes database tables, seeds demonstration users, loads AI models,
and configures CORS and API routers.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.auth import hash_password
from backend.config import settings
from backend.database import SessionLocal, init_db
from backend.models import Complaint, ComplaintPrediction, ComplaintPriority, User, UserRole
from backend.routers import analytics, auth, complaints
from backend.services.ai_service import ai_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("backend")


def seed_initial_data() -> None:
    """Seed initial demo accounts and baseline complaints if database is newly initialized and demo seeding is enabled."""
    if not settings.ENABLE_DEMO_SEED:
        logger.info("Demo data seeding disabled (ENABLE_DEMO_SEED=false).")
        return

    db = SessionLocal()
    try:
        # 1. Seed Demo Users
        user_count = db.query(User).count()
        if user_count == 0:
            logger.warning(
                "[DEVELOPMENT ENVIRONMENT] Seeding demonstration accounts: student, staff, admin "
                "(passwords: student123, staff123, admin123). "
                "These sample credentials are for development/testing only."
            )
            demo_users = [
                User(
                    username="student",
                    email="student@college.edu",
                    hashed_password=hash_password("student123"),
                    full_name="Aarav Sharma (Student)",
                    role=UserRole.STUDENT.value,
                    department="CSE",
                ),
                User(
                    username="staff",
                    email="staff@college.edu",
                    hashed_password=hash_password("staff123"),
                    full_name="Rajesh Verma (Campus Maintenance Staff)",
                    role=UserRole.STAFF.value,
                    department="Campus Maintenance",
                ),
                User(
                    username="admin",
                    email="admin@college.edu",
                    hashed_password=hash_password("admin123"),
                    full_name="Dr. Sunita Rao (Dean of Student Affairs)",
                    role=UserRole.ADMIN.value,
                    department="Administration",
                ),
            ]
            db.add_all(demo_users)
            db.commit()

        # 2. Seed Sample Complaints from validation dataset (first 25 rows) if complaint table is empty
        student_user = db.query(User).filter(User.role == UserRole.STUDENT.value).first()
        complaint_count = db.query(Complaint).count()
        val_path = Path(settings.VAL_DATA_PATH)

        if complaint_count == 0 and student_user and val_path.exists():
            logger.info("Seeding demonstration complaints from validation split...")
            try:
                val_df = pd.read_csv(val_path)
                sample_rows = val_df.head(25)

                for _, row in sample_rows.iterrows():
                    cid = str(row["complaint_id"])
                    text = str(row["complaint_text"])
                    loc = str(row["location"]) if pd.notna(row["location"]) else "Campus Main"

                    triage = ai_service.analyze_full(text, location=loc)
                    pred_data = triage["prediction"]
                    prio_data = triage["priority"]

                    c = Complaint(
                        id=cid,
                        user_id=student_user.id,
                        complaint_text=text,
                        location=loc,
                        student_dept=student_user.department,
                        status="submitted",
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                    )
                    db.add(c)
                    db.flush()

                    pred_rec = ComplaintPrediction(
                        complaint_id=cid,
                        predicted_category=pred_data["predicted_category"],
                        category_name=pred_data["category_name"],
                        confidence=pred_data["confidence"],
                        low_confidence=pred_data["low_confidence"],
                        needs_human_review=pred_data["needs_human_review"],
                    )
                    pred_rec.all_scores = pred_data.get("all_scores", {})
                    db.add(pred_rec)

                    prio_rec = ComplaintPriority(
                        complaint_id=cid,
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

                db.commit()
                logger.info("Successfully seeded %d sample complaints into database.", len(sample_rows))
            except Exception as exc:
                db.rollback()
                logger.warning("Could not seed sample complaints: %s", exc)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for model loading and schema initialization."""
    print("--- LIFESPAN START ---", flush=True)
    logger.info("Starting College Complaint Intelligence System backend...")
    init_db()
    print("--- INIT DB DONE ---", flush=True)
    ai_service.load_models()
    print("--- LOAD MODELS DONE ---", flush=True)
    seed_initial_data()
    print("--- SEED INITIAL DATA DONE ---", flush=True)
    yield
    print("--- LIFESPAN END ---", flush=True)
    logger.info("Shutting down backend...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Intelligent AI backend for complaint classification, duplicate retrieval, and priority triage.",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(complaints.router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def health_check():
    """Root health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "models_loaded": {
            "classifier_e2": ai_service.is_classifier_loaded,
            "retriever_e6": ai_service.is_retriever_loaded,
        },
    }
