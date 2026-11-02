"""Inspect clean English candidates from DF2 Ragging."""
import re
import pandas as pd

df2 = pd.read_csv("data/external/kaggle_multilingual_complaint/ML_Project_Complaint_Dataset_Duration_Imp.csv")
ragging = df2[df2["category"].astype(str).str.strip().str.lower() == "ragging"].copy()

# PII masking function
def anonymize(t):
    return re.sub(r"Rugved Deolekar\s*(Sir)?", "A faculty member", t, flags=re.IGNORECASE)

hindi_words = {
    'hai', 'hain', 'nahi', 'karo', 'raha', 'rahi', 'rahe', 'bohot', 'bahut', 'paani', 'kharaab',
    'bhi', 'aur', 'ke', 'ki', 'ka', 'ko', 'se', 'yeh', 'woh', 'kya', 'kyun', 'ab', 'bina',
    'saath', 'karta', 'karte', 'karti', 'diya', 'de', 'liye', 'lag', 'ne', 'mein', 'kiya',
    'karein', 'aap', 'toh', 'hum', 'bura', 'ek', 'baar', 'baaki', 'unko', 'mujhe', 'hota',
    'hoti', 'hote', 'chal', 'kuch', 'pe', 'ho', 'jaao', 'waise', 'karna', 'karta', 'karti',
    'unhone', 'kaha', 'itna', 'yahan', 'aise', 'poori', 'saamne', 'pucha', 'puchte', 'jawab',
    'galat', 'rona', 'shuru', 'gayi', 'gaya', 'gaye', 'baat', 'kaatne', 'gaali', 'di',
    'badh', 'aaya', 'sir'
}

candidates = []
for idx, row in ragging.iterrows():
    text = anonymize(str(row["complaint_text"]).strip())
    # check tokens
    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
    hindi_found = [w for w in words if w in hindi_words]
    # Allow 'sir' if all other words are standard English
    hindi_strict = [w for w in hindi_found if w != 'sir']
    if not hindi_strict and len(text) >= 20:
        candidates.append((row["complaint_text"], text, hindi_found))

df_clean = pd.DataFrame(candidates, columns=["raw", "anonymized", "hindi_tokens"]).drop_duplicates(subset=["anonymized"])
print(f"Clean distinct English candidates: {len(df_clean)}")
for i, r in df_clean.iterrows():
    print(f"- ({len(r['anonymized'])} chars): {r['anonymized'][:100]}...")

