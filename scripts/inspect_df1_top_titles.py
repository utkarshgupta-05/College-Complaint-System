"""Inspect top titles in Hostel, Transport, Academic from DF1."""
import pandas as pd

df1 = pd.read_csv("data/external/kaggle_college_complaint/complaints_dataset_final.csv")
for cat in ["Hostel", "Transport", "Academic"]:
    sub = df1[df1["category"] == cat]
    print(f"\n=== Top Titles in {cat} (Total {len(sub)}) ===")
    for t, cnt in sub["title"].value_counts().head(20).items():
        print(f"  [{cnt:2d}] {t}")

