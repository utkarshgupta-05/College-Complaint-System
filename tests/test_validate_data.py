"""
tests/test_validate_data.py
----------------------------
Unit tests for src/data/validate_data.py.

These tests verify the validation logic against controlled inputs.
Tests are designed to catch regressions as the data pipeline evolves.

STATUS: Phase 1 — test stubs written. Tests will be run and verified in Phase 2
after the validation module is fully implemented and a dataset is available.
Do NOT mark these tests as passing until pytest has actually been executed.
"""

import pandas as pd
import pytest

from src.data.validate_data import (
    ValidationReport,
    check_class_distribution,
    check_empty_text,
    check_exact_duplicates,
    check_label_coverage,
    check_pii_presence,
    check_required_columns,
    validate_dataframe,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def minimal_df():
    """A minimal valid DataFrame for testing."""
    return pd.DataFrame({
        "complaint_text": [
            "The water supply in Block B has been cut for two days.",
            "Internet is not working in the library.",
            "The mess food quality has deteriorated this week.",
        ],
        "category": ["C02", "C03", "C04"],
    })


@pytest.fixture
def df_with_empty_texts():
    return pd.DataFrame({
        "complaint_text": ["", None, "Valid complaint about electricity."],
        "category": ["C02", "C02", "C02"],
    })


@pytest.fixture
def df_with_duplicates():
    text = "There is no electricity in Block A."
    return pd.DataFrame({
        "complaint_text": [text, text, "Different complaint about food."],
        "category": ["C02", "C02", "C04"],
    })


@pytest.fixture
def df_with_pii():
    return pd.DataFrame({
        "complaint_text": [
            "My roll number is 21CSE1234 and the hostel has no water.",
            "Contact me at test@example.com for details.",
            "Normal complaint about food quality.",
        ],
        "category": ["C01", "C01", "C04"],
    })


# ---------------------------------------------------------------------------
# Tests for individual checks
# ---------------------------------------------------------------------------

class TestCheckRequiredColumns:
    def test_all_present(self, minimal_df):
        result = check_required_columns(minimal_df, ["complaint_text", "category"])
        assert result.passed, result.details

    def test_missing_column(self, minimal_df):
        result = check_required_columns(minimal_df, ["complaint_text", "nonexistent"])
        assert not result.passed
        assert "nonexistent" in result.details


class TestCheckEmptyText:
    def test_no_empty(self, minimal_df):
        result = check_empty_text(minimal_df, "complaint_text", min_length=10)
        assert result.passed, result.details

    def test_detects_empty(self, df_with_empty_texts):
        result = check_empty_text(df_with_empty_texts, "complaint_text", min_length=10)
        assert not result.passed
        assert len(result.affected_rows) >= 2  # empty string and None

    def test_missing_column(self, minimal_df):
        result = check_empty_text(minimal_df, "nonexistent_col")
        assert not result.passed


class TestCheckExactDuplicates:
    def test_no_duplicates(self, minimal_df):
        result = check_exact_duplicates(minimal_df, "complaint_text")
        assert result.passed, result.details

    def test_detects_duplicates(self, df_with_duplicates):
        result = check_exact_duplicates(df_with_duplicates, "complaint_text")
        assert not result.passed
        assert len(result.affected_rows) == 2


class TestCheckLabelCoverage:
    def test_all_valid(self, minimal_df):
        valid_labels = ["C01", "C02", "C03", "C04", "C05"]
        result = check_label_coverage(minimal_df, "category", valid_labels)
        assert result.passed, result.details

    def test_unknown_label(self):
        df = pd.DataFrame({
            "complaint_text": ["Some complaint."],
            "category": ["C99"],  # Not in the valid list
        })
        result = check_label_coverage(df, "category", ["C01", "C02"])
        assert not result.passed
        assert "C99" in result.details


class TestCheckClassDistribution:
    def test_sufficient_examples(self, minimal_df):
        # With min=1, all classes pass
        result = check_class_distribution(minimal_df, "category", min_examples=1)
        assert result.passed, result.details

    def test_insufficient_examples(self, minimal_df):
        # Require 5 examples but each category has only 1
        result = check_class_distribution(minimal_df, "category", min_examples=5)
        assert not result.passed


class TestCheckPIIPresence:
    def test_no_pii(self, minimal_df):
        patterns = [
            {"pattern": r'\b\d{10}\b', "replacement": "[PHONE]"},
            {"pattern": r'\b\d{2}[A-Z]{3}\d{4}\b', "replacement": "[ROLL_NO]"},
        ]
        result = check_pii_presence(minimal_df, "complaint_text", patterns)
        assert result.passed, result.details

    def test_detects_roll_number(self, df_with_pii):
        patterns = [
            {"pattern": r'\b\d{2}[A-Z]{3}\d{4}\b', "replacement": "[ROLL_NO]"},
        ]
        result = check_pii_presence(df_with_pii, "complaint_text", patterns)
        assert not result.passed
        assert len(result.affected_rows) >= 1


# ---------------------------------------------------------------------------
# Tests for the orchestrator
# ---------------------------------------------------------------------------

class TestValidateDataframe:
    def test_valid_dataframe_passes(self, minimal_df):
        report = validate_dataframe(
            minimal_df,
            valid_labels=["C01", "C02", "C03", "C04"],
            min_class_examples=1,
        )
        failed = [r.check_name for r in report.failed_checks]
        assert report.passed, f"Failed checks: {failed}"

    def test_report_summary_is_string(self, minimal_df):
        report = validate_dataframe(minimal_df)
        assert isinstance(report.summary(), str)
        assert len(report.summary()) > 0

    def test_empty_dataframe(self):
        empty_df = pd.DataFrame(columns=["complaint_text", "category"])
        report = validate_dataframe(empty_df)
        # Empty DF is technically valid (no bad rows) but should not crash
        assert isinstance(report, ValidationReport)


# ---------------------------------------------------------------------------
# Edge case tests
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_non_string_text_column(self):
        """Non-string values in text column should be handled gracefully."""
        df = pd.DataFrame({
            "complaint_text": [123, 456.78, None],
            "category": ["C02", "C02", "C02"],
        })
        # Should not raise an exception; should flag as empty/short
        result = check_empty_text(df, "complaint_text", min_length=10)
        assert isinstance(result.passed, bool)

    def test_single_row_dataframe(self):
        df = pd.DataFrame({
            "complaint_text": ["Short but valid enough complaint."],
            "category": ["C01"],
        })
        report = validate_dataframe(
            df,
            valid_labels=["C01"],
            min_class_examples=1,
        )
        assert isinstance(report, ValidationReport)
