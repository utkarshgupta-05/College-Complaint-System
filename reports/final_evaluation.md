# Final Evaluation Report — College Complaint Intelligence System

> **Document ID:** `reports/final_evaluation.md`  
> **Evaluation Date:** November 1, 2026  
> **Evaluation Phase:** Phase 9 (Final Independent Validation)  
> **Evaluator:** Lead AI/ML Engineering System  
> **Evaluation Target:** Held-Out Quarantined Test Split (`data/processed/test.csv`, $N=182$)  
> **Split Quarantine Status:** 100% Leakage-Free Verified (`check_split_leakage()` passed)  
> **Evaluation Protocol:** Single Evaluation Pass — Zero Retraining — Zero Hyperparameter Tuning  

---

## 1. Executive Summary

This report delivers the comprehensive final evaluation of the **AI-Powered College Complaint Intelligence System** on the held-out test dataset ($N=182$ student complaints). The test split was partitioned during Phase 2 using group-aware stratified sampling (`StratifiedGroupKFold`) and remained strictly quarantined and untouched across all intermediate exploration, training, and threshold tuning phases (Phases 3 through 8).

### High-Level Evaluation Findings
1. **Module A — Complaint Classifier (Experiment E2: Calibrated Linear SVM):**
   - **Test Accuracy:** **98.90%** (180 / 182 correct)
   - **Test Macro-F1:** **0.9882** (Generalization gap vs. Validation: $\Delta = -0.0070$, $<1\%$ drop)
   - **Test Weighted-F1:** **0.9889**
   - **Calibration Quality:** Expected Calibration Error (**ECE**) = **0.0825**, Brier Score = **0.0195**, Log Loss = **0.1093**
   - **Operational Automation:** At the recommended operating confidence threshold $\theta = 0.60$, **98.9%** of incoming complaints are automatically routed with **100.00% accuracy**. All misclassified complaints ($N=2$) had confidence $<0.41$ and were successfully diverted to the human review queue (**100.0% Error Recall**, **0.0% False Review Rate**).
   - **Inference Latency:** **0.11 ms** per complaint (batch of 182 processed in 19.8 ms).

2. **Module B — Duplicate and Related Complaint Detection (Experiment E6: TF-IDF Lexical Similarity):**
   - **Top-$k$ Candidate Retrieval on Multi-Report Queries ($N=18$ queries across 7 incident groups):**
     - **Hit@1:** **77.78%** (14 / 18 queries retrieved a true duplicate at rank 1)
     - **Hit@3:** **100.00%** (18 / 18 queries retrieved a true duplicate in top-3)
     - **Hit@5:** **100.00%**
     - **Mean Reciprocal Rank (MRR):** **0.8889**
     - **Recall@3:** **100.00%**
     - **Average Query Latency:** **2.15 ms**
   - **Pairwise Classification Matrix ($N=16,471$ candidate pairs, 15 true positive pairs):**
     - **ROC-AUC:** **0.9978** (near-perfect ranking separation across candidate pairs)
     - **Primary Pre-Fixed Threshold ($\tau = 0.60$, selected on validation split):**
       - **Precision:** **19.18%** (14 / 73 candidate pairs flagged)
       - **Recall:** **93.33%** (14 / 15 true positive duplicate pairs detected)
       - **F1 Score:** **0.3182** (TP=14, FP=59, FN=1, TN=16,397)
     - **Canonical Operational Thresholds:**
       - **Probable Duplicate ($\tau_{\text{high}} = 0.80$):** Precision = 7.69%, Recall = 6.67%, F1 = 0.0714 (TP=1, FP=12, FN=14)
       - **Similar / Related ($\tau_{\text{mid}} = 0.50$):** Precision = 15.96%, Recall = 100.00%, F1 = 0.2752 (TP=15, FP=79, FN=0)
     - **Post-Hoc Test-Set Sweep (Disclosed as Exploratory):** $\tau = 0.65$ maximized F1 on the test set post-hoc (F1 = 0.3288, Precision = 20.69%, Recall = 80.00%). This is reported purely as an exploratory comparison and is not an unbiased pre-fixed estimate.
     - *Key Finding:* In dense, highly imbalanced pairwise matrices ($0.091\%$ positive prevalence), exhaustive pairwise thresholding is impacted by false positives across large negative pools. In contrast, Top-$k$ similarity retrieval achieves an outstanding **100% Hit@3 and 0.89 MRR**, perfectly validating the UI design choice of advisory candidate cards rather than automated closures.

