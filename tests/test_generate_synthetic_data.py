"""
tests/test_generate_synthetic_data.py
-------------------------------------
Unit tests for src/data/generate_synthetic_data.py.

Verifies:
- Deterministic reproducibility under identical random seed.
- Complete coverage of all 11 categories with >= 100 examples each.
- Full schema compatibility with config.yaml and DATASET_CARD.md.
- Explicit data_source='synthetic' tagging.
- Text uniqueness and non-empty text constraints.
- Multi-report incident group presence.
"""

import pandas as pd
import pytest

from src.data.generate_synthetic_data import generate_synthetic_dataset

EXPECTED_CATEGORIES = [
    "C01", "C02", "C03", "C04", "C05",
    "C06", "C07", "C08", "C09", "C10", "C11",
]

EXPECTED_COLUMNS = [
    "complaint_id",
    "complaint_text",
    "category",
    "category_name",
    "location",
    "created_at",
    "status",
    "priority_label",
    "incident_group_id",
    "data_source",
]


class TestSyntheticDatasetGeneration:
    @pytest.fixture(scope="class")
    def sample_dataset(self):
        """Generate a test dataset with 105 examples per category."""
        return generate_synthetic_dataset(
            target_count_per_category=105,
            random_seed=42,
        )

    def test_reproducibility(self):
        """Identical seeds must produce bit-for-bit identical DataFrames."""
        df1 = generate_synthetic_dataset(target_count_per_category=10, random_seed=123)
        df2 = generate_synthetic_dataset(target_count_per_category=10, random_seed=123)
        pd.testing.assert_frame_equal(df1, df2)

    def test_different_seeds_produce_different_order(self):
        """Different seeds must produce different ordering/texts."""
        df1 = generate_synthetic_dataset(target_count_per_category=10, random_seed=42)
        df2 = generate_synthetic_dataset(target_count_per_category=10, random_seed=999)
        assert not df1["complaint_text"].equals(df2["complaint_text"])

    def test_all_expected_columns_present(self, sample_dataset):
        for col in EXPECTED_COLUMNS:
            assert col in sample_dataset.columns, f"Missing required column: {col}"

    def test_category_coverage(self, sample_dataset):
        unique_cats = set(sample_dataset["category"].unique())
        for expected in EXPECTED_CATEGORIES:
            assert expected in unique_cats, f"Category {expected} missing from dataset."
            count = (sample_dataset["category"] == expected).sum()
            assert count >= 100, f"Category {expected} has only {count} examples (expected >= 100)."

    def test_data_source_tag(self, sample_dataset):
        assert (sample_dataset["data_source"] == "synthetic").all(), (
            "All records must be explicitly marked with data_source='synthetic'"
        )

    def test_no_empty_or_short_complaints(self, sample_dataset):
        lengths = sample_dataset["complaint_text"].str.len()
        assert (lengths >= 10).all(), "Every complaint text must be at least 10 characters."
        assert not sample_dataset["complaint_text"].isnull().any(), "No complaint text can be null."

    def test_text_uniqueness(self, sample_dataset):
        """No exact duplicate complaint texts allowed."""
        duplicates = sample_dataset["complaint_text"].duplicated()
        assert not duplicates.any(), f"Found {duplicates.sum()} exact duplicate texts."

    def test_incident_groups_present(self, sample_dataset):
        grouped = sample_dataset[sample_dataset["incident_group_id"] != ""]
        assert len(grouped) > 0, "Dataset must contain grouped incident complaints."
        # Every incident group must contain at least 2 reports
        counts = grouped["incident_group_id"].value_counts()
        assert (counts >= 2).all(), "Each incident group must have at least 2 reports."

    def test_safety_critical_complaints_present(self, sample_dataset):
        critical_count = (sample_dataset["priority_label"] == "critical").sum()
        assert critical_count > 0, "Dataset must include critical safety-related complaints."
