"""
tests/test_clustering.py
------------------------
Unit and integration tests for Phase 7 (Recurring-Issue Discovery and Pattern Analysis).
Tests frequency analysis, trend sufficiency, K-Means clustering, DBSCAN, and cluster interpretation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.clustering.discover import (
    ClusterSummary,
    ClusteringResult,
    run_dbscan,
    run_kmeans,
    tune_kmeans_k,
)
from src.clustering.frequency import (
    aggregate_by_category,
    aggregate_by_department,
    aggregate_by_location,
    aggregate_by_time_period,
    assess_trend_sufficiency,
    find_hotspots,
)


@pytest.fixture
def sample_complaints_df() -> pd.DataFrame:
    """Fixture with realistic small complaint DataFrame."""
    return pd.DataFrame({
        "complaint_id": [f"C{i:03d}" for i in range(1, 11)],
        "complaint_text": [
            "Wi-Fi connection is down in Hostel 3 2nd floor rooms.",
            "Internet speed is terribly slow in Hostel 3 common room.",
            "Water leakage in washroom of Academic Block 1.",
            "Classroom 101 projector bulb is broken and flickering.",
            "Mess food quality in dining hall is stale and cold.",
            "Hostel 3 Wi-Fi router appears completely dead.",
            "Another water pipe burst in Academic Block 1 first floor washroom.",
            "Projector HDMI port in Classroom 102 does not transmit audio.",
            "Mess dal was completely watery and tasteless today.",
            "Hostel 3 corridor lights are fused and dark at night.",
        ],
        "category": [
            "C03", "C03", "C07", "C06", "C04",
            "C03", "C07", "C06", "C04", "C01",
        ],
        "location": [
            "Hostel 3", "Hostel 3", "Academic Block 1", "Academic Block 2", "Dining Hall",
            "Hostel 3", "Academic Block 1", "Academic Block 2", "Dining Hall", "Hostel 3",
        ],
        "created_at": [
            "2026-03-01 10:00:00", "2026-03-02 11:30:00", "2026-03-05 09:15:00",
            "2026-03-10 14:00:00", "2026-03-12 19:45:00", "2026-03-15 12:00:00",
            "2026-03-16 08:30:00", "2026-03-20 16:20:00", "2026-03-22 20:00:00",
            "2026-03-25 22:10:00",
        ],
    })


# =========================================================================
# 1. Frequency and Trend Analysis Tests
# =========================================================================

def test_aggregate_by_category(sample_complaints_df):
    counts = aggregate_by_category(sample_complaints_df)
    assert not counts.empty
    assert "category" in counts.columns
    assert "count" in counts.columns
    assert "percentage" in counts.columns
    assert counts["count"].sum() == 10
    # C03 has 3 complaints
    c03_row = counts[counts["category"] == "C03"]
    assert len(c03_row) == 1
    assert c03_row["count"].iloc[0] == 3
    assert c03_row["percentage"].iloc[0] == 30.0


def test_aggregate_by_category_missing_and_empty():
    empty_df = pd.DataFrame()
    assert aggregate_by_category(empty_df).empty

    df_missing = pd.DataFrame({"complaint_text": ["Test complaint"]})
    res = aggregate_by_category(df_missing)
    assert res.empty


def test_aggregate_by_location(sample_complaints_df):
    loc_counts = aggregate_by_location(sample_complaints_df)
    assert not loc_counts.empty
    # Hostel 3 has 4 occurrences
    h3_row = loc_counts[loc_counts["location"] == "Hostel 3"]
    assert len(h3_row) == 1
    assert h3_row["count"].iloc[0] == 4

    # Test handling of missing location without inventing data
    df_no_loc = pd.DataFrame({"complaint_text": ["A", "B"]})
    res_no_loc = aggregate_by_location(df_no_loc)
    assert res_no_loc["location"].iloc[0] == "<Unspecified Location>"
    assert res_no_loc["count"].iloc[0] == 2


def test_aggregate_by_department():
    df_dept = pd.DataFrame({
        "complaint_text": ["A", "B", "C"],
        "student_dept": ["CSE", "CSE", "EEE"],
    })
    res = aggregate_by_department(df_dept)
    assert len(res) == 2
    assert res[res["department"] == "CSE"]["count"].iloc[0] == 2


def test_aggregate_by_time_period(sample_complaints_df):
    res_w = aggregate_by_time_period(sample_complaints_df, freq="W")
    assert not res_w.empty
    assert res_w["count"].sum() == 10

    # With unparseable timestamps
    df_bad_dates = pd.DataFrame({
        "created_at": ["2026-01-01", "not-a-date", None],
    })
    res_bad = aggregate_by_time_period(df_bad_dates, freq="M")
    missing_row = res_bad[res_bad["period"] == "<Missing Timestamp>"]
    assert len(missing_row) == 1
    assert missing_row["count"].iloc[0] == 2


def test_find_hotspots(sample_complaints_df):
    hotspots = find_hotspots(sample_complaints_df, min_count=2)
    assert not hotspots.empty
    # (Hostel 3, C03) occurred 3 times
    h3_c03 = hotspots[(hotspots["location"] == "Hostel 3") & (hotspots["category"] == "C03")]
    assert len(h3_c03) == 1
    assert h3_c03["count"].iloc[0] == 3

    # (Academic Block 1, C07) occurred 2 times
    ab1_c07 = hotspots[(hotspots["location"] == "Academic Block 1") & (hotspots["category"] == "C07")]
    assert len(ab1_c07) == 1
    assert ab1_c07["count"].iloc[0] == 2


def test_assess_trend_sufficiency(sample_complaints_df):
    report = assess_trend_sufficiency(sample_complaints_df)
    assert report.total_records == 10
    assert report.valid_timestamps == 10
    assert report.span_days < 60
    # Must correctly flag that 24 days cannot substantiate seasonality
    assert report.is_sufficient_for_seasonality is False
    assert report.warning is not None
    assert "seasonality" in report.warning.lower()


# =========================================================================
# 2. Unsupervised Clustering Tests (K-Means & DBSCAN)
# =========================================================================

def test_tune_kmeans_k(sample_complaints_df):
    texts = sample_complaints_df["complaint_text"].tolist()
    tune_df = tune_kmeans_k(texts, k_range=[2, 3, 4], random_seed=42)
    assert not tune_df.empty
    assert list(tune_df["k"]) == [2, 3, 4]
    assert "inertia" in tune_df.columns
    assert "silhouette_score" in tune_df.columns
    assert "davies_bouldin_index" in tune_df.columns


def test_run_kmeans_basic(sample_complaints_df):
    texts = sample_complaints_df["complaint_text"].tolist()
    cats = sample_complaints_df["category"].tolist()
    locs = sample_complaints_df["location"].tolist()

    res = run_kmeans(
        texts,
        k=3,
        random_seed=42,
        categories=cats,
        locations=locs,
        min_cluster_size=2,
    )

    assert isinstance(res, ClusteringResult)
    assert res.method == "K-Means"
    assert res.n_clusters == 3
    assert len(res.cluster_labels) == 10
    assert len(res.clusters) == 3

    # Check each cluster summary
    for c in res.clusters:
        assert isinstance(c, ClusterSummary)
        assert c.size > 0
        assert len(c.representative_complaints) > 0
        assert isinstance(c.top_terms, list)
        assert isinstance(c.category_distribution, dict)
        assert isinstance(c.location_distribution, dict)


def test_run_kmeans_reproducibility(sample_complaints_df):
    texts = sample_complaints_df["complaint_text"].tolist()
    res1 = run_kmeans(texts, k=3, random_seed=42)
    res2 = run_kmeans(texts, k=3, random_seed=42)
    assert res1.cluster_labels == res2.cluster_labels
    assert res1.inertia == res2.inertia


def test_run_kmeans_weak_cluster_warning(sample_complaints_df):
    texts = sample_complaints_df["complaint_text"].tolist()
    # High k with min_cluster_size=4 forces small clusters to trigger warning
    res = run_kmeans(texts, k=4, random_seed=42, min_cluster_size=4)
    has_weak = any(c.is_weakly_supported for c in res.clusters)
    assert has_weak is True
    weak_cluster = [c for c in res.clusters if c.is_weakly_supported][0]
    assert weak_cluster.warning is not None
    assert "support threshold" in weak_cluster.warning


def test_run_kmeans_edge_cases():
    # Empty list
    res_empty = run_kmeans([])
    assert res_empty.n_clusters == 0
    assert res_empty.cluster_labels == []

    # Single item
    res_single = run_kmeans(["Lonely complaint"], k=3)
    assert res_single.n_clusters == 1
    assert res_single.clusters[0].size == 1
    assert res_single.clusters[0].is_weakly_supported is True


def test_run_dbscan_basic(sample_complaints_df):
    texts = sample_complaints_df["complaint_text"].tolist()
    cats = sample_complaints_df["category"].tolist()
    locs = sample_complaints_df["location"].tolist()

    res = run_dbscan(
        texts,
        eps=0.65,
        min_samples=2,
        categories=cats,
        locations=locs,
    )

    assert isinstance(res, ClusteringResult)
    assert res.method == "DBSCAN"
    assert len(res.cluster_labels) == 10
    # Noise points must be non-negative
    assert res.n_noise >= 0
    # Every cluster summary must be properly populated
    for c in res.clusters:
        assert c.size >= 2
        assert len(c.representative_complaints) > 0


def test_run_dbscan_all_noise_edge_case():
    # Very small eps with diverse text leads to all noise points
    texts = [
        "Quantum computing superposition experiment failed.",
        "Organic chemistry benzene distillation temperature warning.",
        "Classical philosophy symposium on ethics.",
    ]
    res = run_dbscan(texts, eps=0.1, min_samples=2)
    assert res.n_clusters == 0
    assert res.n_noise == 3
    assert res.cluster_labels == [-1, -1, -1]
    assert res.silhouette_score is None
