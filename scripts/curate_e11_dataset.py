"""
scripts/curate_e11_dataset.py
-----------------------------
Curate external complaint records from Kaggle datasets and create the
E11 augmented training dataset.

Preserves existing train.csv, val.csv, and test.csv without modification.
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, os.path.abspath("."))

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.data.preprocess import normalize_text

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

CATEGORY_MAP = {
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


def get_file_hash(path: Path) -> str:
    """Calculate MD5 hash of a file to verify immutability."""
    hasher = hashlib.md5()
    with open(path, "rb") as f:
        hasher.update(f.read())
    return hasher.hexdigest()


def curate_dataset_1(df1_path: Path) -> list[dict[str, Any]]:
    """Curate records from Dataset 1 (ayushcl/college-complaint)."""
    logger.info("Loading Dataset 1 from %s...", df1_path)
    df1 = pd.read_csv(df1_path)

    # Filtering patterns to eliminate misclassified or ambiguous records
    hostel_exclude = re.compile(
        r"\b(mess|canteen|food|tiffin|lunch|dinner|breakfast|internet|wifi|wi-fi|router|broadband)\b",
        re.IGNORECASE,
    )
    academic_exclude = re.compile(
        r"\b(marker|whiteboard|projector|dustbin in classroom|broken bench|fan in room)\b",
        re.IGNORECASE,
    )
    others_exclude = re.compile(
        r"\b(canteen|food|mess|ragging|cheating|exam|exam portal|bus|transport|fee receipt|admission|tc |transfer certificate|id card|water cooler|wifi|internet)\b",
        re.IGNORECASE,
    )

    def clean_text(row):
        title = str(row["title"]).strip()
        desc = str(row["description"]).strip()
        if title.lower() in desc.lower():
            text = desc
        else:
            text = f"{title}. {desc}"
        return re.sub(r"\s+", " ", text).strip()

    curated_records = []
    ext_id_counter = 1

    targets = [
        ("Hostel", "C01", hostel_exclude, 150),
        ("Transport", "C09", None, 150),
        ("Academic", "C05", academic_exclude, 150),
        ("Others", "C11", others_exclude, 150),
    ]

    for source_cat, target_code, exclude_pattern, target_count in targets:
        sub = df1[df1["category"] == source_cat].copy()
        sub["cleaned_text"] = sub.apply(clean_text, axis=1)

        if exclude_pattern is not None:
            sub = sub[~sub["cleaned_text"].str.contains(exclude_pattern, regex=True)]

        # Length filter (remove trivial phrases)
        sub = sub[sub["cleaned_text"].str.len() >= 60]
        # Deduplicate titles to ensure diversity
        sub = sub.drop_duplicates(subset=["title"])

        sampled = sub.sample(n=min(target_count, len(sub)), random_state=42)
        logger.info("Selected %d records for %s (%s)", len(sampled), target_code, source_cat)

        for _, r in sampled.iterrows():
            prio = str(r.get("priority", "medium")).strip().lower()
            if prio not in {"low", "medium", "high"}:
                prio = "medium"

            loc = str(r.get("location", "Campus")).strip()
            if not loc or loc.lower() == "nan":
                loc = "Campus"

            curated_records.append({
                "complaint_id": f"EXT-AYU-{ext_id_counter:05d}",
                "complaint_text": r["cleaned_text"],
                "category": target_code,
                "category_name": CATEGORY_MAP[target_code],
                "location": loc,
                "created_at": "2026-10-31 12:00:00",
                "status": "pending_review",
                "priority_label": prio,
                "incident_group_id": "",
                "data_source": "kaggle_ayushcl",
                "normalized_text": normalize_text(r["cleaned_text"]),
            })
            ext_id_counter += 1

    return curated_records


def curate_dataset_2(df2_path: Path) -> list[dict[str, Any]]:
    """Curate clean English ragging records from Dataset 2 (sheshanksingh/complaint)."""
    logger.info("Loading Dataset 2 from %s...", df2_path)
    df2 = pd.read_csv(df2_path)

    ragging = df2[df2["category"].astype(str).str.strip().str.lower() == "ragging"].copy()

    def anonymize_text(t: str) -> str:
        # PII anonymization
        t = re.sub(r"Rugved Deolekar\s*(Sir)?", "A faculty member", t, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", t).strip()

    hindi_stop_tokens = {
        'hai', 'hain', 'nahi', 'karo', 'raha', 'rahi', 'rahe', 'bohot', 'bahut', 'paani', 'kharaab',
        'bhi', 'aur', 'ke', 'ki', 'ka', 'ko', 'se', 'yeh', 'woh', 'kya', 'kyun', 'ab', 'bina',
        'saath', 'karta', 'karte', 'karti', 'diya', 'de', 'liye', 'lag', 'ne', 'mein', 'kiya',
        'karein', 'aap', 'toh', 'hum', 'bura', 'ek', 'baar', 'baaki', 'unko', 'mujhe', 'hota',
        'hoti', 'hote', 'chal', 'kuch', 'pe', 'ho', 'jaao', 'waise', 'karna', 'karta', 'karti',
        'unhone', 'kaha', 'itna', 'yahan', 'aise', 'poori', 'saamne', 'pucha', 'puchte', 'jawab',
        'galat', 'rona', 'shuru', 'gayi', 'gaya', 'gaye', 'baat', 'kaatne', 'gaali', 'di',
        'badh', 'aaya'
    }

    candidates = []
    for _, r in ragging.iterrows():
        raw_text = anonymize_text(str(r["complaint_text"]))
        tokens = re.findall(r"\b[a-zA-Z]+\b", raw_text.lower())
        found_hindi = [w for w in tokens if w in hindi_stop_tokens]

        if not found_hindi and len(raw_text) >= 25:
            urgency = str(r.get("urgency", "High")).strip().lower()
            prio = "high" if "high" in urgency or "urgent" in urgency else "medium"
            candidates.append({
                "text": raw_text,
                "priority": prio,
            })

    # Deduplicate candidate texts
    df_cand = pd.DataFrame(candidates).drop_duplicates(subset=["text"])
    logger.info("Selected %d clean English ragging records from Dataset 2", len(df_cand))

    curated_records = []
    ext_id_counter = 1
    for _, r in df_cand.iterrows():
        curated_records.append({
            "complaint_id": f"EXT-SS-{ext_id_counter:05d}",
            "complaint_text": r["text"],
            "category": "C08",
            "category_name": CATEGORY_MAP["C08"],
            "location": "College Campus",
            "created_at": "2026-10-31 12:00:00",
            "status": "pending_review",
            "priority_label": r["priority"],
            "incident_group_id": "",
            "data_source": "kaggle_sheshanksingh",
            "normalized_text": normalize_text(r["text"]),
        })
        ext_id_counter += 1

    return curated_records


def main() -> None:
    data_dir = Path("data/processed")
    train_path = data_dir / "train.csv"
    val_path = data_dir / "val.csv"
    test_path = data_dir / "test.csv"
    output_path = data_dir / "e11_augmented_train.csv"

    df1_path = Path("data/external/kaggle_college_complaint/complaints_dataset_final.csv")
    df2_path = Path("data/external/kaggle_multilingual_complaint/ML_Project_Complaint_Dataset_Duration_Imp.csv")

    # Record hashes before processing
    train_hash_before = get_file_hash(train_path)
    val_hash_before = get_file_hash(val_path)
    test_hash_before = get_file_hash(test_path)

    logger.info("Loading existing base training set from %s...", train_path)
    base_train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)
    test_df = pd.read_csv(test_path)

    existing_texts = set(base_train_df["complaint_text"].str.strip().str.lower())
    val_texts = list(val_df["complaint_text"].str.strip())
    test_texts = list(test_df["complaint_text"].str.strip())

    # Curate external datasets
    rec1 = curate_dataset_1(df1_path)
    rec2 = curate_dataset_2(df2_path)
    all_external = rec1 + rec2

    ext_df = pd.DataFrame(all_external)
    logger.info("Total external records curated: %d", len(ext_df))

    # Verify 0 collisions with train, val, and test splits
    for idx, r in ext_df.iterrows():
        t_clean = r["complaint_text"].strip().lower()
        if t_clean in existing_texts:
            raise ValueError(f"Collision detected with base train: {r['complaint_text']}")
        if t_clean in set(t.lower() for t in val_texts):
            raise ValueError(f"Collision detected with validation set: {r['complaint_text']}")
        if t_clean in set(t.lower() for t in test_texts):
            raise ValueError(f"Collision detected with test set: {r['complaint_text']}")

    logger.info("Integrity check passed: 0 text collisions across train, val, and test splits.")

    # Check cosine similarity against val and test
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
    eval_tfidf = vec.fit_transform(val_texts + test_texts)
    cand_tfidf = vec.transform(ext_df["complaint_text"])
    sim = cosine_similarity(cand_tfidf, eval_tfidf)
    max_sim = float(sim.max())
    logger.info("Max cosine similarity with evaluation sets: %.4f (safe threshold < 0.70)", max_sim)

    # Combine base train + external records
    augmented_df = pd.concat([base_train_df, ext_df], ignore_index=True)
    logger.info("Combined augmented dataset shape: %s (Base: %d, External: %d)",
                augmented_df.shape, len(base_train_df), len(ext_df))

    # Save e11_augmented_train.csv
    augmented_df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info("Successfully saved augmented training set to %s", output_path)

    # Verify hashes of base files
    assert get_file_hash(train_path) == train_hash_before, "train.csv was modified!"
    assert get_file_hash(val_path) == val_hash_before, "val.csv was modified!"
    assert get_file_hash(test_path) == test_hash_before, "test.csv was modified!"
    logger.info("Baseline verification successful: train.csv, val.csv, and test.csv are completely UNMODIFIED.")


if __name__ == "__main__":
    main()
