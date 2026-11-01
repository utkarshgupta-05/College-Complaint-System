"""
src/evaluation/metrics.py
--------------------------
Shared metric utilities used across classification, duplicate detection,
and clustering evaluation modules.
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


def precision_at_k(
    relevant: set[Any],
    retrieved: list[Any],
    k: int,
) -> float:
    """Compute Precision@K for a single query.

    P@K = |relevant ∩ retrieved[:k]| / k

    Args:
        relevant: Set of ground-truth relevant IDs.
        retrieved: Ordered list of retrieved IDs.
        k: Cut-off rank.

    Returns:
        Precision@K as a float in [0.0, 1.0].
    """
    if k <= 0:
        return 0.0
    top_k = set(retrieved[:k])
    return len(relevant & top_k) / k


def recall_at_k(
    relevant: set[Any],
    retrieved: list[Any],
    k: int,
) -> float:
    """Compute Recall@K for a single query.

    R@K = |relevant ∩ retrieved[:k]| / |relevant|

    Args:
        relevant: Set of ground-truth relevant IDs.
        retrieved: Ordered list of retrieved IDs.
        k: Cut-off rank.

    Returns:
        Recall@K as a float in [0.0, 1.0]. Returns 0.0 if relevant is empty.
    """
    if not relevant:
        return 0.0
    top_k = set(retrieved[:k])
    return len(relevant & top_k) / len(relevant)


def append_experiment_result(
    results_path: str | Path,
    experiment: dict[str, Any],
) -> None:
    """Upsert a single experiment result row in the CSV results table.

    If experiment_id exists in the file, it updates that row in place;
    otherwise, it appends a new row.

    Args:
        results_path: Path to reports/experiment_results.csv.
        experiment: Dict with experiment fields (must include 'experiment_id').
    """
    results_path = Path(results_path)
    results_path.parent.mkdir(parents=True, exist_ok=True)

    headers = [
        "experiment_id", "phase", "module", "method", "dataset",
        "data_source",  # 'real', 'synthetic', 'public'
        "primary_metric", "primary_metric_value",
        "macro_f1", "weighted_f1", "accuracy",
        "training_time_s", "inference_time_ms_per_example",
        "notes", "model_artifact_path",
    ]

    exp_id = experiment.get("experiment_id")
    rows: list[dict[str, Any]] = []

    if results_path.exists():
        with open(results_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                if exp_id and r.get("experiment_id") == exp_id:
                    continue  # Replace this row
                rows.append(r)

    rows.append(experiment)

    # Sort rows by experiment_id if format E<int>
    def sort_key(row):
        eid = str(row.get("experiment_id", ""))
        if eid.startswith("E") and eid[1:].isdigit():
            return int(eid[1:])
        return 999

    rows.sort(key=sort_key)

    with open(results_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    logger.info("Experiment result upserted for %s in %s", exp_id, results_path)