3. **Module C — Priority Assessment Rules Engine:**
   - Evaluated across 8 canonical test scenarios representing acute physical safety, ragging/harassment, structural collapse, building-wide utility outages, minor individual cosmetic defects, waiting time escalation, recurrence escalation, and authorized staff overrides.
   - **Safety Override Evaluation Finding:** All explicitly constructed safety scenarios in the current rule-based test suite triggered the expected override. This does not establish universal real-world emergency detection.
   - Deterministic keyword matching is bounded by lexicon coverage (55 keywords) and cannot detect unlisted novel phrasing or metaphorical usage. Mandatory human review is strictly retained for all safety-flagged tickets.
   - Base numerical scoring rigorously scales from 5.0 to 100.0 with dynamic escalation for unresolved aging tickets ($>72$ hours, $+10.0$ points) and recurring incident clusters ($5$ reports, $+10.0$ points).
   - Authorized staff override workflow verified with immutable audit trail.

4. **Module D — Recurring Issue Discovery & Hotspot Analysis:**
   - **Validation-Set Exploratory Benchmark ($N=183$, Phase 7):** Unsupervised TF-IDF Spherical K-Means ($k=12$, Silhouette = $0.0941$) and Cosine DBSCAN ($\epsilon=0.58$, $\text{min\_samples}=3$, Non-Noise Silhouette = $0.4274$, 21 clusters, 87 noise points).
   - **Test Set Evaluation Status:** **N/A (Exploratory validation metric only; deliberately not evaluated on held-out test data to avoid exploratory snooping).**
   - **Auxiliary Real-World OOD Evaluation:** Evaluated on `sanchit-19/university-students-complaints` ($N=332$, CC-BY-4.0) strictly isolated from training, confirming semantic clustering around dining facilities, lab terminals, and transit scheduling.

---

## 2. Test Split Integrity & Leakage Verification

### 2.1 Dataset Partitioning Summary
The complete synthetic dataset contains 1,273 records partitioned into train, validation, and test splits:

| Split | File Path | Record Count | Percentage | Multi-Report Incident Groups | Multi-Report Complaints |
|---|---|---|---|---|---|
| **Train** | `data/processed/train.csv` | 908 | 71.3% | 35 | 92 |
| **Validation** | `data/processed/val.csv` | 183 | 14.4% | 8 | 19 |
| **Held-Out Test** | `data/processed/test.csv` | 182 | 14.3% | 7 | 18 |
| **Total** | — | **1,273** | **100.0%** | **50** | **129** |

### 2.2 Leakage Audit Results
A strict audit executed via `src.data.preprocess.check_split_leakage` confirmed:
- **Index Disjointness:** **0** overlapping complaint IDs across all three splits.
- **Exact Text Leakage:** **0** matching text complaints across splits.
- **Incident Group Leakage:** **0** overlapping `incident_group_id` values between train, validation, and test. All multi-student reports for any incident cluster remain strictly quarantined in a single split.

---

## 3. Module A — Final Classification Evaluation (E2 Calibrated Linear SVM)

### 3.1 Model Architecture & Configuration
- **Model Pipeline:** `sklearn.pipeline.Pipeline`
  1. `TfidfVectorizer(ngram_range=(1, 2), max_features=10000, sublinear_tf=True, min_df=2, max_df=0.95)`
  2. `CalibratedClassifierCV(estimator=LinearSVC(C=1.0, class_weight='balanced', max_iter=2000, random_state=42), method='sigmoid', cv=5)`
- **Artifact:** `models/e2.joblib` (frozen since Phase 3, untouched)

### 3.2 Held-Out Test Set Performance vs. Validation Set

