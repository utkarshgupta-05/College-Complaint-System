"""Inspect all 49 unique ragging texts in DF2."""
import re
import pandas as pd

df2 = pd.read_csv("data/external/kaggle_multilingual_complaint/ML_Project_Complaint_Dataset_Duration_Imp.csv")
ragging = df2[df2["category"].astype(str).str.strip().str.lower() == "ragging"]
uniques = ragging["complaint_text"].dropna().unique()

hinglish_pattern = re.compile(
    r"\b(hai|hain|nahi|karo|raha|rahi|rahe|bohot|bahut|paani|kharaab|bhi|aur|ke|ki|ka|ko|se|yeh|woh|kya|kyun|ab|bina|saath|karta|karte|karti|diya|de|liye|lag|sir)\b",
    re.IGNORECASE
)

english_list = []
hinglish_list = []

for text in uniques:
    text_clean = text.strip()
    words = set(re.findall(r"\b[a-zA-Z]+\b", text_clean.lower()))
    hinglish_matches = [w for w in words if hinglish_pattern.search(w)]
    if hinglish_matches:
        hinglish_list.append((text_clean, hinglish_matches))
    else:
        english_list.append(text_clean)

print(f"Total unique texts: {len(uniques)}")
print(f"English texts ({len(english_list)}):")
for i, t in enumerate(english_list, 1):
    print(f"  [{i}] ({len(t)} chars): {t[:120]}")

print(f"\nHinglish texts ({len(hinglish_list)}):")
for i, (t, m) in enumerate(hinglish_list[:5], 1):
    print(f"  [{i}] Matches {m}: {t[:100]}")

