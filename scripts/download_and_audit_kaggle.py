"""
Download and Audit Kaggle External Datasets
AI-Powered College Complaint Intelligence System

This script safely downloads and audits:
1. ayushcl/college-complaint -> data/external/kaggle_college_complaint/
2. sheshanksingh/complaint -> data/external/kaggle_multilingual_complaint/

Requires KAGGLE credentials (either ~/.kaggle/kaggle.json or KAGGLE_USERNAME / KAGGLE_KEY).
Never logs or prints user credentials.
"""

import os
import sys
import glob
import pandas as pd
from pathlib import Path

def download_datasets():
    print("Checking Kaggle API credentials...")
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi()
        api.authenticate()
        print("Kaggle API authenticated successfully.")
    except Exception as e:
        print(f"Error authenticating Kaggle API: {e}")
        print("Please configure credentials via ~/.kaggle/kaggle.json or set KAGGLE_USERNAME / KAGGLE_KEY.")
        return False

    targets = [
        ("ayushcl/college-complaint", "data/external/kaggle_college_complaint"),
        ("sheshanksingh/complaint", "data/external/kaggle_multilingual_complaint")
    ]

    for dataset_id, target_dir in targets:
        os.makedirs(target_dir, exist_ok=True)
        print(f"\nDownloading {dataset_id} to {target_dir}...")
        try:
            api.dataset_download_files(dataset_id, path=target_dir, unzip=True)
            print(f"Downloaded and unzipped {dataset_id} successfully.")
        except Exception as e:
            print(f"Failed to download {dataset_id}: {e}")

    return True

def audit_downloaded_data():
    print("\n" + "="*60)
    print("AUDITING DOWNLOADED EXTERNAL DATASETS")
    print("="*60)

    dirs = [
        ("Kaggle College Complaint (ayushcl)", "data/external/kaggle_college_complaint"),
        ("Kaggle Multilingual Complaint (sheshanksingh)", "data/external/kaggle_multilingual_complaint")
    ]

    for name, directory in dirs:
        print(f"\n--- {name} ---")
        p = Path(directory)
        if not p.exists():
            print(f"Directory {directory} does not exist.")
            continue

        files = list(p.glob("*.*"))
        if not files:
            print(f"No files found in {directory}.")
            continue

        for f in files:
            print(f"\nFile: {f.name} ({f.stat().st_size:,} bytes)")
            if f.suffix.lower() == '.csv':
                try:
                    df = pd.read_csv(f)
                    print(f"Rows: {len(df):,}, Columns: {len(df.columns)}")
                    print(f"Columns: {list(df.columns)}")
                    print("Missing Values:\n", df.isnull().sum())
                    print("Sample Head (first 2 rows):\n", df.head(2).to_dict(orient='records'))
                except Exception as e:
                    print(f"Error reading CSV: {e}")
            elif f.suffix.lower() in ['.xlsx', '.xls']:
                try:
                    df = pd.read_excel(f)
                    print(f"Rows: {len(df):,}, Columns: {len(df.columns)}")
                    print(f"Columns: {list(df.columns)}")
                except Exception as e:
                    print(f"Error reading Excel: {e}")

if __name__ == "__main__":
    success = download_datasets()
    if success:
        audit_downloaded_data()
    else:
        print("\nDownload skipped due to unauthenticated Kaggle session.")

