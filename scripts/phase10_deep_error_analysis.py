"""
scripts/phase10_deep_error_analysis.py
--------------------------------------
Systematic classification error and boundary analysis for Phase 10.
Analyzes:
1. Validation errors and low-confidence predictions (< 0.70) across E2 and E11.
2. Historical errors from E1, E2, E3, E4.
3. Confusion matrices and class overlap pairs:
   - C05 (Academic) vs C06 (Classroom/Lab)
   - C06 (Classroom/Lab) vs C08 (Campus Safety)
   - C02 (Electricity/Water) vs C06 (Classroom/Lab)
   - C03 (Internet/Network) vs C06 (Classroom/Lab)
   - C07 (Sanitation) vs C06 (Classroom/Lab)
4. Vocabulary analysis and n-gram overlap between confusing categories.
5. Training data representation, length distributions, and style divergence.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.abspath("."))

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix

CATEGORY_NAMES = {
    "C01": "Hostel and Accommodation",
    "C02": "Electricity and Water",
    "C03": "Internet and Network",
    "C04": "Mess and Food",
    "C05": "Academic and Examination",
    "C06": "Classroom and Laboratory",
    "C07": "Sanitation and Cleanliness",
    "C08": "Campus Safety",
    "C09": "Transportation",
    "C10": "Administrative Services",
    "C11": "Other / Unclassified",
}

val_df = pd.read_csv("data/processed/val.csv")
train_df = pd.read_csv("data/processed/train.csv")
e11_train_df = pd.read_csv("data/processed/e11_augmented_train.csv")

val_texts = val_df["complaint_text"].tolist()
val_labels = val_df["category"].tolist()
label_names = sorted(list(CATEGORY_NAMES.keys()))

e2 = joblib.load("models/e2.joblib")["pipeline"]
e11 = joblib.load("models/e11_augmented.joblib")["pipeline"]

# Load other baseline models if available
models_dict = {"E2": e2, "E11": e11}
for exp in ["e1", "e3", "e4"]:
    p = Path(f"models/{exp}.joblib")
    if p.exists():
        models_dict[exp.upper()] = joblib.load(p)["pipeline"]

# Compute predictions and probabilities
preds = {}
probs = {}
confs = {}

for name, model in models_dict.items():
    p = model.predict(val_texts)
    pr = model.predict_proba(val_texts)
    c = np.max(pr, axis=1)
    preds[name] = p
    probs[name] = pr
    confs[name] = c

# 1. Identify all errors in E2 and E11
print("=== VALIDATION ERRORS (E2 & E11) ===")
error_indices = set()
for i, true_cat in enumerate(val_labels):
    if preds["E2"][i] != true_cat or preds["E11"][i] != true_cat:
        error_indices.add(i)

for i in sorted(list(error_indices)):
    print(f"\n--- Sample {i} ---")
    print(f"True: {val_labels[i]} ({CATEGORY_NAMES[val_labels[i]]})")
    print(f"E2 Pred:  {preds['E2'][i]} (conf={confs['E2'][i]:.4f})")
    print(f"E11 Pred: {preds['E11'][i]} (conf={confs['E11'][i]:.4f})")
    for name in ["E1", "E3", "E4"]:
        if name in preds:
            print(f"{name} Pred:  {preds[name][i]} (conf={confs[name][i]:.4f})")
    print(f"Text:\n{val_texts[i]}")

# 2. Identify low confidence cases (conf < 0.70) in E2 or E11
print("\n=== LOW CONFIDENCE SAMPLES (< 0.70 in E2 or E11) ===")
low_conf_indices = set()
for i in range(len(val_texts)):
    if confs["E2"][i] < 0.70 or confs["E11"][i] < 0.70:
        low_conf_indices.add(i)

print(f"Total low-confidence samples (< 0.70): {len(low_conf_indices)}")
for i in sorted(list(low_conf_indices)):
    is_err = "ERROR" if (preds["E2"][i] != val_labels[i] or preds["E11"][i] != val_labels[i]) else "CORRECT"
    print(f"Sample {i} [{is_err}]: True={val_labels[i]} | E2={preds['E2'][i]} (conf={confs['E2'][i]:.3f}) | E11={preds['E11'][i]} (conf={confs['E11'][i]:.3f})")
    print(f"   Text: {val_texts[i][:110]}...")

# 3. Confusion Matrix of E2 and E11
cm_e2 = confusion_matrix(val_labels, preds["E2"], labels=label_names)
cm_e11 = confusion_matrix(val_labels, preds["E11"], labels=label_names)

print("\n=== CONFUSION MATRIX E2 ===")
print(pd.DataFrame(cm_e2, index=label_names, columns=label_names))

print("\n=== CONFUSION MATRIX E11 ===")
print(pd.DataFrame(cm_e11, index=label_names, columns=label_names))

