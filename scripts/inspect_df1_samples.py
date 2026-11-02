"""Inspect title and description combinations in DF1."""
import pandas as pd

df1 = pd.read_csv("data/external/kaggle_college_complaint/complaints_dataset_final.csv")
for cat in ["Hostel", "Transport", "Academic", "Others"]:
    sub = df1[df1["category"] == cat]
    print(f"=== {cat} ===")
    sample = sub.sample(3, random_state=42)
    for _, r in sample.iterrows():
        print(f"TITLE: {r['title']}")
        print(f"DESC:  {r['description']}")
        print(f"LOC:   {r['location']}")
        print(f"PRIO:  {r['priority']}")
        print("---")

