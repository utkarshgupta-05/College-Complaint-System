import os
import re
import pandas as pd
import numpy as np

def inspect_dataset_1():
    path = "data/external/kaggle_college_complaint/complaints_dataset_final.csv"
    print("=" * 80)
    print(f"INSPECTING DATASET 1: {path}")
    print("=" * 80)
    
    df = pd.read_csv(path)
    print(f"Total Rows: {len(df):,}")
    print(f"Total Columns: {len(df.columns)}")
    print(f"Columns: {list(df.columns)}")
    print("\nData Types:")
    print(df.dtypes)
    print("\nMissing Values Count:")
    print(df.isnull().sum())
    
    print("\nFirst 3 rows:")
    for i, r in df.head(3).iterrows():
        print(f"\n--- Row {i} ---")
        for c in df.columns:
            val = str(r[c])
            if len(val) > 100:
                val = val[:100] + "..."
            print(f"  {c}: {val}")

    # Inspect potential label columns
    for col in df.columns:
        n_unique = df[col].nunique()
        print(f"\nColumn '{col}': {n_unique} unique values")
        if n_unique <= 50:
            print(df[col].value_counts(dropna=False))

    return df

def inspect_dataset_2():
    path = "data/external/kaggle_multilingual_complaint/ML_Project_Complaint_Dataset_Duration_Imp.csv"
    print("\n" + "=" * 80)
    print(f"INSPECTING DATASET 2: {path}")
    print("=" * 80)
    
    df = pd.read_csv(path)
    print(f"Total Rows: {len(df):,}")
    print(f"Total Columns: {len(df.columns)}")
    print(f"Columns: {list(df.columns)}")
    print("\nData Types:")
    print(df.dtypes)
    print("\nMissing Values Count:")
    print(df.isnull().sum())
    
    print("\nFirst 3 rows:")
    for i, r in df.head(3).iterrows():
        print(f"\n--- Row {i} ---")
        for c in df.columns:
            val = str(r[c])
            if len(val) > 100:
                val = val[:100] + "..."
            print(f"  {c}: {val}")

    for col in df.columns:
        n_unique = df[col].nunique()
        print(f"\nColumn '{col}': {n_unique} unique values")
        if n_unique <= 50:
            print(df[col].value_counts(dropna=False))

    return df

if __name__ == "__main__":
    df1 = inspect_dataset_1()
    df2 = inspect_dataset_2()

