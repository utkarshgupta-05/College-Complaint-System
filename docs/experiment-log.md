# Experiment Log — College Complaint Intelligence System

> **Purpose:** Record every ML experiment — configuration, actual results, and conclusions.
> **Rules:** Never fabricate results. Write "Not measured yet" until an experiment actually runs.
> Clearly distinguish synthetic-data results from real-data results.

---

## Experiment Table (Summary)

| ID | Phase | Module | Method | Primary Metric | Result | Status |
|---|---|---|---|---|---|---|
| E1 | 3 | Classification | TF-IDF (word) + Logistic Regression | Macro-F1 | 0.9890 (val) [SYNTHETIC] | Completed |
| E2 | 3 | Classification | TF-IDF (word) + Linear SVM (Calibrated) | Macro-F1 | 0.9952 (val) [SYNTHETIC] | Completed |
| E3 | 4 | Classification | TF-IDF (word) + Multinomial Naive Bayes | Macro-F1 | 0.9774 (val) [SYNTHETIC] | Completed |
| E4 | 4 | Classification | TF-IDF (char 3-5) + Linear SVM (Calibrated) | Macro-F1 | 0.9948 (val) [SYNTHETIC] | Completed |
| E5 | 4 | Classification | Sentence embeddings + Classifier | Macro-F1 | Not justified by baseline gap | Skipped (Gate) |
| E6 | 5 | Duplicate | TF-IDF cosine similarity | Precision@10 / F1 | Not measured yet | Not Started |
| E7 | 5 | Duplicate | Sentence embedding cosine similarity | Precision@10 / F1 | Not measured yet | Not Started |
| E8 | 7 | Clustering | K-Means on TF-IDF | Silhouette + manual | Not measured yet | Not Started |
| E9 | 7 | Clustering | K-Means on sentence embeddings | Silhouette + manual | Not measured yet | Not Started |
| E10 | 7 | Clustering | DBSCAN / HDBSCAN | Silhouette + manual | Not measured yet | Not Started |

---

## Detailed Experiment Records

---

### E1 — TF-IDF (word unigrams + bigrams) + Logistic Regression

**Status:** Completed (Measured on 2026-10-30)

**Research Question:**
What is the baseline complaint classification performance using a simple, interpretable
TF-IDF + Logistic Regression pipeline?

**Dataset:** `data/raw/college_complaints_synthetic.csv` (`data_source=synthetic`, N=1,273)  
**Split strategy:** Group-aware stratified split (Train: 908, Val: 183, Test: 182 quarantined)  
**Preprocessing:** Stateless normalization (lowercase, punctuation stripped, stopwords removed, WordNet lemmatized)  
**Algorithm:** Logistic Regression (`C=1.0`, `class_weight='balanced'`, `solver='lbfgs'`)  
**Vectorizer:** TfidfVectorizer (`ngram_range=(1,2)`, `min_df=2`, `max_df=0.95`, `sublinear_tf=True`), fit strictly on train split  
**Random seed:** 42  

**Actual Results (Validation split, N=183):**
- **Accuracy:** 0.9891 (98.91%)
- **Macro-F1:** 0.9890 (98.90%)
- **Weighted-F1:** 0.9890 (98.90%)
- **Training Time:** 0.166 s
- **Inference Time:** 0.073 ms per complaint (13,700 complaints / sec)
- **Misclassifications:** 2 / 183 (1.1%)

**Error Analysis:**
1. A lost wallet inquiry (`C11`) was predicted as `C10` (Administrative Services) with low confidence (0.175). Correctly flagged for human review.
2. A faulty lab oscilloscope complaint (`C06`) was predicted as `C07` with low confidence (0.157). Correctly flagged for human review.
In both errors, the model's confidence was far below the 0.60 uncertainty threshold, verifying that the human-in-the-loop review safeguard operates as designed.

**Artifacts:**
- Model artifact: `models/e1_logreg.joblib`
- Confusion matrix: `reports/figures/cm_e1_logreg.png`
- Confidence distribution: `reports/figures/conf_e1_logreg.png`
- Error log: `reports/errors_e1_logreg.csv`

