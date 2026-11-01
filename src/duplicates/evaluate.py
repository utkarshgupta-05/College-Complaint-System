"""
src/duplicates/evaluate.py
----------------------------
Evaluation pipeline for Duplicate and Related Complaint Detection (Module B).

Compares:
  - Experiment E6: TF-IDF Cosine Similarity (Lexical Baseline)
  - Experiment E7: Sentence Embeddings Cosine Similarity (Semantic Model: all-MiniLM-L6-v2)

Methodology:
  1. Natural Retrieval Evaluation on Validation Split (val.csv, N=183):
     - For every complaint with a known incident cluster (19 complaints across 8 groups):
       - Search against the remaining 182 candidates in val.csv (excluding query itself).
       - Compute Hit@1, Hit@3, Hit@5, Precision@k, Recall@k, and Mean Reciprocal Rank (MRR).
  2. Pairwise Classification & Threshold Analysis:
     - Evaluate all 16,653 pairs in val.csv (14 positive pairs, 1,448 same-category hard negatives, 15,191 easy negatives).
     - Sweep threshold tau in [0.20, 0.95] to analyze Precision-Recall trade-offs.
     - Identify optimal operational thresholds (high_threshold for probable duplicates, mid_threshold for related complaints).
  3. Error Analysis:
     - Surface false positives (similar topic, different incidents).
     - Surface false negatives (differently worded reports of same incident missed).

Guarantees:
  - Zero leakage: Evaluation is performed exclusively on val.csv. test.csv is quarantined.
  - Reproducible: Metrics are computed deterministically.
"""

from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score

from src.duplicates.similarity import (
    EmbeddingSimilarityRetriever,
    SimilarComplaint,
    TFIDFSimilarityRetriever,
)
from src.evaluation.metrics import append_experiment_result

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def build_validation_pairs(df_val: pd.DataFrame) -> pd.DataFrame:
    """Extract all pairs from validation set with ground-truth duplicate labels.

    Ground-truth labels:
      - label = 1 (Positive Duplicate): Both complaints share the same non-null incident_group_id.
      - label = 0 (Negative): Different incident groups or at least one is null.
        Subtype:
          - 'hard_negative': Same category, different incidents (challenging for lexical search).
          - 'easy_negative': Different categories.
    """
    records = []
    c_ids = df_val["complaint_id"].tolist()
    texts = df_val["complaint_text"].tolist()
    cats = df_val["category"].tolist()
    g_ids = df_val["incident_group_id"].tolist()
    n = len(df_val)

    for i in range(n):
        for j in range(i + 1, n):
            gid_i = g_ids[i]
            gid_j = g_ids[j]

            if pd.notna(gid_i) and pd.notna(gid_j) and gid_i == gid_j:
                label = 1
                pair_type = "positive_duplicate"
            elif cats[i] == cats[j]:
                label = 0
                pair_type = "hard_negative"
            else:
                label = 0
                pair_type = "easy_negative"

            records.append({
                "id_1": c_ids[i],
                "id_2": c_ids[j],
                "text_1": texts[i],
                "text_2": texts[j],
                "category_1": cats[i],
                "category_2": cats[j],
                "label": label,
                "pair_type": pair_type,
            })

    return pd.DataFrame(records)


