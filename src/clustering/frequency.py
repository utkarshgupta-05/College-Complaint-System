"""
src/clustering/frequency.py
---------------------------
Spatiotemporal, categorical, and departmental frequency analysis for complaint intelligence.

Provides defensible aggregation across available dimensions:
- Complaint category distribution
- Location distribution & hotspot identification
- Department distribution
- Temporal aggregation (daily, weekly, monthly) with trend sufficiency validation

Design Principles:
- Never invent missing location or timestamp data.
- Explicitly label and isolate missing/null values (<Unspecified Location>, <Missing Timestamp>).
- Issue explicit warnings when observation counts or date ranges are insufficient to infer seasonal trends.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class TrendSufficiencyReport:
    """Assessment of whether temporal observations permit reliable trend inference."""
    total_records: int
    valid_timestamps: int
    missing_timestamps: int
    start_date: str | None
    end_date: str | None
    span_days: int
    is_sufficient_for_seasonality: bool
    is_sufficient_for_weekly_patterns: bool
    warning: str | None


def _resolve_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Find the first matching column name from candidate list (case-insensitive)."""
    cols_lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in cols_lower:
            return cols_lower[cand.lower()]
    return None


def aggregate_by_category(
    df: pd.DataFrame,
    category_col: str | None = None,
) -> pd.DataFrame:
    """Aggregate complaint counts and percentages by category.
    
    Args:
        df: Input DataFrame containing complaint records.
        category_col: Name of category column. If None, auto-detected.
        
    Returns:
        DataFrame with columns ['category', 'count', 'percentage'].
    """
    if df.empty:
        return pd.DataFrame(columns=["category", "count", "percentage"])

    col = category_col or _resolve_column(df, ["category", "category_name", "category_code", "label"])
    if col is None or col not in df.columns:
        logger.warning("No category column found in DataFrame.")
        return pd.DataFrame(columns=["category", "count", "percentage"])

    series = df[col].fillna("<Missing Category>").astype(str)
    counts = series.value_counts(dropna=False).reset_index()
    counts.columns = ["category", "count"]
    total = counts["count"].sum()
    counts["percentage"] = (counts["count"] / total * 100.0).round(2)
    return counts


def aggregate_by_location(
    df: pd.DataFrame,
    location_col: str | None = None,
) -> pd.DataFrame:
    """Aggregate complaint counts and percentages by location.
    
    Missing or empty locations are grouped under '<Unspecified Location>'.
    
    Args:
        df: Input DataFrame.
        location_col: Name of location column. If None, auto-detected.
        
    Returns:
        DataFrame with columns ['location', 'count', 'percentage'].
    """
    if df.empty:
        return pd.DataFrame(columns=["location", "count", "percentage"])

    col = location_col or _resolve_column(df, ["location", "place", "building", "venue"])
    if col is None or col not in df.columns:
        # Explicitly report all as unspecified without inventing data
        return pd.DataFrame([{"location": "<Unspecified Location>", "count": len(df), "percentage": 100.0}])

    series = df[col].replace("", np.nan).fillna("<Unspecified Location>").astype(str)
    counts = series.value_counts(dropna=False).reset_index()
    counts.columns = ["location", "count"]
    total = counts["count"].sum()
    counts["percentage"] = (counts["count"] / total * 100.0).round(2)
    return counts


def aggregate_by_department(
    df: pd.DataFrame,
    dept_col: str | None = None,
) -> pd.DataFrame:
    """Aggregate complaint counts by responsible or student department.
    
    Args:
        df: Input DataFrame.
        dept_col: Name of department column. If None, auto-detected.
        
    Returns:
        DataFrame with columns ['department', 'count', 'percentage'].
    """
    if df.empty:
        return pd.DataFrame(columns=["department", "count", "percentage"])

    col = dept_col or _resolve_column(df, [
        "primary_department", "responsible_departments", "student_dept",
        "department", "dept"
    ])
    if col is None or col not in df.columns:
        return pd.DataFrame([{"department": "<Unspecified Department>", "count": len(df), "percentage": 100.0}])

    series = df[col].replace("", np.nan).fillna("<Unspecified Department>").astype(str)
    counts = series.value_counts(dropna=False).reset_index()
    counts.columns = ["department", "count"]
    total = counts["count"].sum()
    counts["percentage"] = (counts["count"] / total * 100.0).round(2)
    return counts


def aggregate_by_time_period(
    df: pd.DataFrame,
    freq: str = "W",  # 'D' (daily), 'W' (weekly), 'M' (monthly)
    timestamp_col: str | None = None,
) -> pd.DataFrame:
    """Aggregate complaint volume by time interval.
    
    Explicitly tracks records with missing or unparseable timestamps.
    
    Args:
        df: Input DataFrame.
        freq: Pandas period frequency string ('D', 'W', 'M').
        timestamp_col: Name of timestamp column. If None, auto-detected.
        
    Returns:
        DataFrame with columns ['period', 'count'].
    """
    if df.empty:
        return pd.DataFrame(columns=["period", "count"])

    col = timestamp_col or _resolve_column(df, ["created_at", "timestamp", "date", "submission_date"])
    if col is None or col not in df.columns:
        return pd.DataFrame([{"period": "<Missing Timestamp>", "count": len(df)}])

    parsed = pd.to_datetime(df[col], errors="coerce")
    valid_mask = parsed.notna()
    n_missing = int((~valid_mask).sum())

    results: list[dict[str, Any]] = []
    if valid_mask.any():
        periods = parsed[valid_mask].dt.to_period(freq).astype(str)
        period_counts = periods.value_counts().sort_index().reset_index()
        period_counts.columns = ["period", "count"]
        results.extend(period_counts.to_dict(orient="records"))

    if n_missing > 0:
        results.append({"period": "<Missing Timestamp>", "count": n_missing})

    return pd.DataFrame(results)