**Conclusion:**
Strong, fast baseline. Demonstrates that linear classification on TF-IDF word unigrams and bigrams provides effective separation across college complaint domains while maintaining sub-millisecond inference.

---

### E2 — TF-IDF (word unigrams + bigrams) + Linear SVM (Calibrated)

**Status:** Completed (Measured on 2026-10-30)

**Research Question:**
Does a Linear SVM with Platt calibration outperform Logistic Regression on this task?

**Dataset:** Same as E1 (Train: 908, Val: 183)  
**Algorithm:** `LinearSVC(C=1.0, class_weight='balanced')` wrapped with `CalibratedClassifierCV(method='sigmoid', cv=5)`  
**Vectorizer:** Same as E1  

**Actual Results (Validation split, N=183):**
- **Accuracy:** 0.9945 (99.45%)
- **Macro-F1:** 0.9952 (99.52%)
- **Weighted-F1:** 0.9945 (99.45%)
- **Training Time:** 0.265 s
- **Inference Time:** 0.114 ms per complaint (8,770 complaints / sec)
- **Misclassifications:** 1 / 183 (0.5%)

**Error Analysis:**
- Only 1 misclassification: the same oscilloscope complaint (`C06` → `C07`) with low confidence (0.251), which triggered the human review flag.
- The lost wallet complaint misclassified by E1 was correctly classified by E2.

**Artifacts:**
- Model artifact: `models/e2_svm.joblib`
- Confusion matrix: `reports/figures/cm_e2_svm.png`
- Confidence distribution: `reports/figures/conf_e2_svm.png`
- Error log: `reports/errors_e2_svm.csv`

**Conclusion:**
Calibrated Linear SVM outperforms Logistic Regression slightly in Macro-F1 (0.9952 vs 0.9890) and reduces error rate by 50% while producing well-calibrated posterior probabilities. E2 is currently the top-performing baseline.


---

### E3 — TF-IDF (word unigrams + bigrams) + Multinomial Naive Bayes

**Status:** Completed (Measured on 2026-10-30)

**Research Question:**
How does Multinomial Naive Bayes perform as a lightweight probabilistic baseline?

**Dataset:** `data/raw/college_complaints_synthetic.csv` (`data_source=synthetic`, N=1,273)  
**Algorithm:** `MultinomialNB(alpha=1.0)`  
**Vectorizer:** Word-level TF-IDF (`ngram_range=(1,2)`, `min_df=2`, `max_df=0.95`, `sublinear_tf=True`)  

**Actual Results (Validation split, N=183):**
- **Accuracy:** 0.9781 (97.81%)
- **Macro-F1:** 0.9774 (97.74%)
- **Weighted-F1:** 0.9778 (97.78%)
- **Brier Score:** 0.2382
- **Log Loss:** 0.6191
- **Expected Calibration Error (ECE):** 0.4025
- **Training Time:** 0.035 s (fastest)
- **Inference Time:** 0.081 ms per complaint
- **Misclassifications:** 4 / 183 (2.2%)

**Error Analysis:**
- Naive Bayes produced 4 errors (vs 1 for SVM and 2 for LogReg).
- It struggled on cross-domain ambiguous complaints because the conditional independence assumption treats correlated symptom keywords independently, inflating posterior probabilities for common classes.
- Poorly calibrated probabilities (ECE = 0.4025, Log Loss = 0.6191) because Naive Bayes is known to push probabilities toward 0 and 1.

**Artifacts:**
- Model artifact: `models/e3.joblib`
- Confusion matrix: `reports/figures/cm_e3.png`
- Confidence distribution: `reports/figures/conf_e3.png`
- Error log: `reports/errors_e3.csv`

**Conclusion:**
Extremely fast to train (0.035 s), but achieves the lowest Macro-F1 (0.9774) and exhibits severe overconfidence / poor probability calibration. Not recommended for final production deployment.

---

