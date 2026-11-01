"""
tests/test_classification.py
----------------------------
Unit tests for complaint classification modules:
  - src/classification/train.py
  - src/classification/predict.py
  - src/classification/evaluate.py
"""

from pathlib import Path
import numpy as np
import pytest

from src.classification.train import (
    build_logreg_pipeline,
    build_svm_pipeline,
    train_pipeline,
    save_pipeline,
    load_pipeline,
)
from src.classification.predict import ComplaintClassifier, PredictionResult
from src.classification.evaluate import compute_classification_metrics, analyze_errors
from src.data.preprocess import build_word_tfidf_vectorizer

SAMPLE_CLASSES = ["C01", "C02", "C03"]


@pytest.fixture
def small_corpus():
    texts = [
        "Hostel room ceiling fan is screeching loudly at night.",
        "Hostel bed frame broken wooden slats.",
        "Water supply in hostel bathroom is completely cut off.",
        "No electricity and power cut in block B.",
        "Wi-Fi connection keeps dropping every five minutes.",
        "Internet is unreachable in computer laboratory.",
    ]
    labels = ["C01", "C01", "C02", "C02", "C03", "C03"]
    return texts, labels


class TestPipelineBuilders:
    def test_logreg_pipeline_structure(self):
        vec = build_word_tfidf_vectorizer(min_df=1)
        pipe = build_logreg_pipeline(vec, C=1.0)
        assert "tfidf" in pipe.named_steps
        assert "clf" in pipe.named_steps

    def test_svm_pipeline_structure(self):
        vec = build_word_tfidf_vectorizer(min_df=1)
        pipe = build_svm_pipeline(vec, C=1.0)
        assert "tfidf" in pipe.named_steps
        assert "clf" in pipe.named_steps


class TestTrainingAndSerialization:
    def test_train_and_save_load_roundtrip(self, small_corpus, tmp_path):
        texts, labels = small_corpus
        vec = build_word_tfidf_vectorizer(min_df=1)
        pipe = build_logreg_pipeline(vec, C=1.0)

        fitted_pipe, elapsed = train_pipeline(pipe, texts, labels)
        assert elapsed >= 0.0

        model_path = tmp_path / "test_model.joblib"
        metadata = {"experiment_id": "TEST", "accuracy": 1.0}
        save_pipeline(fitted_pipe, model_path, metadata=metadata)

        assert model_path.exists()
        loaded_pipe, loaded_meta = load_pipeline(model_path)
        assert loaded_meta.get("experiment_id") == "TEST"
        assert hasattr(loaded_pipe, "predict")


class TestInferenceClassifier:
    @pytest.fixture
    def fitted_classifier(self, small_corpus):
        texts, labels = small_corpus
        vec = build_word_tfidf_vectorizer(min_df=1)
        pipe = build_logreg_pipeline(vec, C=1.0)
        fitted, _ = train_pipeline(pipe, texts, labels)
        return ComplaintClassifier(fitted, label_names=SAMPLE_CLASSES, confidence_threshold=0.60)

    def test_predict_one_returns_valid_result(self, fitted_classifier):
        res = fitted_classifier.predict_one("Hostel ceiling fan broken")
        assert isinstance(res, PredictionResult)
        assert res.predicted_category in SAMPLE_CLASSES
        assert 0.0 <= res.confidence <= 1.0
        assert isinstance(res.low_confidence, bool)
        assert isinstance(res.needs_human_review, bool)

    def test_empty_text_routes_to_human_review(self, fitted_classifier):
        res = fitted_classifier.predict_one("")
        assert res.predicted_category == "C11"
        assert res.confidence == 0.0
        assert res.needs_human_review is True

    def test_predict_batch(self, fitted_classifier):
        texts = ["Hostel room broken", "Water supply cut"]
        results = fitted_classifier.predict_batch(texts)
        assert len(results) == 2
        assert all(isinstance(r, PredictionResult) for r in results)


class TestEvaluationMetrics:
    def test_metric_computation(self):
        y_true = ["C01", "C02", "C03", "C01"]
        y_pred = ["C01", "C02", "C01", "C01"]
        metrics = compute_classification_metrics(y_true, y_pred, label_names=["C01", "C02", "C03"])
        assert metrics["accuracy"] == 0.75
        assert 0.0 <= metrics["macro_f1"] <= 1.0
        assert 0.0 <= metrics["weighted_f1"] <= 1.0

    def test_analyze_errors_identifies_mismatches(self):
        texts = ["Text 1", "Text 2", "Text 3"]
        y_true = ["C01", "C02", "C03"]
        y_pred = ["C01", "C03", "C03"]
        confidences = [0.95, 0.45, 0.90]

        errors = analyze_errors(texts, y_true, y_pred, confidences)
        assert len(errors) == 1
        assert errors.iloc[0]["true_label"] == "C02"
        assert errors.iloc[0]["predicted_label"] == "C03"

    def test_naive_bayes_pipeline_structure(self):
        from src.classification.train import build_naive_bayes_pipeline
        vec = build_word_tfidf_vectorizer(min_df=1)
        pipe = build_naive_bayes_pipeline(vec, alpha=1.0)
        assert "tfidf" in pipe.named_steps
        assert "clf" in pipe.named_steps

    def test_calibration_metrics(self):
        from src.classification.evaluate import compute_calibration_metrics
        y_true = ["C01", "C02", "C03"]
        # Perfect probabilities
        y_prob = np.array([
            [0.9, 0.05, 0.05],
            [0.1, 0.8, 0.1],
            [0.05, 0.05, 0.9],
        ])
        cal = compute_calibration_metrics(y_true, y_prob, label_names=["C01", "C02", "C03"])
        assert "brier_score" in cal
        assert "log_loss" in cal
        assert "ece" in cal
        assert cal["brier_score"] >= 0.0
        assert cal["ece"] >= 0.0

    def test_evaluate_confidence_thresholds(self):
        from src.classification.evaluate import evaluate_confidence_thresholds
        y_true = ["C01", "C02", "C03", "C01"]
        y_pred = ["C01", "C02", "C01", "C01"]  # 1 error at index 2
        confidences = [0.95, 0.85, 0.40, 0.90]
        df_th = evaluate_confidence_thresholds(y_true, y_pred, confidences, thresholds=[0.50, 0.80])
        assert len(df_th) == 2
        assert "auto_routed_pct" in df_th.columns
        assert "error_recall" in df_th.columns
        # At threshold 0.50, the error (conf 0.40) is caught
        row_50 = df_th[df_th["threshold"] == 0.50].iloc[0]
        assert row_50["error_recall"] == 100.0

