"""
src/classification/train.py
----------------------------
Train complaint classification models.

IMPORTANT — data leakage prevention:
  1. Split data BEFORE calling any fit() method.
  2. Fit the TF-IDF vectorizer on training data ONLY.
  3. Apply the fitted vectorizer to val and test data using transform() only.
  4. Do NOT use validation or test data to select hyperparameters without
     documenting the search clearly (use cross-validation on training data).
  5. The test split must NOT be evaluated until final model selection is done.

Experiments implemented here:
  E1 — TF-IDF (word n-grams) + Logistic Regression
  E2 — TF-IDF (word n-grams) + Linear SVM (with Platt calibration)
  E3 — TF-IDF (word n-grams) + Multinomial Naive Bayes
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import yaml
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

logger = logging.getLogger(__name__)


def load_config(config_path: str | Path = "config.yaml") -> dict:
    """Load project configuration."""
    with open(config_path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def build_logreg_pipeline(
    vectorizer,
    *,
    C: float = 1.0,
    max_iter: int = 1000,
    class_weight: str | None = "balanced",
    random_state: int = 42,
) -> Pipeline:
    """Build a TF-IDF + Logistic Regression pipeline (Experiment E1).

    Args:
        vectorizer: An UNFITTED TfidfVectorizer (from preprocess.py).
        C: Inverse regularization strength.
        max_iter: Maximum number of solver iterations.
        class_weight: 'balanced' compensates for class imbalance.
        random_state: Random seed for reproducibility.

    Returns:
        sklearn Pipeline (not yet fitted).
    """
    clf = LogisticRegression(
        C=C,
        max_iter=max_iter,
        class_weight=class_weight,
        solver="lbfgs",
        random_state=random_state,
    )
    return Pipeline([("tfidf", vectorizer), ("clf", clf)])


def build_svm_pipeline(
    vectorizer,
    *,
    C: float = 1.0,
    class_weight: str | None = "balanced",
    calibration_method: str = "sigmoid",
    random_state: int = 42,
) -> Pipeline:
    """Build a TF-IDF + Linear SVM pipeline (Experiment E2).

    LinearSVC does not natively produce probabilities.
    CalibratedClassifierCV wraps it to produce calibrated probability estimates
    via Platt scaling (sigmoid) or isotonic regression.

    Args:
        vectorizer: An UNFITTED TfidfVectorizer.
        C: Regularization parameter.
        class_weight: 'balanced' for imbalanced data.
        calibration_method: 'sigmoid' (Platt) or 'isotonic'.
        random_state: Random seed.

    Returns:
        sklearn Pipeline with calibrated SVM (not yet fitted).
    """
    base_svm = LinearSVC(
        C=C,
        class_weight=class_weight,
        random_state=random_state,
        max_iter=2000,
    )
    calibrated_svm = CalibratedClassifierCV(base_svm, method=calibration_method, cv=5)
    return Pipeline([("tfidf", vectorizer), ("clf", calibrated_svm)])


def build_naive_bayes_pipeline(
    vectorizer,
    *,
    alpha: float = 1.0,
) -> Pipeline:
    """Build a TF-IDF + Multinomial Naive Bayes pipeline (Experiment E3).

    Note: MultinomialNB requires non-negative feature values.
    Standard TF-IDF produces non-negative values, so this is safe.

    Args:
        vectorizer: An UNFITTED TfidfVectorizer.
        alpha: Laplace smoothing parameter.

    Returns:
        sklearn Pipeline (not yet fitted).
    """
    clf = MultinomialNB(alpha=alpha)
    return Pipeline([("tfidf", vectorizer), ("clf", clf)])


def train_pipeline(
    pipeline: Pipeline,
    train_texts: list[str],
    train_labels: list[str],
) -> tuple[Pipeline, float]:
    """Fit a pipeline on training data and record training time.

    Args:
        pipeline: Unfitted sklearn Pipeline.
        train_texts: List of normalized complaint texts (training split ONLY).
        train_labels: Corresponding category labels.

    Returns:
        Tuple of (fitted_pipeline, training_time_seconds).
    """
    logger.info("Starting training on %d examples...", len(train_texts))
    start = time.perf_counter()
    pipeline.fit(train_texts, train_labels)
    elapsed = time.perf_counter() - start
    logger.info("Training complete in %.2f seconds.", elapsed)
    return pipeline, elapsed


def save_pipeline(
    pipeline: Pipeline,
    output_path: str | Path,
    metadata: dict | None = None,
) -> None:
    """Save a fitted pipeline to disk using joblib.

    Args:
        pipeline: Fitted sklearn Pipeline.
        output_path: File path for the saved artifact (e.g., models/e1_logreg.joblib).
        metadata: Optional dict of experiment metadata to save alongside.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": pipeline, "metadata": metadata or {}}, output_path)
    logger.info("Pipeline saved to %s", output_path)


