"""
scripts/run_e13_experiment.py
-----------------------------
Execute Experiment E13: Category Boundary & Hybrid Feature Improvement.

Pipeline:
- Word-level TF-IDF: ngram_range=(1,2), max_features=10,000, min_df=2, max_df=0.95, sublinear_tf=True
- Char-level TF-IDF: analyzer='char', ngram_range=(3,5), max_features=5,000, min_df=2, max_df=0.95, sublinear_tf=True
- Combined via sklearn.pipeline.FeatureUnion
- Estimator: LinearSVC(class_weight='balanced', random_state=42, max_iter=2000)
- Calibration: CalibratedClassifierCV(method='sigmoid', cv=5)
- Hyperparameter sweep: C in [0.2, 0.5, 1.0, 2.0]

Strict evaluation rules:
- Train split: data/processed/train.csv (N=908)
- Validation split: data/processed/val.csv (N=183)
- Held-out test split: NEVER LOADED OR ACCESSED.
"""

from __future__ import annotations

import datetime
import hashlib
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, os.path.abspath("."))

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC

from src.classification.evaluate import (
    compute_calibration_metrics,
    compute_classification_metrics,
)
from src.data.preprocess import (
    build_char_tfidf_vectorizer,
    build_word_tfidf_vectorizer,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

CATEGORY_NAMES = {
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


def get_file_hash(path: Path) -> str:
    hasher = hashlib.md5()
    with open(path, "rb") as f:
        hasher.update(f.read())
    return hasher.hexdigest()


def build_hybrid_pipeline(c_value: float) -> Pipeline:
    word_vec = build_word_tfidf_vectorizer(
        max_features=10000,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95,
        sublinear_tf=True,
    )
    char_vec = build_char_tfidf_vectorizer(
        max_features=5000,
        ngram_range=(3, 5),
        min_df=2,
        max_df=0.95,
        sublinear_tf=True,
    )
    union = FeatureUnion([
        ("word", word_vec),
        ("char", char_vec),
    ])
    base_svm = LinearSVC(
        C=c_value,
        class_weight="balanced",
        random_state=42,
        max_iter=2000,
    )
    calibrated_clf = CalibratedClassifierCV(
        estimator=base_svm,
        method="sigmoid",
        cv=5,
    )
    return Pipeline([
        ("features", union),
        ("clf", calibrated_clf),
    ])


def main() -> None:
    train_path = Path("data/processed/train.csv")
    val_path = Path("data/processed/val.csv")
    e2_path = Path("models/e2.joblib")

    logger.info("Loading train data from %s...", train_path)
    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)

    train_texts = train_df["complaint_text"].tolist()
    train_labels = train_df["category"].tolist()
    val_texts = val_df["complaint_text"].tolist()
    val_labels = val_df["category"].tolist()
    label_names = sorted(list(CATEGORY_NAMES.keys()))

    logger.info("Train samples: %d | Val samples: %d | Classes: %d", len(train_texts), len(val_texts), len(label_names))

    # Evaluate baseline E2 on val
    logger.info("Evaluating baseline E2...")
    e2_artifact = joblib.load(e2_path)
    e2_pipeline = e2_artifact["pipeline"]

    start = time.perf_counter()
    e2_preds = e2_pipeline.predict(val_texts)
    e2_probs = e2_pipeline.predict_proba(val_texts)
    e2_infer_ms = ((time.perf_counter() - start) / len(val_texts)) * 1000.0

    e2_metrics = compute_classification_metrics(val_labels, list(e2_preds), label_names)
    e2_calib = compute_calibration_metrics(val_labels, e2_probs, label_names)

    # Controlled sweep over C in [0.2, 0.5, 1.0, 2.0]
    c_candidates = [0.2, 0.5, 1.0, 2.0]
    sweep_results = []
    trained_pipelines = {}

    for c in c_candidates:
        logger.info("--- Testing E13 with C = %.2f ---", c)
        pipeline = build_hybrid_pipeline(c)

        # Train pipeline strictly on train_texts
        t0 = time.perf_counter()
        pipeline.fit(train_texts, train_labels)
        train_time = time.perf_counter() - t0

        # Inference on validation set
        t0_inf = time.perf_counter()
        preds = pipeline.predict(val_texts)
        probs = pipeline.predict_proba(val_texts)
        infer_ms = ((time.perf_counter() - t0_inf) / len(val_texts)) * 1000.0

        metrics = compute_classification_metrics(val_labels, list(preds), label_names)
        calib = compute_calibration_metrics(val_labels, probs, label_names)

        # Inspect Sample 33 and Sample 52
        p33 = preds[33]
        conf33 = np.max(probs[33])
        p52 = preds[52]
        conf52 = np.max(probs[52])

        # Identify all error indices
        errors = [i for i in range(len(val_labels)) if preds[i] != val_labels[i]]

        sweep_results.append({
            "C": c,
            "train_time_s": round(train_time, 3),
            "infer_ms_per_sample": round(infer_ms, 3),
            "accuracy": metrics["accuracy"],
            "macro_f1": metrics["macro_f1"],
            "weighted_f1": metrics["weighted_f1"],
            "ece": calib["ece"],
            "brier_score": calib["brier_score"],
            "log_loss": calib["log_loss"],
            "errors_count": len(errors),
            "error_indices": errors,
            "s33_pred": p33,
            "s33_conf": round(conf33, 4),
            "s52_pred": p52,
            "s52_conf": round(conf52, 4),
            "pipeline": pipeline,
            "per_class": metrics["per_class"],
            "preds": preds,
            "probs": probs,
        })
        logger.info("C=%.2f -> Acc: %.4f, Macro-F1: %.4f, ECE: %.4f, Errors: %d (S33=%s, S52=%s)",
                    c, metrics["accuracy"], metrics["macro_f1"], calib["ece"], len(errors), p33, p52)

    # Select best C: maximize Macro-F1, then Accuracy, then minimize ECE
    sweep_df = pd.DataFrame([
        {k: v for k, v in r.items() if k not in ["pipeline", "per_class", "preds", "probs"]}
        for r in sweep_results
    ])
    print("\n================== C-SWEEP COMPARISON ==================")
    print(sweep_df.to_string(index=False))

    best_result = sorted(
        sweep_results,
        key=lambda r: (r["macro_f1"], r["accuracy"], -r["ece"]),
        reverse=True,
    )[0]
    best_c = best_result["C"]
    best_pipeline = best_result["pipeline"]
    logger.info("Best C value selected: %.2f (Macro-F1=%.4f, Acc=%.4f)", best_c, best_result["macro_f1"], best_result["accuracy"])

    # Save model artifact
    models_dir = Path("models")
    e13_model_path = models_dir / "e13_hybrid.joblib"
    metadata = {
        "experiment_id": "E13",
        "method": "Hybrid TF-IDF (Word 1-2 + Char 3-5) + Linear SVM (Calibrated)",
        "model_type": "svm",
        "vectorizer_type": "hybrid_word_char",
        "word_max_features": 10000,
        "word_ngram_range": [1, 2],
        "char_max_features": 5000,
        "char_ngram_range": [3, 5],
        "C": best_c,
        "train_samples": len(train_texts),
        "val_samples": len(val_texts),
        "accuracy": round(best_result["accuracy"], 4),
        "macro_f1": round(best_result["macro_f1"], 4),
        "weighted_f1": round(best_result["weighted_f1"], 4),
        "calibration": {
            "brier_score": best_result["brier_score"],
            "log_loss": best_result["log_loss"],
            "ece": best_result["ece"],
        },
        "training_time_s": best_result["train_time_s"],
        "inference_ms_per_example": best_result["infer_ms_per_sample"],
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    joblib.dump({"pipeline": best_pipeline, "metadata": metadata}, e13_model_path)
    logger.info("Saved E13 model artifact to %s", e13_model_path)
    model_size_mb = os.path.getsize(e13_model_path) / (1024 * 1024)
    e2_size_mb = os.path.getsize(e2_path) / (1024 * 1024)

    # Save e13_model_comparison.csv
    comp_rows = [
        {
            "Metric": "Training Set Size",
            "E2 Baseline (Word TF-IDF)": 908,
            "E13 Hybrid (Word + Char)": 908,
            "Delta (E13 - E2)": "0 (identical base data)",
        },
        {
            "Metric": "Feature Count",
            "E2 Baseline (Word TF-IDF)": "10,000 (Word 1-2)",
            "E13 Hybrid (Word + Char)": "15,000 (10k Word + 5k Char)",
            "Delta (E13 - E2)": "+5,000 features",
        },
        {
            "Metric": "Optimal C Regularization",
            "E2 Baseline (Word TF-IDF)": "1.0",
            "E13 Hybrid (Word + Char)": f"{best_c:.1f}",
            "Delta (E13 - E2)": f"{best_c - 1.0:+.1f}",
        },
        {
            "Metric": "Validation Accuracy",
            "E2 Baseline (Word TF-IDF)": f"{e2_metrics['accuracy']:.4f}",
            "E13 Hybrid (Word + Char)": f"{best_result['accuracy']:.4f}",
            "Delta (E13 - E2)": f"{best_result['accuracy'] - e2_metrics['accuracy']:+.4f}",
        },
        {
            "Metric": "Validation Macro-F1",
            "E2 Baseline (Word TF-IDF)": f"{e2_metrics['macro_f1']:.4f}",
            "E13 Hybrid (Word + Char)": f"{best_result['macro_f1']:.4f}",
            "Delta (E13 - E2)": f"{best_result['macro_f1'] - e2_metrics['macro_f1']:+.4f}",
        },
        {
            "Metric": "Validation Weighted-F1",
            "E2 Baseline (Word TF-IDF)": f"{e2_metrics['weighted_f1']:.4f}",
            "E13 Hybrid (Word + Char)": f"{best_result['weighted_f1']:.4f}",
            "Delta (E13 - E2)": f"{best_result['weighted_f1'] - e2_metrics['weighted_f1']:+.4f}",
        },
        {
            "Metric": "Expected Calibration Error (ECE)",
            "E2 Baseline (Word TF-IDF)": f"{e2_calib['ece']:.4f}",
            "E13 Hybrid (Word + Char)": f"{best_result['ece']:.4f}",
            "Delta (E13 - E2)": f"{best_result['ece'] - e2_calib['ece']:+.4f}",
        },
        {
            "Metric": "Brier Score",
            "E2 Baseline (Word TF-IDF)": f"{e2_calib['brier_score']:.4f}",
            "E13 Hybrid (Word + Char)": f"{best_result['brier_score']:.4f}",
            "Delta (E13 - E2)": f"{best_result['brier_score'] - e2_calib['brier_score']:+.4f}",
        },
        {
            "Metric": "Log Loss",
            "E2 Baseline (Word TF-IDF)": f"{e2_calib['log_loss']:.4f}",
            "E13 Hybrid (Word + Char)": f"{best_result['log_loss']:.4f}",
            "Delta (E13 - E2)": f"{best_result['log_loss'] - e2_calib['log_loss']:+.4f}",
        },
        {
            "Metric": "Inference Latency (ms/sample)",
            "E2 Baseline (Word TF-IDF)": f"{e2_infer_ms:.2f} ms",
            "E13 Hybrid (Word + Char)": f"{best_result['infer_ms_per_sample']:.2f} ms",
            "Delta (E13 - E2)": f"{best_result['infer_ms_per_sample'] - e2_infer_ms:+.2f} ms",
        },
        {
            "Metric": "Model File Size",
            "E2 Baseline (Word TF-IDF)": f"{e2_size_mb:.2f} MB",
            "E13 Hybrid (Word + Char)": f"{model_size_mb:.2f} MB",
            "Delta (E13 - E2)": f"{model_size_mb - e2_size_mb:+.2f} MB",
        },
        {
            "Metric": "Sample 33 Prediction (True: C06)",
            "E2 Baseline (Word TF-IDF)": f"C07 (conf=0.2507) [Error]",
            "E13 Hybrid (Word + Char)": f"{best_result['s33_pred']} (conf={best_result['s33_conf']:.4f})",
            "Delta (E13 - E2)": "Corrected" if best_result["s33_pred"] == "C06" else "Incorrect",
        },
        {
            "Metric": "Sample 52 Prediction (True: C06)",
            "E2 Baseline (Word TF-IDF)": f"C06 (conf=0.2371) [Correct]",
            "E13 Hybrid (Word + Char)": f"{best_result['s52_pred']} (conf={best_result['s52_conf']:.4f})",
            "Delta (E13 - E2)": "Maintained" if best_result["s52_pred"] == "C06" else "Regressed",
        },
    ]
    comp_df = pd.DataFrame(comp_rows)
    comp_csv_path = Path("reports/e13_model_comparison.csv")
    comp_df.to_csv(comp_csv_path, index=False, encoding="utf-8")
    logger.info("Saved comparison table to %s", comp_csv_path)

    # Save per-class classification report
    p2 = e2_metrics["per_class"]
    p13 = best_result["per_class"]
    per_class_rows = []
    for cat in label_names:
        per_class_rows.append({
            "category": cat,
            "category_name": CATEGORY_NAMES[cat],
            "support": int(p2.loc[cat, "support"]) if cat in p2.index else 0,
            "e2_precision": round(float(p2.loc[cat, "precision"]), 4) if cat in p2.index else 0.0,
            "e13_precision": round(float(p13.loc[cat, "precision"]), 4) if cat in p13.index else 0.0,
            "e2_recall": round(float(p2.loc[cat, "recall"]), 4) if cat in p2.index else 0.0,
            "e13_recall": round(float(p13.loc[cat, "recall"]), 4) if cat in p13.index else 0.0,
            "e2_f1": round(float(p2.loc[cat, "f1-score"]), 4) if cat in p2.index else 0.0,
            "e13_f1": round(float(p13.loc[cat, "f1-score"]), 4) if cat in p13.index else 0.0,
            "f1_delta": round(float(p13.loc[cat, "f1-score"] - p2.loc[cat, "f1-score"]), 4) if cat in p13.index and cat in p2.index else 0.0,
        })
    per_class_df = pd.DataFrame(per_class_rows)
    report_csv_path = Path("reports/e13_classification_report.csv")
    per_class_df.to_csv(report_csv_path, index=False, encoding="utf-8")
    logger.info("Saved per-class classification report to %s", report_csv_path)

    # Plot Confusion Matrix
    from sklearn.metrics import confusion_matrix
    cm = confusion_matrix(val_labels, best_result["preds"], labels=label_names)
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=[f"{c}" for c in label_names],
        yticklabels=[f"{c}" for c in label_names],
    )
    plt.title(f"Experiment E13 Confusion Matrix (C={best_c}, Validation N=183)", fontsize=13, pad=12)
    plt.xlabel("Predicted Category", fontsize=11)
    plt.ylabel("True Category", fontsize=11)
    plt.tight_layout()
    cm_path = Path("reports/e13_confusion_matrix.png")
    plt.savefig(cm_path, dpi=200)
    plt.close()
    logger.info("Saved confusion matrix heatmap to %s", cm_path)

    # Detailed Inspection of Errors
    print("\n================== DETAILED ERROR INSPECTION (E13) ==================")
    if best_result["errors_count"] == 0:
        print("PERFECT SCORE: 183 / 183 (100.0%) correct on the validation split!")
    else:
        for idx in best_result["error_indices"]:
            print(f"Sample {idx}: True={val_labels[idx]} ({CATEGORY_NAMES[val_labels[idx]]}) | Pred={best_result['preds'][idx]} (conf={np.max(best_result['probs'][idx]):.4f})")
            print(f"Text: {val_texts[idx]}\n")


if __name__ == "__main__":
    main()

