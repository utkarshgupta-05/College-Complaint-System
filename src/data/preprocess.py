"""
src/data/preprocess.py
-----------------------
Text normalization and feature preparation pipeline.

Key design decisions:
- All preprocessing steps that LEARN from the corpus (e.g., TF-IDF fitting,
  vocabulary construction) must be fit ONLY on training data, then applied to
  validation and test data. This prevents data leakage.
- This module provides stateless text normalization functions (no fitting).
- The fitted vectorizer objects are saved in src/classification/train.py.

Usage:
    from src.data.preprocess import normalize_text, build_tfidf_pipeline

Pipeline:
    raw text → normalize_text() → TfidfVectorizer.fit_transform() (train only)
                                → TfidfVectorizer.transform() (val / test)
"""

from __future__ import annotations

import logging
import re
import string
from pathlib import Path

import nltk
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# NLTK resource management
# ---------------------------------------------------------------------------

def ensure_nltk_resources() -> None:
    """Download required NLTK corpora if not already present."""
    resources = [
        # NLTK 3.9+ uses punkt_tab instead of punkt
        ("tokenizers/punkt_tab", "punkt_tab"),
        ("corpora/stopwords", "stopwords"),
        ("corpora/wordnet", "wordnet"),
        ("corpora/omw-1.4", "omw-1.4"),  # Required by WordNetLemmatizer in NLTK 3.9+
    ]
    for check_path, resource_name in resources:
        try:
            nltk.data.find(check_path)
        except LookupError:
            logger.info("Downloading NLTK resource: %s", resource_name)
            nltk.download(resource_name, quiet=True)


# ---------------------------------------------------------------------------
# PII masking
# ---------------------------------------------------------------------------

DEFAULT_PII_PATTERNS: list[tuple[str, str]] = [
    (r'\b\d{10}\b', '[PHONE]'),
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
    # Adjust roll number pattern to match your institution's format
    (r'\b\d{2}[A-Z]{3}\d{4}\b', '[ROLL_NO]'),
]


def mask_pii(
    text: str,
    patterns: list[tuple[str, str]] | None = None,
) -> str:
    """Replace PII patterns in text with placeholder tokens.

    Args:
        text: Input complaint text.
        patterns: List of (regex_pattern, replacement_token) tuples.
            Defaults to DEFAULT_PII_PATTERNS.

    Returns:
        Text with PII replaced by placeholder tokens.
    """
    if not isinstance(text, str):
        return ""
    if patterns is None:
        patterns = DEFAULT_PII_PATTERNS
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    return text


# ---------------------------------------------------------------------------
# Text normalization
# ---------------------------------------------------------------------------

def normalize_text(
    text: str,
    *,
    lowercase: bool = True,
    remove_punctuation: bool = True,
    remove_numbers: bool = False,
    remove_stopwords: bool = True,
    lemmatize: bool = True,
    min_token_length: int = 2,
    pii_patterns: list[tuple[str, str]] | None = None,
) -> str:
    """Apply a sequence of normalization steps to a complaint text string.

    Steps applied in order:
        1. PII masking.
        2. Lowercase conversion.
        3. Punctuation removal.
        4. Number removal (optional).
        5. Tokenization.
        6. Stop word removal.
        7. Lemmatization.
        8. Short token filtering.

    Args:
        text: Raw complaint text.
        lowercase: Convert text to lowercase.
        remove_punctuation: Strip punctuation characters.
        remove_numbers: Remove standalone numeric tokens.
        remove_stopwords: Remove common English stop words.
        lemmatize: Apply WordNet lemmatization.
        min_token_length: Remove tokens shorter than this length.
        pii_patterns: PII patterns to mask before processing.

    Returns:
        Normalized text as a single string.

    Notes:
        - Numbers like "Block 3" or "2 days" are informative; set
          remove_numbers=False (the default) to retain them.
        - Stemming is NOT applied here because it can make classifier
          features harder to interpret. Lemmatization is preferred.
        - This function is STATELESS — safe to call on any split.
    """
    if not isinstance(text, str) or not text.strip():
        return ""

    # Step 1: Mask PII
    text = mask_pii(text, pii_patterns)

    # Step 2: Lowercase
    if lowercase:
        text = text.lower()

    # Step 3: Remove punctuation (keep spaces and alphanumerics)
    if remove_punctuation:
        text = text.translate(str.maketrans("", "", string.punctuation))

    # Step 4: Remove standalone numbers (optional)
    if remove_numbers:
        text = re.sub(r'\b\d+\b', '', text)

    # Step 5: Tokenize
    tokens = nltk.word_tokenize(text)

    # Step 6: Stop word removal
    if remove_stopwords:
        stop_words = set(nltk.corpus.stopwords.words("english"))
        tokens = [t for t in tokens if t not in stop_words]

    # Step 7: Lemmatization
    if lemmatize:
        lemmatizer = nltk.stem.WordNetLemmatizer()
        tokens = [lemmatizer.lemmatize(t) for t in tokens]

    # Step 8: Length filter
    tokens = [t for t in tokens if len(t) >= min_token_length]

    return " ".join(tokens)