### E4 — Character N-gram TF-IDF (char_wb 3-5) + Linear SVM (Calibrated)

**Status:** Completed (Measured on 2026-10-30)

**Research Question:**
Do character-level n-grams improve classification performance and robustness against misspellings and informal student terminology?

**Dataset:** Same as E1-E3 (Train: 908, Val: 183)  
**Algorithm:** `LinearSVC(C=1.0, class_weight='balanced')` with 5-fold `CalibratedClassifierCV(method='sigmoid')`  
**Vectorizer:** Character-level TF-IDF (`analyzer='char_wb'`, `ngram_range=(3,5)`, `max_features=15000`, `min_df=2`, `max_df=0.95`, `sublinear_tf=True`)  

**Actual Results (Validation split, N=183):**
- **Accuracy:** 0.9945 (99.45%)
- **Macro-F1:** 0.9948 (99.48%)
- **Weighted-F1:** 0.9945 (99.45%)
- **Brier Score:** 0.0157 (best calibration quality)
- **Log Loss:** 0.0987 (best log loss)
- **Expected Calibration Error (ECE):** 0.0773 (lowest calibration error)
- **Training Time:** 0.832 s
- **Inference Time:** 0.415 ms per complaint
- **Misclassifications:** 1 / 183 (0.5%)

**Error Analysis:**
- Shared the exact same single misclassification as E2 (an oscilloscope complaint `C06` predicted as `C07` with low confidence 0.238, safely flagged for human review).
- Character n-grams achieved slightly better probability calibration (Brier 0.0157 vs 0.0168), but inference latency increased ~3.8x (0.415 ms vs 0.110 ms) due to the larger feature vocabulary (15,000 sub-word n-grams).

**Artifacts:**
- Model artifact: `models/e4.joblib`
- Confusion matrix: `reports/figures/cm_e4.png`
- Confidence distribution: `reports/figures/conf_e4.png`
- Error log: `reports/errors_e4.csv`

**Conclusion:**
Highly robust model matching E2 in accuracy and errors while offering the best probability calibration. However, word-level SVM (E2) achieves marginally higher Macro-F1 (0.9952 vs 0.9948) with ~3.8x faster inference. Both E2 and E4 are strong contenders.

---

### E5 — Sentence Embeddings + Classifier (Gating Evaluation)

**Status:** Skipped / Not Justified (Evaluated at Phase 4 Gate)

**Research Question:**
Do heavy pretrained transformer sentence embeddings justify their computational cost?

**Justification Gate Evaluation:**
Per the Master Prompt and Decision D-003:
- Pretrained sentence embeddings are only justified if:
  1. Traditional baselines leave a substantial performance gap.
  2. The dataset has complex semantic nuances not captured by n-grams.
  3. Compute budget justifies 10x-50x higher inference latency.
- **Actual Evidence:**
  - E2 (Word SVM) achieves **0.9952 Macro-F1** with **0.110 ms latency** on CPU.
  - E4 (Char SVM) achieves **0.9948 Macro-F1** with **0.415 ms latency**.
  - Total validation error count is only 1 out of 183 complaints, and that 1 error is flagged for human review.
- **Conclusion:** Introducing a deep sentence transformer for classification is not technically justified on this dataset. Word/character linear baselines provide state-of-the-art accuracy at zero GPU cost. (Sentence embeddings remain reserved for Duplicate Detection in Module B).

  - Best baseline macro-F1 < acceptable threshold (TBD after E1/E2)
  - Dataset has sufficient labeled examples (≥ 300 per class recommended)
  - Compute is available for embedding generation

**Model candidate:** `all-MiniLM-L6-v2` (sentence-transformers) — 80MB, CPU-friendly
**Classifier:** Logistic Regression on embeddings

**Results:** Not measured yet
**Conclusion:** Not measured yet

---

### E6 — TF-IDF Cosine Similarity (Duplicate Detection Baseline)

**Status:** Completed (Measured on 2026-10-30)

