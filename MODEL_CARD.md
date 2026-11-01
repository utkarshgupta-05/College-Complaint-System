# Model Card — College Complaint Intelligence System

> **Standard:** Adheres to the Model Cards for Model Reporting framework (Mitchell et al., 2019).  
> **Status:** Final & Verified (Phase 9 Completed)  
> **Evaluation Date:** November 1, 2026  
> **Model Release Version:** v1.0.0  

---

## 1. Model Details

### 1.1 Overview
The College Complaint Intelligence System encompasses four specialized AI/ML modules designed to automate triage, similarity detection, priority assessment, and pattern discovery for university campus operations:

- **Module A (Complaint Classifier):** Multi-class text classification pipeline mapping unstructured complaints to 11 campus operational categories.
- **Module B (Duplicate & Related Complaint Detector):** Lexical and semantic similarity retrieval engine surfacing candidate duplicates for human triage.
- **Module C (Priority Assessment Engine):** Deterministic, auditable rules-based prioritization and SLA engine with hard safety override circuits.
- **Module D (Recurring-Issue Discovery):** Unsupervised clustering (Spherical K-Means and Cosine DBSCAN) and spatiotemporal hotspot discovery.

### 1.2 Model Architecture & Implementation

| Module | Primary Method | Underlying Architecture | Artifact Path | Size on Disk |
|---|---|---|---|---|
| **Module A** | Calibrated Linear SVM | `TfidfVectorizer(ngram_range=(1,2), max_features=10000, sublinear_tf=True)` + `CalibratedClassifierCV(LinearSVC(C=1.0, class_weight='balanced'), method='sigmoid', cv=5)` | `models/e2.joblib` | 1.84 MB |
| **Module B** | TF-IDF Cosine Similarity Retriever | `TfidfVectorizer(ngram_range=(1,2), max_features=10000, sublinear_tf=True)` with pre-indexed corpus matrix and dynamic online incremental indexing | `models/e6_tfidf_retriever.joblib` | 420 KB |
| **Module C** | Auditable Priority Rules Engine | Canonical multi-factor linear formulation ($P_{\text{base}}$) + Regex Safety Hazard Scanner + Staff Override Audit Hooks | `src/prioritization/rules.py` | Code |
| **Module D** | Spherical K-Means & Cosine DBSCAN | TF-IDF Vectorizer + `KMeans(k=12)` / `DBSCAN(eps=0.58, min_samples=3, metric='cosine')` | `models/e8_kmeans_clusters.joblib`, `models/e10_dbscan_clusters.joblib` | 2.1 MB |

---

## 2. Intended Use

### 2.1 Primary Intended Uses
- **Real-Time Pre-Triage Assistance:** Provide immediate, debounced category suggestions, confidence scores, and potential duplicate warnings to students during complaint drafting to improve clarity.
- **Staff Queue Routing:** Automatically direct high-confidence complaints ($\text{confidence} \ge 0.60$) to the relevant campus departmental queues (e.g., Electrical, Mess, Sanitation, Security).
- **Advisory Duplicate Surfacing:** Identify multi-student reports of shared incidents (e.g., water pipe bursts, dining hall food contamination) and present them as advisory candidate cards to department triage staff.
- **Emergency Escalation:** Detect acute hazards (fire, electric shock, structural collapse, assault, ragging) and immediately escalate complaints to `CRITICAL` priority with mandatory human review.
- **Campus Analytics:** Help university administrators identify geographic maintenance hotspots and emergent incident spikes across campus facilities.

### 2.2 Out-of-Scope & Prohibited Use Cases
- **Autonomous Ticket Closure or Merging:** The model is **strictly prohibited** from automatically closing, deleting, merging, or discarding complaints without explicit human staff verification.
- **Sole Arbiter of Safety Emergencies:** The system is an operational triage aid, **not** an automated 911/emergency dispatch system. Any active life-safety hazard must still be reported via primary physical campus security channels.
- **Disciplinary or Punitive Action:** The model must **never** be used to penalize, profile, or discipline students based on complaint frequency or linguistic sentiment.
- **Unreviewed High-Stakes Legal/Disciplinary Decisions:** Sexual harassment or physical assault reports require immediate confidential human counselor routing, bypassing automated resolution workflows.

