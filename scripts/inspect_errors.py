"""Inspect specific validation errors between E2 and E11."""
import joblib
import pandas as pd

val_df = pd.read_csv("data/processed/val.csv")
e2 = joblib.load("models/e2.joblib")["pipeline"]
e11 = joblib.load("models/e11_augmented.joblib")["pipeline"]

for idx in [33, 52]:
    text = val_df.loc[idx, "complaint_text"]
    true_cat = val_df.loc[idx, "category"]
    print(f"=== SAMPLE {idx} ===")
    print(f"True Category: {true_cat}")
    print(f"Text:\n{text}\n")
    p2 = e2.predict([text])[0]
    p11 = e11.predict([text])[0]
    prob2 = dict(zip(e2.classes_, e2.predict_proba([text])[0]))
    prob11 = dict(zip(e11.classes_, e11.predict_proba([text])[0]))
    print(f"E2 Prediction:  {p2} (conf={prob2[p2]:.4f}) | prob[C06]={prob2.get('C06', 0):.4f}")
    print(f"E11 Prediction: {p11} (conf={prob11[p11]:.4f}) | prob[C06]={prob11.get('C06', 0):.4f}")
    print("---")