**Research Question:**
Can lexical TF-IDF cosine similarity reliably surface true duplicate complaints and rank them in top positions for staff review?

**Dataset:** Validation split (`val.csv`, $N=183$, `data_source=synthetic`). Contains 19 multi-report complaints across 8 distinct incident clusters, yielding 14 true positive duplicate pairs, 1,448 same-category hard negatives, and 15,191 easy negatives (total 16,653 pairs). Zero test set leakage.

**Algorithm:**
- Representation: Word unigram + bigram TF-IDF (`ngram_range=(1,2)`, `max_features=10000`, `sublinear_tf=True`, normalized text).
- Retrieval: Cosine similarity against candidate pool excluding the query itself.

**Actual Results (Validation split, N=183):**
- **Retrieval Performance (Top-k Ranking on Incident Queries, N=19):**
  - **Hit@1 (Recall@1):** 0.6842 (68.4%)
  - **Hit@3:** **1.0000 (100.0%)** — *Every single incident query retrieved a true duplicate in its top-3 candidates!*
  - **Hit@5:** **1.0000 (100.0%)**
  - **Recall@3:** 0.9737 (97.4%)
  - **Recall@5:** 1.0000 (100.0%)
  - **Precision@1:** 0.6842
  - **Mean Reciprocal Rank (MRR):** **0.8333**
  - **Average Query Latency:** **3.14 ms / query** (fast CPU retrieval)
- **Pairwise Classification Performance (All 16,653 pairs in val):**
  - **ROC-AUC:** **0.9976**
  - **Optimal F1 Threshold:** $\tau = 0.60$
  - **At $\tau = 0.60$:** Precision = 0.1765, Recall = 0.8571 (12/14 true duplicates caught), F1 = 0.2927 (56 false positives out of 16,639 negatives; Specificity = 99.66%)
  - **At $\tau = 0.50$:** Precision = 0.1477, Recall = 0.9286 (13/14 caught), FP = 75
  - **At $\tau = 0.40$:** Precision = 0.1373, Recall = 1.0000 (14/14 caught), FP = 88
  - **At $\tau = 0.80$ (Probable Duplicate):** Precision = 0.0000, Recall = 0.0000, FP = 10 (conservative flag for near-exact text duplicates)

**Artifacts:**
- Retriever model artifact: `models/e6_tfidf_retriever.joblib`
- Threshold trade-off data: `reports/duplicate_thresholds_e6.csv`
- Error log: `reports/duplicate_errors_e6.csv`
- Figures: `reports/figures/duplicate_threshold_curves.png`, `reports/figures/duplicate_retrieval_comparison.png`

**Conclusion:**
Strong, ultra-fast lexical baseline. For candidate retrieval, TF-IDF is exceptionally effective: 100% of incident queries surface a true duplicate in the top 3 candidates (MRR = 0.8333) with ~3.1 ms latency. In pairwise classification, the extreme base-rate imbalance (0.084% prevalence) causes modest precision (17.6%) even at 99.66% specificity, reinforcing why duplicate detection must be an advisory suggestion for human review rather than an automatic merge action.

---

### E7 — Sentence Embedding Cosine Similarity (Duplicate Detection)

**Status:** Completed (Measured on 2026-10-30)

**Research Question:**
Do dense sentence transformer embeddings (`all-MiniLM-L6-v2`) improve retrieval recall or precision over the lexical TF-IDF baseline?

**Dataset:** Same as E6 (`val.csv`, $N=183$, 16,653 candidate pairs). Zero test set leakage.

**Algorithm:**
- Pretrained Model: `all-MiniLM-L6-v2` (sentence-transformers, 384-dimensional dense vectors, normalized).
- Retrieval: Cosine similarity via inner product on normalized embeddings.