---

## 3. Factors and Sub-Populations

### 3.1 Relevant Factors
- **Linguistic Formality:** Informal student colloquialisms, short sentence fragments, slang ("mess food is pathetic", "washroom stinks", "wifi dead").
- **Campus Facilities & Locations:** Hostels, academic departments, laboratories, libraries, dining halls, sports complexes, transit routes.
- **Incident Urgency:** Routine cosmetic defects vs. acute life-safety hazards.

### 3.2 Evaluation Factors
- Performance was evaluated across all 11 standardized operational categories (C01 through C11).
- Evaluated on held-out incident groups to measure generalization to unseen maintenance events.
- Evaluated on low-confidence edge cases and cross-domain complaints.

---

## 4. Metrics & Decision Thresholds

### 4.1 Evaluation Metrics
- **Classification:** Macro-F1 (primary metric to penalize minority class degradation), Weighted-F1, Overall Accuracy, Expected Calibration Error (ECE, 10 bins), Multiclass Brier Score, Multiclass Log Loss, and Single-Sample Inference Latency (ms).
- **Duplicate Retrieval:** Hit@1, Hit@3, Hit@5, Precision@k, Recall@k, Mean Reciprocal Rank (MRR), and Pairwise ROC-AUC.
- **Priority Assessment:** Safety Override Recall (must be 100% for hazard keywords), Base Score Calibration, and SLA Escalation Reliability.

### 4.2 Approved Decision Thresholds
- **Auto-Routing Confidence Threshold:** $\theta = 0.60$.
  - Selected during Phase 4 validation comparative analysis (Decision D-012) and fixed before test evaluation.
  - Predictions with $\text{confidence} \ge 0.60$ are automatically assigned to the predicted departmental queue.
  - Predictions with $\text{confidence} < 0.60$ or predicted as `C11` (Other/Unclassified) are flagged with `needs_human_review = True` and sent to the general triage queue.
- **Duplicate Similarity Thresholds (Pre-Fixed on Validation Split, Decision D-013):**
  - **Optimal Pairwise F1 Threshold ($\tau = 0.60$):** Derived from validation sweep (`duplicate_thresholds_e6.csv`). Balances precision and recall for linking candidate reports.
  - **Probable Duplicate ($\tau_{\text{high}} = 0.80$):** High lexical match; flagged prominently as a potential duplicate.
  - **Related Complaint ($\tau_{\text{mid}} = 0.50$):** Moderate semantic overlap; surfaced as contextual related background.
  - All duplicate thresholds generate **advisory suggestions only**; no automated mergers or ticket closures occur.

---

## 5. Evaluation Data

### 5.1 Held-Out Test Split (`data/processed/test.csv`)
- **Sample Size:** 182 records ($14.3\%$ of total corpus).
- **Partitioning Method:** `StratifiedGroupKFold(n_splits=7, shuffle=True, random_state=42)`.
- **Integrity Status:** Strictly quarantined from all training, validation, and threshold selection phases. Leakage verified: **0 shared complaint IDs, 0 shared texts, 0 shared incident groups**.
- **Class Balance:** 15 to 19 examples per category across all 11 classes.
- **Incident Groups:** 7 multi-report groups representing 18 complaints and 15 true duplicate pairs.

---

## 6. Training Data

### 6.1 Training Split (`data/processed/train.csv`)
- **Sample Size:** 908 records ($71.3\%$ of total corpus).
- **Class Balance:** Uniformly distributed across 11 categories (80 to 87 records per category).
- **Incident Groups:** 35 multi-report incident groups (92 records total).
- **Preprocessing:** Lowercasing, punctuation stripping, whitespace normalization, synthetic PII masking. TF-IDF vectorizer fit **strictly on training texts**.

### 6.2 Validation Split (`data/processed/val.csv`)
- **Sample Size:** 183 records ($14.4\%$ of total corpus).
- **Purpose:** Used for model selection between E1, E2, E3, and E4, and for threshold calibration ($\theta=0.60$, $\tau=0.80$).