| Metric | Validation Split ($N=183$) | Held-Out Test Split ($N=182$) | Generalization Gap ($\Delta = \text{Test} - \text{Val}$) | Target Specification |
|---|---|---|---|---|
| **Accuracy** | 0.9945 (99.45%) | **0.9890 (98.90%)** | $-0.0055$ ($-0.55\%$) | $\ge 0.85$ |
| **Macro-F1** | 0.9952 | **0.9882** | $-0.0070$ ($-0.70\%$) | $\ge 0.80$ |
| **Weighted-F1** | 0.9945 | **0.9889** | $-0.0056$ ($-0.56\%$) | $\ge 0.80$ |
| **Expected Calibration Error (ECE)** | 0.0823 | **0.0825** | $+0.0002$ | $\le 0.15$ |
| **Multiclass Brier Score** | 0.0168 | **0.0195** | $+0.0027$ | Low |
| **Multiclass Log Loss** | 0.1005 | **0.1093** | $+0.0088$ | Low |
| **Single-Sample Inference Latency** | 0.11 ms | **0.11 ms** | $0.00\text{ ms}$ | $\le 50\text{ ms}$ |

*Interpretation:* The generalization gap is extraordinarily small ($\Delta \text{ Macro-F1} = -0.0070$). The model exhibits zero signs of overfitting or data leakage. Calibration quality on the test set is virtually identical to validation ($\text{ECE} = 0.0825$ vs $0.0823$).

### 3.3 Detailed Per-Class Performance Breakdown

| Class Code | Category Name | Precision | Recall | F1-Score | Support (Test) | Misclassifications |
|---|---|---|---|---|---|---|
| **C01** | Hostel and Accommodation | 1.0000 | 1.0000 | 1.0000 | 19 | 0 |
| **C02** | Electricity and Water | 1.0000 | 1.0000 | 1.0000 | 19 | 0 |
| **C03** | Internet and Network | 1.0000 | 1.0000 | 1.0000 | 16 | 0 |
| **C04** | Mess and Food | 1.0000 | 1.0000 | 1.0000 | 18 | 0 |
| **C05** | Academic and Examination | 1.0000 | 1.0000 | 1.0000 | 18 | 0 |
| **C06** | Classroom and Laboratory | 1.0000 | 0.8667 | 0.9286 | 15 | 2 (predicted as C07) |
| **C07** | Sanitation and Cleanliness | 0.8889 | 1.0000 | 0.9412 | 16 | 0 |
| **C08** | Campus Safety | 1.0000 | 1.0000 | 1.0000 | 16 | 0 |
| **C09** | Transportation | 1.0000 | 1.0000 | 1.0000 | 15 | 0 |
| **C10** | Administrative Services | 1.0000 | 1.0000 | 1.0000 | 15 | 0 |
| **C11** | Other / Unclassified | 1.0000 | 1.0000 | 1.0000 | 15 | 0 |
| **Total / Avg** | **Macro Average** | **0.9899** | **0.9879** | **0.9882** | **182** | **2** |
| **Total / Avg** | **Weighted Average** | **0.9902** | **0.9890** | **0.9889** | **182** | **2** |

*Generated Plot:* `reports/figures/final_test_confusion_matrix.png`

### 3.4 In-Depth Error Analysis
Out of 182 held-out complaints, exactly **2** misclassifications occurred. Both cases are detailed below:

| Complaint ID | True Category | Predicted Category | Confidence | Complaint Text Summary | Root Cause Analysis |
|---|---|---|---|---|---|
| `SYN-00196` | **C06** (Classroom & Lab) | **C07** (Sanitation & Cleanliness) | **0.4052** | *"Digital oscilloscope and function generators in Sports Complex - Indoor Badminton Court are faulty and displaying distorted signals. When approached, staff told us that spare parts have not been sanctioned yet."* | Lab equipment placed in a non-standard location ("Sports Complex - Indoor Badminton Court") caused feature attenuation. Vocabulary ambiguity reduced confidence. |
| `SYN-00326` | **C06** (Classroom & Lab) | **C07** (Sanitation & Cleanliness) | **0.2075** | *"Digital oscilloscope and function generators in Hostel Block A - Floor 3 are faulty and displaying distorted signals. Mid-semester exams are ongoing and this disturbance is making it very difficult to concentrate. Please fix this on priority."* | Lab equipment placed in a hostel location ("Hostel Block A - Floor 3") with noise keywords ("disturbance", "concentrate") created cross-category interference. |

### 3.5 Confidence Thresholding & Human-in-the-Loop Safeguards
To verify whether confidence scores effectively prevent bad auto-routing in production, we evaluated the operational trade-off across decision thresholds $\theta$:

| Threshold ($\theta$) | Auto-Routed Rate | Auto-Routing Accuracy | Human Review Rate | Error Recall (% Caught) | False Review Rate |
|---|---|---|---|---|---|
| $0.40$ | 99.5% | 99.45% | 0.5% | 50.0% | 0.00% |
| **$0.50$** | **98.9%** | **100.00%** | **1.1%** | **100.0%** | **0.00%** |
| **$0.55$** | **98.9%** | **100.00%** | **1.1%** | **100.0%** | **0.00%** |
| **$0.60$ (Approved)**| **98.9%** | **100.00%** | **1.1%** | **100.0%** | **0.00%** |
| $0.65$ | 98.4% | 100.00% | 1.6% | 100.0% | 0.56% |
| $0.70$ | 98.4% | 100.00% | 1.6% | 100.0% | 0.56% |
| $0.75$ | 97.3% | 100.00% | 2.7% | 100.0% | 1.67% |
| $0.80$ | 96.2% | 100.00% | 3.8% | 100.0% | 2.78% |
| $0.90$ | 92.9% | 100.00% | 7.1% | 100.0% | 6.11% |

*Critical Finding:* At the system's operational threshold $\theta = 0.60$:
1. Both misclassified complaints had confidence scores of **$0.4052$** and **$0.2075$** (well below $0.60$).
2. Both errors are flagged as `needs_human_review=True` and routed to the staff triage queue.
3. **Zero incorrect complaints are auto-routed.** Auto-routed accuracy is **100.00%**.
4. Only $1.1\%$ of total volume is sent to review, achieving **$0.00\%$ false review rate** (no correctly classified tickets are needlessly held up).

*Generated Plots:*
- `reports/figures/final_test_confidence_dist.png`
- `reports/figures/final_test_threshold_tradeoff.png`

---

## 4. Module B — Final Duplicate Detection Evaluation (E6 TF-IDF Retriever)

### 4.1 Multi-Report Incidents and Query Formulation in Held-Out Test Set
In `data/processed/test.csv` ($N=182$), exactly 18 complaints correspond to 7 real underlying multi-report incident groups:
- 4 groups of size 3: `INC-C04-017` (3 reports), `INC-C07-029` (3 reports), `INC-C04-016` (3 reports), `INC-C02-010` (3 reports) $\implies 4 \times 3 = 12$ complaints.
- 3 groups of size 2: `INC-C09-037` (2 reports), `INC-C08-034` (2 reports), `INC-C02-007` (2 reports) $\implies 3 \times 2 = 6$ complaints.
- **Total Multi-Report Complaints:** $12 + 6 = 18$ complaints.

**Relation Between Incident Groups, Queries, and Positive Pairs:**
1. **Retrieval Queries ($N=18$):** Each of the 18 complaints with a known `incident_group_id` serves as an independent query evaluated against the candidate pool of all other 181 complaints in `test.csv` (excluding the query itself). The denominator for Hit@$k$, Recall@$k$, Precision@$k$, and MRR is strictly **18 queries**.
2. **True Positive Duplicate Pairs ($N=15$):**
   - For each 3-complaint group: $\binom{3}{2} = 3$ positive pairs $\implies 4 \times 3 = 12$ pairs.
   - For each 2-complaint group: $\binom{2}{2} = 1$ positive pair $\implies 3 \times 1 = 3$ pairs.
   - Total true duplicate pairs across the entire pairwise matrix: $12 + 3 = \mathbf{15}$ positive pairs.
   - Total candidate pairs in test split: $182 \times 181 / 2 = \mathbf{16,471}$ pairs (prevalence rate = $15 / 16,471 \approx 0.091\%$).

### 4.2 Top-$k$ Candidate Retrieval Performance ($N=18$ Queries)
For each of the 18 multi-report complaints, the remaining 181 complaints in `test.csv` served as the candidate pool (the query itself is strictly excluded from candidates).

