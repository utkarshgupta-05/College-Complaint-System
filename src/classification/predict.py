"""
src/classification/predict.py
------------------------------
Inference functions for the trained complaint classifier.

Design:
- Loads a fitted pipeline from disk (built by train.py).
- Applies the same text normalization used at training time.
- Returns a predicted category AND a confidence score.
- Flags predictions below the confidence threshold for human review.
- Never routes a prediction to the "final" category without a confidence check.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)


@dataclass
class PredictionResult:
    """Result of classifying a single complaint."""
    complaint_text: str
    predicted_category: str
    confidence: float
    low_confidence: bool
    all_scores: dict[str, float]  # {category: probability}
    needs_human_review: bool

    def __repr__(self) -> str:
        flag = " ⚠ NEEDS REVIEW" if self.needs_human_review else ""
        return (
            f"PredictionResult("
            f"category='{self.predicted_category}', "
            f"confidence={self.confidence:.3f}{flag})"
        )


class ComplaintClassifier:
    """Wraps a trained sklearn Pipeline for complaint inference.

    Args:
        pipeline: A fitted sklearn Pipeline with predict_proba support.
        label_names: Ordered list of category labels matching pipeline output.
        confidence_threshold: Predictions below this threshold trigger
            low_confidence and needs_human_review flags.
    """

    def __init__(
        self,
        pipeline: Pipeline,
        label_names: list[str],
        confidence_threshold: float = 0.60,
    ) -> None:
        self.pipeline = pipeline
        self.label_names = label_names
        self.confidence_threshold = confidence_threshold

    def predict_one(self, text: str) -> PredictionResult:
        """Classify a single complaint text.

        Args:
            text: Raw or normalized complaint text.

        Returns:
            PredictionResult with prediction, confidence, and review flag.

        Notes:
            - The confidence score is the softmax probability from the classifier.
            - This is NOT a calibrated probability unless CalibratedClassifierCV
              was used during training. Do not claim it is.
        """
        if not isinstance(text, str) or not text.strip():
            logger.warning("Empty or invalid complaint text received.")
            return PredictionResult(
                complaint_text=text,
                predicted_category="C11",  # Other / Unclassified
                confidence=0.0,
                low_confidence=True,
                all_scores={},
                needs_human_review=True,
            )

        proba = self.pipeline.predict_proba([text])[0]
        predicted_idx = int(np.argmax(proba))
        predicted_label = self.label_names[predicted_idx]
        confidence = float(proba[predicted_idx])
        all_scores = dict(zip(self.label_names, proba.tolist()))

        low_confidence = confidence < self.confidence_threshold
        needs_review = low_confidence or predicted_label == "C11"

        return PredictionResult(
            complaint_text=text,
            predicted_category=predicted_label,
            confidence=confidence,
            low_confidence=low_confidence,
            all_scores=all_scores,
            needs_human_review=needs_review,
        )

    def predict_batch(self, texts: list[str]) -> list[PredictionResult]:
        """Classify a list of complaint texts.

        Args:
            texts: List of complaint text strings.

        Returns:
            List of PredictionResult objects in the same order.
        """
        return [self.predict_one(t) for t in texts]


# ---------------------------------------------------------------------------
# NOTE: This module is a stub created in Phase 1.
# It will be exercised with a fitted model in Phase 3.
# No predictions have been made yet.
# ---------------------------------------------------------------------------