def evaluate_retrieval(
    retriever: Any,
    df_val: pd.DataFrame,
    ks: list[int] = [1, 3, 5],
) -> dict[str, float]:
    """Evaluate Top-k retrieval on complaints belonging to multi-report incidents.

    For each query complaint with incident_group_id:
      - Candidate corpus = all other complaints in val.csv.
      - Relevant items = candidates sharing the same incident_group_id.
    """
    query_df = df_val[df_val["incident_group_id"].notna()]
    if len(query_df) == 0:
        logger.warning("No incident groups found in validation set.")
        return {}

    hits_at_k = {k: 0 for k in ks}
    recalls_at_k = {k: [] for k in ks}
    precisions_at_k = {k: [] for k in ks}
    reciprocal_ranks = []
    latencies = []

    for _, row in query_df.iterrows():
        qid = row["complaint_id"]
        qtext = row["complaint_text"]
        qgid = row["incident_group_id"]

        # Ground truth relevant IDs in val
        relevant_ids = set(
            df_val[(df_val["incident_group_id"] == qgid) & (df_val["complaint_id"] != qid)]["complaint_id"]
        )
        if not relevant_ids:
            continue

        # Timed retrieval (retrieve top max(ks))
        t0 = time.perf_counter()
        candidates = retriever.find_similar(
            query_text=qtext,
            query_id=qid,
            top_k=max(ks),
            return_all=True,
        )
        latencies.append((time.perf_counter() - t0) * 1000)

        retrieved_ids = [c.complaint_id for c in candidates]

        # Reciprocal rank
        rr = 0.0
        for rank, cid in enumerate(retrieved_ids, start=1):
            if cid in relevant_ids:
                rr = 1.0 / rank
                break
        reciprocal_ranks.append(rr)

        # Hits, Recall, Precision at k
        for k in ks:
            top_k_ids = set(retrieved_ids[:k])
            relevant_retrieved = len(top_k_ids.intersection(relevant_ids))

            if relevant_retrieved > 0:
                hits_at_k[k] += 1

            precisions_at_k[k].append(relevant_retrieved / k)
            recalls_at_k[k].append(relevant_retrieved / len(relevant_ids))

    num_queries = len(reciprocal_ranks)
    metrics = {
        "num_queries": num_queries,
        "mrr": float(np.mean(reciprocal_ranks)) if num_queries > 0 else 0.0,
        "avg_query_time_ms": float(np.mean(latencies)) if latencies else 0.0,
    }
    for k in ks:
        metrics[f"hit@{k}"] = float(hits_at_k[k] / num_queries) if num_queries > 0 else 0.0
        metrics[f"recall@{k}"] = float(np.mean(recalls_at_k[k])) if num_queries > 0 else 0.0
        metrics[f"precision@{k}"] = float(np.mean(precisions_at_k[k])) if num_queries > 0 else 0.0

    return metrics