| Retrieval Metric | Validation Set ($N=19$ queries) | Held-Out Test Set ($N=18$ queries) | Interpretation |
|---|---|---|---|
| **Hit@1** | 0.6842 (68.4%) | **0.7778 (77.8%)** | In 14 of 18 queries, the top retrieved candidate was a true matching duplicate. |
| **Hit@3** | 1.0000 (100.0%) | **1.0000 (100.0%)** | In 18 of 18 queries, a true duplicate appeared in the top-3 candidates. |
| **Hit@5** | 1.0000 (100.0%) | **1.0000 (100.0%)** | In 18 of 18 queries, a true duplicate appeared in the top-5 candidates. |
| **MRR (Mean Reciprocal Rank)**| 0.8333 | **0.8889** | 14 queries ranked duplicate at #1 (RR=1.0), 4 ranked duplicate at #2 (RR=0.5). $(14\times 1.0 + 4\times 0.5)/18 = 0.8889$. |
| **Recall@1** | 0.4737 | **0.4444** | Partial coverage at $k=1$ because 3-report groups have 2 true duplicate matches. |
| **Recall@3** | 0.9737 | **1.0000** | All multi-report duplicates retrieved within top-3 window. |
| **Precision@1** | 0.6842 | **0.7778** | Top candidate is relevant in 77.8% of queries. |
| **Precision@3** | 0.4737 | **0.5556** | High precision in top-3 window. |
| **Average Query Latency** | 3.14 ms | **2.15 ms** | Real-time performance for keystroke search. |

### 4.3 Pairwise Matrix Classification Analysis ($N=16,471$ Pairs)
Evaluating all $182 \times 181 / 2 = 16,471$ candidate pairs:
- **Pairwise ROC-AUC:** **0.9978** (near-flawless ranking separation across negative vs. positive pairs)
- **Primary Pre-Fixed Validation Threshold ($\tau = 0.60$):**
  - **Selection History:** Established during Phase 5 on validation data (`reports/duplicate_thresholds_e6.csv`). Fixed before test evaluation.
  - **Precision:** **19.18%** (14 / 73 candidate pairs flagged)
  - **Recall:** **93.33%** (14 / 15 true duplicates caught; only 1 missed)
  - **F1 Score:** **0.3182**
  - **True Positives:** 14
  - **False Positives:** 59
  - **False Negatives:** 1
  - **True Negatives:** 16,397
- **Canonical Operational Duplicate Threshold ($\tau_{\text{high}} = 0.80$):**
  - **Precision:** 7.69% (1 / 13 flagged pairs)
  - **Recall:** 6.67% (1 / 15 true duplicates caught)
  - **F1 Score:** 0.0714
  - **True Positives:** 1, **False Positives:** 12, **False Negatives:** 14, **True Negatives:** 16,444
- **Canonical Operational Similar Threshold ($\tau_{\text{mid}} = 0.50$):**
  - **Precision:** 15.96% (15 / 94 flagged pairs)
  - **Recall:** 100.00% (15 / 15 true duplicates caught)
  - **F1 Score:** 0.2752
  - **True Positives:** 15, **False Positives:** 79, **False Negatives:** 0, **True Negatives:** 16,377
- **Exploratory Post-Hoc Test Observation ($\tau = 0.65$):**
  - Sweeping thresholds on the test set post-hoc showed that $\tau = 0.65$ yielded the highest test F1 (Precision = 20.69%, Recall = 80.00%, F1 = 0.3288, TP=12, FP=46, FN=3, TN=16,410).
  - *Integrity Note:* Because $\tau = 0.65$ was identified by inspecting test set metrics, it is strictly an exploratory descriptive result and **must not be treated as an unbiased pre-fixed estimate**. The authoritative pre-fixed estimate is $\tau = 0.60$ (F1 = 0.3182).

*Architectural Takeaway:* Because of severe pair imbalance ($15$ positives vs. $16,456$ negatives, a 1:1,097 ratio), global pairwise thresholding is sub-optimal for operational triage. Conversely, **Top-$k$ candidate retrieval** ($k=3$, Hit@3 = 100%, MRR = 0.8889) paired with **advisory candidate suggestions** in the UI allows staff to confirm or dismiss suspected duplicates with high recall and zero danger of accidental auto-merges.

*Generated Plot:* `reports/figures/final_test_duplicate_thresholds.png`

---

## 5. Module C — Final Priority Assessment Validation

### 5.1 Rules Engine Canonical Formula
The priority engine calculates an objective base urgency score $P_{\text{base}} \in [0, 100]$:
$$P_{\text{base}} = 0.35 \times \text{severity} + 0.25 \times \text{safety\_risk} + 0.20 \times \text{affected\_population} + 0.10 \times \text{waiting\_time} + 0.10 \times \text{recurrence}$$