def load_pipeline(artifact_path: str | Path) -> tuple[Pipeline, dict]:
    """Load a fitted pipeline from disk.

    Args:
        artifact_path: Path to the saved .joblib artifact.

    Returns:
        Tuple of (fitted_pipeline, metadata_dict).
    """
    artifact_path = Path(artifact_path)
    if not artifact_path.exists():
        raise FileNotFoundError(f"Model artifact not found: {artifact_path}")
    artifact = joblib.load(artifact_path)
    return artifact["pipeline"], artifact.get("metadata", {})


def run_classification_experiment(
    experiment_id: str = "E1",
    model_type: str = "logreg",
    *,
    vectorizer_type: str = "word",
    config_path: str | Path = "config.yaml",
    data_dir: str | Path = "data/processed",
    models_dir: str | Path = "models",
    figures_dir: str | Path = "reports/figures",
    results_csv: str | Path = "reports/experiment_results.csv",
) -> dict[str, Any]:
    """Execute a complete classification training and evaluation run on validation data.

    Follows rigorous experimental protocol:
    1. Loads train.csv and val.csv (never touches test.csv).
    2. Vectorizer is fit ONLY on training texts.
    3. Model is trained and training time recorded.
    4. Evaluates on validation split, computing Accuracy, Macro-F1, Weighted-F1,
       and per-class performance.
    5. Saves confusion matrix heatmap and confidence distribution plots.
    6. Performs error analysis on misclassifications.
    7. Evaluates probability calibration and threshold tradeoffs.
    8. Persists fitted model pipeline to models_dir.
    9. Appends measured results to experiment_results.csv.

    Args:
        experiment_id: Identifier (e.g. 'E1', 'E2', 'E3', 'E4').
        model_type: 'logreg', 'svm', or 'nb'.
        vectorizer_type: 'word' or 'char'.
        config_path: Path to config.yaml.
        data_dir: Path to directory containing train.csv and val.csv.
        models_dir: Directory where trained artifacts will be saved.
        figures_dir: Directory where evaluation plots will be saved.
        results_csv: Path to experiment results CSV log.

    Returns:
        dict: Evaluated metrics and artifact paths.
    """
    from src.data.load_data import load_config, load_csv
    from src.data.preprocess import build_word_tfidf_vectorizer, build_char_tfidf_vectorizer
    from src.classification.evaluate import (
        compute_classification_metrics,
        plot_confusion_matrix,
        plot_confidence_distribution,
        analyze_errors,
        compute_calibration_metrics,
        evaluate_confidence_thresholds,
        plot_threshold_tradeoff,
    )
    from src.evaluation.metrics import append_experiment_result

    cfg = load_config(config_path)
    data_dir = Path(data_dir)
    models_dir = Path(models_dir)
    figures_dir = Path(figures_dir)
    models_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    text_col = cfg["data"]["text_column"]
    label_col = cfg["data"]["label_column"]
    valid_labels = list(cfg["categories"].keys())

    # Load train and validation splits (STRICT: test.csv is NOT loaded)
    train_df = load_csv(data_dir / "train.csv")
    val_df = load_csv(data_dir / "val.csv")

    train_texts = train_df[text_col].tolist()
    train_labels = train_df[label_col].tolist()
    val_texts = val_df[text_col].tolist()
    val_labels = val_df[label_col].tolist()

    # Build unfitted TF-IDF vectorizer using config settings
    if vectorizer_type.lower() == "char":
        char_cfg = cfg.get("tfidf", {}).get("char", {})
        vectorizer = build_char_tfidf_vectorizer(
            max_features=char_cfg.get("max_features", 15000),
            ngram_range=tuple(char_cfg.get("ngram_range", [3, 5])),
            min_df=char_cfg.get("min_df", 2),
            max_df=char_cfg.get("max_df", 0.95),
            sublinear_tf=char_cfg.get("sublinear_tf", True),
        )
        vec_desc = "TF-IDF (Char n-grams 3-5)"
    else:
        tfidf_cfg = cfg.get("tfidf", {}).get("word", {})
        vectorizer = build_word_tfidf_vectorizer(
            max_features=tfidf_cfg.get("max_features", 10000),
            ngram_range=tuple(tfidf_cfg.get("ngram_range", [1, 2])),
            min_df=tfidf_cfg.get("min_df", 2),
            max_df=tfidf_cfg.get("max_df", 0.95),
            sublinear_tf=tfidf_cfg.get("sublinear_tf", True),
        )
        vec_desc = "TF-IDF (Word n-grams 1-2)"

    seed = cfg["project"].get("random_seed", 42)

    # Instantiate chosen pipeline
    if model_type.lower() == "logreg":
        pipeline = build_logreg_pipeline(
            vectorizer,
            C=1.0,
            class_weight="balanced",
            random_state=seed,
        )
        method_name = f"{vec_desc} + Logistic Regression"
    elif model_type.lower() == "svm":
        pipeline = build_svm_pipeline(
            vectorizer,
            C=1.0,
            class_weight="balanced",
            calibration_method="sigmoid",
            random_state=seed,
        )
        method_name = f"{vec_desc} + Linear SVM (Calibrated)"
    elif model_type.lower() == "nb":
        pipeline = build_naive_bayes_pipeline(vectorizer, alpha=1.0)
        method_name = f"{vec_desc} + Multinomial Naive Bayes"
    else:
        raise ValueError(f"Unknown model_type: {model_type}. Choose 'logreg', 'svm', or 'nb'.")

    # Train model on train split ONLY
    logger.info("Executing %s (%s) on %d training samples...", experiment_id, method_name, len(train_texts))
    fitted_pipeline, train_time = train_pipeline(pipeline, train_texts, train_labels)

    # Evaluate inference time on validation split
    start_infer = time.perf_counter()
    val_preds = fitted_pipeline.predict(val_texts)
    val_probs = fitted_pipeline.predict_proba(val_texts)
    infer_time_total = time.perf_counter() - start_infer
    ms_per_example = (infer_time_total / len(val_texts)) * 1000.0

    confidences = np.max(val_probs, axis=1).tolist()

    # Compute metrics
    metrics = compute_classification_metrics(
        y_true=val_labels,
        y_pred=val_preds.tolist(),
        label_names=valid_labels,
    )

    # Calibration quality evaluation
    calib_metrics = compute_calibration_metrics(val_labels, val_probs, valid_labels)

    # Threshold trade-off evaluation
    threshold_df = evaluate_confidence_thresholds(val_labels, val_preds.tolist(), confidences)
    threshold_csv_path = Path("reports") / f"thresholds_{experiment_id.lower()}.csv"
    threshold_df.to_csv(threshold_csv_path, index=False)
    tradeoff_plot_path = figures_dir / f"tradeoff_{experiment_id.lower()}.png"
    plot_threshold_tradeoff(threshold_df, output_path=tradeoff_plot_path)

    # Save confusion matrix plot
    cm_path = figures_dir / f"cm_{experiment_id.lower()}.png"
    plot_confusion_matrix(
        y_true=val_labels,
        y_pred=val_preds.tolist(),
        label_names=valid_labels,
        output_path=cm_path,
        title=f"Confusion Matrix — {experiment_id} ({method_name})",
    )

    # Save confidence distribution plot
    conf_path = figures_dir / f"conf_{experiment_id.lower()}.png"
    plot_confidence_distribution(
        confidences=confidences,
        y_true=val_labels,
        y_pred=val_preds.tolist(),
        threshold=0.60,
        output_path=conf_path,
    )

    # Error analysis
    error_df = analyze_errors(
        texts=val_texts,
        y_true=val_labels,
        y_pred=val_preds.tolist(),
        confidences=confidences,
        n_samples=len(val_texts),
    )
    error_csv_path = Path("reports") / f"errors_{experiment_id.lower()}.csv"
    if not error_df.empty:
        error_df.to_csv(error_csv_path, index=False, encoding="utf-8")
        logger.info("Saved %d misclassifications to %s", len(error_df), error_csv_path)

    # Save fitted model artifact
    model_artifact_path = models_dir / f"{experiment_id.lower()}.joblib"
    metadata = {
        "experiment_id": experiment_id,
        "method": method_name,
        "model_type": model_type,
        "vectorizer_type": vectorizer_type,
        "train_samples": len(train_texts),
        "val_samples": len(val_texts),
        "accuracy": round(metrics["accuracy"], 4),
        "macro_f1": round(metrics["macro_f1"], 4),
        "weighted_f1": round(metrics["weighted_f1"], 4),
        "calibration": calib_metrics,
        "training_time_s": round(train_time, 3),
        "inference_ms_per_example": round(ms_per_example, 3),
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    save_pipeline(fitted_pipeline, model_artifact_path, metadata=metadata)

    # Append to experiment_results.csv
    experiment_record = {
        "experiment_id": experiment_id,
        "phase": "Phase 4" if experiment_id in ["E3", "E4"] else "Phase 3",
        "module": "Classification (Module A)",
        "method": method_name,
        "dataset": "college_complaints_synthetic.csv",
        "data_source": "synthetic",
        "primary_metric": "Macro-F1",
        "primary_metric_value": round(metrics["macro_f1"], 4),
        "macro_f1": round(metrics["macro_f1"], 4),
        "weighted_f1": round(metrics["weighted_f1"], 4),
        "accuracy": round(metrics["accuracy"], 4),
        "training_time_s": round(train_time, 3),
        "inference_time_ms_per_example": round(ms_per_example, 3),
        "notes": f"Validation split (N={len(val_texts)}). Zero test leakage.",
        "model_artifact_path": str(model_artifact_path),
    }
    append_experiment_result(results_csv, experiment_record)

    return {
        "experiment_id": experiment_id,
        "method": method_name,
        "metrics": metrics,
        "calibration": calib_metrics,
        "thresholds": threshold_df,
        "training_time_s": train_time,
        "inference_ms_per_example": ms_per_example,
        "error_count": len(error_df),
        "model_path": str(model_artifact_path),
        "cm_plot": str(cm_path),
        "conf_plot": str(conf_path),
        "tradeoff_plot": str(tradeoff_plot_path),
    }


def main() -> None:
    """CLI runner to execute classification baseline and improvement experiments."""
    import argparse
    from src.classification.evaluate import plot_model_comparison

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(description="Train and evaluate complaint classification models.")
    parser.add_argument(
        "--experiment",
        type=str,
        default="all",
        choices=["E1", "E2", "E3", "E4", "all"],
        help="Experiment to run: E1 (LogReg), E2 (Word SVM), E3 (Naive Bayes), E4 (Char SVM), or all.",
    )
    args = parser.parse_args()

    experiment_definitions = [
        ("E1", "logreg", "word"),
        ("E2", "svm", "word"),
        ("E3", "nb", "word"),
        ("E4", "svm", "char"),
    ]

    if args.experiment != "all":
        selected_exps = [e for e in experiment_definitions if e[0] == args.experiment]
    else:
        selected_exps = experiment_definitions

    print("\n" + "=" * 65)
    print("CLASSIFICATION EXPERIMENTS & MODEL IMPROVEMENT")
    print("=" * 65)

    comparison_rows = []
    for exp_id, m_type, v_type in selected_exps:
        res = run_classification_experiment(
            experiment_id=exp_id,
            model_type=m_type,
            vectorizer_type=v_type,
        )
        m = res["metrics"]
        cal = res["calibration"]
        print(f"\n--- Results for {exp_id} ({res['method']}) ---")
        print(f"Accuracy     : {m['accuracy']:.4f}")
        print(f"Macro-F1     : {m['macro_f1']:.4f}")
        print(f"Weighted-F1  : {m['weighted_f1']:.4f}")
        print(f"Brier Score  : {cal['brier_score']:.4f}")
        print(f"Log Loss     : {cal['log_loss']:.4f}")
        print(f"ECE (Calib)  : {cal['ece']:.4f}")
        print(f"Train Time   : {res['training_time_s']:.3f} s")
        print(f"Infer Time   : {res['inference_ms_per_example']:.3f} ms / example")
        print(f"Errors       : {res['error_count']} / 183 validation examples")
        print(f"Artifact     : {res['model_path']}")

        comparison_rows.append({
            "experiment_id": exp_id,
            "method": res["method"],
            "accuracy": m["accuracy"],
            "macro_f1": m["macro_f1"],
            "weighted_f1": m["weighted_f1"],
            "brier_score": cal["brier_score"],
            "log_loss": cal["log_loss"],
            "ece": cal["ece"],
            "training_time_s": res["training_time_s"],
            "inference_time_ms_per_example": res["inference_ms_per_example"],
            "error_count": res["error_count"],
        })

    # If multiple experiments were run, generate comparison plot and summary
    if len(comparison_rows) > 1:
        comp_df = pd.DataFrame(comparison_rows)
        comp_plot_path = Path("reports/figures/model_comparison.png")
        plot_model_comparison(comp_df, output_path=comp_plot_path)

        print("\n" + "=" * 65)
        print("FAIR MODEL COMPARISON TABLE (VALIDATION SPLIT, N=183)")
        print("=" * 65)
        display_cols = ["experiment_id", "accuracy", "macro_f1", "weighted_f1", "brier_score", "inference_time_ms_per_example", "error_count"]
        print(comp_df[display_cols].to_string(index=False))
        print(f"\nComparison chart saved to {comp_plot_path}")
        print("=" * 65)


if __name__ == "__main__":
    main()


