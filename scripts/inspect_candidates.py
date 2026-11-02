"""Inspect candidate records from external datasets."""
import pandas as pd

df1 = pd.read_csv("data/external/kaggle_college_complaint/complaints_dataset_final.csv")
for cat in ["Hostel", "Transport", "Academic", "Others"]:
    sub = df1[df1["category"] == cat]
    print(f"=== {cat} (Total {len(sub)}) ===")
    print(f"Unique titles: {sub['title'].nunique()}, Unique descs: {sub['description'].nunique()}")
    for i, row in sub.head(3).iterrows():
        print(f"  ID: {row['complaint_id']}")
        print(f"  Title: {row['title']}")
        print(f"  Desc: {str(row['description'])[:120]}...")
        print(f"  Loc: {row['location']}")

print("\n=== DF2 Ragging Inspection ===")
df2 = pd.read_csv("data/external/kaggle_multilingual_complaint/ML_Project_Complaint_Dataset_Duration_Imp.csv")
ragging = df2[df2["category"].astype(str).str.strip().str.lower() == "ragging"]
print(f"Total Ragging rows: {len(ragging)}")
print(f"Unique texts: {ragging['complaint_text'].nunique()}")
for i, row in ragging.head(10).iterrows():
    print(f"  Text: {row['complaint_text']}")