Where:
- **Severity ($0-100$):** Weighted count of critical operational keywords (`flooded`, `outage`, `broken`, `unbearable`, etc.).
- **Safety Risk ($0-100$):** Acute hazard terms (`fire`, `smoke`, `shock`, `ragging`, `collapse`, etc.).
- **Affected Population ($0-100$):** Scope estimation (Individual $=25$, Room $=50$, Floor/Hostel $=75$, Campus-wide $=100$). Missing or unspecified scope defaults safely to $25.0$ (never $0.0$).
- **Waiting Time ($0-100$):** Linear aging bonus $\min(100, (\text{elapsed\_hours} / 72.0) \times 100)$.
- **Recurrence ($0-100$):** Cluster size scaling $\min(100, (\text{recurrence\_count} / 5.0) \times 100)$.

### 5.2 Hard Safety Override Policy & Real-World Limitations
Any complaint containing verified acute hazard terminology (scanned across 55 regex keywords) or an explicit verified hazard flag triggers an **immediate policy override to `CRITICAL`** with mandatory human review (`needs_human_review = True`), regardless of mathematical $P_{\text{base}}$.

> [!WARNING]
> **Safety Detection Boundary:**
> All explicitly constructed safety scenarios in the current rule-based test suite triggered the expected override. **This does not establish universal real-world emergency detection.**
> 
> *Known Limitations:*
> 1. **False Negatives:** Emergent or severe hazards described without matching the exact 55 keywords (e.g. *"The liquid leaking from the container has an acrid smell and is sizzling through the linoleum floor"* or *"Sparks are jumping from an exposed high-voltage terminal box"*) will evade the regex safety circuit and receive only standard linguistic severity scoring.
> 2. **False Positives:** Non-emergency metaphorical expressions (e.g. *"I am drowning under mid-semester assignments"* or *"Professor's lecture was absolute fire"*) will trigger the override.
> 
> *Mandatory Human Safeguard:* Because keyword rules cannot replace human judgment, **mandatory human review is strictly retained for all safety-flagged tickets**.

### 5.3 Empirical Test Case Validation Matrix

| Test ID | Scenario Description | Base Score | Suggested Band | Final Band | Safety Override | Mandatory Review | Triggered Keywords | Staff Override Action |
|---|---|---|---|---|---|---|---|---|
| **TC-01** | Acute physical safety hazard (Fire/Smoke) | 30.00 | **CRITICAL** | **CRITICAL** | **True** | **True** | `evacuation`, `fire`, `smoke` | None |
| **TC-02** | Harassment / Ragging emergency | 36.67 | **CRITICAL** | **CRITICAL** | **True** | **True** | `ragging` | None |
| **TC-03** | Structural collapse hazard | 30.00 | **CRITICAL** | **CRITICAL** | **True** | **True** | `fell off`, `unsafe` | None |
| **TC-04** | Widespread utility failure (Building water outage) | 56.67 | **MEDIUM** | **MEDIUM** | False | False | None | None |
| **TC-05** | Minor individual cosmetic issue (Room fan clicking) | 16.67 | **LOW** | **LOW** | False | False | None | None |
| **TC-06** | Recurrence escalation (5 prior duplicate reports) | 15.00 | **LOW** | **LOW** | False | False | None (Score $+10.0$ pts) | None |
| **TC-07** | Aging complaint escalation ($>72$ hours pending) | 15.00 | **LOW** | **LOW** | False | False | None (Score $+10.0$ pts) | None |
| **TC-08** | Authorized staff priority adjustment | 5.00 | **LOW** | **HIGH** | False | False | None | Overridden to `HIGH` (Logged) |

*Analysis of Under-Prioritization Risk:* 
Without hard safety overrides, a short complaint like *"Fire in meter room"* scores $P_{\text{base}} \approx 30.0$ because it lacks lengthy descriptive adjectives or explicit affected population estimates. The hard safety override ensures that known acute hazard keywords immediately escalate tickets to `CRITICAL`.

---

## 6. Module D — Recurring-Issue Discovery & Pattern Analysis

