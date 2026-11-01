"""
backend/services/ai_service.py
------------------------------
Singleton service that wraps and serves existing Phase 2-7 AI modules:
- Classification (E2 Calibrated Linear SVM)
- Duplicate Retrieval (E6 TF-IDF Cosine Similarity)
- Priority Assessment (Rules Engine with Safety Overrides)
- Recurring-Issue Discovery (Frequency Hotspots & Topic Clustering)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from backend.config import settings
from src.classification.predict import ComplaintClassifier, PredictionResult
from src.classification.train import load_pipeline
from src.clustering.discover import run_dbscan, run_kmeans
from src.clustering.frequency import (
    aggregate_by_category,
    aggregate_by_location,
    assess_trend_sufficiency,
    find_hotspots,
)
from src.duplicates.similarity import SimilarComplaint, SimilarityLevel, TFIDFSimilarityRetriever
from src.prioritization.rules import PriorityLevel, PriorityResult, assess_priority

logger = logging.getLogger(__name__)

CATEGORY_NAMES: dict[str, str] = {
    "C01": "Hostel and Accommodation",
    "C02": "Electricity and Water",
    "C03": "Internet and Network",
    "C04": "Mess and Food",
    "C05": "Academic and Examination",
    "C06": "Classroom and Laboratory",
    "C07": "Sanitation and Cleanliness",
    "C08": "Campus Safety",
    "C09": "Transportation",
    "C10": "Administrative Services",
    "C11": "Other / Unclassified",
}


class AIService:
    """Manages loaded model artifacts and provides unified inference."""

    _instance: AIService | None = None

    def __init__(self) -> None:
        self.classifier: ComplaintClassifier | None = None
        self.retriever: TFIDFSimilarityRetriever | None = None
        self.is_classifier_loaded: bool = False
        self.is_retriever_loaded: bool = False

    @classmethod
    def get_instance(cls) -> AIService:
        if cls._instance is None:
            cls._instance = AIService()
            cls._instance.load_models()
        return cls._instance

    def load_models(self) -> None:
        """Load classification and duplicate detection models from disk once."""
        # 1. Load E2 Classifier
        e2_path = Path(settings.E2_MODEL_PATH)
        if e2_path.exists():
            try:
                pipeline, meta = load_pipeline(e2_path)
                label_names = list(pipeline.classes_)
                self.classifier = ComplaintClassifier(
                    pipeline=pipeline,
                    label_names=label_names,
                    confidence_threshold=settings.CONFIDENCE_THRESHOLD,
                )
                self.is_classifier_loaded = True
                logger.info(
                    "Loaded E2 classifier from %s (Trained on %d samples, val Macro-F1: %.4f)",
                    e2_path, meta.get("train_samples", 0), meta.get("macro_f1", 0.0)
                )
            except Exception as exc:
                logger.error("Failed to load E2 model from %s: %s", e2_path, exc)
                self.is_classifier_loaded = False
        else:
            logger.warning("E2 model file not found at %s. Classifier fallback active.", e2_path)

        # 2. Load E6 Duplicate Retriever
        e6_path = Path(settings.E6_RETRIEVER_PATH)
        if e6_path.exists():
            try:
                e6_dict = joblib.load(e6_path)
                if isinstance(e6_dict, dict) and "retriever" in e6_dict:
                    self.retriever = e6_dict["retriever"]
                elif isinstance(e6_dict, TFIDFSimilarityRetriever):
                    self.retriever = e6_dict
                else:
                    raise ValueError(f"Unrecognized retriever bundle structure: {type(e6_dict)}")

                self.is_retriever_loaded = True
                logger.info(
                    "Loaded E6 retriever from %s (Fitted on %d corpus items)",
                    e6_path, len(self.retriever._corpus_ids)
                )
            except Exception as exc:
                logger.error("Failed to load E6 retriever from %s: %s", e6_path, exc)
                self.is_retriever_loaded = False
        else:
            logger.warning("E6 retriever file not found at %s. Duplicate detection disabled.", e6_path)

    def classify(self, text: str) -> dict[str, Any]:
        """Run classification inference with confidence and review flag."""
        if not self.is_classifier_loaded or self.classifier is None:
            # Fallback safe behavior if artifact is unavailable
            return {
                "predicted_category": "C11",
                "category_name": CATEGORY_NAMES.get("C11", "Other / Unclassified"),
                "confidence": 0.0,
                "low_confidence": True,
                "needs_human_review": True,
                "all_scores": {},
            }

        res: PredictionResult = self.classifier.predict_one(text)
        cat_name = CATEGORY_NAMES.get(res.predicted_category, "Other / Unclassified")
        return {
            "predicted_category": res.predicted_category,
            "category_name": cat_name,
            "confidence": round(res.confidence, 4),
            "low_confidence": res.low_confidence,
            "needs_human_review": res.needs_human_review,
            "all_scores": {k: round(v, 4) for k, v in res.all_scores.items()},
        }

    def prioritize(
        self,
        text: str,
        created_at: datetime | None = None,
        recurrence_count: int = 0,
    ) -> dict[str, Any]:
        """Run priority assessment rules engine."""
        res: PriorityResult = assess_priority(
            complaint_text=text,
            created_at=created_at or datetime.now(timezone.utc),
            recurrence_count=recurrence_count,
        )
        return {
            "score": round(res.score, 1),
            "suggested_priority": res.suggested_priority.value,
            "final_priority": res.final_priority.value,
            "safety_flag": res.safety_flag,
            "safety_override": res.safety_override,
            "needs_human_review": res.needs_human_review,
            "signals": {k: round(v, 1) for k, v in res.signals.items()},
            "explanation": res.explanation,
        }

    def find_duplicates(
        self,
        text: str,
        exclude_id: str | None = None,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Find candidate duplicates using the fitted TF-IDF retriever."""
        if not self.is_retriever_loaded or self.retriever is None:
            return []

        try:
            candidates: list[SimilarComplaint] = self.retriever.find_similar(
                query_text=text,
                query_id=exclude_id,
                top_k=top_k,
                return_all=False,  # only return candidates >= mid_threshold (0.50)
            )

            out = []
            for c in candidates:
                if c.similarity_level in (SimilarityLevel.PROBABLE_DUPLICATE, SimilarityLevel.SIMILAR):
                    out.append({
                        "candidate_id": str(c.complaint_id),
                        "candidate_text": c.complaint_text,
                        "similarity_score": round(float(c.similarity_score), 4),
                        "similarity_level": c.similarity_level.value,
                        "candidate_category": c.category,
                        "candidate_location": c.location,
                    })
            return out
        except Exception as exc:
            logger.warning("Error finding duplicates: %s", exc)
            return []

    def index_complaint(
        self,
        complaint_id: str,
        text: str,
        category: str | None = None,
        location: str | None = None,
        created_at: str | None = None,
    ) -> None:
        """Dynamically index a newly submitted complaint into the runtime retriever."""
        if not self.is_retriever_loaded or self.retriever is None:
            return

        try:
            if complaint_id in self.retriever._corpus_ids:
                return

            # Transform new text using existing fitted vectorizer
            new_vec = self.retriever.vectorizer.transform([text])
            if self.retriever._corpus_matrix is not None:
                import scipy.sparse as sp
                self.retriever._corpus_matrix = sp.vstack([self.retriever._corpus_matrix, new_vec])
            else:
                self.retriever._corpus_matrix = new_vec

            self.retriever._corpus_ids.append(complaint_id)
            self.retriever._corpus_texts.append(text)
            self.retriever._corpus_metadata.append({
                "category": category,
                "location": location,
                "created_at": created_at,
            })
            logger.info("Dynamically indexed complaint %s into duplicate retriever.", complaint_id)
        except Exception as exc:
            logger.warning("Failed to index complaint %s: %s", complaint_id, exc)

    def analyze_full(
        self,
        text: str,
        location: str | None = None,
        recurrence_count: int = 0,
        exclude_id: str | None = None,
    ) -> dict[str, Any]:
        """Perform end-to-end triage: Classification + Priority + Duplicate Retrieval."""
        pred = self.classify(text)
        prio = self.prioritize(text, recurrence_count=recurrence_count)
        dups = self.find_duplicates(text, exclude_id=exclude_id, top_k=5)

        return {
            "prediction": pred,
            "priority": prio,
            "duplicate_suggestions": dups,
        }


ai_service = AIService.get_instance()

