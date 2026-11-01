"""
src/duplicates/similarity.py
------------------------------
Similarity-based duplicate and related-complaint detection for Module B.

Two approaches implemented and evaluated:
  Approach 1 (E6) — TF-IDF + Cosine Similarity (Lexical Baseline)
    Fast, interpretable, zero deep learning dependencies.
    Captures lexical overlap and near-exact / template duplicates.

  Approach 2 (E7) — Sentence Transformer Embeddings + Cosine Similarity (Semantic)
    Dense contextual representation using all-MiniLM-L6-v2.
    Captures semantic similarity across paraphrased student complaints.

Ethical Design Mandate:
  - This system NEVER automatically merges, deletes, suppresses, or rejects complaints.
  - All surfaced duplicates are advisory suggestions for authorized human staff review.
  - Thresholds distinguish:
      PROBABLE_DUPLICATE: score >= high_threshold (flag for immediate human review)
      SIMILAR: mid_threshold <= score < high_threshold (potential related incident)
      UNRELATED: score < mid_threshold
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.data.preprocess import normalize_text

logger = logging.getLogger(__name__)


class SimilarityLevel(str, Enum):
    """Classification of similarity between complaint pairs."""
    PROBABLE_DUPLICATE = "PROBABLE_DUPLICATE"
    SIMILAR = "SIMILAR"
    UNRELATED = "UNRELATED"


@dataclass
class SimilarComplaint:
    """A candidate similar complaint surfaced for human review."""
    complaint_id: Any
    complaint_text: str
    similarity_score: float
    similarity_level: SimilarityLevel
    category: str | None = None
    location: str | None = None
    created_at: str | None = None

    def __repr__(self) -> str:
        return (
            f"SimilarComplaint(id={self.complaint_id}, "
            f"score={self.similarity_score:.3f}, "
            f"level={self.similarity_level.value})"
        )


# Default thresholds tuned on validation data in Phase 5
DEFAULT_HIGH_THRESHOLD = 0.80   # Probable duplicate -> review immediately
DEFAULT_MID_THRESHOLD = 0.50    # Similar complaint -> may be related


class TFIDFSimilarityRetriever:
    """Retrieve candidate similar complaints using lexical TF-IDF cosine similarity.

    Experiment E6 Baseline.
    """

    def __init__(
        self,
        high_threshold: float = DEFAULT_HIGH_THRESHOLD,
        mid_threshold: float = DEFAULT_MID_THRESHOLD,
        max_features: int = 10000,
        ngram_range: tuple[int, int] = (1, 2),
        sublinear_tf: bool = True,
    ) -> None:
        self.high_threshold = high_threshold
        self.mid_threshold = mid_threshold
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=ngram_range,
            sublinear_tf=sublinear_tf,
            preprocessor=normalize_text,
        )
        self._corpus_matrix = None
        self._corpus_ids: list[Any] = []
        self._corpus_texts: list[str] = []
        self._corpus_metadata: list[dict[str, Any]] = []
        self._fitted = False

    def fit(
        self,
        texts: list[str],
        ids: list[Any],
        metadata: list[dict[str, Any]] | None = None,
    ) -> "TFIDFSimilarityRetriever":
        """Fit the vectorizer on the existing complaint corpus."""
        if len(texts) != len(ids):
            raise ValueError(
                f"texts ({len(texts)}) and ids ({len(ids)}) must have identical lengths."
            )

        # Handle empty corpus safely
        if len(texts) == 0:
            logger.warning("Fitting TFIDFSimilarityRetriever on empty corpus.")
            self._corpus_ids = []
            self._corpus_texts = []
            self._corpus_metadata = []
            self._corpus_matrix = None
            self._fitted = True
            return self

        # Clean non-string texts
        safe_texts = [str(t) if t is not None else "" for t in texts]

        self._corpus_matrix = self.vectorizer.fit_transform(safe_texts)
        self._corpus_ids = list(ids)
        self._corpus_texts = list(texts)
        self._corpus_metadata = list(metadata) if metadata is not None else [{} for _ in ids]
        self._fitted = True
        logger.info("TFIDFSimilarityRetriever fitted on %d complaints.", len(texts))
        return self

    def find_similar(
        self,
        query_text: str,
        query_id: Any | None = None,
        top_k: int = 10,
        exclude_ids: list[Any] | None = None,
        return_all: bool = False,
    ) -> list[SimilarComplaint]:
        """Find candidate similar complaints for a query.

        Args:
            query_text: The new complaint text.
            query_id: Optional ID of the query complaint (automatically excluded).
            top_k: Maximum candidate complaints to return.
            exclude_ids: Additional complaint IDs to exclude.
            return_all: If True, returns top_k regardless of mid_threshold.
                        If False, filters to score >= mid_threshold.

        Returns:
            List of SimilarComplaint objects ranked by score descending.
        """
        if not self._fitted:
            raise RuntimeError("Retriever must be fitted before calling find_similar().")

        if not isinstance(query_text, str) or not query_text.strip():
            logger.warning("Empty or invalid query_text received.")
            return []

        if len(self._corpus_ids) == 0 or self._corpus_matrix is None:
            return []

        exclude_set = set(exclude_ids or [])
        if query_id is not None:
            exclude_set.add(query_id)

        query_vec = self.vectorizer.transform([query_text])
        scores = cosine_similarity(query_vec, self._corpus_matrix)[0]

        ranked_indices = np.argsort(scores)[::-1]
        results: list[SimilarComplaint] = []

        for idx in ranked_indices:
            if len(results) >= top_k:
                break
            cid = self._corpus_ids[idx]
            if cid in exclude_set:
                continue

            score = float(scores[idx])
            if not return_all and score < self.mid_threshold:
                break  # Array is sorted descending

            level = self._score_to_level(score)
            meta = self._corpus_metadata[idx] if idx < len(self._corpus_metadata) else {}

            results.append(
                SimilarComplaint(
                    complaint_id=cid,
                    complaint_text=self._corpus_texts[idx],
                    similarity_score=score,
                    similarity_level=level,
                    category=meta.get("category"),
                    location=meta.get("location"),
                    created_at=meta.get("created_at"),
                )
            )

        return results

    def _score_to_level(self, score: float) -> SimilarityLevel:
        if score >= self.high_threshold:
            return SimilarityLevel.PROBABLE_DUPLICATE
        elif score >= self.mid_threshold:
            return SimilarityLevel.SIMILAR
        return SimilarityLevel.UNRELATED


class EmbeddingSimilarityRetriever:
    """Retrieve candidate similar complaints using dense sentence embeddings.

    Experiment E7 Semantic Model using sentence-transformers (all-MiniLM-L6-v2).
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        high_threshold: float = DEFAULT_HIGH_THRESHOLD,
        mid_threshold: float = DEFAULT_MID_THRESHOLD,
    ) -> None:
        self.model_name = model_name
        self.high_threshold = high_threshold
        self.mid_threshold = mid_threshold
        self._model = None
        self._corpus_embeddings = None
        self._corpus_ids: list[Any] = []
        self._corpus_texts: list[str] = []
        self._corpus_metadata: list[dict[str, Any]] = []
        self._fitted = False

    def _load_model(self) -> None:
        """Lazy-load the sentence transformer model."""
        if self._model is None:
            try:
                import os
                from sentence_transformers import SentenceTransformer
                logger.info("Loading sentence transformer: %s", self.model_name)
                try:
                    self._model = SentenceTransformer(self.model_name)
                except Exception as net_err:
                    logger.info("Network request failed (%s). Loading from offline cache...", net_err)
                    os.environ["HF_HUB_OFFLINE"] = "1"
                    os.environ["TRANSFORMERS_OFFLINE"] = "1"
                    self._model = SentenceTransformer(self.model_name, local_files_only=True)
            except ImportError as e:
                raise ImportError(
                    "sentence-transformers is required for EmbeddingSimilarityRetriever. "
                    "Install it with: pip install sentence-transformers"
                ) from e

    def fit(
        self,
        texts: list[str],
        ids: list[Any],
        metadata: list[dict[str, Any]] | None = None,
    ) -> "EmbeddingSimilarityRetriever":
        """Compute and cache normalized embeddings for corpus."""
        if len(texts) != len(ids):
            raise ValueError(
                f"texts ({len(texts)}) and ids ({len(ids)}) must have identical lengths."
            )

        if len(texts) == 0:
            logger.warning("Fitting EmbeddingSimilarityRetriever on empty corpus.")
            self._corpus_ids = []
            self._corpus_texts = []
            self._corpus_metadata = []
            self._corpus_embeddings = None
            self._fitted = True
            return self

        self._load_model()
        safe_texts = [str(t) if t is not None else "" for t in texts]

        logger.info("Encoding %d complaints using %s...", len(safe_texts), self.model_name)
        embeddings = self._model.encode(
            safe_texts,
            batch_size=64,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        self._corpus_embeddings = np.asarray(embeddings, dtype=np.float32)
        self._corpus_ids = list(ids)
        self._corpus_texts = list(texts)
        self._corpus_metadata = list(metadata) if metadata is not None else [{} for _ in ids]
        self._fitted = True
        return self

    def find_similar(
        self,
        query_text: str,
        query_id: Any | None = None,
        top_k: int = 10,
        exclude_ids: list[Any] | None = None,
        return_all: bool = False,
    ) -> list[SimilarComplaint]:
        """Find candidate semantically similar complaints for a query."""
        if not self._fitted:
            raise RuntimeError("Retriever must be fitted before calling find_similar().")

        if not isinstance(query_text, str) or not query_text.strip():
            logger.warning("Empty or invalid query_text received.")
            return []

        if len(self._corpus_ids) == 0 or self._corpus_embeddings is None:
            return []

        self._load_model()
        exclude_set = set(exclude_ids or [])
        if query_id is not None:
            exclude_set.add(query_id)

        query_emb = self._model.encode(
            [query_text],
            normalize_embeddings=True,
            show_progress_bar=False,
        )[0]

        # Normalized embeddings cosine similarity = dot product
        scores = np.dot(self._corpus_embeddings, query_emb)

        ranked_indices = np.argsort(scores)[::-1]
        results: list[SimilarComplaint] = []

        for idx in ranked_indices:
            if len(results) >= top_k:
                break
            cid = self._corpus_ids[idx]
            if cid in exclude_set:
                continue

            score = float(scores[idx])
            if not return_all and score < self.mid_threshold:
                break

            level = self._score_to_level(score)
            meta = self._corpus_metadata[idx] if idx < len(self._corpus_metadata) else {}

            results.append(
                SimilarComplaint(
                    complaint_id=cid,
                    complaint_text=self._corpus_texts[idx],
                    similarity_score=score,
                    similarity_level=level,
                    category=meta.get("category"),
                    location=meta.get("location"),
                    created_at=meta.get("created_at"),
                )
            )

        return results

    def _score_to_level(self, score: float) -> SimilarityLevel:
        if score >= self.high_threshold:
            return SimilarityLevel.PROBABLE_DUPLICATE
        elif score >= self.mid_threshold:
            return SimilarityLevel.SIMILAR
        return SimilarityLevel.UNRELATED
