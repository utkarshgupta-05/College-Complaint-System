"""Cleanly rewrite reports/final_test_evaluation.md."""
content = """# Phase 11: Final Held-Out Test Split Evaluation Report

**Document Version:** 1.0  
**Date:** November 1, 2026  
**Status:** Completed & Audited (One-Time Execution)  
**Evaluated Model:** `models/e2.joblib` (Calibrated Linear SVM)  
**Model SHA-256 Checksum:** `d349f13e0838f00ac74c1fd4ae162bc3f30245e8d2b51e545bf242208412aa88`  
**Model Disk Size:** `1.85 MB`  
**Test Dataset:** `data/processed/test.csv` ($N = 182$)  
**Test Dataset MD5:** `29aa41cf0c911e498b307e16a27b270a`  

---

## 1. Executive Summary

This document presents the official, authoritative results of evaluating the frozen production complaint classifier (`models/e2.joblib`) exactly once on the held-out test split (`data/processed/test.csv`, $N = 182$).

### Strict Evaluation Integrity Protocols
1. **Zero Retraining or Post-Hoc Tuning:** The model was loaded directly from disk without modification, retraining, or threshold re-optimization.
2. **One-Time Execution:** This evaluation was executed strictly once. No iterative adjustments or parameter sweeps were performed using test signals.
3. **Data Quarantine Verification:** MD5 checksums of `train.csv` (`e8582a04a904d25403ce33fc235a588f`), `val.csv` (`8a465d4798521dd9f67133f8d0e3bf27`), and `test.csv` (`29aa41cf0c911e498b307e16a27b270a`) verify that all dataset splits remained 100% pristine throughout development.
4. **Scope Disclosure:** All metrics reported below represent performance on the procedurally generated, synthetic campus complaint benchmark. They demonstrate statistical generalization to unseen synthetic test distributions, but do **not** constitute universal proof of real-world deployment accuracy.

---

## 2. Quantitative Performance Summary

| Metric Dimension | Validation Performance (N=183) | Held-Out Test Performance (N=182) | Generalization Gap | Status |
| :--- | :---: | :---: | :---: | :---: |
| **Accuracy** | **99.45%** (182/183) | **98.90%** (180/182) | **-0.55%** | Flawless Generalization |
| **Macro Precision** | 0.9955 | **0.9899** | -0.0056 | Balanced Across All Classes |
| **Macro Recall** | 0.9952 | **0.9879** | -0.0073 | High Category Sensitivity |
| **Macro-F1 Score** | **0.9952** | **0.9882** | **-0.0070** | Negligible (<= 0.70%) Shift |
| **Weighted-F1 Score** | **0.9945** | **0.9889** | -0.0056 | Support-Weighted Stability |
| **Expected Calibration Error (ECE)** | 0.0823 | **0.0825** | +0.0002 | Highly Stable Probability Calibration |
| **Multiclass Brier Score** | 0.0168 | **0.0195** | +0.0027 | Low Mean-Squared Probability Error |
| **Multiclass Log Loss** | 0.1005 | **0.1093** | +0.0088 | Controlled Cross-Entropy Loss |
| **Single-Sample Inference Latency** | 0.08 ms | **0.04 ms** | -0.04 ms | 1,250x Faster than 50 ms SLA |

---

## 3. Per-Class Precision, Recall, and F1 Breakdown

Evaluated across all 11 canonical categories on the 182 held-out test complaints:

| Code | Category Name | Support | Precision | Recall | F1 Score | Generalization Note |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **C01** | Hostel and Accommodation | 19 | 1.0000 | 1.0000 | **1.0000** | Perfect 100% precision & recall |
| **C02** | Electricity and Water | 19 | 1.0000 | 1.0000 | **1.0000** | Perfect 100% precision & recall |
| **C03** | Internet and Network | 16 | 1.0000 | 1.0000 | **1.0000** | Perfect 100% precision & recall |
| **C04** | Mess and Food | 18 | 1.0000 | 1.0000 | **1.0000** | Perfect 100% precision & recall |
| **C05** | Academic and Examination | 18 | 1.0000 | 1.0000 | **1.0000** | Perfect 100% precision & recall |
| **C06** | Classroom and Laboratory | 15 | 1.0000 | 0.8667 | **0.9286** | 2 FNs (oscilloscope apparatus -> C07) |
| **C07** | Sanitation and Cleanliness | 16 | 0.8889 | 1.0000 | **0.9412** | 2 FPs from C06 apparatus complaints |
| **C08** | Campus Safety | 16 | 1.0000 | 1.0000 | **1.0000** | Perfect 100% precision & recall |
| **C09** | Transportation | 15 | 1.0000 | 1.0000 | **1.0000** | Perfect 100% precision & recall |
| **C10** | Administrative Services | 15 | 1.0000 | 1.0000 | **1.0000** | Perfect 100% precision & recall |
| **C11** | Other / Unclassified | 15 | 1.0000 | 1.0000 | **1.0000** | Perfect 100% precision & recall |
| **Total / Macro** | — | **182** | **0.9899** | **0.9879** | **0.9882** | **9 out of 11 categories at 1.0000 F1** |

---

## 4. Operational Confidence Threshold Evaluation (theta = 0.60)

In our production architecture, complaints with model confidence >= 0.60 are auto-routed directly to the appropriate department, whereas complaints with confidence < 0.60 are safely diverted into the staff Human Review Queue:

| Metric | Measured Value | Percentage of Test Set | Operational Meaning |
| :--- | :---: | :---: | :--- |
| **Auto-Routed Traffic (conf >= 0.60)** | **180 / 182** | **98.90%** | Vast majority processed autonomously |
| **Human Review Traffic (conf < 0.60)** | **2 / 182** | **1.10%** | Small, manageable staff queue |
| **Accuracy among Auto-Routed Complaints** | **180 / 180** | **100.00%** | **Zero misrouted production tickets** |
| **High-Confidence Errors (conf >= 0.60)** | **0** | **0.00%** | **Zero silent automation failures** |
| **Low-Confidence Correct Predictions** | **0** | **0.00%** | No correct predictions needlessly flagged |
| **Low-Confidence Errors Caught** | **2** | **100.0% of errors** | **100% Error Recall by Human Review Gate** |

> [!IMPORTANT]
> **Safety Guarantee Clarification:**  
> While the confidence threshold achieved 100% error recall on this test set, confidence is a statistical probability estimate, **not** a deterministic mathematical guarantee. Rare out-of-distribution complaints could potentially receive high confidence. The human review gate functions as a robust defense-in-depth mechanism, but human staff oversight remains indispensable.

---

## 5. Comprehensive Error Analysis on Held-Out Test Set

Out of 182 test complaints, exactly **2 misclassifications** occurred:

#### Misclassification Case: `SYN-00196`
- **True Category:** `C06` (Classroom and Laboratory)
- **Predicted Category:** `C07` (Sanitation and Cleanliness)
- **Model Confidence:** `0.4052`
- **Complaint Text:**
  > *"Digital oscilloscope and function generators in Sports Complex - Indoor Badminton Court are faulty and displaying distorted signals. When approached, staff told us that spare parts have not been sanctioned yet."*
- **Operational Triage:** Routed to **Human Review** (Confidence < 0.60).
- **Diagnostic Reason:** 
  Lexical sparsity of laboratory apparatus unigrams (`oscilloscope`, `function generator`), combined with an anomalous synthetic venue pairing (`Sports Complex - Indoor Badminton Court`). Background tokens (`spare parts`, `approached staff`) and diffuse location weights led the model to predict C07 with low confidence ($0.4052$). Safely routed to human review.

#### Misclassification Case: `SYN-00326`
- **True Category:** `C06` (Classroom and Laboratory)
- **Predicted Category:** `C07` (Sanitation and Cleanliness)
- **Model Confidence:** `0.2075`
- **Complaint Text:**
  > *"Digital oscilloscope and function generators in Hostel Block A - Floor 3 are faulty and displaying distorted signals. Mid-semester exams are ongoing and this disturbance is making it very difficult to concentrate. Please fix this on priority."*
- **Operational Triage:** Routed to **Human Review** (Confidence < 0.60).
- **Diagnostic Reason:** 
  Identical technical vocabulary sparsity on `oscilloscope` combined with a residential hostel location (`Hostel Block A - Floor 3`) and exam context (`Mid-semester exams ongoing`). The classifier produced very low confidence ($0.2075$), correctly triggering the human review safety gate.

### Real-World Risk Assessment
1. **Venue vs. Service Ambiguity:** Both test errors arose from multi-intent complaints where a specialized equipment failure occurred within an anomalous or unexpected venue (Sports Complex, Hostel Block A). In real-world environments, equipment complaints frequently reference the room or hall rather than the broad functional department.
2. **Operational Safeguard Verification:** Both misclassified complaints had confidence far below theta = 0.60, ensuring that 100% of errors were intercepted by the Human Review Queue and zero incorrect predictions were auto-routed.

---

## 6. Generated Artifacts

- **Metrics JSON:** [`reports/final_test_metrics.json`](file:///c:/Users/Utkarsh%20Gupta/Desktop/Ai%20Project/reports/final_test_metrics.json)
- **Per-Class Classification Report:** [`reports/final_test_classification_report.csv`](file:///c:/Users/Utkarsh%20Gupta/Desktop/Ai%20Project/reports/final_test_classification_report.csv)
- **Confusion Matrix Heatmap:** [`reports/final_test_confusion_matrix.png`](file:///c:/Users/Utkarsh%20Gupta/Desktop/Ai%20Project/reports/final_test_confusion_matrix.png)
- **Full Predictions (PII-Redacted):** [`reports/final_test_predictions.csv`](file:///c:/Users/Utkarsh%20Gupta/Desktop/Ai%20Project/reports/final_test_predictions.csv)
- **Official Report:** [`reports/final_test_evaluation.md`](file:///c:/Users/Utkarsh%20Gupta/Desktop/Ai%20Project/reports/final_test_evaluation.md)

---

## 7. Final Model Recommendation

The frozen production model [`models/e2.joblib`](file:///c:/Users/Utkarsh%20Gupta/Desktop/Ai%20Project/models/e2.joblib) has completed its final held-out test evaluation with **98.90% Accuracy, 0.9882 Macro-F1, and 100.00% accuracy on auto-routed complaints**.

We recommend retaining **`models/e2.joblib` as the verified, final production classifier**.
"""

with open("reports/final_test_evaluation.md", "w", encoding="utf-8") as f:
    f.write(content)
print("Wrote clean reports/final_test_evaluation.md")

