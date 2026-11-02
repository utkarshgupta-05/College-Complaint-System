"""
scripts/evaluate_e11_validation.py
----------------------------------
Compare Experiment E2 baseline vs Experiment E11 augmented on the
UNCHANGED validation split (data/processed/val.csv, N=183).

Strictly enforces test-set quarantine: data/processed/test.csv is NOT loaded.
"""

from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, os.path.abspath("."))

import joblib
import numpy as np
import pandas as pd

from src.classification.evaluate import (
    compute_calibration_metrics,
    compute_classification_metrics,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

CATEGORY_MAP = {
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


def evaluate_model(
    model_path: Path,
    val_texts: list[str],
    val_labels: list[str],
    label_names: list[str],
) -> dict[str, Any]:
    """Evaluate a fitted model pipeline on validation data."""
    logger.info("Loading model from %s...", model_path)
    artifact = joblib.load(model_path)
    pipeline = artifact["pipeline"]
    meta = artifact.get("metadata", {})

    # Warm-up inference
    _ = pipeline.predict(val_texts[:5])

    # Measure inference time over entire validation set
    start_time = time.perf_counter()
    y_pred = pipeline.predict(val_texts)
    y_prob = pipeline.predict_proba(val_texts)
    infer_total = time.perf_counter() - start_time
    ms_per_sample = (infer_total / len(val_texts)) * 1000.0

    # Compute classification metrics
    class_metrics = compute_classification_metrics(val_labels, list(y_pred), label_names)

    # Compute calibration metrics
    calib_metrics = compute_calibration_metrics(val_labels, y_prob, label_names)

    return {
        "pipeline": pipeline,
        "metadata": meta,
        "y_pred": y_pred,
        "y_prob": y_prob,
        "accuracy": class_metrics["accuracy"],
        "macro_f1": class_metrics["macro_f1"],
        "weighted_f1": class_metrics["weighted_f1"],
        "per_class_df": class_metrics["per_class"],
        "calib_metrics": calib_metrics,
        "ms_per_sample": round(ms_per_sample, 4),
    }


def main() -> None:
    val_path = Path("data/processed/val.csv")
    e2_path = Path("models/e2.joblib")
    e11_path = Path("models/e11_augmented.joblib")
    output_csv = Path("reports/e11_classification_comparison.csv")

    logger.info("Loading validation data from %s...", val_path)
    val_df = pd.read_csv(val_path)
    val_texts = val_df["complaint_text"].tolist()
    val_labels = val_df["category"].tolist()
    label_names = sorted(list(CATEGORY_MAP.keys()))

    logger.info("Validation samples: %d. Classes: %d.", len(val_texts), len(label_names))

    # Evaluate E2
    logger.info("--- Evaluating E2 Baseline ---")
    res_e2 = evaluate_model(e2_path, val_texts, val_labels, label_names)

    # Evaluate E11
    logger.info("--- Evaluating E11 Augmented ---")
    res_e11 = evaluate_model(e11_path, val_texts, val_labels, label_names)

    # Build comparison summary table
    summary_rows = [
        {
            "Metric": "Training Set Size",
            "E2 Baseline (Synthetic)": 908,
            "E11 Augmented": 1524,
            "Delta (E11 - E2)": "+616 (+67.8%)",
        },
        {
            "Metric": "Validation Accuracy",
            "E2 Baseline (Synthetic)": f"{res_e2['accuracy']:.4f}",
            "E11 Augmented": f"{res_e11['accuracy']:.4f}",
            "Delta (E11 - E2)": f"{res_e11['accuracy'] - res_e2['accuracy']:+.4f}",
        },
        {
            "Metric": "Validation Macro-F1",
            "E2 Baseline (Synthetic)": f"{res_e2['macro_f1']:.4f}",
            "E11 Augmented": f"{res_e11['macro_f1']:.4f}",
            "Delta (E11 - E2)": f"{res_e11['macro_f1'] - res_e2['macro_f1']:+.4f}",
        },
        {
            "Metric": "Validation Weighted-F1",
            "E2 Baseline (Synthetic)": f"{res_e2['weighted_f1']:.4f}",
            "E11 Augmented": f"{res_e11['weighted_f1']:.4f}",
            "Delta (E11 - E2)": f"{res_e11['weighted_f1'] - res_e2['weighted_f1']:+.4f}",
        },
        {
            "Metric": "Expected Calibration Error (ECE)",
            "E2 Baseline (Synthetic)": f"{res_e2['calib_metrics']['ece']:.4f}",
            "E11 Augmented": f"{res_e11['calib_metrics']['ece']:.4f}",
            "Delta (E11 - E2)": f"{res_e11['calib_metrics']['ece'] - res_e2['calib_metrics']['ece']:+.4f}",
        },
        {
            "Metric": "Brier Score",
            "E2 Baseline (Synthetic)": f"{res_e2['calib_metrics']['brier_score']:.4f}",
            "E11 Augmented": f"{res_e11['calib_metrics']['brier_score']:.4f}",
            "Delta (E11 - E2)": f"{res_e11['calib_metrics']['brier_score'] - res_e2['calib_metrics']['brier_score']:+.4f}",
        },
        {
            "Metric": "Log Loss",
            "E2 Baseline (Synthetic)": f"{res_e2['calib_metrics']['log_loss']:.4f}",
            "E11 Augmented": f"{res_e11['calib_metrics']['log_loss']:.4f}",
            "Delta (E11 - E2)": f"{res_e11['calib_metrics']['log_loss'] - res_e2['calib_metrics']['log_loss']:+.4f}",
        },
        {
            "Metric": "Inference Latency (ms/sample)",
            "E2 Baseline (Synthetic)": f"{res_e2['ms_per_sample']:.2f} ms",
            "E11 Augmented": f"{res_e11['ms_per_sample']:.2f} ms",
            "Delta (E11 - E2)": f"{res_e11['ms_per_sample'] - res_e2['ms_per_sample']:+.2f} ms",
        },
    ]

    summary_df = pd.DataFrame(summary_rows)
    print("\n================== OVERALL METRICS COMPARISON ==================")
    print(summary_df.to_string(index=False))

    # Per-class breakdown
    per_class_rows = []
    p2 = res_e2["per_class_df"]
    p11 = res_e11["per_class_df"]

    for cat in label_names:
        name = CATEGORY_MAP[cat]
        f1_e2 = p2.loc[cat, "f1-score"] if cat in p2.index else 0.0
        f1_e11 = p11.loc[cat, "f1-score"] if cat in p11.index else 0.0
        prec_e2 = p2.loc[cat, "precision"] if cat in p2.index else 0.0
        prec_e11 = p11.loc[cat, "precision"] if cat in p11.index else 0.0
        rec_e2 = p2.loc[cat, "recall"] if cat in p2.index else 0.0
        rec_e11 = p11.loc[cat, "recall"] if cat in p11.index else 0.0
        support = int(p2.loc[cat, "support"]) if cat in p2.index else 0

        per_class_rows.append({
            "Category Code": cat,
            "Category Name": name,
            "Support (Val)": support,
            "E2 Precision": round(prec_e2, 4),
            "E11 Precision": round(prec_e11, 4),
            "E2 Recall": round(rec_e2, 4),
            "E11 Recall": round(rec_e11, 4),
            "E2 F1": round(f1_e2, 4),
            "E11 F1": round(f1_e11, 4),
            "F1 Delta": round(f1_e11 - f1_e2, 4),
        })

    per_class_df = pd.DataFrame(per_class_rows)
    print("\n================== PER-CLASS F1 COMPARISON ==================")
    print(per_class_df.to_string(index=False))

    # Save detailed comparison table to CSV
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    per_class_df.to_csv(output_csv, index=False, encoding="utf-8")
    logger.info("Saved comparison table to %s", output_csv)

    # Check misclassifications in E11 vs E2
    diff_mask = res_e2["y_pred"] != res_e11["y_pred"]
    if np.any(diff_mask):
        print("\n================== PREDICTION DIFFERENCES ON VAL ==================")
        for i in np.where(diff_mask)[0]:
            print(f"Sample {i}: True={val_labels[i]} | E2={res_e2['y_pred'][i]} | E11={res_e11['y_pred'][i]}")
            print(f"Text: {val_texts[i][:120]}...\n")
    else:
        print("\nNo prediction differences between E2 and E11 on the validation set!")


if __name__ == "__main__":
    main()

