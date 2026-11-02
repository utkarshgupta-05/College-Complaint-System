"""Test curation and filtering logic for E11 data augmentation."""
import re
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load existing splits
train_df = pd.read_csv("data/processed/train.csv")
val_df = pd.read_csv("data/processed/val.csv")
test_df = pd.read_csv("data/processed/test.csv")

existing_texts = set(train_df["complaint_text"].str.strip().str.lower())
val_texts = list(val_df["complaint_text"].str.strip())
test_texts = list(test_df["complaint_text"].str.strip())
all_eval_texts = val_texts + test_texts

# Vectorizer for similarity checking against validation and test sets
eval_vec = TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_df=1.0)
eval_tfidf = eval_vec.fit_transform(all_eval_texts)

# 1. Dataset 1 Curation
df1 = pd.read_csv("data/external/kaggle_college_complaint/complaints_dataset_final.csv")

# Negative keywords for filtering out mislabeled classes in DF1:
# Hostel: avoid mess, food, canteen, internet, wifi, water cooler, fee receipt
hostel_exclude = re.compile(r"\b(mess|canteen|food|tiffin|lunch|dinner|breakfast|internet|wifi|wi-fi|router|broadband)\b", re.IGNORECASE)

# Academic: avoid classroom markers, broken bench, lab equipment, projector
academic_exclude = re.compile(r"\b(marker|whiteboard|projector|dustbin in classroom|broken bench|fan in room)\b", re.IGNORECASE)

# Others: avoid mess/food, ragging, cheating in exam, fee receipt, id card, tc, bus, admission docs
others_exclude = re.compile(r"\b(canteen|food|mess|ragging|cheating|exam|exam portal|bus|transport|fee receipt|admission|tc |transfer certificate|id card|water cooler|wifi|internet)\b", re.IGNORECASE)

def clean_df1_text(row):
    title = str(row["title"]).strip()
    desc = str(row["description"]).strip()
    if title.lower() in desc.lower():
        text = desc
    else:
        text = f"{title}. {desc}"
    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text

curated_df1 = {}

# C01 Hostel
sub = df1[df1["category"] == "Hostel"].copy()
sub["text"] = sub.apply(clean_df1_text, axis=1)
sub = sub[~sub["text"].str.contains(hostel_exclude)]
sub = sub[sub["text"].str.len() >= 60]
sub = sub.drop_duplicates(subset=["title"])
sub = sub.sample(n=min(150, len(sub)), random_state=42)
curated_df1["C01"] = sub
print(f"C01 Hostel curated: {len(sub)}")

# C09 Transport
sub = df1[df1["category"] == "Transport"].copy()
sub["text"] = sub.apply(clean_df1_text, axis=1)
sub = sub[sub["text"].str.len() >= 60]
sub = sub.drop_duplicates(subset=["title"])
sub = sub.sample(n=min(150, len(sub)), random_state=42)
curated_df1["C09"] = sub
print(f"C09 Transport curated: {len(sub)}")

# C05 Academic
sub = df1[df1["category"] == "Academic"].copy()
sub["text"] = sub.apply(clean_df1_text, axis=1)
sub = sub[~sub["text"].str.contains(academic_exclude)]
sub = sub[sub["text"].str.len() >= 60]
sub = sub.drop_duplicates(subset=["title"])
sub = sub.sample(n=min(150, len(sub)), random_state=42)
curated_df1["C05"] = sub
print(f"C05 Academic curated: {len(sub)}")

# C11 Others
sub = df1[df1["category"] == "Others"].copy()
sub["text"] = sub.apply(clean_df1_text, axis=1)
sub = sub[~sub["text"].str.contains(others_exclude)]
sub = sub[sub["text"].str.len() >= 60]
sub = sub.drop_duplicates(subset=["title"])
sub = sub.sample(n=min(150, len(sub)), random_state=42)
curated_df1["C11"] = sub
print(f"C11 Others curated: {len(sub)}")

# 2. Dataset 2 Curation (C08 Campus Safety / Ragging)
df2 = pd.read_csv("data/external/kaggle_multilingual_complaint/ML_Project_Complaint_Dataset_Duration_Imp.csv")
ragging = df2[df2["category"].astype(str).str.strip().str.lower() == "ragging"].copy()

def anonymize_text(t):
    t = re.sub(r"Rugved Deolekar\s*(Sir)?", "A faculty member", t, flags=re.IGNORECASE)
    return t

hindi_words = {
    'hai', 'hain', 'nahi', 'karo', 'raha', 'rahi', 'rahe', 'bohot', 'bahut', 'paani', 'kharaab',
    'bhi', 'aur', 'ke', 'ki', 'ka', 'ko', 'se', 'yeh', 'woh', 'kya', 'kyun', 'ab', 'bina',
    'saath', 'karta', 'karte', 'karti', 'diya', 'de', 'liye', 'lag', 'ne', 'mein', 'kiya',
    'karein', 'aap', 'toh', 'hum', 'bura', 'ek', 'baar', 'baaki', 'unko', 'mujhe', 'hota',
    'hoti', 'hote', 'chal', 'kuch', 'pe', 'ho', 'jaao', 'waise', 'karna', 'karta', 'karti',
    'unhone', 'kaha', 'itna', 'yahan', 'aise', 'poori', 'saamne', 'pucha', 'puchte', 'jawab',
    'galat', 'rona', 'shuru', 'gayi', 'gaya', 'gaye', 'baat', 'kaatne', 'gaali', 'di',
    'badh', 'aaya'
}

curated_df2_rows = []
for idx, r in ragging.iterrows():
    text = anonymize_text(str(r["complaint_text"]).strip())
    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
    hindi_strict = [w for w in words if w in hindi_words]
    if not hindi_strict and len(text) >= 25:
        curated_df2_rows.append({
            "text": text,
            "raw_category": r["category"],
            "urgency": r.get("urgency", "High"),
            "source": r.get("source", "student_portal"),
        })

df2_clean = pd.DataFrame(curated_df2_rows).drop_duplicates(subset=["text"])
print(f"C08 Ragging curated: {len(df2_clean)}")

# Check collision against existing texts and similarity against val/test
all_curated_texts = []
for cat, sub in curated_df1.items():
    all_curated_texts.extend(sub["text"].tolist())
all_curated_texts.extend(df2_clean["text"].tolist())

print(f"\nTotal curated external records: {len(all_curated_texts)}")

exact_collisions = [t for t in all_curated_texts if t.strip().lower() in existing_texts]
print(f"Exact collisions with train set: {len(exact_collisions)}")

# Check max similarity with val/test
cand_tfidf = eval_vec.transform(all_curated_texts)
sim_matrix = cosine_similarity(cand_tfidf, eval_tfidf)
max_sim = sim_matrix.max()
print(f"Max cosine similarity with val/test: {max_sim:.4f}")