def find_hotspots(
    df: pd.DataFrame,
    min_count: int = 2,
    location_col: str | None = None,
    category_col: str | None = None,
) -> pd.DataFrame:
    """Identify recurring location-category pairs exceeding min_count threshold.
    
    Args:
        df: Input DataFrame.
        min_count: Minimum co-occurrences to qualify as a hotspot.
        location_col: Column for location.
        category_col: Column for category.
        
    Returns:
        DataFrame of recurring hotspots sorted by count descending.
    """
    if df.empty:
        return pd.DataFrame(columns=["location", "category", "count", "percentage"])

    loc_col = location_col or _resolve_column(df, ["location", "place", "building"])
    cat_col = category_col or _resolve_column(df, ["category", "category_name"])

    if loc_col is None or cat_col is None or loc_col not in df.columns or cat_col not in df.columns:
        logger.warning("Cannot compute hotspots: missing location or category column.")
        return pd.DataFrame(columns=["location", "category", "count", "percentage"])

    locs = df[loc_col].replace("", np.nan).fillna("<Unspecified Location>").astype(str)
    cats = df[cat_col].replace("", np.nan).fillna("<Missing Category>").astype(str)

    grouped = pd.DataFrame({"location": locs, "category": cats}).groupby(
        ["location", "category"]
    ).size().reset_index(name="count")

    hotspots = grouped[grouped["count"] >= min_count].sort_values(by="count", ascending=False).reset_index(drop=True)
    total = len(df)
    hotspots["percentage"] = (hotspots["count"] / total * 100.0).round(2)
    return hotspots


def assess_trend_sufficiency(
    df: pd.DataFrame,
    timestamp_col: str | None = None,
) -> TrendSufficiencyReport:
    """Assess whether complaint timestamps permit statistically sound trend analysis.
    
    Prevents unwarranted claims of 'seasonality' or 'long-term cycles' from
    sparse or brief observation intervals.
    """
    total = len(df)
    if total == 0:
        return TrendSufficiencyReport(
            total_records=0, valid_timestamps=0, missing_timestamps=0,
            start_date=None, end_date=None, span_days=0,
            is_sufficient_for_seasonality=False,
            is_sufficient_for_weekly_patterns=False,
            warning="Dataset is empty. No temporal analysis possible."
        )

    col = timestamp_col or _resolve_column(df, ["created_at", "timestamp", "date"])
    if col is None or col not in df.columns:
        return TrendSufficiencyReport(
            total_records=total, valid_timestamps=0, missing_timestamps=total,
            start_date=None, end_date=None, span_days=0,
            is_sufficient_for_seasonality=False,
            is_sufficient_for_weekly_patterns=False,
            warning="No timestamp column found. Temporal trend analysis is unavailable."
        )

    parsed = pd.to_datetime(df[col], errors="coerce")
    valid = parsed.dropna()
    n_valid = len(valid)
    n_missing = total - n_valid

    if n_valid == 0:
        return TrendSufficiencyReport(
            total_records=total, valid_timestamps=0, missing_timestamps=total,
            start_date=None, end_date=None, span_days=0,
            is_sufficient_for_seasonality=False,
            is_sufficient_for_weekly_patterns=False,
            warning="All timestamps are invalid or unparseable."
        )

    min_date = valid.min()
    max_date = valid.max()
    span_days = int((max_date - min_date).total_seconds() / 86400)

    # Heuristics for defensible temporal claims:
    # - Seasonality requires at least 365 days of observation or 4 distinct quarters.
    # - Weekly patterns require at least 60 days and >= 50 valid observations.
    is_season = (span_days >= 365) and (n_valid >= 200)
    is_weekly = (span_days >= 60) and (n_valid >= 50)

    warnings: list[str] = []
    if not is_season:
        warnings.append(
            f"Observation window ({span_days} days, N={n_valid}) is insufficient to infer "
            "seasonal or annual cyclical trends. Claims of seasonality are statistically unsupported."
        )
    if not is_weekly:
        warnings.append(
            f"Observation count (N={n_valid}) or span ({span_days} days) is too sparse for "
            "reliable weekly rhythm or day-of-week recurrence modeling."
        )

    warning_str = " | ".join(warnings) if warnings else None

    return TrendSufficiencyReport(
        total_records=total,
        valid_timestamps=n_valid,
        missing_timestamps=n_missing,
        start_date=str(min_date.date()),
        end_date=str(max_date.date()),
        span_days=span_days,
        is_sufficient_for_seasonality=is_season,
        is_sufficient_for_weekly_patterns=is_weekly,
        warning=warning_str,
    )
