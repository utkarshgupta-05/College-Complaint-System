"""
src/evaluation/error_analysis.py
----------------------------------
Error investigation helpers — used to understand WHY models fail.

Understanding misclassifications is as important as measuring accuracy.
These utilities support structured error analysis required by all classification
and similarity experiments.
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def build_error_dataframe(
    texts: list[str],
    y_true: list[str],
    y_pred: list[str],
    confidences: list[float] | None = None,
    ids: list[Any] | None = None,
) -> pd.DataFrame:
    """Build a DataFrame of misclassified complaints.

    Args:
        texts: Complaint texts.
        y_true: Ground-truth labels.
        y_pred: Predicted labels.
        confidences: Model confidence scores (optional).
        ids: Complaint IDs (optional).

    Returns:
        DataFrame containing only misclassified rows, with columns:
        complaint_id (if provided), complaint_text, true_label,
        predicted_label, confidence (if provided), error_pair.
    """
    rows = []
    for i, (text, true, pred) in enumerate(zip(texts, y_true, y_pred)):
        if true == pred:
            continue
        row: dict[str, Any] = {
            "complaint_text": text,
            "true_label": true,
            "predicted_label": pred,
            "error_pair": f"{true} → {pred}",
        }
        if ids is not None:
            row["complaint_id"] = ids[i]
        if confidences is not None:
            row["confidence"] = confidences[i]
        rows.append(row)

    if not rows:
        logger.info("No misclassifications found.")
        return pd.DataFrame()

    error_df = pd.DataFrame(rows)
    if "confidence" in error_df:
        error_df = error_df.sort_values("confidence", ascending=False)
    return error_df


def most_common_error_pairs(
    error_df: pd.DataFrame,
    top_n: int = 10,
) -> pd.DataFrame:
    """Identify the most frequent (true_label → predicted_label) error pairs.

    Helps answer: "Which categories is the model most often confusing?"

    Args:
        error_df: DataFrame from build_error_dataframe().
        top_n: Number of most common pairs to return.

    Returns:
        DataFrame with columns: error_pair, count, percentage.
    """
    if error_df.empty or "error_pair" not in error_df.columns:
        return pd.DataFrame(columns=["error_pair", "count", "percentage"])

    counts = Counter(error_df["error_pair"])
    total = len(error_df)
    rows = [
        {"error_pair": pair, "count": cnt, "percentage": 100 * cnt / total}
        for pair, cnt in counts.most_common(top_n)
    ]
    return pd.DataFrame(rows)


def high_confidence_errors(
    error_df: pd.DataFrame,
    threshold: float = 0.80,
) -> pd.DataFrame:
    """Extract misclassifications where the model was highly confident.

    High-confidence errors are the most concerning because they indicate
    systematic failures, not uncertain borderline cases.

    Args:
        error_df: DataFrame from build_error_dataframe().
        threshold: Confidence level above which an error is 'high-confidence'.

    Returns:
        Subset of error_df where confidence >= threshold.
    """
    if error_df.empty or "confidence" not in error_df.columns:
        return pd.DataFrame()
    return error_df[error_df["confidence"] >= threshold].copy()


def category_error_rate(
    y_true: list[str],
    y_pred: list[str],
    label_names: list[str],
) -> pd.DataFrame:
    """Compute per-category error rate.

    Args:
        y_true: Ground-truth labels.
        y_pred: Predicted labels.
        label_names: All category labels to include in output.

    Returns:
        DataFrame with columns: category, total, correct, errors, error_rate.
    """
    rows = []
    for label in label_names:
        total = sum(1 for t in y_true if t == label)
        correct = sum(1 for t, p in zip(y_true, y_pred) if t == label and t == p)
        errors = total - correct
        error_rate = errors / total if total > 0 else 0.0
        rows.append({
            "category": label,
            "total": total,
            "correct": correct,
            "errors": errors,
            "error_rate": error_rate,
        })
    return pd.DataFrame(rows).sort_values("error_rate", ascending=False)


# ---------------------------------------------------------------------------
# NOTE: This module is a stub created in Phase 1.
# All functions will be exercised in Phase 3 error analysis.
# ---------------------------------------------------------------------------