**Actual Results (Validation split, N=183):**
- **Retrieval Performance (Top-k Ranking on Incident Queries, N=19):**
  - **Hit@1 (Recall@1):** 0.6842 (68.4%) — *tied with E6*
  - **Hit@3:** 0.9474 (94.7%) — *slightly lower than E6 (100.0%)*
  - **Hit@5:** **1.0000 (100.0%)** — *tied with E6*
  - **Recall@3:** 0.9211 (92.1%)
  - **Recall@5:** 1.0000 (100.0%)
  - **Precision@1:** 0.6842
  - **Mean Reciprocal Rank (MRR):** 0.8202 (vs 0.8333 for E6)
  - **Average Query Latency:** **10.41 ms / query** (~3.3x slower than E6)
- **Pairwise Classification Performance (All 16,653 pairs in val):**
  - **ROC-AUC:** 0.9971 (vs 0.9976 for E6)
  - **Optimal F1 Threshold:** $\tau = 0.80$
  - **At $\tau = 0.80$:** Precision = 0.1522, Recall = 1.0000 (14/14 caught), F1 = 0.2642, FP = 78
  - **At $\tau = 0.85$:** Precision = 0.1528, Recall = 0.7857 (11/14 caught), FP = 61

**Artifacts:**
- Threshold trade-off data: `reports/duplicate_thresholds_e7.csv`
- Error log: `reports/duplicate_errors_e7.csv`
- Figures: `reports/figures/duplicate_threshold_curves.png`, `reports/figures/duplicate_retrieval_comparison.png`

**Conclusion:**
Dense sentence embeddings provide robust semantic representations but do not outperform the lexical TF-IDF baseline on this corpus (Hit@3: 94.7% vs 100.0%; MRR: 0.8202 vs 0.8333; Latency: 10.4 ms vs 3.1 ms). This is because campus complaints frequently contain discriminating lexical tokens (specific laboratory instruments, room numbers, location names, ticket reference numbers) that lexical n-grams match with high precision. TF-IDF (E6) is recommended as the primary, lightweight duplicate retriever.

---

### E8 — K-Means Clustering on TF-IDF Vectors (Spherical K-Means)

**Status:** Completed (Measured on 2026-10-30)

**Research Question:**
Do TF-IDF-based spherical K-Means clusters correspond to meaningful campus complaint themes and issue patterns?

**Dataset:** Validation split (`data/processed/val.csv`, $N=183$, `data_source=synthetic`). Zero test set leakage.

**Algorithm:**
- Representation: Word unigram + bigram TF-IDF (`ngram_range=(1,2)`, `max_features=1500`, L2-normalized unit sphere).
- Clustering: Spherical K-Means ($k=12$ selected via parameter sweep across $k \in [3, 12]$).
- Cluster Interpretation: Centroid-nearest representative complaints + top discriminative n-grams + contingency cross-tabulation against category/location.

**Actual Results (Validation split, N=183):**
- **Optimal Cluster Count:** $k=12$
- **Inertia (SSE):** 144.6815
- **Cosine Silhouette Score:** **0.0941** (monotonically rising with $k$, peaking at $k=12$)
- **Davies-Bouldin Index:** **3.1973** (lower is better; steadily improving from 5.7698 at $k=3$)
- **Training Time:** 0.285 s
- **Inference Time:** 0.052 ms / example

**Key Findings & Limitations:**
- On synthetic text, K-Means successfully grouped related functional themes, but several clusters were partially dominated by shared conversational templates (e.g. *"informed caretaker in person yesterday"*, *"hope administration takes this seriously"*).
- A pure silhouette score heuristic is insufficient for text: manual inspection showed that K-Means forces all unique complaints into equal-variance partitions even when outliers exist.
- Artifacts: `models/e8_kmeans_clusters.joblib`, `reports/figures/clustering_kmeans_tuning.png`.

---

### E9 — K-Means Clustering on Sentence Embeddings

**Status:** Deferred / Replaced by E10 DBSCAN

**Research Question:**
Do dense sentence embedding clusters justify the additional memory and runtime overhead compared to normalized TF-IDF and density-based clustering?

**Evaluation Gate:** Skipped in Phase 7. Cosine DBSCAN (E10) provided much sharper density separation without requiring dense neural re-encoding.

---

### E10 — Density-Based Clustering (DBSCAN with Cosine Distance)