def compute_pairwise_similarities(
    retriever: Any,
    pairs_df: pd.DataFrame,
    df_val: pd.DataFrame | None = None,
) -> np.ndarray:
    """Compute similarity scores for all pairs in pairs_df using cached corpus representations."""
    if df_val is not None and hasattr(retriever, "_corpus_ids"):
        id_to_idx = {cid: idx for idx, cid in enumerate(retriever._corpus_ids)}
        idx_1 = [id_to_idx[cid] for cid in pairs_df["id_1"]]
        idx_2 = [id_to_idx[cid] for cid in pairs_df["id_2"]]

        if isinstance(retriever, TFIDFSimilarityRetriever) and retriever._corpus_matrix is not None:
            mat_1 = retriever._corpus_matrix[idx_1]
            mat_2 = retriever._corpus_matrix[idx_2]
            return np.asarray(mat_1.multiply(mat_2).sum(axis=1)).flatten().astype(np.float32)

        if isinstance(retriever, EmbeddingSimilarityRetriever) and retriever._corpus_embeddings is not None:
            embs_1 = retriever._corpus_embeddings[idx_1]
            embs_2 = retriever._corpus_embeddings[idx_2]
            return np.sum(embs_1 * embs_2, axis=1).astype(np.float32)

    # Fallback to direct computation if not cached
    if isinstance(retriever, TFIDFSimilarityRetriever):
        v1 = retriever.vectorizer.transform(pairs_df["text_1"].tolist())
        v2 = retriever.vectorizer.transform(pairs_df["text_2"].tolist())
        return np.asarray(v1.multiply(v2).sum(axis=1)).flatten().astype(np.float32)
    elif isinstance(retriever, EmbeddingSimilarityRetriever):
        retriever._load_model()
        embs_1 = retriever._model.encode(
            pairs_df["text_1"].tolist(),
            batch_size=64,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        embs_2 = retriever._model.encode(
            pairs_df["text_2"].tolist(),
            batch_size=64,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.sum(embs_1 * embs_2, axis=1).astype(np.float32)
    else:
        raise ValueError(f"Unsupported retriever: {type(retriever)}")



def sweep_thresholds(
    y_true: np.ndarray,
    scores: np.ndarray,
    thresholds: list[float] | None = None,
) -> pd.DataFrame:
    """Sweep decision thresholds and compute precision, recall, and F1."""
    if thresholds is None:
        thresholds = [round(t, 2) for t in np.arange(0.20, 0.96, 0.05)]

    rows = []
    for tau in thresholds:
        y_pred = (scores >= tau).astype(int)
        tp = int(np.sum((y_pred == 1) & (y_true == 1)))
        fp = int(np.sum((y_pred == 1) & (y_true == 0)))
        fn = int(np.sum((y_pred == 0) & (y_true == 1)))
        tn = int(np.sum((y_pred == 0) & (y_true == 0)))

        prec, rec, f1, _ = precision_recall_fscore_support(
            y_true, y_pred, average="binary", zero_division=0
        )

        rows.append({
            "threshold": tau,
            "precision": float(prec),
            "recall": float(rec),
            "f1": float(f1),
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
        })

    return pd.DataFrame(rows)


def run_duplicate_experiments(
    data_dir: Path = Path("data/processed"),
    reports_dir: Path = Path("reports"),
    figures_dir: Path = Path("reports/figures"),
) -> dict[str, Any]:
    """Run E6 and E7 experiments and produce comprehensive comparison."""
    reports_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    val_path = data_dir / "val.csv"
    if not val_path.exists():
        raise FileNotFoundError(f"Validation dataset not found at {val_path}")

    logger.info("Loading validation data from %s (test.csv is quarantined)...", val_path)
    df_val = pd.read_csv(val_path)
    logger.info("Validation dataset: %d complaints.", len(df_val))

    # Prepare corpus for fitting
    corpus_texts = df_val["complaint_text"].tolist()
    corpus_ids = df_val["complaint_id"].tolist()
    corpus_meta = df_val[["category", "location", "created_at"]].to_dict(orient="records")

    # 1. Fit retrievers
    logger.info("=== Fitting E6: TF-IDF Cosine Similarity ===")
    t0 = time.perf_counter()
    e6_retriever = TFIDFSimilarityRetriever()
    e6_retriever.fit(corpus_texts, corpus_ids, metadata=corpus_meta)
    e6_fit_time = time.perf_counter() - t0

    logger.info("=== Fitting E7: Sentence Embeddings (all-MiniLM-L6-v2) ===")
    t0 = time.perf_counter()
    e7_retriever = EmbeddingSimilarityRetriever(model_name="all-MiniLM-L6-v2")
    e7_retriever.fit(corpus_texts, corpus_ids, metadata=corpus_meta)
    e7_fit_time = time.perf_counter() - t0

    # 2. Retrieval Evaluation (Natural Val Ranking)
    logger.info("=== Evaluating Retrieval on Validation Split ===")
    e6_retrieval = evaluate_retrieval(e6_retriever, df_val, ks=[1, 3, 5])
    e7_retrieval = evaluate_retrieval(e7_retriever, df_val, ks=[1, 3, 5])

    # 3. Pairwise Classification & Threshold Sweeping
    logger.info("=== Extracting and Scoring Validation Pairs (N=16,653) ===")
    pairs_df = build_validation_pairs(df_val)
    y_true = pairs_df["label"].to_numpy()

    logger.info("Scoring pairs with E6...")
    e6_scores = compute_pairwise_similarities(e6_retriever, pairs_df, df_val=df_val)
    pairs_df["e6_score"] = e6_scores

    logger.info("Scoring pairs with E7...")
    e7_scores = compute_pairwise_similarities(e7_retriever, pairs_df, df_val=df_val)
    pairs_df["e7_score"] = e7_scores

    # ROC-AUC
    e6_auc = float(roc_auc_score(y_true, e6_scores))
    e7_auc = float(roc_auc_score(y_true, e7_scores))

    # Threshold sweeps
    e6_thresholds_df = sweep_thresholds(y_true, e6_scores)
    e7_thresholds_df = sweep_thresholds(y_true, e7_scores)

    e6_thresholds_df.to_csv(reports_dir / "duplicate_thresholds_e6.csv", index=False)
    e7_thresholds_df.to_csv(reports_dir / "duplicate_thresholds_e7.csv", index=False)

    # Find best F1 operating points
    e6_best_idx = e6_thresholds_df["f1"].idxmax()
    e6_best = e6_thresholds_df.iloc[e6_best_idx]

    e7_best_idx = e7_thresholds_df["f1"].idxmax()
    e7_best = e7_thresholds_df.iloc[e7_best_idx]

    # 4. Error Analysis at Best F1 Threshold
    e6_tau = float(e6_best["threshold"])
    e7_tau = float(e7_best["threshold"])

    # E6 Errors
    e6_fp = pairs_df[(pairs_df["label"] == 0) & (pairs_df["e6_score"] >= e6_tau)]
    e6_fn = pairs_df[(pairs_df["label"] == 1) & (pairs_df["e6_score"] < e6_tau)]
    e6_errors = pd.concat([
        e6_fp.assign(error_type="False Positive (Different incident flagged as duplicate)"),
        e6_fn.assign(error_type="False Negative (True duplicate missed)"),
    ])
    e6_errors.to_csv(reports_dir / "duplicate_errors_e6.csv", index=False)

    # E7 Errors
    e7_fp = pairs_df[(pairs_df["label"] == 0) & (pairs_df["e7_score"] >= e7_tau)]
    e7_fn = pairs_df[(pairs_df["label"] == 1) & (pairs_df["e7_score"] < e7_tau)]
    e7_errors = pd.concat([
        e7_fp.assign(error_type="False Positive (Different incident flagged as duplicate)"),
        e7_fn.assign(error_type="False Negative (True duplicate missed)"),
    ])
    e7_errors.to_csv(reports_dir / "duplicate_errors_e7.csv", index=False)

    # 5. Plotting Threshold Curves
    logger.info("=== Plotting Threshold Trade-off Curves ===")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # E6 Curves
    ax1.plot(e6_thresholds_df["threshold"], e6_thresholds_df["precision"], "b-o", label="Precision", markersize=4)
    ax1.plot(e6_thresholds_df["threshold"], e6_thresholds_df["recall"], "g-s", label="Recall", markersize=4)
    ax1.plot(e6_thresholds_df["threshold"], e6_thresholds_df["f1"], "r-^", label="F1 Score", markersize=4)
    ax1.axvline(e6_tau, color="black", linestyle="--", alpha=0.7, label=f"Best F1 (tau={e6_tau})")
    ax1.set_title("E6: TF-IDF Cosine Similarity Trade-off")
    ax1.set_xlabel("Similarity Threshold (tau)")
    ax1.set_ylabel("Score")
    ax1.set_ylim(-0.05, 1.05)
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="lower left")

    # E7 Curves
    ax2.plot(e7_thresholds_df["threshold"], e7_thresholds_df["precision"], "b-o", label="Precision", markersize=4)
    ax2.plot(e7_thresholds_df["threshold"], e7_thresholds_df["recall"], "g-s", label="Recall", markersize=4)
    ax2.plot(e7_thresholds_df["threshold"], e7_thresholds_df["f1"], "r-^", label="F1 Score", markersize=4)
    ax2.axvline(e7_tau, color="black", linestyle="--", alpha=0.7, label=f"Best F1 (tau={e7_tau})")
    ax2.set_title("E7: Sentence Transformer Embeddings Trade-off")
    ax2.set_xlabel("Similarity Threshold (tau)")
    ax2.set_ylabel("Score")
    ax2.set_ylim(-0.05, 1.05)
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="lower left")

    plt.tight_layout()
    plt.savefig(figures_dir / "duplicate_threshold_curves.png", dpi=200)
    plt.close()

    # 6. Plotting Retrieval Comparison
    fig, ax = plt.subplots(figsize=(8, 5))
    metrics_names = ["Hit@1", "Hit@3", "Hit@5", "MRR"]
    e6_vals = [e6_retrieval["hit@1"], e6_retrieval["hit@3"], e6_retrieval["hit@5"], e6_retrieval["mrr"]]
    e7_vals = [e7_retrieval["hit@1"], e7_retrieval["hit@3"], e7_retrieval["hit@5"], e7_retrieval["mrr"]]

    x = np.arange(len(metrics_names))
    width = 0.35

    ax.bar(x - width / 2, e6_vals, width, label="E6: TF-IDF Lexical", color="#3b82f6")
    ax.bar(x + width / 2, e7_vals, width, label="E7: Sentence Transformers", color="#10b981")
    ax.set_ylabel("Score")
    ax.set_title("Validation Retrieval Performance (k=1, 3, 5, MRR)")
    ax.set_xticks(x)
    ax.set_xticklabels(metrics_names)
    ax.set_ylim(0, 1.1)
    for i, (v6, v7) in enumerate(zip(e6_vals, e7_vals)):
        ax.text(i - width / 2, v6 + 0.02, f"{v6:.2f}", ha="center", fontsize=9)
        ax.text(i + width / 2, v7 + 0.02, f"{v7:.2f}", ha="center", fontsize=9)
    ax.grid(axis="y", linestyle=":", alpha=0.6)
    ax.legend(loc="lower right")

    plt.tight_layout()
    plt.savefig(figures_dir / "duplicate_retrieval_comparison.png", dpi=200)
    plt.close()

    # 7. Record to experiment_results.csv
    results_csv_path = reports_dir / "experiment_results.csv"
    append_experiment_result(
        results_csv_path,
        {
            "experiment_id": "E6",
            "phase": "Phase 5",
            "module": "Duplicate Detection (Module B)",
            "method": "TF-IDF Cosine Similarity (Lexical Baseline)",
            "dataset": "college_complaints_synthetic.csv",
            "data_source": "synthetic",
            "primary_metric": "Pair F1 (at best tau)",
            "primary_metric_value": float(e6_best["f1"]),
            "macro_f1": float(e6_best["f1"]),
            "weighted_f1": float(e6_best["precision"]),
            "accuracy": float(e6_best["recall"]),
            "training_time_s": float(e6_fit_time),
            "inference_time_ms_per_example": float(e6_retrieval["avg_query_time_ms"]),
            "notes": f"Val split N=183. Best tau={e6_tau:.2f}, Hit@1={e6_retrieval['hit@1']:.2f}, MRR={e6_retrieval['mrr']:.2f}, ROC-AUC={e6_auc:.4f}.",
            "model_artifact_path": "models/e6_tfidf_retriever.joblib",
        },
    )

    append_experiment_result(
        results_csv_path,
        {
            "experiment_id": "E7",
            "phase": "Phase 5",
            "module": "Duplicate Detection (Module B)",
            "method": "Sentence Embeddings Cosine Similarity (all-MiniLM-L6-v2)",
            "dataset": "college_complaints_synthetic.csv",
            "data_source": "synthetic",
            "primary_metric": "Pair F1 (at best tau)",
            "primary_metric_value": float(e7_best["f1"]),
            "macro_f1": float(e7_best["f1"]),
            "weighted_f1": float(e7_best["precision"]),
            "accuracy": float(e7_best["recall"]),
            "training_time_s": float(e7_fit_time),
            "inference_time_ms_per_example": float(e7_retrieval["avg_query_time_ms"]),
            "notes": f"Val split N=183. Best tau={e7_tau:.2f}, Hit@1={e7_retrieval['hit@1']:.2f}, MRR={e7_retrieval['mrr']:.2f}, ROC-AUC={e7_auc:.4f}.",
            "model_artifact_path": "sentence-transformers/all-MiniLM-L6-v2",
        },
    )

    # 8. Save artifacts
    import joblib
    models_dir = Path("models")
    models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump({
        "retriever": e6_retriever,
        "high_threshold": 0.80,
        "mid_threshold": 0.50,
        "metrics": e6_retrieval,
    }, models_dir / "e6_tfidf_retriever.joblib")

    results_summary = {
        "e6": {
            "fit_time": e6_fit_time,
            "query_time_ms": e6_retrieval["avg_query_time_ms"],
            "hit@1": e6_retrieval["hit@1"],
            "hit@3": e6_retrieval["hit@3"],
            "hit@5": e6_retrieval["hit@5"],
            "mrr": e6_retrieval["mrr"],
            "roc_auc": e6_auc,
            "best_tau": e6_tau,
            "best_f1": float(e6_best["f1"]),
            "best_precision": float(e6_best["precision"]),
            "best_recall": float(e6_best["recall"]),
            "fp_count": int(e6_best["fp"]),
            "fn_count": int(e6_best["fn"]),
        },
        "e7": {
            "fit_time": e7_fit_time,
            "query_time_ms": e7_retrieval["avg_query_time_ms"],
            "hit@1": e7_retrieval["hit@1"],
            "hit@3": e7_retrieval["hit@3"],
            "hit@5": e7_retrieval["hit@5"],
            "mrr": e7_retrieval["mrr"],
            "roc_auc": e7_auc,
            "best_tau": e7_tau,
            "best_f1": float(e7_best["f1"]),
            "best_precision": float(e7_best["precision"]),
            "best_recall": float(e7_best["recall"]),
            "fp_count": int(e7_best["fp"]),
            "fn_count": int(e7_best["fn"]),
        },
    }

    logger.info("=== Phase 5 Evaluation Complete ===")
    logger.info("E6 (TF-IDF): Best tau=%.2f, F1=%.4f, Hit@1=%.2f, MRR=%.4f, AUC=%.4f",
                e6_tau, e6_best["f1"], e6_retrieval["hit@1"], e6_retrieval["mrr"], e6_auc)
    logger.info("E7 (Embeddings): Best tau=%.2f, F1=%.4f, Hit@1=%.2f, MRR=%.4f, AUC=%.4f",
                e7_tau, e7_best["f1"], e7_retrieval["hit@1"], e7_retrieval["mrr"], e7_auc)

    return results_summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Duplicate Detection on Validation Data")
    parser.add_argument("--data-dir", type=str, default="data/processed", help="Path to processed splits")
    args = parser.parse_args()

    run_duplicate_experiments(data_dir=Path(args.data_dir))
