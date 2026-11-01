"""Clustering and pattern discovery subpackage (Phase 7)."""

from src.clustering.discover import (
    ClusterSummary,
    ClusteringResult,
    get_default_vectorizer,
    run_dbscan,
    run_kmeans,
    tune_kmeans_k,
)
from src.clustering.frequency import (
    TrendSufficiencyReport,
    aggregate_by_category,
    aggregate_by_department,
    aggregate_by_location,
    aggregate_by_time_period,
    assess_trend_sufficiency,
    find_hotspots,
)

__all__ = [
    "ClusterSummary",
    "ClusteringResult",
    "get_default_vectorizer",
    "run_kmeans",
    "run_dbscan",
    "tune_kmeans_k",
    "aggregate_by_category",
    "aggregate_by_location",
    "aggregate_by_department",
    "aggregate_by_time_period",
    "find_hotspots",
    "assess_trend_sufficiency",
    "TrendSufficiencyReport",
]
