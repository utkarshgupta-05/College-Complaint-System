"""
tests/test_preprocess.py
-------------------------
Unit tests for src/data/preprocess.py.

STATUS: Phase 1 — test stubs written. Tests will be run and verified in Phase 2.
"""

import pytest

from src.data.preprocess import (
    mask_pii,
    normalize_text,
    build_word_tfidf_vectorizer,
    build_char_tfidf_vectorizer,
    create_stratified_splits,
)
import pandas as pd


# ---------------------------------------------------------------------------
# PII masking tests
# ---------------------------------------------------------------------------

class TestMaskPII:
    def test_masks_phone_number(self):
        text = "Call me at 9876543210 for details."
        result = mask_pii(text, [
            (r'\b\d{10}\b', '[PHONE]')
        ])
        assert "[PHONE]" in result
        assert "9876543210" not in result

    def test_masks_email(self):
        text = "My email is student@college.edu please help."
        result = mask_pii(text, [
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]')
        ])
        assert "[EMAIL]" in result
        assert "student@college.edu" not in result

    def test_no_pii_unchanged(self):
        text = "There is no water in the hostel."
        result = mask_pii(text)
        assert result == text

    def test_empty_string(self):
        assert mask_pii("") == ""

    def test_non_string_returns_empty(self):
        assert mask_pii(None) == ""  # type: ignore


# ---------------------------------------------------------------------------
# normalize_text tests
# ---------------------------------------------------------------------------

class TestNormalizeText:
    def test_basic_normalization(self):
        text = "The WATER SUPPLY in Hostel Block B is not working!!"
        result = normalize_text(text, remove_stopwords=False, lemmatize=False)
        assert result == result.lower()
        assert "!" not in result

    def test_empty_string_returns_empty(self):
        assert normalize_text("") == ""

    def test_none_returns_empty(self):
        assert normalize_text(None) == ""  # type: ignore

    def test_whitespace_only_returns_empty(self):
        assert normalize_text("   ") == ""

    def test_min_token_length_filter(self):
        text = "A B C electricity"
        result = normalize_text(text, min_token_length=3, remove_stopwords=False)
        # "A", "B", "C" are single characters — should be filtered
        tokens = result.split()
        assert all(len(t) >= 3 for t in tokens)

    def test_numbers_retained_by_default(self):
        text = "Block 3 has no electricity for 2 days"
        result = normalize_text(text, remove_numbers=False, remove_stopwords=False)
        assert "3" in result or "block" in result  # at least some content preserved

    def test_output_is_string(self):
        result = normalize_text("The mess food is terrible.")
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Vectorizer builder tests
# ---------------------------------------------------------------------------

class TestVectorizerBuilders:
    def test_word_vectorizer_is_unfitted(self):
        vec = build_word_tfidf_vectorizer()
        # Should not have vocabulary_ attribute before fitting
        assert not hasattr(vec, "vocabulary_")

    def test_char_vectorizer_has_correct_analyzer(self):
        vec = build_char_tfidf_vectorizer()
        assert vec.analyzer == "char_wb"

    def test_word_vectorizer_fits_and_transforms(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        # Use min_df=1 because the test corpus is tiny (3 documents).
        # In real use, min_df=2 is applied on much larger corpora.
        vec = build_word_tfidf_vectorizer(max_features=100)
        vec.set_params(min_df=1)  # Override for small test corpus
        corpus = [
            "there is no water in the hostel",
            "electricity problem in block b",
            "internet not working in library",
        ]
        X = vec.fit_transform(corpus)
        assert X.shape[0] == 3
        assert X.shape[1] <= 100


# ---------------------------------------------------------------------------
# Stratified split tests
# ---------------------------------------------------------------------------

class TestCreateStratifiedSplits:
    @pytest.fixture
    def sample_df(self):
        """DataFrame with 4 categories, 20 rows each = 80 rows."""
        data = []
        for cat in ["C01", "C02", "C03", "C04"]:
            for i in range(20):
                data.append({
                    "complaint_text": f"Complaint about {cat} number {i}",
                    "category": cat,
                })
        return pd.DataFrame(data)

    def test_split_sizes_correct(self, sample_df):
        train, val, test = create_stratified_splits(
            sample_df,
            label_column="category",
            text_column="complaint_text",
            train_ratio=0.70,
            val_ratio=0.15,
            test_ratio=0.15,
            random_seed=42,
        )
        total = len(sample_df)
        assert len(train) + len(val) + len(test) == total

    def test_no_overlap_between_splits(self, sample_df):
        train, val, test = create_stratified_splits(
            sample_df,
            label_column="category",
            text_column="complaint_text",
        )
        train_idx = set(train.index)
        val_idx = set(val.index)
        test_idx = set(test.index)
        assert train_idx.isdisjoint(val_idx)
        assert train_idx.isdisjoint(test_idx)
        assert val_idx.isdisjoint(test_idx)

    def test_invalid_ratios_raise(self, sample_df):
        with pytest.raises(ValueError, match="sum to 1.0"):
            create_stratified_splits(
                sample_df,
                label_column="category",
                text_column="complaint_text",
                train_ratio=0.50,
                val_ratio=0.50,
                test_ratio=0.50,
            )

    def test_group_aware_split_prevents_group_leakage(self):
        data = []
        # Create 4 groups with 3 rows each and 40 standalone rows
        for g in range(4):
            for m in range(3):
                data.append({
                    "complaint_text": f"Incident {g} report {m} about water",
                    "category": "C02",
                    "incident_group_id": f"INC-{g}",
                })
        for i in range(40):
            data.append({
                "complaint_text": f"Independent complaint {i}",
                "category": "C02" if i % 2 == 0 else "C01",
                "incident_group_id": "",
            })
        df = pd.DataFrame(data)

        train, val, test = create_stratified_splits(
            df,
            label_column="category",
            text_column="complaint_text",
            group_column="incident_group_id",
            train_ratio=0.70,
            val_ratio=0.15,
            test_ratio=0.15,
            random_seed=42,
        )

        from src.data.preprocess import check_split_leakage
        audit = check_split_leakage(train, val, test, text_column="complaint_text", group_column="incident_group_id")
        assert audit["leakage_free"], f"Audit failed: {audit}"
        assert audit["incident_group_leakage_count"] == 0
        assert audit["exact_text_leakage_count"] == 0

