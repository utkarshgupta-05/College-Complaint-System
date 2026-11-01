"""
backend/config.py
-----------------
Application configuration and environment settings for the FastAPI backend.
Pure-Python configuration reading directly from environment variables.
Enforces strict production safeguards: no silent SQLite fallback or insecure secrets in production.
"""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load .env if present
env_path = PROJECT_ROOT / "backend" / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv(PROJECT_ROOT / ".env")


class Settings:
    """Application settings with dynamic environment variable validation."""
    _DEFAULT_INSECURE_SECRET = "insecure-dev-secret-key-change-in-production-32bytes"

    def __init__(self) -> None:
        self.PROJECT_NAME: str = os.getenv("PROJECT_NAME", "College Complaint Intelligence System API")
        self.VERSION: str = "1.0.0"
        self.API_V1_PREFIX: str = "/api"

        # Environment
        self.ENV: str = os.getenv("ENV", "development").lower().strip()
        self.DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes") if self.ENV != "production" else False

        # Security & Auth
        self.SECRET_KEY: str = os.getenv("SECRET_KEY", self._DEFAULT_INSECURE_SECRET)
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24)))

        # Database: Supports PostgreSQL for production with isolated SQLite for local development/testing
        raw_db_url: str = os.getenv("DATABASE_URL", "").strip()

        if self.ENV == "production":
            # Strict Production Invariant: Silent SQLite fallback is strictly prohibited
            if not raw_db_url or raw_db_url.startswith("sqlite"):
                raise ValueError(
                    "PRODUCTION CONFIGURATION ERROR: ENV is set to 'production' but DATABASE_URL is "
                    f"{'pointing to SQLite' if raw_db_url.startswith('sqlite') else 'unset'}. "
                    "PostgreSQL is the approved production database (e.g. postgresql://user:pass@host:5432/dbname). "
                    "SQLite is restricted to development and isolated test suites."
                )
            if self.SECRET_KEY == self._DEFAULT_INSECURE_SECRET:
                raise ValueError(
                    "PRODUCTION CONFIGURATION ERROR: Default insecure SECRET_KEY cannot be used in production. "
                    "Set a secure, random 32+ character SECRET_KEY in your production environment variables."
                )
            self.DATABASE_URL = raw_db_url
            self.ENABLE_DEMO_SEED: bool = os.getenv("ENABLE_DEMO_SEED", "false").lower() in ("true", "1", "yes")
        else:
            # Development / Testing fallback
            self.DATABASE_URL = raw_db_url if raw_db_url else f"sqlite:///{PROJECT_ROOT / 'backend' / 'complaints.db'}"
            self.ENABLE_DEMO_SEED: bool = os.getenv("ENABLE_DEMO_SEED", "true").lower() in ("true", "1", "yes")

        # CORS
        self.CORS_ORIGINS: list[str] = [
            origin.strip()
            for origin in os.getenv(
                "CORS_ORIGINS",
                "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://localhost:8000,http://127.0.0.1:8000"
            ).split(",")
            if origin.strip()
        ]

        # Model Artifact Paths
        self.E2_MODEL_PATH: str = os.getenv("E2_MODEL_PATH", str(PROJECT_ROOT / "models" / "e2.joblib"))
        self.E6_RETRIEVER_PATH: str = os.getenv("E6_RETRIEVER_PATH", str(PROJECT_ROOT / "models" / "e6_tfidf_retriever.joblib"))
        self.VAL_DATA_PATH: str = str(PROJECT_ROOT / "data" / "processed" / "val.csv")

        # Classification & Priority Thresholds
        self.CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.60"))
        self.DUPLICATE_HIGH_THRESHOLD: float = float(os.getenv("DUPLICATE_HIGH_THRESHOLD", "0.80"))
        self.DUPLICATE_MID_THRESHOLD: float = float(os.getenv("DUPLICATE_MID_THRESHOLD", "0.50"))


settings = Settings()
