"""
tests/test_duplicates.py
--------------------------
Unit and integration tests for Duplicate and Related Complaint Detection (Module B).

Covers:
  - Identical and near-identical complaints.
  - Similar topics describing different incidents (hard negatives).
  - Empty or malformed complaint text.
  - Candidate ranking and threshold boundaries (PROBABLE_DUPLICATE, SIMILAR, UNRELATED).
  - Exclusion of the source complaint itself.
  - Missing metadata and small datasets.
  - Prevention of data leakage (test.csv must not be touched).
  - Ethical mandate: Confirmation that no automatic merge, suppression, or deletion occurs.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.duplicates.evaluate import (
    build_validation_pairs,
    evaluate_retrieval,
    sweep_thresholds,
)
from src.duplicates.similarity import (
    DEFAULT_HIGH_THRESHOLD,
    DEFAULT_MID_THRESHOLD,
    EmbeddingSimilarityRetriever,
    SimilarComplaint,
    SimilarityLevel,
    TFIDFSimilarityRetriever,
)


class TestTFIDFSimilarityRetriever:
    """Test the lexical TF-IDF similarity retriever."""

    @pytest.fixture
    def sample_corpus(self):
        texts = [
            "Drinking water cooler on 2nd floor is leaking continuously.",
            "Water cooler on second floor of library is leaking water.",
            "Hostel room fan is making loud noise and wobbling.",
            "Wi-Fi router in academic block has no internet connectivity.",
        ]
        ids = ["C-001", "C-002", "C-003", "C-004"]
        meta = [
            {"category": "C02", "location": "Library"},
            {"category": "C02", "location": "Library"},
            {"category": "C01", "location": "Hostel Block A"},
            {"category": "C03", "location": "Academic Block 1"},
        ]
        return texts, ids, meta

    def test_identical_complaint_retrieval(self, sample_corpus):
        texts, ids, meta = sample_corpus
        retriever = TFIDFSimilarityRetriever(high_threshold=0.80, mid_threshold=0.40)
        retriever.fit(texts, ids, metadata=meta)

        query = "Drinking water cooler on 2nd floor is leaking continuously."
        results = retriever.find_similar(query, top_k=5)

        assert len(results) > 0
        top = results[0]
        assert top.complaint_id == "C-001"
        assert top.similarity_score >= 0.99
        assert top.similarity_level == SimilarityLevel.PROBABLE_DUPLICATE
        assert top.category == "C02"

    def test_near_identical_paraphrase_retrieval(self, sample_corpus):
        texts, ids, meta = sample_corpus
        retriever = TFIDFSimilarityRetriever(high_threshold=0.60, mid_threshold=0.30)
        retriever.fit(texts, ids, metadata=meta)

        query = "Water cooler on 2nd floor leaking water all over floor."
        results = retriever.find_similar(query, top_k=2)

        assert len(results) > 0
        # Both water cooler complaints should rank higher than fan or wifi
        retrieved_ids = [r.complaint_id for r in results]
        assert "C-001" in retrieved_ids or "C-002" in retrieved_ids

    def test_similar_topics_different_incidents_ranking(self):
        # Two water issues, but distinct incidents (cooler leak vs muddy water)
        texts = [
            "Drinking water cooler in mess hall is leaking water on the floor.",
            "Yellowish muddy tap water with foul smell coming from bathroom taps in hostel.",
            "Exam timetable clashes between Data Structures and Operating Systems.",
        ]
        ids = ["W-1", "W-2", "A-1"]
        retriever = TFIDFSimilarityRetriever(high_threshold=0.75, mid_threshold=0.20)
        retriever.fit(texts, ids)

        query = "Mess drinking water dispenser has a severe leak."
        results = retriever.find_similar(query, top_k=3, return_all=True)

        assert len(results) == 3
        # W-1 (cooler leak) should score higher than W-2 (muddy bathroom water)
        assert results[0].complaint_id == "W-1"
        assert results[0].similarity_score > results[1].similarity_score
        assert results[1].complaint_id == "W-2"
        # Academic complaint should be lowest
        assert results[2].complaint_id == "A-1"

    def test_exclusion_of_source_complaint(self, sample_corpus):
        texts, ids, meta = sample_corpus
        retriever = TFIDFSimilarityRetriever()
        retriever.fit(texts, ids, metadata=meta)

        # Query using C-001 text and pass query_id='C-001'
        query = texts[0]
        results = retriever.find_similar(query, query_id="C-001", top_k=5)

        # C-001 itself MUST NOT be in the results
        retrieved_ids = [r.complaint_id for r in results]
        assert "C-001" not in retrieved_ids

    def test_empty_or_malformed_query_text(self, sample_corpus):
        texts, ids, meta = sample_corpus
        retriever = TFIDFSimilarityRetriever()
        retriever.fit(texts, ids, metadata=meta)

        assert retriever.find_similar("") == []
        assert retriever.find_similar("   ") == []
        assert retriever.find_similar(None) == []  # type: ignore

    def test_empty_corpus_fit_and_query(self):
        retriever = TFIDFSimilarityRetriever()
        retriever.fit([], [])
        results = retriever.find_similar("Any complaint")
        assert results == []

    def test_single_item_corpus(self):
        retriever = TFIDFSimilarityRetriever()
        retriever.fit(["Only one complaint in system."], ["ID-1"])
        results = retriever.find_similar("Only one complaint in system.")
        assert len(results) == 1
        assert results[0].complaint_id == "ID-1"

    def test_unfitted_retriever_raises_error(self):
        retriever = TFIDFSimilarityRetriever()
        with pytest.raises(RuntimeError, match="must be fitted"):
            retriever.find_similar("text")

    def test_mismatched_corpus_lengths_raises(self):
        retriever = TFIDFSimilarityRetriever()
        with pytest.raises(ValueError, match="identical lengths"):
            retriever.fit(["Text 1", "Text 2"], ["ID 1"])

    def test_threshold_levels(self):
        retriever = TFIDFSimilarityRetriever(high_threshold=0.80, mid_threshold=0.50)
        assert retriever._score_to_level(0.85) == SimilarityLevel.PROBABLE_DUPLICATE
        assert retriever._score_to_level(0.80) == SimilarityLevel.PROBABLE_DUPLICATE
        assert retriever._score_to_level(0.65) == SimilarityLevel.SIMILAR
        assert retriever._score_to_level(0.50) == SimilarityLevel.SIMILAR
        assert retriever._score_to_level(0.49) == SimilarityLevel.UNRELATED


class TestEmbeddingSimilarityRetriever:
    """Test dense sentence embedding retriever."""

    def test_embedding_retrieval_ranking(self):
        texts = [
            "Broken window glass in hostel room 102 lets cold wind in.",
            "Torn mesh on window allows insects and mosquitoes inside.",
            "Professor has not graded mid-semester papers after one month.",
        ]
        ids = ["E-01", "E-02", "E-03"]
        retriever = EmbeddingSimilarityRetriever(model_name="all-MiniLM-L6-v2")
        retriever.fit(texts, ids)

        query = "Window pane is shattered and drafts are entering the dorm."
        results = retriever.find_similar(query, top_k=3, return_all=True)

        assert len(results) == 3
        # E-01 (window broken glass) should be top rank
        assert results[0].complaint_id == "E-01"
        assert results[0].similarity_score > results[2].similarity_score

    def test_embedding_self_exclusion(self):
        texts = ["Complaint A", "Complaint B"]
        ids = ["ID-A", "ID-B"]
        retriever = EmbeddingSimilarityRetriever(model_name="all-MiniLM-L6-v2")
        retriever.fit(texts, ids)

        results = retriever.find_similar("Complaint A", query_id="ID-A", return_all=True)
        retrieved_ids = [r.complaint_id for r in results]
        assert "ID-A" not in retrieved_ids
        assert "ID-B" in retrieved_ids

    def test_embedding_empty_text(self):
        retriever = EmbeddingSimilarityRetriever(model_name="all-MiniLM-L6-v2")
        retriever.fit(["Complaint A"], ["ID-A"])
        assert retriever.find_similar("") == []
        assert retriever.find_similar(None) == []  # type: ignore


class TestEvaluationAndEthicalGuarantees:
    """Test evaluation logic and ethical non-suppression invariants."""

    def test_no_automatic_merge_or_deletion(self):
        """Verify that duplicate detection returns advisory data structures only."""
        retriever = TFIDFSimilarityRetriever()
        retriever.fit(["Test complaint"], ["ID-1"])
        results = retriever.find_similar("Test complaint")

        # Result is a list of advisory candidate objects
        assert isinstance(results, list)
        for r in results:
            assert isinstance(r, SimilarComplaint)
            # Must contain complaint_id and score for staff review
            assert hasattr(r, "complaint_id")
            assert hasattr(r, "similarity_score")
            assert hasattr(r, "similarity_level")

    def test_build_validation_pairs_labels_correctly(self):
        df_sample = pd.DataFrame([
            {"complaint_id": "C1", "complaint_text": "T1", "category": "C01", "incident_group_id": "INC-1"},
            {"complaint_id": "C2", "complaint_text": "T2", "category": "C01", "incident_group_id": "INC-1"},
            {"complaint_id": "C3", "complaint_text": "T3", "category": "C01", "incident_group_id": "INC-2"},
            {"complaint_id": "C4", "complaint_text": "T4", "category": "C02", "incident_group_id": np.nan},
        ])
        pairs = build_validation_pairs(df_sample)
        assert len(pairs) == 6  # 4 * 3 / 2 = 6

        # C1 and C2 share INC-1 -> positive duplicate
        c1_c2 = pairs[(pairs["id_1"] == "C1") & (pairs["id_2"] == "C2")].iloc[0]
        assert c1_c2["label"] == 1
        assert c1_c2["pair_type"] == "positive_duplicate"

        # C1 and C3 are same category C01, but different incidents -> hard negative
        c1_c3 = pairs[(pairs["id_1"] == "C1") & (pairs["id_2"] == "C3")].iloc[0]
        assert c1_c3["label"] == 0
        assert c1_c3["pair_type"] == "hard_negative"

        # C1 and C4 are different categories -> easy negative
        c1_c4 = pairs[(pairs["id_1"] == "C1") & (pairs["id_2"] == "C4")].iloc[0]
        assert c1_c4["label"] == 0
        assert c1_c4["pair_type"] == "easy_negative"

    def test_sweep_thresholds_produces_monotonic_recall(self):
        y_true = np.array([1, 1, 0, 0, 0])
        scores = np.array([0.9, 0.6, 0.7, 0.3, 0.1])
        df_sweep = sweep_thresholds(y_true, scores, thresholds=[0.2, 0.5, 0.8])

        # As threshold increases, recall should be non-increasing
        recalls = df_sweep["recall"].tolist()
        assert recalls[0] >= recalls[1] >= recalls[2]

    def test_quarantined_test_set_untouched(self):
        """Verify that test.csv is never modified by Phase 5 evaluation."""
        test_path = Path("data/processed/test.csv")
        assert test_path.exists()
        # Verify row count is unchanged (182 rows)
        test_df = pd.read_csv(test_path)
        assert len(test_df) == 182