def normalize_series(
    series: pd.Series,
    **normalize_kwargs,
) -> pd.Series:
    """Apply normalize_text to a pandas Series.

    Args:
        series: Series of raw complaint text strings.
        **normalize_kwargs: Keyword arguments forwarded to normalize_text.

    Returns:
        Series of normalized text strings.
    """
    return series.fillna("").apply(lambda t: normalize_text(t, **normalize_kwargs))


# ---------------------------------------------------------------------------
# Train / Val / Test splitting
# ---------------------------------------------------------------------------

def create_stratified_splits(
    df: pd.DataFrame,
    label_column: str,
    text_column: str,
    *,
    group_column: str | None = None,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    random_seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split a DataFrame into stratified train, validation, and test sets.

    Supports group-aware splitting if group_column is provided, ensuring all
    complaints belonging to the same incident group remain in the same split.

    IMPORTANT: This function must be called BEFORE fitting any vectorizer
    or preprocessing that learns from the corpus. Fitting on the full dataset
    and then splitting would cause data leakage.

    Args:
        df: Labeled DataFrame.
        label_column: Column used for stratification.
        text_column: Text column (used to confirm no empty rows leak through).
        group_column: Optional column defining shared incident groups.
        train_ratio: Fraction for training (default 0.70).
        val_ratio: Fraction for validation (default 0.15).
        test_ratio: Fraction for test (default 0.15).
        random_seed: Random state for reproducibility.

    Returns:
        Tuple of (train_df, val_df, test_df).

    Raises:
        ValueError: If ratios do not sum to approximately 1.0.
    """
    total = train_ratio + val_ratio + test_ratio
    if not (0.99 < total < 1.01):
        raise ValueError(
            f"Split ratios must sum to 1.0, got {total:.3f}. "
            f"Received: train={train_ratio}, val={val_ratio}, test={test_ratio}"
        )

    # If group_column is provided and has non-empty entries, perform group-aware split
    has_groups = (
        group_column is not None
        and group_column in df.columns
        and (df[group_column].fillna("").astype(str).str.strip() != "").any()
    )

    if has_groups:
        from sklearn.model_selection import StratifiedGroupKFold
        # Construct effective groups: use incident_group_id if present, else unique row ID
        raw_groups = df[group_column].fillna("").astype(str).str.strip().tolist()
        groups = [
            g if g else f"__standalone_{df.index[i]}"
            for i, g in enumerate(raw_groups)
        ]

        # Stage 1: split into (train+val) and test
        n_splits_test = max(2, round(1.0 / test_ratio))
        sgkf_test = StratifiedGroupKFold(n_splits=n_splits_test, shuffle=True, random_state=random_seed)
        train_val_idx, test_idx = next(sgkf_test.split(df, df[label_column], groups=groups))

        train_val = df.iloc[train_val_idx].copy()
        test_df = df.iloc[test_idx].copy()
        train_val_groups = [groups[i] for i in train_val_idx]

        # Stage 2: split train_val into train and val
        val_share_of_train_val = val_ratio / (train_ratio + val_ratio)
        n_splits_val = max(2, round(1.0 / val_share_of_train_val))
        sgkf_val = StratifiedGroupKFold(n_splits=n_splits_val, shuffle=True, random_state=random_seed)
        train_sub_idx, val_sub_idx = next(sgkf_val.split(train_val, train_val[label_column], groups=train_val_groups))

        train_df = train_val.iloc[train_sub_idx].copy()
        val_df = train_val.iloc[val_sub_idx].copy()
    else:
        # Standard stratified split
        test_size = test_ratio
        train_val, test_df = train_test_split(
            df,
            test_size=test_size,
            stratify=df[label_column],
            random_state=random_seed,
        )

        adjusted_val_size = val_ratio / (train_ratio + val_ratio)
        train_df, val_df = train_test_split(
            train_val,
            test_size=adjusted_val_size,
            stratify=train_val[label_column],
            random_state=random_seed,
        )

    logger.info(
        "Splits — train: %d | val: %d | test: %d",
        len(train_df), len(val_df), len(test_df),
    )
    return train_df, val_df, test_df


def check_split_leakage(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    text_column: str = "complaint_text",
    group_column: str | None = "incident_group_id",
) -> dict[str, Any]:
    """Verify that no data or incident leakage exists between splits.

    Checks:
        1. Index disjointness (no shared rows).
        2. Exact text duplicates across splits (must be 0).
        3. Incident group overlap across splits (must be 0 for grouped incidents).

    Returns:
        dict: Summary of checks and whether splits are leakage-free.
    """
    if (
        "complaint_id" in train_df.columns
        and "complaint_id" in val_df.columns
        and "complaint_id" in test_df.columns
    ):
        train_idx = set(train_df["complaint_id"])
        val_idx = set(val_df["complaint_id"])
        test_idx = set(test_df["complaint_id"])
    else:
        train_idx = set(train_df.index)
        val_idx = set(val_df.index)
        test_idx = set(test_df.index)

    index_overlap = (
        len(train_idx.intersection(val_idx))
        + len(train_idx.intersection(test_idx))
        + len(val_idx.intersection(test_idx))
    )

    # Check exact text overlap
    train_texts = set(train_df[text_column].dropna().str.strip())
    val_texts = set(val_df[text_column].dropna().str.strip())
    test_texts = set(test_df[text_column].dropna().str.strip())

    text_overlap_tv = train_texts.intersection(val_texts)
    text_overlap_tt = train_texts.intersection(test_texts)
    text_overlap_vt = val_texts.intersection(test_texts)
    exact_text_leakage = len(text_overlap_tv) + len(text_overlap_tt) + len(text_overlap_vt)

    # Check group overlap if group_column present
    group_leakage = 0
    group_details = ""
    if group_column and group_column in train_df.columns:
        train_grps = set(train_df[group_column].dropna().astype(str).str.strip()) - {""}
        val_grps = set(val_df[group_column].dropna().astype(str).str.strip()) - {""}
        test_grps = set(test_df[group_column].dropna().astype(str).str.strip()) - {""}

        grp_overlap = (
            train_grps.intersection(val_grps)
            | train_grps.intersection(test_grps)
            | val_grps.intersection(test_grps)
        )
        group_leakage = len(grp_overlap)
        if group_leakage > 0:
            group_details = f"Leaked group IDs: {list(grp_overlap)}"

    leakage_free = (index_overlap == 0 and exact_text_leakage == 0 and group_leakage == 0)

    return {
        "leakage_free": leakage_free,
        "index_overlap_count": index_overlap,
        "exact_text_leakage_count": exact_text_leakage,
        "incident_group_leakage_count": group_leakage,
        "group_details": group_details,
    }



# ---------------------------------------------------------------------------
# TF-IDF vectorizer builders
# (vectorizers are FIT on train data only — see train.py)
# ---------------------------------------------------------------------------

def build_word_tfidf_vectorizer(
    max_features: int = 10000,
    ngram_range: tuple[int, int] = (1, 2),
    min_df: int = 2,
    max_df: float = 0.95,
    sublinear_tf: bool = True,
) -> TfidfVectorizer:
    """Create (but do NOT fit) a word-level TF-IDF vectorizer.

    The returned object must be fit on training data only:
        vectorizer.fit_transform(train_texts)  # training
        vectorizer.transform(val_texts)        # validation / test

    Args:
        max_features: Maximum vocabulary size.
        ngram_range: (min_n, max_n) n-gram range for word n-grams.
        min_df: Minimum document frequency for a token to be included.
        max_df: Maximum document frequency (removes very common terms).
        sublinear_tf: Apply log(1 + tf) scaling.

    Returns:
        Unfitted TfidfVectorizer instance.
    """
    return TfidfVectorizer(
        analyzer="word",
        max_features=max_features,
        ngram_range=ngram_range,
        min_df=min_df,
        max_df=max_df,
        sublinear_tf=sublinear_tf,
        token_pattern=r"(?u)\b\w\w+\b",  # at least 2-char tokens
    )


def build_char_tfidf_vectorizer(
    max_features: int = 15000,
    ngram_range: tuple[int, int] = (3, 5),
    min_df: int = 2,
    max_df: float = 0.95,
    sublinear_tf: bool = True,
) -> TfidfVectorizer:
    """Create (but do NOT fit) a character-level TF-IDF vectorizer.

    Character n-grams are more robust to misspellings than word n-grams.
    Useful as a comparison in Experiment E4.

    Args:
        max_features: Maximum vocabulary size.
        ngram_range: Character n-gram range.
        min_df: Minimum document frequency.
        max_df: Maximum document frequency.
        sublinear_tf: Apply log(1 + tf) scaling.

    Returns:
        Unfitted TfidfVectorizer instance (analyzer='char_wb').
    """
    return TfidfVectorizer(
        analyzer="char_wb",  # char_wb pads word boundaries with spaces
        max_features=max_features,
        ngram_range=ngram_range,
        min_df=min_df,
        max_df=max_df,
        sublinear_tf=sublinear_tf,
    )



# ---------------------------------------------------------------------------
# Preprocessing Pipeline Runner
# ---------------------------------------------------------------------------

def prepare_dataset_splits(
    data_path: str | Path = "data/raw/college_complaints_synthetic.csv",
    output_dir: str | Path = "data/processed",
    config_path: str | Path = "config.yaml",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Execute the end-to-end preprocessing and stratified group splitting pipeline.

    Steps:
      1. Load raw data and configuration.
      2. Ensure required NLTK resources are downloaded.
      3. Apply PII masking to ensure no sensitive tokens reach downstream models.
      4. Compute normalized_text feature column via stateless normalization.
      5. Split data into train/val/test using group-aware stratified sampling
         (guaranteeing related incident reports never leak across splits).
      6. Audit for index overlap, exact text leakage, and group leakage.
      7. Persist train.csv, val.csv, and test.csv into output_dir.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]: (train_df, val_df, test_df)
    """
    import yaml

    data_path = Path(data_path)
    output_dir = Path(output_dir)
    config_path = Path(config_path)

    with open(config_path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)

    ensure_nltk_resources()

    logger.info("Loading raw dataset from %s", data_path)
    df = pd.read_csv(data_path, encoding="utf-8")

    text_col = cfg["data"]["text_column"]
    label_col = cfg["data"]["label_column"]
    group_col = "incident_group_id"

    # Step 1: Mask PII on text column
    pii_patterns_config = cfg.get("preprocessing", {}).get("pii_patterns", [])
    pii_tuples = [(p["pattern"], p["replacement"]) for p in pii_patterns_config if "pattern" in p]
    df[text_col] = df[text_col].apply(lambda t: mask_pii(t, patterns=pii_tuples if pii_tuples else None))

    # Step 2: Compute normalized representation
    logger.info("Computing normalized text tokens...")
    df["normalized_text"] = normalize_series(
        df[text_col],
        lowercase=cfg["preprocessing"].get("lowercase", True),
        remove_punctuation=cfg["preprocessing"].get("remove_punctuation", True),
        remove_numbers=cfg["preprocessing"].get("remove_numbers", False),
        remove_stopwords=cfg["preprocessing"].get("remove_stopwords", True),
        lemmatize=cfg["preprocessing"].get("lemmatization", True),
        min_token_length=cfg["preprocessing"].get("min_token_length", 2),
    )

    # Step 3: Stratified group-aware split
    train_ratio = cfg["data"].get("train_ratio", 0.70)
    val_ratio = cfg["data"].get("val_ratio", 0.15)
    test_ratio = cfg["data"].get("test_ratio", 0.15)
    seed = cfg["project"].get("random_seed", 42)

    train_df, val_df, test_df = create_stratified_splits(
        df,
        label_column=label_col,
        text_column=text_col,
        group_column=group_col,
        train_ratio=train_ratio,
        val_ratio=val_ratio,
        test_ratio=test_ratio,
        random_seed=seed,
    )

    # Step 4: Audit split leakage
    leakage_audit = check_split_leakage(train_df, val_df, test_df, text_column=text_col, group_column=group_col)
    logger.info("Split leakage audit result: %s", leakage_audit)
    if not leakage_audit["leakage_free"]:
        raise RuntimeError(f"Split leakage audit failed: {leakage_audit}")

    # Step 5: Save splits to disk
    output_dir.mkdir(parents=True, exist_ok=True)
    train_path = output_dir / "train.csv"
    val_path = output_dir / "val.csv"
    test_path = output_dir / "test.csv"

    train_df.to_csv(train_path, index=False, encoding="utf-8")
    val_df.to_csv(val_path, index=False, encoding="utf-8")
    test_df.to_csv(test_path, index=False, encoding="utf-8")

    logger.info("Saved train (%d), val (%d), test (%d) to %s", len(train_df), len(val_df), len(test_df), output_dir)
    return train_df, val_df, test_df


def main() -> None:
    """CLI entry point for data preprocessing and splitting."""
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(description="Preprocess dataset and create verified stratified splits.")
    parser.add_argument("--data-path", type=str, default="data/raw/college_complaints_synthetic.csv")
    parser.add_argument("--output-dir", type=str, default="data/processed")
    parser.add_argument("--config-path", type=str, default="config.yaml")
    args = parser.parse_args()

    train_df, val_df, test_df = prepare_dataset_splits(
        data_path=args.data_path,
        output_dir=args.output_dir,
        config_path=args.config_path,
    )

    print("\n" + "=" * 60)
    print("DATA PREPROCESSING & SPLIT SUMMARY")
    print("=" * 60)
    print(f"Train split : {len(train_df):5d} rows ({len(train_df) / (len(train_df) + len(val_df) + len(test_df)):.1%})")
    print(f"Val split   : {len(val_df):5d} rows ({len(val_df) / (len(train_df) + len(val_df) + len(test_df)):.1%})")
    print(f"Test split  : {len(test_df):5d} rows ({len(test_df) / (len(train_df) + len(val_df) + len(test_df)):.1%})")
    print(f"Total rows  : {len(train_df) + len(val_df) + len(test_df):5d} rows")
    print("\nClass distribution in Train split:")
    print(train_df["category"].value_counts().sort_index().to_string())
    print("\nZero leakage confirmed across all splits.")
    print("=" * 60)


if __name__ == "__main__":
    main()

