"""Inspect topics in DF1 Others."""
import pandas as pd

df1 = pd.read_csv("data/external/kaggle_college_complaint/complaints_dataset_final.csv")
others = df1[df1["category"] == "Others"]
print(f"Total Others: {len(others)}")
print("Sample titles in Others:")
for t in others["title"].value_counts().head(30).index:
    print(f"  - {t}")

