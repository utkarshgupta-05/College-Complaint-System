"""
src/data/load_data.py
---------------------
Load complaint datasets from disk into pandas DataFrames.

Design principles:
- Functions are small and single-purpose.
- Every function validates inputs before processing.
- The loader never modifies the raw file on disk.
- All field names come from config.yaml (no hardcoded column names here).
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import yaml

logger = logging.getLogger(__name__)


def load_config(config_path: str | Path = "config.yaml") -> dict:
    """Load the project YAML configuration file.

    Args:
        config_path: Path to config.yaml (default: project root).

    Returns:
        dict: Parsed configuration dictionary.

    Raises:
        FileNotFoundError: If config.yaml does not exist at the given path.
    """
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_csv(
    filepath: str | Path,
    *,
    required_columns: list[str] | None = None,
    encoding: str = "utf-8",
) -> pd.DataFrame:
    """Load a CSV file into a DataFrame with basic sanity checks.

    Args:
        filepath: Path to the CSV file.
        required_columns: Column names that MUST be present in the file.
            Raises ValueError if any are missing.
        encoding: File encoding (default: utf-8).

    Returns:
        pd.DataFrame: Loaded data.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If required columns are missing.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Data file not found: {filepath}")

    df = pd.read_csv(filepath, encoding=encoding)
    logger.info("Loaded %d rows from %s", len(df), filepath)

    if required_columns:
        missing = [c for c in required_columns if c not in df.columns]
        if missing:
            raise ValueError(
                f"Required columns missing from {filepath}: {missing}\n"
                f"Available columns: {list(df.columns)}"
            )

    return df


def load_processed_splits(
    processed_dir: str | Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load the train, validation, and test splits from the processed directory.

    These files are created by src/data/preprocess.py after Phase 2.
    Do NOT load the test split until final evaluation.

    Args:
        processed_dir: Path to data/processed/.

    Returns:
        Tuple of (train_df, val_df, test_df).

    Raises:
        FileNotFoundError: If any split file is missing.
    """
    processed_dir = Path(processed_dir)
    train_path = processed_dir / "train.csv"
    val_path = processed_dir / "val.csv"
    test_path = processed_dir / "test.csv"

    logger.info("Loading train split from %s", train_path)
    train_df = load_csv(train_path)

    logger.info("Loading validation split from %s", val_path)
    val_df = load_csv(val_path)

    logger.info("Loading test split from %s", test_path)
    test_df = load_csv(test_path)

    logger.info(
        "Split sizes — train: %d | val: %d | test: %d",
        len(train_df), len(val_df), len(test_df),
    )
    return train_df, val_df, test_df


# ---------------------------------------------------------------------------
# NOTE: This module is a stub created in Phase 1.
# Implementation will be completed and tested in Phase 2.
# ---------------------------------------------------------------------------