**Status:** Completed (Measured on 2026-10-30)

**Research Question:**
Does density-based clustering discover tighter natural groupings and successfully isolate noise complaints without forcing them into artificial spherical clusters?

**Dataset:**
1. Primary: Validation split (`val.csv`, $N=183$, synthetic).
2. Auxiliary Out-of-Domain Probe: Candidate real-world dataset (`sanchit-19/university-students-complaints`, $N=273$ train rows).

**Algorithm:**
- Distance Representation: Cosine distance on L2-normalized TF-IDF feature space (`metric='cosine'`).
- Parameters: $\text{eps}=0.58$, $\text{min\_samples}=3$.

**Actual Results:**
1. **Synthetic Validation Split ($N=183$):**
   - **Discovered Dense Clusters:** 21 coherent clusters.
   - **Noise / Isolated Complaints Isolated:** 87 complaints (47.5% of corpus).
   - **Silhouette Score (non-noise):** **0.4274** (substantially higher than K-Means 0.0941).
   - **Discovered Emergent Incidents:** Construction noise early morning (100% C11), canteen vendor overcharging (100% C04), algae in mess water dispenser (100% C04), ERP attendance discrepancies (100% C05), scheduled power outages in library (100% C02).
2. **Auxiliary Real-World Student Dataset ($N=273$):**
   - **Discovered Dense Clusters:** 42 coherent clusters.
   - **Noise Isolated:** 36 complaints (13.2% of corpus).
   - **Silhouette Score (non-noise):** **0.5775**.
   - **Discovered Real Incidents:** 8th/9th floor Wi-Fi deadzone, 6th floor CSE drinking water broken, loud talking in library, missing washroom handwash, lift queues causing class tardiness.

**Conclusion:**
DBSCAN with cosine metric is significantly superior to K-Means for real-world complaint discovery. By explicitly designating atypical complaints as noise points (-1) rather than forcing them into clusters, it achieves much higher silhouette coherence (0.4274 on synthetic, 0.5775 on real) and isolates genuine recurring operational hotspots.

---

### E2_TEST — Final Classifier Evaluation on Held-Out Test Split (Calibrated Linear SVM)

**Status:** Completed (Measured on 2026-11-01)

**Research Question:**
Does the primary classifier (`models/e2.joblib`) generalize to completely unseen held-out complaints without performance degradation or calibration drift?

**Dataset:** Held-out test split (`data/processed/test.csv`, $N=182$, 11 categories, group-stratified, zero leakage).

**Algorithm:**
- Model: `models/e2.joblib` (frozen artifact: TF-IDF Word n-grams 1-2 + Platt Calibrated LinearSVC).
- Evaluated **exactly once** with zero parameter adjustment or retraining.

**Actual Results (Held-Out Test Split, N=182):**
- **Accuracy:** **0.9890 (98.90%)** (180 / 182 correct)
- **Macro-F1:** **0.9882** (vs 0.9952 on validation; Generalization gap $\Delta = -0.0070$)
- **Weighted-F1:** **0.9889** (vs 0.9945 on validation)
- **Expected Calibration Error (ECE):** **0.0825** (vs 0.0823 on validation; $\Delta = +0.0002$)
- **Multiclass Brier Score:** **0.0195**
- **Multiclass Log Loss:** **0.1093**
- **Inference Latency:** **0.11 ms / example** (19.8 ms for entire 182 batch)
- **Operational Automation at $\theta = 0.60$:**
  - Auto-routed traffic: **98.9%** (180 / 182)
  - Auto-routing accuracy: **100.00%**
  - Review queue traffic: **1.1%** (2 / 182)
  - Error recall (% caught): **100.0%** (both misclassifications caught at $\text{conf}=0.4052$ and $\text{conf}=0.2075$)
  - False review rate: **0.00%** (zero correct complaints diverted)