---

## 7. Quantitative Analyses

### 7.1 Primary Classifier (E2 Calibrated Linear SVM) on Held-Out Test Set

| Metric | Validation Set ($N=183$) | Held-Out Test Set ($N=182$) | Generalization Gap | Status |
|---|---|---|---|---|
| **Accuracy** | 99.45% | **98.90%** | $-0.55\%$ | Exceeds $\ge 85\%$ Target |
| **Macro-F1** | 0.9952 | **0.9882** | $-0.0070$ | Exceeds $\ge 0.80$ Target |
| **Weighted-F1** | 0.9945 | **0.9889** | $-0.0056$ | Exceeds $\ge 0.80$ Target |
| **Expected Calibration Error (ECE)** | 0.0823 | **0.0825** | $+0.0002$ | Strong Probabilistic Fit |
| **Multiclass Brier Score** | 0.0168 | **0.0195** | $+0.0027$ | Low Mean Squared Error |
| **Multiclass Log Loss** | 0.1005 | **0.1093** | $+0.0088$ | Low Entropy Penalty |
| **Inference Latency** | 0.11 ms | **0.11 ms** | $0.00\text{ ms}$ | Real-Time Keystroke Capable |

### 7.2 Per-Class Classification Report (Test Split)

| Code | Category Name | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|---|
| C01 | Hostel and Accommodation | 1.0000 | 1.0000 | 1.0000 | 19 |
| C02 | Electricity and Water | 1.0000 | 1.0000 | 1.0000 | 19 |
| C03 | Internet and Network | 1.0000 | 1.0000 | 1.0000 | 16 |
| C04 | Mess and Food | 1.0000 | 1.0000 | 1.0000 | 18 |
| C05 | Academic and Examination | 1.0000 | 1.0000 | 1.0000 | 18 |
| C06 | Classroom and Laboratory | 1.0000 | 0.8667 | 0.9286 | 15 |
| C07 | Sanitation and Cleanliness | 0.8889 | 1.0000 | 0.9412 | 16 |
| C08 | Campus Safety | 1.0000 | 1.0000 | 1.0000 | 16 |
| C09 | Transportation | 1.0000 | 1.0000 | 1.0000 | 15 |
| C10 | Administrative Services | 1.0000 | 1.0000 | 1.0000 | 15 |
| C11 | Other / Unclassified | 1.0000 | 1.0000 | 1.0000 | 15 |
| **Avg** | **Macro Average** | **0.9899** | **0.9879** | **0.9882** | **182** |

### 7.3 Operational Thresholding & Error Recall ($\theta = 0.60$)
- **Auto-Routed Traffic:** **98.9%** of incoming complaints.
- **Auto-Routing Accuracy:** **100.00%** (zero incorrectly routed complaints).
- **Human Review Traffic:** **1.1%** (2 out of 182).
- **Error Recall:** **100.0%** (both misclassifications were successfully caught by the review filter).
- **False Review Rate:** **0.00%** (no correctly classified complaints were unnecessarily diverted).

### 7.4 Duplicate Retrieval Performance (E6 TF-IDF Retriever on Test Split)
- **Top-$k$ Ranking Across Multi-Report Incident Queries ($N=18$ queries across 7 groups, 15 true positive pairs):**
  - **Hit@1:** **77.78%** (14 of 18 queries returned a true duplicate at rank 1)
  - **Hit@3:** **100.00%** (18 of 18 queries returned a true duplicate in top-3 candidates)
  - **Hit@5:** **100.00%**
  - **MRR (Mean Reciprocal Rank):** **0.8889**
  - **Pairwise ROC-AUC:** **0.9978** ($N=16,471$ total candidate pairs)
  - **Average Query Latency:** **2.15 ms**
