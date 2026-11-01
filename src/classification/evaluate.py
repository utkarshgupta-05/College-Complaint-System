"""
src/classification/evaluate.py
--------------------------------
Evaluation utilities for the complaint classifier.

Computes:
  - Accuracy
  - Per-class Precision, Recall, F1
  - Macro-F1 and Weighted-F1 (primary metrics)
  - Confusion matrix
  - Training and inference time (passed in, not measured here)
  - Confidence distribution analysis
  - Error analysis: sample of misclassified complaints

All results are returned as structured dicts so they can be written to
reports/experiment_results.csv and docs/experiment-log.md.

IMPORTANT: Evaluation must ALWAYS use held-out data that was NOT used to
fit the vectorizer or tune the model. This module does not enforce this —
the caller is responsible for passing the correct split.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)

logger = logging.getLogger(__name__)


def compute_classification_metrics(
    y_true: list[str],
    y_pred: list[str],
    label_names: list[str],
) -> dict[str, Any]:
    """Compute all required classification metrics.

    Args:
        y_true: Ground-truth category labels.
        y_pred: Predicted category labels.
        label_names: Complete list of category labels (for confusion matrix ordering).

    Returns:
        Dict with keys: accuracy, macro_f1, weighted_f1, per_class (DataFrame),
        classification_report_str.
    """
    accuracy = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)
    report_str = classification_report(
        y_true, y_pred, labels=label_names, zero_division=0
    )
    report_dict = classification_report(
        y_true, y_pred, labels=label_names, output_dict=True, zero_division=0
    )
    per_class_df = pd.DataFrame(report_dict).T

    logger.info("Accuracy: %.4f", accuracy)
    logger.info("Macro-F1: %.4f", macro_f1)
    logger.info("Weighted-F1: %.4f", weighted_f1)

    return {
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "per_class": per_class_df,
        "classification_report": report_str,
    }


def plot_confusion_matrix(
    y_true: list[str],
    y_pred: list[str],
    label_names: list[str],
    output_path: str | Path | None = None,
    title: str = "Confusion Matrix",
) -> plt.Figure:
    """Plot and optionally save a confusion matrix heatmap.

    Args:
        y_true: Ground-truth labels.
        y_pred: Predicted labels.
        label_names: Ordered list of category labels.
        output_path: If provided, save the figure to this path.
        title: Plot title.

    Returns:
        matplotlib Figure object.
    """
    cm = confusion_matrix(y_true, y_pred, labels=label_names)
    fig, ax = plt.subplots(figsize=(12, 10))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=label_names,
        yticklabels=label_names,
        ax=ax,
    )
    ax.set_xlabel("Predicted Label")
    ax.set_ylabel("True Label")
    ax.set_title(title)
    plt.tight_layout()

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        logger.info("Confusion matrix saved to %s", output_path)

    return fig


def analyze_errors(
    texts: list[str],
    y_true: list[str],
    y_pred: list[str],
    confidences: list[float],
    n_samples: int = 20,
) -> pd.DataFrame:
    """Extract a sample of misclassified complaints for error analysis.

    Args:
        texts: Original complaint texts.
        y_true: True labels.
        y_pred: Predicted labels.
        confidences: Model confidence scores for each prediction.
        n_samples: Number of error examples to return.

    Returns:
        DataFrame with columns: complaint_text, true_label, predicted_label,
        confidence, sorted by confidence (lowest first for high-interest errors).
    """
    errors = [
        {
            "complaint_text": text,
            "true_label": true,
            "predicted_label": pred,
            "confidence": conf,
        }
        for text, true, pred, conf in zip(texts, y_true, y_pred, confidences)
        if true != pred
    ]

    error_df = pd.DataFrame(errors)
    if error_df.empty:
        logger.info("No misclassifications found.")
        return error_df

    # Sort by confidence so we can inspect high-confidence errors (most concerning)
    error_df = error_df.sort_values("confidence", ascending=False)
    logger.info(
        "Total misclassifications: %d / %d (%.1f%%)",
        len(error_df), len(texts), 100 * len(error_df) / len(texts),
    )
    return error_df.head(n_samples)


def plot_confidence_distribution(
    confidences: list[float],
    y_true: list[str],
    y_pred: list[str],
    threshold: float = 0.60,
    output_path: str | Path | None = None,
) -> plt.Figure:
    """Plot the distribution of model confidence scores, colored by correctness.

    Args:
        confidences: Confidence scores for each prediction.
        y_true: True labels.
        y_pred: Predicted labels.
        threshold: Confidence threshold for flagging uncertain predictions.
        output_path: If provided, save the figure.

    Returns:
        matplotlib Figure.
    """
    correct = [t == p for t, p in zip(y_true, y_pred)]
    df = pd.DataFrame({"confidence": confidences, "correct": correct})

    fig, ax = plt.subplots(figsize=(10, 5))
    df[df["correct"]]["confidence"].hist(
        ax=ax, bins=20, alpha=0.6, label="Correct", color="steelblue"
    )
    df[~df["correct"]]["confidence"].hist(
        ax=ax, bins=20, alpha=0.6, label="Incorrect", color="salmon"
    )
    ax.axvline(threshold, color="black", linestyle="--", label=f"Threshold={threshold}")
    ax.set_xlabel("Confidence Score")
    ax.set_ylabel("Count")
    ax.set_title("Confidence Distribution by Prediction Correctness")
    ax.legend()
    plt.tight_layout()

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        logger.info("Confidence distribution saved to %s", output_path)

    return fig



def compute_calibration_metrics(
    y_true: list[str],
    y_prob: np.ndarray,
    label_names: list[str],
) -> dict[str, float]:
    """Compute calibration quality metrics for predicted probability distributions.

    Calculates:
      1. Multiclass Brier score: Mean squared error of probabilities vs one-hot targets.
      2. Multiclass Log Loss: Cross-entropy penalty.
      3. Expected Calibration Error (ECE): Weighted average difference between
         binned confidence and binned accuracy (10 bins).

    Args:
        y_true: Ground-truth category strings.
        y_prob: Array of predicted probability distributions of shape (N, K).
        label_names: Ordered category label names corresponding to y_prob columns.

    Returns:
        dict: {'brier_score': float, 'log_loss': float, 'ece': float}
    """
    from sklearn.metrics import log_loss
    from sklearn.preprocessing import label_binarize

    # One-hot encode ground truth
    y_true_binary = label_binarize(y_true, classes=label_names)
    if y_true_binary.shape[1] == 1 and len(label_names) == 2:
        y_true_binary = np.hstack([1 - y_true_binary, y_true_binary])

    # 1. Multiclass Brier Score: 1/N * sum((p - y)^2)
    brier_score = float(np.mean(np.sum((y_prob - y_true_binary) ** 2, axis=1)))

    # 2. Log Loss
    try:
        loss = float(log_loss(y_true, y_prob, labels=label_names))
    except Exception as e:
        logger.warning("Log loss computation failed: %s", e)
        loss = float("nan")

    # 3. Expected Calibration Error (ECE) with 10 bins
    confidences = np.max(y_prob, axis=1)
    predictions = [label_names[idx] for idx in np.argmax(y_prob, axis=1)]
    accuracies = np.array([p == t for p, t in zip(predictions, y_true)], dtype=float)

    n_bins = 10
    bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    total_samples = len(y_true)

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        in_bin = (confidences > bin_lower) & (confidences <= bin_upper)
        prop_in_bin = np.sum(in_bin)
        if prop_in_bin > 0:
            avg_confidence = float(np.mean(confidences[in_bin]))
            avg_accuracy = float(np.mean(accuracies[in_bin]))
            ece += (prop_in_bin / total_samples) * abs(avg_accuracy - avg_confidence)

    return {
        "brier_score": round(brier_score, 4),
        "log_loss": round(loss, 4),
        "ece": round(float(ece), 4),
    }


def evaluate_confidence_thresholds(
    y_true: list[str],
    y_pred: list[str],
    confidences: list[float],
    thresholds: list[float] | None = None,
) -> pd.DataFrame:
    """Evaluate how varying the confidence threshold affects automatic routing vs human review.

    For each threshold theta:
      - Predictions with confidence >= theta:
          Auto-routed. We measure count and auto-routing accuracy.
      - Predictions with confidence < theta:
          Sent to human review. We measure:
            - Error Recall (% of all misclassifications caught by review queue)
            - Review Queue Precision (% of review queue that are actual errors)
            - False Review Rate (% of correct predictions needlessly flagged)

    Returns:
        pd.DataFrame with columns: threshold, auto_routed_pct, auto_accuracy,
        review_pct, error_recall, false_review_rate
    """
    if thresholds is None:
        thresholds = [0.40, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.90]

    conf_arr = np.array(confidences)
    is_correct = np.array([p == t for p, t in zip(y_pred, y_true)])
    is_error = ~is_correct
    total_samples = len(y_true)
    total_errors = np.sum(is_error)

    rows = []
    for th in thresholds:
        auto_mask = conf_arr >= th
        review_mask = ~auto_mask

        n_auto = np.sum(auto_mask)
        n_review = np.sum(review_mask)

        auto_acc = float(np.mean(is_correct[auto_mask])) if n_auto > 0 else 0.0
        errors_caught = np.sum(is_error[review_mask])
        error_recall = float(errors_caught / total_errors) if total_errors > 0 else 1.0

        correct_flagged = np.sum(is_correct[review_mask])
        total_correct = np.sum(is_correct)
        false_review_rate = float(correct_flagged / total_correct) if total_correct > 0 else 0.0

        rows.append({
            "threshold": th,
            "auto_routed_pct": round(float(n_auto / total_samples) * 100, 1),
            "auto_accuracy": round(auto_acc * 100, 2),
            "review_pct": round(float(n_review / total_samples) * 100, 1),
            "error_recall": round(error_recall * 100, 1),
            "false_review_rate": round(false_review_rate * 100, 2),
        })

    return pd.DataFrame(rows)


def plot_threshold_tradeoff(
    threshold_df: pd.DataFrame,
    output_path: str | Path | None = None,
) -> plt.Figure:
    """Plot the trade-off curve between Error Recall and Automation Rate."""
    fig, ax1 = plt.subplots(figsize=(8, 4.5))

    color1 = "#2b6cb0"
    color2 = "#c53030"

    ax1.set_xlabel("Confidence Threshold (θ)", fontsize=11)
    ax1.set_ylabel("Auto-Routed Coverage (%)", color=color1, fontsize=11)
    line1 = ax1.plot(threshold_df["threshold"], threshold_df["auto_routed_pct"], color=color1, marker="o", label="Auto Coverage (%)")
    ax1.tick_params(axis="y", labelcolor=color1)

    ax2 = ax1.twinx()
    ax2.set_ylabel("Error Detection Recall (%)", color=color2, fontsize=11)
    line2 = ax2.plot(threshold_df["threshold"], threshold_df["error_recall"], color=color2, marker="s", linestyle="--", label="Error Recall (%)")
    ax2.tick_params(axis="y", labelcolor=color2)
    ax2.set_ylim(-5, 105)

    # Highlight recommended threshold range (0.60)
    ax1.axvline(0.60, color="#4a5568", linestyle=":", alpha=0.8, label="Selected θ=0.60")

    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc="center left")
    plt.title("Uncertainty Threshold Trade-off: Coverage vs Error Detection", fontsize=12, fontweight="bold", pad=10)
    plt.tight_layout()

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150)
        logger.info("Threshold plot saved to %s", output_path)

    return fig


def plot_model_comparison(
    comparison_df: pd.DataFrame,
    output_path: str | Path | None = None,
) -> plt.Figure:
    """Generate a grouped bar chart comparing Macro-F1 and Latency across experiments."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

    # Plot 1: Macro-F1 comparison
    bars1 = ax1.bar(
        comparison_df["experiment_id"],
        comparison_df["macro_f1"],
        color=["#2b6cb0", "#319795", "#d69e2e", "#805ad5"][:len(comparison_df)],
        edgecolor="#1a202c",
    )
    ax1.set_title("Validation Macro-F1 by Experiment", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Macro-F1 Score")
    ax1.set_ylim(0.90, 1.01)
    for b in bars1:
        yval = b.get_height()
        ax1.text(b.get_x() + b.get_width() / 2, yval + 0.002, f"{yval:.4f}", ha="center", va="bottom", fontsize=9)

    # Plot 2: Inference Latency
    bars2 = ax2.bar(
        comparison_df["experiment_id"],
        comparison_df["inference_time_ms_per_example"],
        color="#4a5568",
        edgecolor="#1a202c",
    )
    ax2.set_title("Inference Latency (ms / complaint)", fontsize=12, fontweight="bold")
    ax2.set_ylabel("Latency (ms)")
    for b in bars2:
        yval = b.get_height()
        ax2.text(b.get_x() + b.get_width() / 2, yval + 0.005, f"{yval:.3f} ms", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150)
        logger.info("Model comparison plot saved to %s", output_path)

    return fig

