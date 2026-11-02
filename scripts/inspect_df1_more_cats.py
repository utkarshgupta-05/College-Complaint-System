"""Inspect IT Support and Infrastructure in DF1."""
import pandas as pd

df1 = pd.read_csv("data/external/kaggle_college_complaint/complaints_dataset_final.csv")
for cat in ["IT Support", "Infrastructure", "Library"]:
    sub = df1[df1["category"] == cat]
    print(f"\n=== Top Titles in {cat} (Total {len(sub)}) ===")
    for t, cnt in sub["title"].value_counts().head(10).items():
        print(f"  [{cnt:2d}] {t}")

