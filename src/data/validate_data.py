"""
src/data/validate_data.py
--------------------------
Validate a loaded DataFrame against the project's expected schema and quality rules.

Each check returns a ValidationResult describing what was found.
No check silently modifies the DataFrame — findings are reported for human review.

Design principles:
- All checks are independent; a failing check does not prevent others from running.
- Results are collected and returned together so callers can decide how to proceed.
- No check raises an exception for data quality issues (only for programming errors).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class CheckResult:
    """Outcome of a single validation check."""
    check_name: str
    passed: bool
    details: str
    affected_rows: list[Any] = field(default_factory=list)  # row indices or IDs

    def __repr__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.check_name}: {self.details}"


@dataclass
class ValidationReport:
    """Aggregated report from all validation checks."""
    results: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def failed_checks(self) -> list[CheckResult]:
        return [r for r in self.results if not r.passed]

    def summary(self) -> str:
        total = len(self.results)
        failed = len(self.failed_checks)
        lines = [f"Validation: {total - failed}/{total} checks passed"]
        for r in self.results:
            lines.append(f"  {r}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_required_columns(
    df: pd.DataFrame, required: list[str]
) -> CheckResult:
    """Verify that all required columns are present."""
    missing = [c for c in required if c not in df.columns]
    passed = len(missing) == 0
    return CheckResult(
        check_name="required_columns",
        passed=passed,
        details=(
            "All required columns present."
            if passed
            else f"Missing columns: {missing}"
        ),
    )


def check_empty_text(
    df: pd.DataFrame, text_column: str, min_length: int = 10
) -> CheckResult:
    """Flag rows where complaint text is null or shorter than min_length characters."""
    if text_column not in df.columns:
        return CheckResult("empty_text", False, f"Column '{text_column}' not found.")

    null_mask = df[text_column].isnull()
    short_mask = df[text_column].fillna("").str.len() < min_length
    problem_mask = null_mask | short_mask
    affected = list(df.index[problem_mask])
    passed = len(affected) == 0
    return CheckResult(
        check_name="empty_or_short_text",
        passed=passed,
        details=(
            "No empty or very short complaints found."
            if passed
            else f"{len(affected)} complaint(s) are null or shorter than {min_length} chars."
        ),
        affected_rows=affected,
    )


def check_exact_duplicates(
    df: pd.DataFrame, text_column: str
) -> CheckResult:
    """Flag complaints with identical text (exact duplicates)."""
    if text_column not in df.columns:
        return CheckResult("exact_duplicates", False, f"Column '{text_column}' not found.")

    dup_mask = df[text_column].duplicated(keep=False)
    affected = list(df.index[dup_mask])
    passed = len(affected) == 0
    return CheckResult(
        check_name="exact_duplicates",
        passed=passed,
        details=(
            "No exact duplicate complaint texts found."
            if passed
            else f"{len(affected)} rows share identical complaint text."
        ),
        affected_rows=affected,
    )


def check_label_coverage(
    df: pd.DataFrame, label_column: str, valid_labels: list[str]
) -> CheckResult:
    """Flag rows with labels not in the known category list."""
    if label_column not in df.columns:
        return CheckResult("label_coverage", False, f"Column '{label_column}' not found.")

    df_labels = df[label_column].dropna().unique().tolist()
    unknown = [lb for lb in df_labels if lb not in valid_labels]
    passed = len(unknown) == 0
    return CheckResult(
        check_name="label_coverage",
        passed=passed,
        details=(
            "All labels are within the known category set."
            if passed
            else f"Unknown labels found: {unknown}"
        ),
    )


def check_class_distribution(
    df: pd.DataFrame, label_column: str, min_examples: int = 30
) -> CheckResult:
    """Flag categories with fewer than min_examples training examples."""
    if label_column not in df.columns:
        return CheckResult(
            "class_distribution", False, f"Column '{label_column}' not found."
        )

    counts = df[label_column].value_counts()
    sparse = counts[counts < min_examples]
    passed = len(sparse) == 0
    details = (
        "All categories meet the minimum example threshold."
        if passed
        else (
            f"{len(sparse)} category/ies have fewer than {min_examples} examples: "
            + ", ".join(f"{k}={v}" for k, v in sparse.items())
        )
    )
    return CheckResult(
        check_name="class_distribution",
        passed=passed,
        details=details,
    )


def check_pii_presence(
    df: pd.DataFrame, text_column: str, pii_patterns: list[dict]
) -> CheckResult:
    """Scan complaint text for likely PII using regex patterns.

    Args:
        df: DataFrame to inspect.
        text_column: Column containing complaint text.
        pii_patterns: List of dicts with keys 'pattern' and 'replacement'.

    Returns:
        CheckResult with rows where PII may be present.
    """
    if text_column not in df.columns:
        return CheckResult("pii_presence", False, f"Column '{text_column}' not found.")

    affected = set()
    matched_types: list[str] = []
    for pat_def in pii_patterns:
        pattern = pat_def.get("pattern", "")
        mask = df[text_column].fillna("").str.contains(pattern, regex=True, na=False)
        rows = list(df.index[mask])
        if rows:
            matched_types.append(pattern)
            affected.update(rows)

    passed = len(affected) == 0
    return CheckResult(
        check_name="pii_presence",
        passed=passed,
        details=(
            "No obvious PII patterns detected."
            if passed
            else (
                f"Potential PII detected in {len(affected)} row(s). "
                f"Patterns matched: {matched_types}. "
                "Run masking before using data in models."
            )
        ),
        affected_rows=sorted(affected),
    )


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def validate_dataframe(
    df: pd.DataFrame,
    *,
    text_column: str = "complaint_text",
    label_column: str = "category",
    valid_labels: list[str] | None = None,
    min_text_length: int = 10,
    min_class_examples: int = 30,
    pii_patterns: list[dict] | None = None,
) -> ValidationReport:
    """Run all validation checks on a DataFrame and return a ValidationReport.

    Args:
        df: DataFrame to validate.
        text_column: Name of the complaint text column.
        label_column: Name of the category label column.
        valid_labels: List of acceptable category values.
        min_text_length: Minimum character length for complaint text.
        min_class_examples: Minimum examples per class.
        pii_patterns: List of regex patterns to detect PII.

    Returns:
        ValidationReport aggregating all check outcomes.
    """
    report = ValidationReport()

    # Always run these checks
    required_cols = [text_column]
    if label_column in df.columns:
        required_cols.append(label_column)

    report.results.append(
        check_required_columns(df, required_cols)
    )
    report.results.append(
        check_empty_text(df, text_column, min_length=min_text_length)
    )
    report.results.append(
        check_exact_duplicates(df, text_column)
    )

    # Label checks — only if label column exists and labels are provided
    if label_column in df.columns and valid_labels:
        report.results.append(
            check_label_coverage(df, label_column, valid_labels)
        )
        report.results.append(
            check_class_distribution(df, label_column, min_examples=min_class_examples)
        )

    # PII check — only if patterns are provided
    if pii_patterns:
        report.results.append(
            check_pii_presence(df, text_column, pii_patterns)
        )

    logger.info("\n" + report.summary())
    return report


def main() -> None:
    """CLI runner to validate a CSV file against config.yaml rules."""
    import argparse
    from src.data.load_data import load_config, load_csv

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(description="Validate a complaint dataset against project rules.")
    parser.add_argument(
        "--data-path",
        type=str,
        default="data/raw/college_complaints_synthetic.csv",
        help="Path to CSV dataset to validate.",
    )
    parser.add_argument(
        "--config-path",
        type=str,
        default="config.yaml",
        help="Path to config.yaml.",
    )
    args = parser.parse_args()

    cfg = load_config(args.config_path)
    df = load_csv(args.data_path)

    valid_labels = list(cfg.get("categories", {}).keys())
    pii_patterns = cfg.get("preprocessing", {}).get("pii_patterns", [])

    report = validate_dataframe(
        df,
        text_column=cfg["data"]["text_column"],
        label_column=cfg["data"]["label_column"],
        valid_labels=valid_labels,
        min_text_length=cfg["data"].get("min_text_length", 10),
        min_class_examples=cfg.get("category_min_examples", 30),
        pii_patterns=pii_patterns,
    )

    print("\n" + "=" * 60)
    print("DATA VALIDATION REPORT")
    print("=" * 60)
    print(report.summary())
    print("=" * 60)

    if not report.passed:
        print(f"\nWARNING: {len(report.failed_checks)} check(s) flagged issues.")
    else:
        print("\nAll validation checks PASSED successfully.")


if __name__ == "__main__":
    main()

