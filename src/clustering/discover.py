"""
src/clustering/discover.py
---------------------------
Recurring issue and complaint pattern discovery (Phase 7).

Implements unsupervised clustering and topic extraction for campus complaint intelligence:
1. TF-IDF Representation with L2 normalization (Spherical feature space)
2. K-Means clustering (E8) with parameter tuning (Elbow inertia, Silhouette, Davies-Bouldin)
3. DBSCAN density-based clustering (E10) with Cosine distance metric for outlier identification
4. Automated cluster interpretation:
   - Representative complaint selection (nearest to cluster centroid / medoid)
   - Discriminative TF-IDF keyword extraction
   - Cross-tabulation against available metadata (categories, locations)
   - Small/weak cluster support warnings

Architectural & Domain Invariants:
- A text cluster represents lexical/topical similarity, NEVER a confirmed physical incident.
- Duplicate detection (Module B) focuses on high-precision incident pairs;
  clustering (Module D) groups broad operational themes and recurring patterns.
- Noise points in DBSCAN (label -1) are treated as valid unique complaints, not errors.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Sequence

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN, KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import davies_bouldin_score, silhouette_score
from sklearn.preprocessing import normalize

logger = logging.getLogger(__name__)


@dataclass
class ClusterSummary:
    """Detailed summary of an individual discovered complaint cluster."""
    cluster_id: int
    size: int
    representative_complaints: list[str]
    top_terms: list[str]
    silhouette_contribution: float | None = None
    category_distribution: dict[str, int] = field(default_factory=dict)
    location_distribution: dict[str, int] = field(default_factory=dict)
    is_weakly_supported: bool = False
    warning: str | None = None
    label: str = "Unnamed Cluster"

    def __repr__(self) -> str:
        weak_flag = " [WEAK]" if self.is_weakly_supported else ""
        return (
            f"Cluster {self.cluster_id}{weak_flag} (n={self.size}, label='{self.label}'): "
            f"top_terms={self.top_terms[:5]}"
        )


@dataclass
class ClusteringResult:
    """Comprehensive output of an unsupervised clustering experiment."""
    method: str
    n_clusters: int
    n_noise: int
    silhouette_score: float | None
    davies_bouldin_index: float | None
    inertia: float | None
    cluster_labels: list[int]
    clusters: list[ClusterSummary]
    notes: str = ""


def get_default_vectorizer(max_features: int = 1500) -> TfidfVectorizer:
    """Returns a standardized TF-IDF vectorizer suitable for complaint clustering."""
    return TfidfVectorizer(
        max_features=max_features,
        ngram_range=(1, 2),
        stop_words="english",
        min_df=2,
        sublinear_tf=True,
    )


def tune_kmeans_k(
    texts: Sequence[str],
    k_range: Sequence[int] = range(3, 13),
    random_seed: int = 42,
    vectorizer: TfidfVectorizer | None = None,
) -> pd.DataFrame:
    """Evaluate candidate values of k using Inertia, Silhouette Score, and Davies-Bouldin Index.
    
    Args:
        texts: List of complaint text strings.
        k_range: Candidate numbers of clusters to test.
        random_seed: Reproducibility seed.
        vectorizer: Optional pre-configured vectorizer.
        
    Returns:
        DataFrame with columns ['k', 'inertia', 'silhouette_score', 'davies_bouldin_index'].
    """
    clean_texts = [str(t) if pd.notna(t) else "" for t in texts]
    n_samples = len(clean_texts)

    if n_samples < 3:
        return pd.DataFrame(columns=["k", "inertia", "silhouette_score", "davies_bouldin_index"])

    vec = vectorizer or get_default_vectorizer()
    X = vec.fit_transform(clean_texts)
    X_norm = normalize(X, norm="l2")
    dense_X = X_norm.toarray()

    rows: list[dict[str, Any]] = []
    for k in k_range:
        if k >= n_samples:
            continue
        km = KMeans(n_clusters=k, random_state=random_seed, n_init=10)
        labels = km.fit_predict(dense_X)

        sil = None
        db_idx = None
        if 1 < len(set(labels)) < n_samples:
            try:
                sil = float(silhouette_score(dense_X, labels, metric="cosine"))
            except Exception:
                sil = None
            try:
                db_idx = float(davies_bouldin_score(dense_X, labels))
            except Exception:
                db_idx = None

        rows.append({
            "k": k,
            "inertia": float(km.inertia_),
            "silhouette_score": round(sil, 4) if sil is not None else None,
            "davies_bouldin_index": round(db_idx, 4) if db_idx is not None else None,
        })

    return pd.DataFrame(rows)


def run_kmeans(
    vectors_or_texts: Any,
    texts: Sequence[str] | None = None,
    *,
    k: int = 5,
    random_seed: int = 42,
    n_representatives: int = 3,
    vectorizer: TfidfVectorizer | None = None,
    categories: Sequence[str] | None = None,
    locations: Sequence[str] | None = None,
    min_cluster_size: int = 3,
) -> ClusteringResult:
    """Run K-Means clustering with L2-normalized representations and cluster interpretation.
    
    Args:
        vectors_or_texts: Either a feature matrix or a sequence of raw text strings.
        texts: Raw text strings if feature matrix was passed as first argument.
        k: Target cluster count.
        random_seed: Seed for reproducibility.
        n_representatives: Number of centroid-nearest complaints to extract per cluster.
        vectorizer: TfidfVectorizer used to extract top n-gram keywords.
        categories: Optional list of category labels for cross-tabulation.
        locations: Optional list of locations for cross-tabulation.
        min_cluster_size: Minimum threshold below which a cluster is flagged as weakly supported.
        
    Returns:
        ClusteringResult dataclass.
    """
    # Parse inputs
    if texts is None:
        raw_texts = [str(t) if pd.notna(t) else "" for t in vectors_or_texts]
        n_samples = len(raw_texts)
        if n_samples == 0:
            return ClusteringResult(
                method="K-Means",
                n_clusters=0,
                n_noise=0,
                silhouette_score=None,
                davies_bouldin_index=None,
                inertia=None,
                cluster_labels=[],
                clusters=[],
                notes="Empty input text sequence. No clusters generated.",
            )
        vec = vectorizer
        if vec is None:
            min_df = 1 if n_samples < 5 else 2
            vec = TfidfVectorizer(
                max_features=1500,
                ngram_range=(1, 2),
                stop_words="english",
                min_df=min_df,
                sublinear_tf=True,
            )
        try:
            X = vec.fit_transform(raw_texts)
        except ValueError:
            # Fallback for stop-word only or sparse small inputs
            try:
                vec = TfidfVectorizer(ngram_range=(1, 1), min_df=1)
                X = vec.fit_transform(raw_texts)
            except ValueError:
                X = np.zeros((n_samples, 1))
        fitted_vec = vec
    else:
        raw_texts = [str(t) if pd.notna(t) else "" for t in texts]
        n_samples = len(raw_texts)
        if n_samples == 0:
            return ClusteringResult(
                method="K-Means",
                n_clusters=0,
                n_noise=0,
                silhouette_score=None,
                davies_bouldin_index=None,
                inertia=None,
                cluster_labels=[],
                clusters=[],
                notes="Empty input text sequence. No clusters generated.",
            )
        X = vectors_or_texts
        fitted_vec = vectorizer


    # Adjust k if sample size is smaller than requested k
    actual_k = min(k, n_samples)
    if actual_k <= 1:
        single_cluster = ClusterSummary(
            cluster_id=0,
            size=n_samples,
            representative_complaints=raw_texts[:n_representatives],
            top_terms=[],
            is_weakly_supported=True,
            warning="Insufficient samples to partition into multiple clusters.",
        )
        return ClusteringResult(
            method="K-Means",
            n_clusters=1,
            n_noise=0,
            silhouette_score=None,
            davies_bouldin_index=None,
            inertia=0.0,
            cluster_labels=[0] * n_samples,
            clusters=[single_cluster],
            notes="Sample count <= 1. Returned single trivial cluster.",
        )

    # Normalize vectors to unit sphere so Euclidean distance is strictly monotonic with Cosine distance
    X_norm = normalize(X, norm="l2")
    dense_X = X_norm.toarray() if hasattr(X_norm, "toarray") else np.array(X_norm)

    km = KMeans(n_clusters=actual_k, random_state=random_seed, n_init=10)
    labels = km.fit_predict(dense_X)

    # Metrics
    sil_score = None
    db_idx = None
    if 1 < len(set(labels)) < n_samples:
        try:
            sil_score = float(silhouette_score(dense_X, labels, metric="cosine"))
        except Exception as exc:
            logger.debug("Silhouette calculation skipped: %s", exc)
        try:
            db_idx = float(davies_bouldin_score(dense_X, labels))
        except Exception as exc:
            logger.debug("Davies-Bouldin calculation skipped: %s", exc)

    feature_names = np.array(fitted_vec.get_feature_names_out()) if fitted_vec is not None else None

    clusters: list[ClusterSummary] = []
    for cid in range(actual_k):
        mask = labels == cid
        c_size = int(mask.sum())
        if c_size == 0:
            continue

        c_indices = np.where(mask)[0]
        c_vecs = dense_X[mask]
        centroid = km.cluster_centers_[cid]

        # Centroid distance ranking
        dists = np.linalg.norm(c_vecs - centroid, axis=1)
        sort_order = np.argsort(dists)
        rep_indices = c_indices[sort_order[:n_representatives]]
        representatives = [raw_texts[idx] for idx in rep_indices]

        # Top discriminative terms
        top_terms: list[str] = []
        if feature_names is not None and len(feature_names) > 0:
            top_kw_indices = np.argsort(centroid)[::-1][:8]
            top_terms = [feature_names[i] for i in top_kw_indices if centroid[i] > 0]

        # Metadata cross-tabulation
        cat_dist: dict[str, int] = {}
        if categories is not None and len(categories) == n_samples:
            cat_series = pd.Series([categories[i] for i in c_indices])
            cat_dist = cat_series.value_counts().to_dict()

        loc_dist: dict[str, int] = {}
        if locations is not None and len(locations) == n_samples:
            loc_series = pd.Series([locations[i] for i in c_indices])
            loc_dist = loc_series.value_counts().to_dict()

        is_weak = c_size < min_cluster_size
        warning_msg = (
            f"Cluster size (n={c_size}) is below minimum support threshold ({min_cluster_size}); "
            "insufficient statistical mass to treat as an established operational trend."
            if is_weak else None
        )

        clusters.append(ClusterSummary(
            cluster_id=cid,
            size=c_size,
            representative_complaints=representatives,
            top_terms=top_terms,
            silhouette_contribution=None,
            category_distribution=cat_dist,
            location_distribution=loc_dist,
            is_weakly_supported=is_weak,
            warning=warning_msg,
        ))

    return ClusteringResult(
        method="K-Means",
        n_clusters=len(clusters),
        n_noise=0,
        silhouette_score=round(sil_score, 4) if sil_score is not None else None,
        davies_bouldin_index=round(db_idx, 4) if db_idx is not None else None,
        inertia=round(float(km.inertia_), 4),
        cluster_labels=labels.tolist(),
        clusters=clusters,
        notes=(
            f"Spherical K-Means (L2-normalized TF-IDF, k={actual_k}). "
            "Clusters reflect lexical theme similarity; human verification required to confirm root causes."
        ),
    )


def run_dbscan(
    vectors_or_texts: Any,
    texts: Sequence[str] | None = None,
    *,
    eps: float = 0.55,
    min_samples: int = 3,
    n_representatives: int = 3,
    vectorizer: TfidfVectorizer | None = None,
    categories: Sequence[str] | None = None,
    locations: Sequence[str] | None = None,
) -> ClusteringResult:
    """Run DBSCAN density-based clustering using Cosine distance metric.
    
    Identifies natural density concentrations and isolates noise points (-1) without
    forcing unique complaints into artificial spherical clusters.
    
    Args:
        vectors_or_texts: Feature matrix or sequence of raw text strings.
        texts: Raw text strings if feature matrix was passed first.
        eps: Maximum cosine distance for points to be considered neighbors (0.0 to 1.0).
        min_samples: Minimum core neighborhood size.
        n_representatives: Number of sample complaints per cluster.
        vectorizer: TfidfVectorizer for top term extraction.
        categories: Optional category metadata.
        locations: Optional location metadata.
        
    Returns:
        ClusteringResult dataclass.
    """
    if texts is None:
        raw_texts = [str(t) if pd.notna(t) else "" for t in vectors_or_texts]
        n_samples = len(raw_texts)
        if n_samples == 0:
            return ClusteringResult(
                method="DBSCAN",
                n_clusters=0,
                n_noise=0,
                silhouette_score=None,
                davies_bouldin_index=None,
                inertia=None,
                cluster_labels=[],
                clusters=[],
                notes="Empty input sequence.",
            )
        vec = vectorizer
        if vec is None:
            min_df = 1 if n_samples < 5 else 2
            vec = TfidfVectorizer(
                max_features=1500,
                ngram_range=(1, 2),
                stop_words="english",
                min_df=min_df,
                sublinear_tf=True,
            )
        try:
            X = vec.fit_transform(raw_texts)
        except ValueError:
            try:
                vec = TfidfVectorizer(ngram_range=(1, 1), min_df=1)
                X = vec.fit_transform(raw_texts)
            except ValueError:
                X = np.zeros((n_samples, 1))
        fitted_vec = vec
    else:
        raw_texts = [str(t) if pd.notna(t) else "" for t in texts]
        n_samples = len(raw_texts)
        if n_samples == 0:
            return ClusteringResult(
                method="DBSCAN",
                n_clusters=0,
                n_noise=0,
                silhouette_score=None,
                davies_bouldin_index=None,
                inertia=None,
                cluster_labels=[],
                clusters=[],
                notes="Empty input sequence.",
            )
        X = vectors_or_texts
        fitted_vec = vectorizer


    # Unit-normalize vectors for cosine metric stability
    X_norm = normalize(X, norm="l2")
    dense_X = X_norm.toarray() if hasattr(X_norm, "toarray") else np.array(X_norm)

    db = DBSCAN(eps=eps, min_samples=min_samples, metric="cosine")
    labels = db.fit_predict(dense_X)

    unique_labels = set(labels)
    n_noise = int((labels == -1).sum())
    cluster_ids = sorted(lb for lb in unique_labels if lb != -1)
    n_clusters = len(cluster_ids)

    # Compute silhouette score on non-noise points if > 1 valid cluster exists
    sil_score = None
    non_noise_mask = labels != -1
    if non_noise_mask.sum() > min_samples and n_clusters > 1:
        try:
            sil_score = float(silhouette_score(
                dense_X[non_noise_mask], labels[non_noise_mask], metric="cosine"
            ))
        except Exception:
            sil_score = None

    feature_names = np.array(fitted_vec.get_feature_names_out()) if fitted_vec is not None else None

    clusters: list[ClusterSummary] = []
    for cid in cluster_ids:
        mask = labels == cid
        c_size = int(mask.sum())
        c_indices = np.where(mask)[0]
        c_vecs = dense_X[mask]

        # Representative complaints: use point closest to cluster mean vector
        c_mean = c_vecs.mean(axis=0)
        dists = np.linalg.norm(c_vecs - c_mean, axis=1)
        sort_order = np.argsort(dists)
        rep_indices = c_indices[sort_order[:n_representatives]]
        representatives = [raw_texts[idx] for idx in rep_indices]

        # Top terms for this density cluster
        top_terms: list[str] = []
        if feature_names is not None and len(feature_names) > 0:
            top_term_indices = np.argsort(c_mean)[::-1][:8]
            top_terms = [feature_names[i] for i in top_term_indices if c_mean[i] > 0]

        cat_dist: dict[str, int] = {}
        if categories is not None and len(categories) == n_samples:
            cat_series = pd.Series([categories[i] for i in c_indices])
            cat_dist = cat_series.value_counts().to_dict()

        loc_dist: dict[str, int] = {}
        if locations is not None and len(locations) == n_samples:
            loc_series = pd.Series([locations[i] for i in c_indices])
            loc_dist = loc_series.value_counts().to_dict()

        clusters.append(ClusterSummary(
            cluster_id=cid,
            size=c_size,
            representative_complaints=representatives,
            top_terms=top_terms,
            silhouette_contribution=None,
            category_distribution=cat_dist,
            location_distribution=loc_dist,
            is_weakly_supported=False,
            warning=None,
        ))

    return ClusteringResult(
        method="DBSCAN",
        n_clusters=n_clusters,
        n_noise=n_noise,
        silhouette_score=round(sil_score, 4) if sil_score is not None else None,
        davies_bouldin_index=None,
        inertia=None,
        cluster_labels=labels.tolist(),
        clusters=clusters,
        notes=(
            f"DBSCAN (metric=cosine, eps={eps}, min_samples={min_samples}). "
            f"Identified {n_clusters} dense clusters and {n_noise} noise points ({round(n_noise/n_samples*100, 1)}% of corpus). "
            "Noise points represent isolated or unique complaints."
        ),
    )