### 6.1 Unsupervised Clustering Benchmark (Validation Corpus Exploratory Baseline)
*Note on Evaluation Scope:* Unsupervised clustering is an exploratory pattern discovery tool rather than a supervised predictive model with fixed test labels. To prevent exploratory data snooping, clustering was evaluated during Phase 7 on the **validation split ($N=183$)** and was **deliberately not evaluated on the held-out test split**:
- **Held-Out Test Split Clustering Status:** **N/A (Exploratory validation metric only; not evaluated on test set to prevent exploratory data snooping).**
- **Validation Split ($N=183$) Baselines (Phase 7, Experiments E8 & E10):**
  - **Spherical K-Means ($k=12$):**
    - Inertia (SSE): $144.68$
    - Cosine Silhouette Score: $0.0941$
    - Davies-Bouldin Index: $3.1973$
  - **Cosine DBSCAN ($\epsilon=0.58$, $\text{min\_samples}=3$):**
    - Dense Outbreak Clusters: $21$ distinct localized incident clusters
    - Noise Points Isolated: $87$ isolated complaints ($47.5\%$)
    - Non-Noise Silhouette Score: **$0.4274$** (substantially tighter semantic coherence than K-Means)

### 6.2 Auxiliary Real-World Evaluation (`sanchit-19/university-students-complaints`)
To evaluate zero-shot transfer without contaminating training splits, we benchmarked the pipeline on 332 external complaints (Hugging Face dataset by Md. Al Amin, CC-BY-4.0):
- **Provenance & Scope:** 332 complaints across 6 university departments (73.8% CSE department skew, single Bangladeshi campus) with 5 coarse administrative buckets (`Infrastructure`, `Technical`, `Academic`, `Finance`, `Administrative`).
- **Isolation:** Strictly quarantined from model training and synthetic splits (Decision D-014).
- **Out-of-Domain Findings:**
  - Lexical TF-IDF successfully matched multi-student complaint groups in real university text with $0.62$ Hit@1 and $0.85$ Hit@3.
  - Cosine DBSCAN ($\epsilon=0.55$, $\text{min\_samples}=3$) extracted 42 natural incident themes (cafeteria hygiene, lab terminal scarcity, elevator queues, library noise) with a non-noise silhouette of **0.5775** (36 noise points isolated, 13.2%).
  - Confirmed that TF-IDF lexical matching and density-based clustering transfer to unconstrained student phrasing.

---

## 7. Real-World Deployment Limitations & Recommendations

1. **Synthetic Vocabulary vs. Real-World Student Text:**
   - Synthetic text has well-formed sentences and explicit keywords. Real student complaints frequently contain typos (`"geyser nt wrking"`), Hinglish (`"paani nahi aa raha hai"`), and emotional shorthand.
   - *Mitigation:* The frontend incorporates real-time preview triage to guide students toward clear descriptions, and the system retains a low-confidence routing fallback to human review.
2. **Multi-Department Cross-Cutting Complaints:**
   - Some complaints span multiple operational areas (e.g., *"Leaking AC ceiling in computer lab damaged exam terminals"* touches C02, C06, and C07).
   - *Mitigation:* The API exposes the full multi-class probability distribution to staff so secondary department assignments can be made immediately.
3. **Absence of Institutional Resolution Data:**
   - Synthetic data lacks empirical repair durations, technician notes, and post-resolution satisfaction scores.
   - *Mitigation:* The platform records lifecycle timestamps (`submitted` $\to$ `in_progress` $\to$ `resolved`) to accumulate genuine institutional SLA datasets for future supervised priority modeling.
4. **Mandatory Human-in-the-Loop Governance:**
   - Under no circumstances should duplicate detection automatically merge or purge complaints. Duplicate cards must remain advisory alerts for staff validation.

---

## 8. Final Verification Sign-Off

- [x] All 182 held-out test records evaluated exactly once with zero leakage.
- [x] Primary classifier achieved **98.90% Accuracy** and **0.9882 Macro-F1** on test split.
- [x] Zero misclassified tickets auto-routed at $\theta=0.60$ threshold (100% Error Recall).
- [x] Duplicate retriever achieved **100.0% Hit@3** and **0.8889 MRR** on multi-report test queries.
- [x] Priority engine verified across safety overrides, aging, and staff audit hooks.
- [x] Python test suite: **128 / 128 passed**.
- [x] Frontend test suite: **27 / 27 passed**.
- [x] Production build: **Successful (0 errors)**.

*Phase 9 Final Evaluation is verified complete and signed off.*

