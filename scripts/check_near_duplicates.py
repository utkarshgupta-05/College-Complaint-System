import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def check_near_duplicates():
    print("=" * 80)
    print("NEAR-DUPLICATE CHECK (TF-IDF Cosine Similarity >= 0.80)")
    print("=" * 80)
    
    # Load project splits
    train_df = pd.read_csv("data/processed/train.csv")
    val_df = pd.read_csv("data/processed/val.csv")
    test_df = pd.read_csv("data/processed/test.csv")
    
    # Load Kaggle datasets
    d1_df = pd.read_csv("data/external/kaggle_college_complaint/complaints_dataset_final.csv")
    d2_df = pd.read_csv("data/external/kaggle_multilingual_complaint/ML_Project_Complaint_Dataset_Duration_Imp.csv")
    
    # Fit vectorizer on combined vocabulary
    vec = TfidfVectorizer(ngram_range=(1, 2), max_features=15000, stop_words='english')
    
    # Fit on train + external to build shared vocabulary
    all_texts = list(train_df['complaint_text']) + list(d1_df['description'][:5000]) + list(d2_df['complaint_text'])
    vec.fit(all_texts)
    
    # Vectorize project splits
    v_test = vec.transform(test_df['complaint_text'])
    v_val = vec.transform(val_df['complaint_text'])
    v_train = vec.transform(train_df['complaint_text'])
    
    # 1. Check Dataset 2 (N=770) against test split (N=182)
    v_d2 = vec.transform(d2_df['complaint_text'])
    sim_d2_test = cosine_similarity(v_d2, v_test)
    near_dupes_d2_test = np.argwhere(sim_d2_test >= 0.80)
    print(f"\nDataset 2 vs Held-Out Test Split (sim >= 0.80): {len(near_dupes_d2_test)} matches")
    for r, c in near_dupes_d2_test[:5]:
        print(f"  Sim={sim_d2_test[r, c]:.3f} | D2[{r}]: {d2_df['complaint_text'].iloc[r][:60]}... <-> Test[{c}]: {test_df['complaint_text'].iloc[c][:60]}...")

    # 2. Check Dataset 1 Sample (N=5,000) against test split (N=182)
    # We sample 5,000 from D1 to check representative near-duplicates
    v_d1_sample = vec.transform(d1_df['description'][:5000])
    sim_d1_test = cosine_similarity(v_d1_sample, v_test)
    near_dupes_d1_test = np.argwhere(sim_d1_test >= 0.80)
    print(f"\nDataset 1 (first 5,000) vs Held-Out Test Split (sim >= 0.80): {len(near_dupes_d1_test)} matches")
    for r, c in near_dupes_d1_test[:5]:
        print(f"  Sim={sim_d1_test[r, c]:.3f} | D1[{r}]: {d1_df['description'].iloc[r][:60]}... <-> Test[{c}]: {test_df['complaint_text'].iloc[c][:60]}...")

    # Max similarity observed
    print(f"\nMax similarity Dataset 2 vs Test: {sim_d2_test.max():.4f}")
    print(f"Max similarity Dataset 1 (first 5k) vs Test: {sim_d1_test.max():.4f}")

if __name__ == "__main__":
    check_near_duplicates()

