import os
import re
import string
import pandas as pd
import numpy as np
from collections import Counter

def run_deep_inspection():
    print("=" * 80)
    print("DEEP QUALITY & LINGUISTIC INSPECTION OF KAGGLE DATASETS")
    print("=" * 80)
    
    # 1. Load Datasets
    p1 = "data/external/kaggle_college_complaint/complaints_dataset_final.csv"
    p2 = "data/external/kaggle_multilingual_complaint/ML_Project_Complaint_Dataset_Duration_Imp.csv"
    
    df1 = pd.read_csv(p1)
    df2 = pd.read_csv(p2)
    
    # -------------------------------------------------------------
    # Deep Inspection of Dataset 1 (ayushcl)
    # -------------------------------------------------------------
    print("\n--- DATASET 1 (ayushcl/college-complaint) ---")
    print(f"File size: {os.path.getsize(p1):,} bytes")
    print(f"Rows: {len(df1):,}, Cols: {len(df1.columns)}")
    
    # Duplicate analysis
    exact_dupes_all = df1.duplicated().sum()
    desc_dupes = df1['description'].duplicated().sum()
    title_dupes = df1['title'].duplicated().sum()
    print(f"Exact full-row duplicates: {exact_dupes_all}")
    print(f"Description duplicates: {desc_dupes} ({desc_dupes/len(df1):.1%})")
    print(f"Title duplicates: {title_dupes} ({title_dupes/len(df1):.1%})")
    
    # Text lengths
    df1['desc_char_len'] = df1['description'].astype(str).str.len()
    df1['desc_word_len'] = df1['description'].astype(str).str.split().str.len()
    df1['title_char_len'] = df1['title'].astype(str).str.len()
    df1['title_word_len'] = df1['title'].astype(str).str.split().str.len()
    
    print("\nDescription Length Summary (Characters):")
    print(df1['desc_char_len'].describe())
    print("\nDescription Length Summary (Words):")
    print(df1['desc_word_len'].describe())
    
    # Script & Language Check
    def check_scripts(text_series):
        has_devanagari = 0
        has_non_ascii = 0
        total = len(text_series)
        for t in text_series:
            s = str(t)
            if any(ord(c) > 127 for c in s):
                has_non_ascii += 1
            if any('\u0900' <= c <= '\u097F' for c in s):
                has_devanagari += 1
        return has_non_ascii, has_devanagari, total

    non_ascii, devanagari, total = check_scripts(df1['description'])
    print(f"\nNon-ASCII descriptions: {non_ascii} / {total} ({non_ascii/total:.2%})")
    print(f"Devanagari script descriptions: {devanagari} / {total}")
    
    # PII Check in Dataset 1
    email_pattern = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
    phone_pattern = re.compile(r'\b(?:\+91|91)?[-. ]?[6-9]\d{9}\b')
    roll_pattern = re.compile(r'\b(?:20\d{2}[A-Z]{2,4}\d{3,5}|\d{2}[A-Z]{2}\d{4,6})\b', re.I)
    
    df1_emails = df1['description'].apply(lambda x: len(email_pattern.findall(str(x)))).sum()
    df1_phones = df1['description'].apply(lambda x: len(phone_pattern.findall(str(x)))).sum()
    df1_rolls = df1['description'].apply(lambda x: len(roll_pattern.findall(str(x)))).sum()
    print(f"\nPII in Dataset 1 Descriptions:")
    print(f"  Emails detected: {df1_emails}")
    print(f"  Phone numbers detected: {df1_phones}")
    print(f"  Roll numbers / Student IDs detected: {df1_rolls}")
    
    # Department vs Category relationship in Dataset 1
    print("\nCategory to Department cross-tabulation in Dataset 1:")
    ct1 = pd.crosstab(df1['category'], df1['department'])
    print(ct1)

    # -------------------------------------------------------------
    # Deep Inspection of Dataset 2 (sheshanksingh)
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print("--- DATASET 2 (sheshanksingh/complaint) ---")
    print(f"File size: {os.path.getsize(p2):,} bytes")
    print(f"Rows: {len(df2):,}, Cols: {len(df2.columns)}")
    
    # Clean category name whitespace
    df2['category_clean'] = df2['category'].astype(str).str.strip()
    print("\nCleaned Category Counts in Dataset 2:")
    print(df2['category_clean'].value_counts())
    
    # Duplicate analysis
    exact_dupes_all_2 = df2.duplicated().sum()
    text_dupes_2 = df2['complaint_text'].duplicated().sum()
    print(f"\nExact full-row duplicates: {exact_dupes_all_2}")
    print(f"Text duplicates: {text_dupes_2} ({text_dupes_2/len(df2):.1%})")
    
    # Inspect duplicate texts: why 399 unique in 770 rows?
    dupe_text_counts = df2['complaint_text'].value_counts()
    print(f"Number of texts appearing >= 2 times: {(dupe_text_counts > 1).sum()}")
    print("Top repeated texts (showing top 3):")
    for text, count in dupe_text_counts.head(3).items():
        print(f"  [{count} times] {text[:80]}...")
    
    # Text lengths
    df2['text_char_len'] = df2['complaint_text'].astype(str).str.len()
    df2['text_word_len'] = df2['complaint_text'].astype(str).str.split().str.len()
    print("\nComplaint Text Length Summary (Characters):")
    print(df2['text_char_len'].describe())
    print("\nComplaint Text Length Summary (Words):")
    print(df2['text_word_len'].describe())
    
    # Script & Language Check
    non_ascii_2, devanagari_2, total_2 = check_scripts(df2['complaint_text'])
    print(f"\nNon-ASCII complaint texts: {non_ascii_2} / {total_2} ({non_ascii_2/total_2:.2%})")
    print(f"Devanagari script texts: {devanagari_2} / {total_2} ({devanagari_2/total_2:.2%})")
    
    # Hinglish / Hindi detection via common Romanized Hindi tokens
    hinglish_keywords = ['hai', 'hain', 'nahi', 'karo', 'kare', 'raha', 'rahi', 'bohot', 'bahut', 
                         'paani', 'khana', 'kharaab', 'ganda', 'gandi', 'kamre', 'bhi', 'kuch', 'humein', 'sir']
    
    def count_hinglish(text_series):
        matches = []
        for idx, t in text_series.items():
            words = set(str(t).lower().translate(str.maketrans('', '', string.punctuation)).split())
            found = words.intersection(hinglish_keywords)
            if found:
                matches.append((idx, str(t), list(found)))
        return matches

    hinglish_matches = count_hinglish(df2['complaint_text'])
    print(f"Hinglish / Romanized Hindi texts detected: {len(hinglish_matches)} / {total_2} ({len(hinglish_matches)/total_2:.1%})")
    print("Sample Hinglish texts:")
    for idx, sample, found_words in hinglish_matches[:5]:
        print(f"  [Row {idx}] (Keywords: {found_words}): {sample[:90]}...")
        
    # PII Check in Dataset 2
    df2_emails = df2['complaint_text'].apply(lambda x: len(email_pattern.findall(str(x)))).sum()
    df2_phones = df2['complaint_text'].apply(lambda x: len(phone_pattern.findall(str(x)))).sum()
    df2_rolls = df2['complaint_text'].apply(lambda x: len(roll_pattern.findall(str(x)))).sum()
    print(f"\nPII in Dataset 2 Complaint Texts:")
    print(f"  Emails detected: {df2_emails}")
    print(f"  Phone numbers detected: {df2_phones}")
    print(f"  Roll numbers detected: {df2_rolls}")
    
    # Source vs Category breakdown in Dataset 2
    print("\nSource vs Category in Dataset 2:")
    print(pd.crosstab(df2['category_clean'], df2['source']))

    # -------------------------------------------------------------
    # Cross-Dataset Collision & Leakage Check Against Project Splits
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print("CROSS-DATASET COLLISION & LEAKAGE AUDIT")
    print("=" * 80)
    
    splits = {
        "train": pd.read_csv("data/processed/train.csv"),
        "val": pd.read_csv("data/processed/val.csv"),
        "test": pd.read_csv("data/processed/test.csv")
    }
    
    def normalize_text(s):
        s = str(s).lower()
        s = re.sub(r'[^a-z0-9\s]', '', s)
        return ' '.join(s.split())
        
    for split_name, df_split in splits.items():
        split_texts = set(df_split['complaint_text'].apply(normalize_text))
        print(f"\nComparing against '{split_name}.csv' ({len(df_split)} rows, {len(split_texts)} unique normalized):")
        
        # Check Dataset 1 Description
        d1_desc_norm = df1['description'].apply(normalize_text)
        d1_title_norm = df1['title'].apply(normalize_text)
        
        match_d1_desc = d1_desc_norm.isin(split_texts).sum()
        match_d1_title = d1_title_norm.isin(split_texts).sum()
        print(f"  Dataset 1 (ayushcl) exact text collisions:")
        print(f"    Description collisions: {match_d1_desc}")
        print(f"    Title collisions: {match_d1_title}")
        
        # Check Dataset 2 Text
        d2_text_norm = df2['complaint_text'].apply(normalize_text)
        match_d2 = d2_text_norm.isin(split_texts).sum()
        print(f"  Dataset 2 (sheshanksingh) exact text collisions: {match_d2}")

if __name__ == "__main__":
    run_deep_inspection()

