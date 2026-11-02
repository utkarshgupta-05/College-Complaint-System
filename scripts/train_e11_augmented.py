"""
scripts/train_e11_augmented.py
------------------------------
Train Experiment E11: Selective External Data Augmentation.

Model: TF-IDF (Word n-grams 1-2) + Calibrated Linear SVM (sigmoid, 5-fold CV)
Training Data: data/processed/e11_augmented_train.csv (N=1,524)
Artifact: models/e11_augmented.joblib

Baseline models/e2.joblib is preserved untouched.
"""

from __future__ import annotations

import datetime
import hashlib
import logging
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.abspath("."))

import joblib
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.svm import LinearSVC

from src.data.preprocess import build_word_tfidf_vectorizer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def get_file_hash(path: Path) -> str:
    hasher = hashlib.md5()
    with open(path, "rb") as f:
        hasher.update(f.read())
    return hasher.hexdigest()


def main() -> None:
    train_path = Path("data/processed/e11_augmented_train.csv")
    e2_path = Path("models/e2.joblib")
    output_path = Path("models/e11_augmented.joblib")

    if not train_path.exists():
        raise FileNotFoundError(f"Augmented dataset not found: {train_path}")

    e2_hash_before = get_file_hash(e2_path) if e2_path.exists() else None

    logger.info("Loading augmented training dataset from %s...", train_path)
    train_df = pd.read_csv(train_path)
    train_texts = train_df["complaint_text"].tolist()
    train_labels = train_df["category"].tolist()
    n_samples = len(train_texts)

    logger.info("Training samples: %d across %d classes.", n_samples, len(set(train_labels)))

    # Exact E2 vectorizer architecture
    vectorizer = build_word_tfidf_vectorizer(
        max_features=10000,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95,
        sublinear_tf=True,
    )

    # Exact E2 base classifier & calibration architecture
    base_svm = LinearSVC(
        C=1.0,
        class_weight="balanced",
        random_state=42,
        max_iter=2000,
    )
    calibrated_svm = CalibratedClassifierCV(
        estimator=base_svm,
        method="sigmoid",
        cv=5,
    )

    from sklearn.pipeline import Pipeline
    pipeline = Pipeline([("tfidf", vectorizer), ("clf", calibrated_svm)])

    logger.info("Fitting TF-IDF + Calibrated Linear SVM on %d augmented training records...", n_samples)
    start_time = time.perf_counter()
    pipeline.fit(train_texts, train_labels)
    elapsed_time = time.perf_counter() - start_time
    logger.info("Training completed in %.3f seconds.", elapsed_time)

    metadata = {
        "experiment_id": "E11",
        "method": "TF-IDF (Word n-grams 1-2) + Linear SVM (Calibrated) [Augmented]",
        "model_type": "svm",
        "vectorizer_type": "word",
        "train_samples": n_samples,
        "base_samples": int((train_df["data_source"] == "synthetic").sum()),
        "external_samples": int((train_df["data_source"] != "synthetic").sum()),
        "data_sources": {
            "synthetic_base": int((train_df["data_source"] == "synthetic").sum()),
            "kaggle_ayushcl": int((train_df["data_source"] == "kaggle_ayushcl").sum()),
            "kaggle_sheshanksingh": int((train_df["data_source"] == "kaggle_sheshanksingh").sum()),
        },
        "training_time_s": round(elapsed_time, 4),
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Save artifact
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": pipeline, "metadata": metadata}, output_path)
    logger.info("Saved E11 augmented model artifact to %s", output_path)

    # Verify baseline model was NOT touched
    if e2_hash_before is not None:
        assert get_file_hash(e2_path) == e2_hash_before, "models/e2.joblib was modified!"
        logger.info("Baseline verification successful: models/e2.joblib is completely UNMODIFIED.")


if __name__ == "__main__":
    main()