- **Pairwise Classification Matrix Results:**
  - **Pre-Fixed Validation Optimal Threshold ($\tau = 0.60$):**
    - **Precision:** **19.18%** (14 / 73 flagged pairs)
    - **Recall:** **93.33%** (14 / 15 true positive duplicate pairs detected)
    - **F1 Score:** **0.3182** (TP=14, FP=59, FN=1, TN=16,397)
  - **Canonical Operational Duplicate Threshold ($\tau_{\text{high}} = 0.80$):**
    - **Precision:** 7.69%, **Recall:** 6.67%, **F1 Score:** 0.0714 (TP=1, FP=12, FN=14)
  - **Canonical Operational Similar Threshold ($\tau_{\text{mid}} = 0.50$):**
    - **Precision:** 15.96%, **Recall:** 100.00%, **F1 Score:** 0.2752 (TP=15, FP=79, FN=0)
  - **Exploratory Post-Hoc Test Observation ($\tau = 0.65$):**
    - F1 = 0.3288, Precision = 20.69%, Recall = 80.00% (TP=12, FP=46, FN=3).
    - *Integrity Note:* Because $\tau = 0.65$ was identified by inspecting test set metrics, it is an exploratory observation and **not** an unbiased pre-fixed estimate.

### 7.5 Unsupervised Clustering Analysis (Validation Exploratory Baseline)
- **Held-Out Test Split Status:** **N/A (Exploratory validation metric only; deliberately not evaluated on test data to prevent exploratory data snooping).**
- **Validation Split ($N=183$, Phase 7):**
  - Spherical K-Means ($k=12$): Cosine Silhouette = 0.0941, Inertia = 144.68, DB-Index = 3.1973.
  - Cosine DBSCAN ($\epsilon=0.58$, $\text{min\_samples}=3$): 21 coherent clusters, 87 noise points isolated (47.5%), Non-noise Silhouette = **0.4274**.
- **Auxiliary Real-World OOD Dataset (`sanchit-19`, $N=332$):** Cosine DBSCAN isolated 42 clusters with a non-noise silhouette of 0.5775.

---

## 8. Ethical Considerations & Safety Controls

1. **Safety Overrides & Real-World Limitations:**
   - The system implements a deterministic regular-expression safety circuit scanning for 55 hazardous keywords (`fire`, `smoke`, `shock`, `ragging`, `collapse`, `assault`, etc.).
   - **Evaluation Finding:** All explicitly constructed safety scenarios in the current rule-based test suite triggered the expected override. **This does not establish universal real-world emergency detection.**
   - *Limitations:* Metaphorical keyword usage (e.g. *"lecture was absolute fire"*) can cause false positives; emerging hazards without matching keywords (e.g. *"unlabeled chemicals sizzling on floor"*) can cause false negatives.
   - *Mandatory Governance:* **Mandatory human review is strictly retained for all safety-flagged tickets.**
2. **Privacy & PII Protection:** The preprocessing pipeline incorporates an automated PII scanner that strips or masks student phone numbers, email addresses, and roll numbers before feature transformation.
3. **Mitigating Automation Bias:** The user interface explicitly presents model outputs as suggestions (with confidence bars, probability distributions, and signal breakdowns). Staff must enter a non-empty textual justification to override priority, creating an accountable audit trail.
4. **Fairness Across Student Demographics:** Because the model does not ingest student identity metadata (gender, nationality, GPA, financial standing), routing decisions are based strictly on textual facility descriptions.

---

## 9. Caveats and Recommendations

1. **Synthetic Training Data vs. Real-World Student Vernacular:**
   - The primary models were trained on procedurally synthesized data. While syntactically diverse, real student text may exhibit regional dialects, Hinglish code-mixing, or severe orthographic errors.
   - *Recommendation:* Deploy in a "shadow" or human-in-the-loop pilot mode for the first academic semester, logging real complaints to retrain and calibrate the vectorizer.
2. **Threshold Monitoring:**
   - The operational confidence threshold ($\theta = 0.60$) was validated on synthetic data. Production deployments should track monthly distribution shifts and empirical human triage agreement rates.
3. **Database Concurrency:**
   - Production deployments must utilize PostgreSQL with dedicated connection pooling. SQLite should remain restricted to local developer testing and CI test runners.

---

*Model Card finalized and approved for Phase 9 submission.*