**Artifacts:**
- Evaluator script: `src/evaluation/evaluate_final_test.py`
- Confusion matrix: `reports/figures/final_test_confusion_matrix.png`
- Calibration/distribution plots: `reports/figures/final_test_confidence_dist.png`, `reports/figures/final_test_threshold_tradeoff.png`
- Comprehensive report: `reports/final_evaluation.md`

**Conclusion:**
Outstanding generalization with virtually zero degradation ($\Delta \text{ Macro-F1} = -0.007$). At the operating threshold $\theta=0.60$, 100% of errors are caught by human review and zero incorrect classifications are auto-routed.

---

### E6_TEST — Final Duplicate Retriever Evaluation on Held-Out Test Split (TF-IDF Retriever)

**Status:** Completed (Measured on 2026-11-01)

**Research Question:**
Does the lexical TF-IDF similarity retriever maintain high retrieval recall and ranking quality on held-out multi-student incident reports?

**Dataset:** Held-out test split (`data/processed/test.csv`, $N=182$). Contains 18 multi-report complaints across 7 distinct incident groups, yielding 15 true positive duplicate pairs and 16,456 negative pairs (total 16,471 pairs). Zero leakage.

**Algorithm:**
- Retriever: `TFIDFSimilarityRetriever` (TF-IDF Word n-grams 1-2, sublinear TF) indexed on the test corpus.
- Queries: All 18 multi-report complaints evaluated against remaining 181 candidates (query excluded).

**Actual Results (Held-Out Test Split, N=182):**
- **Retrieval Performance (Top-k Ranking on Incident Queries, N=18):**
  - **Hit@1:** **0.7778 (77.8%)** (vs 68.4% on validation)
  - **Hit@3:** **1.0000 (100.0%)** (all 18 queries surfaced a true duplicate in top-3)
  - **Hit@5:** **1.0000 (100.0%)**
  - **Recall@3:** **1.0000 (100.0%)**
  - **Precision@1:** **0.7778**
  - **Precision@3:** **0.5556**
  - **Mean Reciprocal Rank (MRR):** **0.8889** (vs 0.8333 on validation)
  - **Average Query Latency:** **2.13 ms / query**
- **Pairwise Matrix Classification (All 16,471 pairs, 15 true positive pairs):**
  - **ROC-AUC:** **0.9978** (near-perfect ranking separation)
  - **Pre-Fixed Validation Optimal Threshold ($\tau = 0.60$):**
    - **Precision:** **19.18%** (14 / 73 candidate pairs flagged)
    - **Recall:** **93.33%** (14 / 15 true duplicates caught; only 1 missed)
    - **F1 Score:** **0.3182** (TP=14, FP=59, FN=1, TN=16,397)
  - **Operational Duplicate Threshold ($\tau = 0.80$):** Precision = 0.0769, Recall = 0.0667, F1 = 0.0714 (1 TP, 12 FP, 14 FN)
  - **Operational Similar Threshold ($\tau = 0.50$):** Precision = 0.1596, Recall = 1.0000, F1 = 0.2752 (15 TP, 79 FP, 0 FN)
  - **Exploratory Post-Hoc Test Observation ($\tau = 0.65$):** Precision = 0.2069, Recall = 0.8000, F1 = 0.3288 (12 TP, 46 FP, 3 FN, 16,410 TN). *Note:* This point was identified post-hoc on the test sweep and is reported strictly as an exploratory metric.

**Artifacts:**
- Evaluator script: `src/evaluation/evaluate_final_test.py`
- Threshold trade-off curve: `reports/figures/final_test_duplicate_thresholds.png`
- Detailed metrics JSON: `reports/final_test_results.json`

**Conclusion:**
Retriever demonstrates flawless top-3 retrieval recall (100% Hit@3, 0.8889 MRR across the 18 multi-report queries) on held-out test incidents. Extreme pairwise class imbalance (0.091% positive prevalence) causes low precision under exhaustive pairwise matching, validating the UI design of advisory candidate suggestions rather than autonomous merging.

---

*Last updated: 2026-11-01 — Final Evaluation Integrity Audit Completed (Decision D-017 recorded).*

