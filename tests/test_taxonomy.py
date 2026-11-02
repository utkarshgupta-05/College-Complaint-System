"""
tests/test_taxonomy.py
----------------------
Regression test suite for the Canonical Complaint Taxonomy (Phase 11A).

Verifies:
1. Exactly 11 canonical categories exist (C01-C11) with exact finalized descriptions.
2. Department routing mappings and scope descriptions exist for all 11 codes.
3. Dataset splits (train.csv, val.csv, test.csv) strictly adhere to canonical taxonomy.
4. Model artifact classes_ matches canonical category codes.
5. Backend AI service aliases canonical taxonomy without discrepancy.
6. Frontend components reference canonical category codes.
"""

from __future__ import annotations

import json
from pathlib import Path
import joblib
import pandas as pd
import pytest

from src.taxonomy import (
    CANONICAL_TAXONOMY,
    CATEGORY_DEPARTMENTS,
    CATEGORY_DESCRIPTIONS,
    get_canonical_categories,
    get_category_name,
    get_department_for_category,
    validate_category_code,
)
from backend.services.ai_service import CATEGORY_NAMES

PROJECT_ROOT = Path(__file__).resolve().parent.parent

EXPECTED_TAXONOMY = {
    "C01": "Hostel and Accommodation",
    "C02": "Electricity and Water",
    "C03": "Internet and Network",
    "C04": "Mess and Food",
    "C05": "Academic and Examination",
    "C06": "Classroom and Laboratory",
    "C07": "Sanitation and Cleanliness",
    "C08": "Campus Safety",
    "C09": "Transportation",
    "C10": "Administrative Services",
    "C11": "Other / Unclassified",
}


def test_canonical_taxonomy_integrity():
    """Verify that CANONICAL_TAXONOMY matches the authoritative 11-category specification."""
    assert len(CANONICAL_TAXONOMY) == 11
    assert CANONICAL_TAXONOMY == EXPECTED_TAXONOMY
    assert get_canonical_categories() == [f"C{i:02d}" for i in range(1, 12)]


def test_department_routing_mappings():
    """Verify all 11 categories have non-empty department mappings and descriptions."""
    assert len(CATEGORY_DEPARTMENTS) == 11
    assert len(CATEGORY_DESCRIPTIONS) == 11
    for code in EXPECTED_TAXONOMY:
        assert code in CATEGORY_DEPARTMENTS
        assert len(CATEGORY_DEPARTMENTS[code]) > 5
        assert code in CATEGORY_DESCRIPTIONS
        assert len(CATEGORY_DESCRIPTIONS[code]) > 10


def test_taxonomy_helper_functions():
    """Verify lookup and validation helper functions."""
    assert validate_category_code("C01") is True
    assert validate_category_code("C11") is True
    assert validate_category_code("C12") is False
    assert validate_category_code("INVALID") is False

    assert get_category_name("C01") == "Hostel and Accommodation"
    assert get_category_name("UNKNOWN") == "Other / Unclassified"

    dept = get_department_for_category("C03")
    assert "IT" in dept or "Network" in dept
    assert get_department_for_category("UNKNOWN") == CATEGORY_DEPARTMENTS["C11"]


def test_dataset_splits_conform_to_canonical_taxonomy():
    """Verify train.csv, val.csv, and test.csv strictly conform to the 11 canonical categories."""
    for split in ["train", "val", "test"]:
        csv_path = PROJECT_ROOT / "data" / "processed" / f"{split}.csv"
        assert csv_path.exists(), f"Split missing: {csv_path}"
        df = pd.read_csv(csv_path)

        assert "category" in df.columns
        assert "category_name" in df.columns

        unique_codes = sorted(df["category"].unique())
        assert unique_codes == [f"C{i:02d}" for i in range(1, 12)], (
            f"Split {split}.csv has mismatched category codes: {unique_codes}"
        )

        # Check that category -> category_name mapping in CSV matches canonical taxonomy
        pairs = df[["category", "category_name"]].drop_duplicates()
        for _, row in pairs.iterrows():
            code = row["category"]
            name = row["category_name"]
            assert EXPECTED_TAXONOMY[code] == name, (
                f"Mismatch in {split}.csv for {code}: expected '{EXPECTED_TAXONOMY[code]}', got '{name}'"
            )


def test_backend_ai_service_taxonomy_match():
    """Verify that backend ai_service CATEGORY_NAMES strictly equals CANONICAL_TAXONOMY."""
    assert CATEGORY_NAMES == CANONICAL_TAXONOMY


def test_model_artifact_classes_match_taxonomy():
    """Verify that models/e2.joblib classifier classes_ match canonical category codes."""
    model_path = PROJECT_ROOT / "models" / "e2.joblib"
    assert model_path.exists()
    artifact = joblib.load(model_path)
    pipeline = artifact["pipeline"]
    classifier = pipeline.named_steps["clf"]
    assert hasattr(classifier, "classes_")
    classes = list(classifier.classes_)
    assert classes == [f"C{i:02d}" for i in range(1, 12)]


def test_frontend_components_taxonomy_codes():
    """Verify that frontend React components reference all 11 canonical codes."""
    frontend_dir = PROJECT_ROOT / "frontend" / "src" / "components"
    components_to_check = [
        "AdminDashboard.jsx",
        "ComplaintDetailModal.jsx",
        "StaffPortal.jsx",
        "StudentPortal.jsx",
    ]
    for comp in components_to_check:
        comp_path = frontend_dir / comp
        assert comp_path.exists(), f"Frontend component missing: {comp_path}"
        content = comp_path.read_text(encoding="utf-8")
        for code in EXPECTED_TAXONOMY:
            assert f"'{code}'" in content or f'"{code}"' in content or f"{code}:" in content, (
                f"Category code {code} missing in {comp}"
            )

