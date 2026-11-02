"""
scripts/phase10_data_inspection.py
----------------------------------
Deep training dataset inspection for Phase 10:
- Class distribution & uniqueness
- Text length & style differences (Synthetic vs Kaggle)
- Distinctive vs overlapping vocabulary for confusing pairs
"""

from __future__ import annotations

import os
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, os.path.abspath("."))

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

train_df = pd.read_csv("data/processed/train.csv")
e11_df = pd.read_csv("data/processed/e11_augmented_train.csv")

CATEGORY_NAMES = {
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

print("=== 1. DATASET VOLUME & UNIQUENESS ===")
print("--- Base train.csv ---")
base_stats = []
for cat in sorted(CATEGORY_NAMES.keys()):
    sub = train_df[train_df["category"] == cat]
    total = len(sub)
    unq_text = sub["complaint_text"].nunique()
    mean_char = sub["complaint_text"].str.len().mean()
    mean_words = sub["complaint_text"].apply(lambda t: len(t.split())).mean()
    base_stats.append({
        "Category": cat,
        "Name": CATEGORY_NAMES[cat],
        "Total": total,
        "Unique Texts": unq_text,
        "Duplicate Texts": total - unq_text,
        "Mean Chars": round(mean_char, 1),
        "Mean Words": round(mean_words, 1),
    })
print(pd.DataFrame(base_stats).to_string(index=False))

print("\n--- E11 Augmented train.csv ---")
e11_stats = []
for cat in sorted(CATEGORY_NAMES.keys()):
    sub = e11_df[e11_df["category"] == cat]
    total = len(sub)
    unq_text = sub["complaint_text"].nunique()
    synth_cnt = (sub["data_source"] == "synthetic").sum()
    ext_cnt = (sub["data_source"] != "synthetic").sum()
    mean_char = sub["complaint_text"].str.len().mean()
    mean_words = sub["complaint_text"].apply(lambda t: len(t.split())).mean()
    e11_stats.append({
        "Category": cat,
        "Name": CATEGORY_NAMES[cat],
        "Total": total,
        "Synth": synth_cnt,
        "External": ext_cnt,
        "Unique Texts": unq_text,
        "Mean Chars": round(mean_char, 1),
        "Mean Words": round(mean_words, 1),
    })
print(pd.DataFrame(e11_stats).to_string(index=False))

print("\n=== 2. TEXT STYLE & LENGTH DIVERGENCE (Synthetic vs Kaggle) ===")
synth_rows = e11_df[e11_df["data_source"] == "synthetic"]
ayu_rows = e11_df[e11_df["data_source"] == "kaggle_ayushcl"]
ss_rows = e11_df[e11_df["data_source"] == "kaggle_sheshanksingh"]

for name, subset in [("Synthetic Base", synth_rows), ("Kaggle ayushcl", ayu_rows), ("Kaggle sheshanksingh", ss_rows)]:
    chars = subset["complaint_text"].str.len()
    words = subset["complaint_text"].apply(lambda t: len(t.split()))
    print(f"\n{name} (N={len(subset)}):")
    print(f"  Chars: Mean={chars.mean():.1f}, Std={chars.std():.1f}, Min={chars.min()}, Max={chars.max()}")
    print(f"  Words: Mean={words.mean():.1f}, Std={words.std():.1f}, Min={words.min()}, Max={words.max()}")

print("\n=== 3. CATEGORY VOCABULARY OVERLAPS ===")
# Fit TF-IDF on base train
vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.95, sublinear_tf=True, stop_words="english")
X = vec.fit_transform(train_df["complaint_text"])
feature_names = np.array(vec.get_feature_names_out())

def get_top_keywords(cat_code, top_n=20):
    sub_indices = train_df.index[train_df["category"] == cat_code].tolist()
    sub_X = X[sub_indices]
    mean_tfidf = np.asarray(sub_X.mean(axis=0)).flatten()
    top_idx = mean_tfidf.argsort()[::-1][:top_n]
    return list(zip(feature_names[top_idx], np.round(mean_tfidf[top_idx], 4)))

pairs = [
    ("C05", "C06"),  # Academic vs Classroom/Lab
    ("C06", "C08"),  # Classroom/Lab vs Campus Safety
    ("C02", "C06"),  # Electricity/Water vs Classroom/Lab
    ("C03", "C06"),  # Internet vs Classroom/Lab
    ("C07", "C06"),  # Sanitation vs Classroom/Lab
]

for c1, c2 in pairs:
    kw1 = dict(get_top_keywords(c1, top_n=35))
    kw2 = dict(get_top_keywords(c2, top_n=35))
    shared = set(kw1.keys()).intersection(set(kw2.keys()))
    print(f"\n--- Overlap between {c1} ({CATEGORY_NAMES[c1]}) and {c2} ({CATEGORY_NAMES[c2]}) ---")
    print(f"Shared top keywords ({len(shared)}): {sorted(list(shared))}")
    print(f"Top 10 distinct to {c1}: {[k for k in list(kw1.keys())[:15] if k not in kw2][:10]}")
    print(f"Top 10 distinct to {c2}: {[k for k in list(kw2.keys())[:15] if k not in kw1][:10]}")

