"""Display all 49 unique ragging texts."""
import pandas as pd

df2 = pd.read_csv("data/external/kaggle_multilingual_complaint/ML_Project_Complaint_Dataset_Duration_Imp.csv")
ragging = df2[df2["category"].astype(str).str.strip().str.lower() == "ragging"]
uniques = ragging["complaint_text"].dropna().unique()

for idx, text in enumerate(uniques, 1):
    print(f"[{idx}] {text}")

