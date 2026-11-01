# Decision Log — College Complaint Intelligence System

> **Purpose:** Record of significant technical and design decisions.
> **Rules:** Never silently change an established decision. Append revisions; preserve history.
> Status: Provisional | Final

---

## Format

```
### D-NNN — [DATE] — Decision Title
**Context / Problem:**
**Options Considered:**
**Selected Option & Rationale:**
**Trade-offs & Limitations:**
**Consequences for Later Work:**
**Status:** Provisional | Final
```

---

## Decisions

---

### D-001 — [2026-10-29] — Core Problem Formulation

**Context / Problem:**
Define the ML tasks this system must solve, and what each task's inputs and outputs are.

**Selected Option & Rationale:**

Four ML tasks are defined:

| Module | Task | Input | Output |
|---|---|---|---|
| A | Complaint Classification | Raw complaint text (+ optional metadata) | Category label + confidence score |
| B | Duplicate/Similar Detection | A new complaint + corpus of existing complaints | Ranked list of candidate similar complaints + similarity scores |
| C | Priority Assessment | Complaint text + metadata (location, time, category) | Priority level (Critical/High/Medium/Low/Needs Review) + explanation |
| D | Recurring Issue Discovery | Corpus of complaints over time | Cluster labels + representative examples + trend charts |

These four tasks are independent enough that each can be built and evaluated separately
before integration. Classification is the prerequisite for modules C and D because
category is a useful feature for priority and clustering.

**Trade-offs & Limitations:**
- Priority assessment depends on trustworthy labels or a defensible annotation process.
  Without these, only a rules-based system is defensible.
- Duplicate detection without labeled pairs can only be evaluated approximately.

**Status:** Final

---

### D-002 — [2026-10-29] — Complaint Category Scheme (Provisional)

**Context / Problem:**
What categories should the classifier use? The scheme must match real complaint topics.

**Options Considered:**
1. Use the 11 categories specified in the master prompt verbatim.
2. Derive categories empirically from data inspection.
3. Use a hierarchical scheme (broad → specific).

**Selected Option & Rationale:**
Option 2 (empirical, data-driven) is the correct approach, but it requires real data.

**Provisional starting point** (to be validated against actual data in Phase 2):

| ID | Category |
|---|---|
| C01 | Hostel and Accommodation |
| C02 | Electricity and Water |
| C03 | Internet and Network |
| C04 | Mess and Food |
| C05 | Academic and Examination |
| C06 | Classroom and Laboratory |
| C07 | Sanitation and Cleanliness |
| C08 | Campus Safety |
| C09 | Transportation |
| C10 | Administrative Services |
| C11 | Other / Unclassified |

**Ambiguity rules (provisional):**
- A complaint touching two topics should be assigned to the *primary* topic (the one
  the student appears to be most urgently reporting).
- Complaints that cannot be reliably assigned get label C11 (Other / Unclassified).
- Short or vague complaints that provide no usable signal go to C11 with a low-confidence flag.
- These rules must be validated against examples during labeling (Phase 2).

**Trade-offs & Limitations:**
- Categories may need merging (e.g., C02 + C07 if data is sparse) or splitting after EDA.
- The C11 category creates intentional ambiguity; its precision/recall must be inspected carefully.

**Consequences for Later Work:**
- Phase 2 must confirm category distribution. Rare categories (< ~30 examples) may need
  merging or a separate handling strategy.
- Annotation guide must operationalize ambiguity rules.

**Status:** Provisional — must be confirmed after Phase 2 EDA.

---

### D-003 — [2026-10-29] — Classification Algorithm Strategy

**Context / Problem:**
Which ML algorithms to use for complaint classification, and in what order.

**Options Considered:**
1. Start with deep learning (BERT/RoBERTa).
2. Start with traditional baselines, add complexity only if justified.
3. Use only a rules-based keyword approach.

**Selected Option & Rationale:**
Option 2. Reasons:
- Baselines are fast, interpretable, and provide a fair performance floor.
- Deep learning requires more data, compute, and complexity to justify.
- Logistic Regression coefficients are directly interpretable (supports Module E).
- Linear SVM typically achieves strong results on short text classification.
- A transformer is justified only if: (a) baseline macro-F1 is significantly below an
  acceptable threshold, AND (b) dataset size is sufficient (rule of thumb: ≥ 500
  examples per class for fine-tuning), AND (c) compute is available.

**Experiment order:**
1. TF-IDF (word unigrams) + Logistic Regression (E1 — baseline).
2. TF-IDF (word/char n-grams) + Linear SVM (E2).
3. Sentence embeddings (all-MiniLM-L6-v2) + Logistic Regression or cosine classifier (E3 — only if E1/E2 results are insufficient).

**Trade-offs & Limitations:**
- TF-IDF loses word order and semantic meaning. This is acceptable for short complaint texts.
- Logistic Regression with calibrated probabilities can produce reasonable confidence scores.
- SVM confidence scores require Platt scaling to be meaningful probabilities.

**Status:** Provisional — may be revised after Phase 2 EDA reveals actual text length / vocabulary.

---

### D-004 — [2026-10-29] — Duplicate Detection Strategy

**Context / Problem:**
How to identify complaints describing the same underlying incident.

**Selected Option & Rationale:**
Two-stage approach:
1. Stage 1 (Lexical): TF-IDF cosine similarity — fast, no GPU needed, good for near-exact duplicates.
2. Stage 2 (Semantic): Sentence embeddings cosine similarity — captures paraphrase-level similarity.

Similarity threshold is tuned on validation data. The system outputs *candidate pairs for
human review*, never automatically merges or deletes complaints.

**Key distinction:**
- Score ≥ HIGH_THRESHOLD → "Probable duplicate — review immediately"
- Score ∈ [MID_THRESHOLD, HIGH_THRESHOLD) → "Similar complaint — may be related"
- Score < MID_THRESHOLD → "Unrelated"

Thresholds are `Provisional` until tuned in Phase 5.

**Status:** Provisional

---

### D-005 — [2026-10-29] (Finalized 2026-10-30) — Priority Assessment Strategy

**Context / Problem:**
How to assign urgency levels and routing priority to complaints in an interpretable, auditable manner.

**Approved Option & Formula (0–100 Scale):**
Transparent rules-based engine combining multi-factor signals with policy safety overrides and staff auditability:

```
P_base = 0.35 * severity + 0.25 * safety_risk + 0.20 * affected_population + 0.10 * waiting_time + 0.10 * recurrence
```

Component Signal Definitions (each factor normalized to [0, 100]):
- `severity` (0–100): Textual severity and acute impact language cues.
- `safety_risk` (0–100): Detection of potential hazard cues (fire, gas leak, electrical hazard, structural collapse, assault/ragging, contamination).
- `affected_population` (0–100): Scale of impact. Non-zero neutral baseline: 25.0 (individual/room), scaling to 50 (multi-person), 75 (building/hostel), 100 (campus-wide).
- `waiting_time` (0–100): Normalized elapsed time: $\min(100.0, \max(0.0, \frac{\text{elapsed\_hours}}{72.0} \times 100.0))$. Future timestamps clamp to 0.0.
- `recurrence` (0–100): Normalized recurrence: $\min(100.0, \max(0.0, \frac{\text{recurrence\_count}}{5.0} \times 100.0))$.

Approved Priority Bands:
- **CRITICAL**: Verified critical safety hazard or policy safety override. Unconditionally requires immediate human staff review.
- **HIGH**: $P_{\text{base}} \ge 75.0$
- **MEDIUM**: $45.0 \le P_{\text{base}} < 75.0$ (Standard SLA)
- **LOW**: $P_{\text{base}} < 45.0$ (Minor / cosmetic)

Safety Override & Auditability:
- Keyword detection flags potential risk for urgent human assessment; it is NOT definitive proof of an emergency.
- Clearly distinguishes: `base_score`, `safety_override`, `suggested_priority`, `final_priority`, and `needs_human_review`.
- Authorized human staff overrides are recorded with `staff_id`, `original_priority`, `override_priority`, `reason`, and `timestamp` for complete auditability.

**Status:** Final


---

### D-006 — [2026-10-29] — Dataset Strategy

**Context / Problem:**
What data to use for training and evaluation.

**Options Considered:**
1. Real authorized college complaint dataset.
2. Suitable public dataset (e.g., customer complaint datasets on Kaggle/UCI).
3. Carefully designed synthetic dataset for pipeline development.

**Selected Option & Rationale:**
Priority order: Real > Public > Synthetic.

- **Real data** is preferred but requires institutional authorization and privacy review.
- **Public datasets** (e.g., consumer complaint datasets) can be adapted but may differ
  from the college domain; transfer is not guaranteed.
- **Synthetic data** is used ONLY for pipeline development and clearly labeled as such.
  Results on synthetic data are NEVER claimed as real-world performance.

Action required: Confirm whether a real or public dataset is available before Phase 2 starts.

**Status:** Provisional — awaiting dataset confirmation.

---

### D-007 — [2026-10-29] — Category Merging Decision (Dataset-Dependent)

**Context:** Category distribution is unknown until Phase 2 EDA.
**Decision:** If any category has fewer than 30 training examples, merge it with the most
semantically similar category or assign to C11. This threshold is provisional.
**Status:** Provisional — depends on dataset.

---

### D-008 — [2026-10-29] — Similarity Threshold Values (Dataset-Dependent)

**Context:** Optimal cosine similarity thresholds depend on the corpus vocabulary and
embedding space of the actual data.
**Decision:** Tune thresholds using validation data in Phase 5.
**Status:** Not Started — depends on dataset.

---

### D-009 — [2026-10-29] — Supervised Priority Model (Dataset-Dependent)

**Context:** A supervised priority classifier requires trustworthy historical priority labels.
**Decision:** Do not train a supervised priority model until Phase 2 confirms that reliable
labels exist and a defensible annotation process is documented.
**Status:** Not Started — depends on dataset.

---

### D-010 — [2026-10-29] — Transformer Fine-Tuning (Dataset-Dependent)

**Context:** Fine-tuning a BERT-class model requires sufficient data and compute.
**Decision:** Consider only if: macro-F1 from baselines is below an acceptable threshold
AND dataset has ≥ 500 labeled examples per class AND compute is available.
**Status:** Not Started — depends on Phase 3 results.

---

### D-011 — [2026-10-29] — Application Technology Stack

**Context:** Phase 8 requires a full-stack demonstration application.

**Selected Stack:**
- Frontend: React 18 + TypeScript + Vite
- Backend: Python 3.11 + FastAPI
- Database: PostgreSQL 16
- ORM & Migrations: SQLAlchemy 2.x + Alembic
- ML: pandas, NumPy, scikit-learn, sentence-transformers (when justified)
- Testing: pytest (backend), Vitest (frontend)
- Process manager (dev): uvicorn with --reload

**Rationale:** Aligned with master prompt specification. React + FastAPI is a well-understood,
beginner-friendly full-stack combination. PostgreSQL is appropriate for relational complaint
data with audit trails.

**Trade-offs:** Adds Phase 8 complexity; must not distract from ML deliverables in Phases 1–7.

**Status:** Final (stack selection confirmed by master prompt)

### D-012 — [2026-10-30] — Primary Classifier & Confidence Threshold Selection

**Context / Problem:**
Select the primary complaint classification model and confidence threshold based on Phase 4 comparative evaluation across E1, E2, E3, and E4 on the validation split.

**Options Evaluated:**
1. E1: Word TF-IDF + Logistic Regression (Macro-F1: 0.9890, Brier: 0.3413, Latency: 0.074 ms)
2. E2: Word TF-IDF + Calibrated Linear SVM (Macro-F1: 0.9952, Brier: 0.0168, Latency: 0.110 ms)
3. E3: Word TF-IDF + Multinomial Naive Bayes (Macro-F1: 0.9774, Brier: 0.2382, Latency: 0.081 ms)
4. E4: Char TF-IDF + Calibrated Linear SVM (Macro-F1: 0.9948, Brier: 0.0157, Latency: 0.415 ms)

**Selected Option & Rationale:**
- **Primary Model:** **E2 (Word TF-IDF + Calibrated Linear SVM)**
  - Highest Macro-F1 (0.9952) and Weighted-F1 (0.9945).
  - Excellent probability calibration (Brier: 0.0168, Log Loss: 0.1005) via 5-fold Platt scaling.
  - Fast CPU inference: 0.110 ms per example (~8,800 complaints/sec).
  - Outperformed Naive Bayes (+0.0178 F1) and Logistic Regression (+0.0062 F1).
  - Marginally faster than E4 (0.110 ms vs 0.415 ms) with slightly better Macro-F1.
- **Confidence Threshold:** **$\theta = 0.60$**
  - Validation sweeping (`reports/thresholds_e2.csv`) demonstrated:
    - Automatic Routing Rate: **97.8%** of complaints routed without human intervention.
    - Automated Routing Accuracy: **100.0%** accuracy on auto-routed complaints.
    - Review Queue Error Recall: **100.0%** of misclassifications caught and flagged.
    - False Review Rate: only **1.65%** of correct complaints sent to review.
- **Deep Learning Gate Decision (E5):** Skipped. With baseline Macro-F1 at 0.9952 and 0.110 ms CPU latency, introducing complex transformer models for classification is unjustified.

**Consequences for Later Work:**
- E2 artifact (`models/e2.joblib`) will serve as the classification engine in Phase 8 FastAPI backend.
- Held-out test set (`data/processed/test.csv`) remains untouched until Phase 9 Final Evaluation.

**Status:** Final

---

### D-013 — [2026-10-30] — Duplicate Detection Model and Similarity Thresholds

**Context / Problem:**
Select the primary duplicate and related-complaint detection architecture (Module B) and tune operational similarity thresholds ($\tau_{\text{high}}$ and $\tau_{\text{mid}}$) based on empirical validation evaluation across E6 (TF-IDF Cosine Similarity) and E7 (Sentence Transformers: `all-MiniLM-L6-v2`).

**Options Evaluated:**
1. E6: TF-IDF Cosine Similarity (Word unigram + bigram, normalized text)
   - Hit@1: 68.4%, Hit@3: **100.0%**, Hit@5: **100.0%**, MRR: **0.8333**
   - Query Latency: **3.14 ms / query** on CPU
   - Pairwise ROC-AUC: **0.9976**
2. E7: Dense Sentence Embeddings (`all-MiniLM-L6-v2`)
   - Hit@1: 68.4%, Hit@3: 94.7%, Hit@5: **100.0%**, MRR: 0.8202
   - Query Latency: 10.41 ms / query (~3.3x slower)
   - Pairwise ROC-AUC: 0.9971

**Selected Option & Rationale:**
- **Primary Model:** **TF-IDF Cosine Similarity (E6)**
  - Higher Top-3 Retrieval Recall (100% vs 94.7%) and MRR (0.8333 vs 0.8202).
  - ~3.3x faster query latency (3.14 ms vs 10.41 ms) with minimal CPU memory footprint.
  - Campus complaints feature discriminating named entities (lab instruments, room numbers, building names) that benefit strongly from exact lexical matching.
- **Operational Thresholds Selected:**
  - $\tau_{\text{high}} = 0.80$: **Probable Duplicate** (triggers high-priority staff advisory to link reports; caught near-exact duplicates with zero false alarms in natural text).
  - $\tau_{\text{mid}} = 0.50$: **Similar Complaint / Related Incident** (surfaces candidates with high recall: 92.9% duplicate recall, catching multi-student incident reports).
  - Below $0.50$: **Unrelated** (not suggested).
- **Core Ethical & Architectural Invariant:**
  - **Zero automated suppression or merging**: Duplicate suggestions are strictly presented as advisory linkages in the staff UI. The system never merges, deletes, or auto-closes tickets without explicit staff authorization.

**Consequences for Later Work:**
- `TFIDFSimilarityRetriever` artifact (`models/e6_tfidf_retriever.joblib`) will serve as the duplicate detection engine for Module B.
- Quarantined test set (`test.csv`) remains untouched until Phase 9.

### D-014 — [2026-10-30] — Auxiliary Real-World Dataset Strategy & Role Definition

**Context / Problem:**
Assess whether to introduce real-world complaint data from Hugging Face dataset `sanchit-19/university-students-complaints` (mirrored from `alaminxpro/university-students-complaints`, CC-BY-4.0, 332 records) into the AI-Powered College Complaint Intelligence System, and determine its role across the four AI modules without corrupting the established synthetic benchmark or causing data leakage.

**Evidence & Investigation:**
1. **Size & Scope:** 332 total rows (train: 273, test: 59). Far too small for 11-class balanced training.
2. **Category Mismatch:** 5 high-level administrative buckets (`Infrastructure`: 143, `Technical`: 65, `Academic`: 64, `Finance`: 33, `Administrative`: 27) vs. our 11 operational campus routing categories (C01–C11). Collapses hostel, sanitation, electrical, and lab maintenance into generic infrastructure.
3. **Fields & Schema:** Contains `Timestamp`, `Gender`, `Semester`, `Student_Dept`, `Aspects`, and `Complaint_Group_ID` (186 unique groups, 58 multi-complaint groups containing 204 rows). However, lacks standardized location coordinates, objective physical hazard flags, or resolution SLAs.
4. **Severity Field:** Coarse subjective 4-level rating (`Urgent`, `High`, `Medium`, `Low`) based on student perception (108/332 marked Urgent), lacking operational ground truth for multi-factor priority scoring.

**Selected Option & Approved Strategy:**
1. **Preserve Synthetic Baseline:** Keep `college_complaints_synthetic.csv` (1,273 rows across C01–C11) as the primary training and comparative evaluation benchmark. All existing train/validation/test splits, trained models (E1, E2, E3, E4, E6), and experiment results are strictly preserved.
2. **No Merging or Replacement:** Do NOT merge or replace the synthetic dataset with the candidate dataset.
3. **Role as Auxiliary Out-of-Domain (OOD) Evaluation Benchmark:** Treat `sanchit-19/university-students-complaints` strictly as an auxiliary external test corpus to evaluate zero-shot transfer, real-world duplicate retrieval on natural paraphrases, and unsupervised topic extraction in Phase 7.
4. **No Classifier Retraining or Priority Ground Truth:** Do not retrain our 11-class classifier on its 5-class labels, and do not use its subjective severity field as ground truth for our priority formula.
5. **Test Set Quarantine Intact:** Held-out test split (`data/processed/test.csv`, 182 rows) remains strictly untouched until Phase 9.

**Trade-offs & Limitations:**
- External evaluation on this dataset reflects single-institution South Asian student context with 73.8% CSE department skew.
- Category mismatch prevents direct supervised classification benchmarking without many-to-one aggregation.

**Consequences for Later Work:**
- Used in Phase 7 as an out-of-domain clustering corpus.
- Documented in `DATASET_CARD.md`.

**Status:** Final

---

### D-015 — [2026-11-01] — Phase 8 Integration and Demonstration Architecture

**Context / Problem:**
In Phase 8, the objective is to integrate all four validated AI modules into an operational, full-stack demonstration application without altering model artifacts or compromising academic rigor. We must select the backend framework, database abstraction, frontend framework, serving architecture, role-based workflows, and audit mechanisms.

**Approved Architecture & Decisions:**
1. **Backend Framework:** FastAPI (Python 3.13)
   - Native integration with Python ML artifacts (`scikit-learn`, `joblib`, `numpy`, `pandas`).
   - High-throughput asynchronous endpoints with Pydantic v2 data validation schemas.
   - Modular routers: `/api/auth`, `/api/complaints`, `/api/analytics`.
2. **Database Engine & Persistence:**
   - SQLAlchemy 2.0 ORM with connection pooling.
   - Dual-engine design: Configured for production PostgreSQL (`postgresql+psycopg2://...`) with transparent local/testing fallback to SQLite (`sqlite:///./complaints.db`).
   - Database migrations managed via Alembic (`backend/alembic/versions/2026_11_01_0001_initial_schema.py`).
3. **Frontend Application:**
   - React 18 + Vite with clean vanilla responsive styling and Lucide icons.
   - 3 Dedicated Role Views:
     - **Student Portal:** Real-time debounced AI triage preview (calls `/api/complaints/analyze` on keystroke), category routing prediction with confidence meter, priority scoring, potential duplicate warning, and ticket tracking.
     - **Staff Portal:** Queue management with multi-criteria filtering, low-confidence review toggles, status updates, deep explainability inspection modal (softmax probability distribution and priority signal breakdown), and priority overrides.
     - **Admin Dashboard:** High-level operational KPIs, category distribution charts, spatiotemporal hotspots table, unsupervised recurring-issue clusters with weak-support indicators, and statistical trend sufficiency warnings.
4. **AI Serving Strategy (`backend/services/ai_service.py`):**
   - Singleton service loading `models/e2.joblib` (Calibrated Linear SVM) and `models/e6_tfidf_retriever.joblib` (TF-IDF Retriever).
   - Priority assessment via rule-based canonical formula from `src/prioritization/rules.py`.
   - **Dynamic Retriever Indexing:** When new complaints are submitted, `index_complaint()` dynamically adds the TF-IDF vector into the in-memory matrix so that subsequent submissions immediately retrieve newly created complaints without offline rebuilds.
5. **Human-in-the-Loop Governance & Audit Trail:**
   - Priority overrides require role `staff` or `admin` and a **mandatory non-empty justification reason**.
   - All overrides are appended to `PriorityOverrideAudit` with user ID, timestamps, old priority, new priority, and rationale.
   - Automatic routing confidence threshold $\tau = 0.65$; complaints below threshold are marked `needs_review=True`.
6. **Data Integrity & Quarantine:**
   - Quarantined test set (`data/processed/test.csv`, 182 rows) remains strictly untouched until Phase 9.

**Status:** Final

---

### D-016 — [2026-11-01] — Phase 9 Final Validation and Project Completion Protocol

**Context / Problem:**
In Phase 9, we must conduct the final, authoritative validation of the entire AI/ML system on the quarantined held-out test split (`data/processed/test.csv`, $N=182$). We must define the evaluation protocol, ensure zero leakage, prevent model retraining or tuning based on test results, finalize standardized Model and Dataset Cards, and produce exhaustive system architecture and demonstration guides.

**Decisions & Protocol:**
1. **Single Evaluation Pass Invariant:**
   - The held-out test split ($N=182$) was evaluated exactly once. Zero hyperparameter tuning or retraining was performed using test signals.
   - Leakage check confirmed 0 index overlap, 0 exact text leaks, and 0 incident group leaks across all splits.
2. **Empirical Performance Acceptance:**
   - **Primary Classifier (`models/e2.joblib`):** Test Macro-F1 = 0.9882, Accuracy = 98.90%, Weighted-F1 = 0.9889, ECE = 0.0825. Generalization gap vs validation is $\le 0.70\%$, confirming zero overfitting.
   - **Operational Confidence Threshold ($\theta = 0.60$):** 98.9% of complaints are auto-routed with 100.00% accuracy. Both misclassified test cases ($N=2$) had confidence $<0.41$ and were successfully routed to human review (100% Error Recall, 0% False Review Rate).
   - **Duplicate Detection (`models/e6_tfidf_retriever.joblib`):** Evaluated on all 18 multi-report complaints in the test set. Top-$k$ retrieval achieved 77.78% Hit@1, 100.0% Hit@3, 100.0% Hit@5, and 0.8889 MRR with 2.13 ms latency. Pairwise ROC-AUC = 0.9978.
   - **Priority Assessment Engine:** 100% recall on hazardous emergencies via deterministic safety override circuits. Base numerical scale validated across 8 canonical test scenarios.
3. **Artifact and Card Finalization:**
   - Finalized `MODEL_CARD.md` adhering to Mitchell et al. (2019).
   - Finalized `DATASET_CARD.md` detailing group stratification, procedural synthesis, and the auxiliary out-of-domain evaluation benchmark.
   - Authored `reports/final_evaluation.md`, `reports/architecture.md`, and `reports/final_demo_guide.md`.
   - Updated `README.md` to production standard.

**Status:** Final

---

### D-017 — [2026-11-01] — Final Evaluation Integrity Audit and Metric Corrections

**Context / Problem:**
Conduct a strict post-Phase 9 evaluation integrity audit across duplicate detection thresholds, unsupervised clustering evaluation claims, priority safety override guarantees, external dataset provenance, and classification verification. Identify any post-hoc test optimizations, unqualified claims, or metric discrepancies and correct all documentation.

**Audit Findings & Approved Decisions:**
1. **Duplicate Detection Threshold Audit:**
   - *Finding:* The threshold $\tau = 0.65$ was identified post-hoc by sweeping test-set scores and picking `idxmax()` of test F1 (0.3288). It was **not** pre-fixed on validation data.
   - *Correction:* The pre-fixed validation threshold selected in Phase 5 was **$\tau = 0.60$** (from `duplicate_thresholds_e6.csv`). On the held-out test split, $\tau = 0.60$ achieves **F1 = 0.3182**, **Precision = 19.18%**, and **Recall = 93.33%** (TP=14, FP=59, FN=1, TN=16,397). This is now the authoritative pre-fixed test estimate.
   - $\tau = 0.65$ is explicitly designated as an exploratory/post-hoc test-set observation.
   - *Query Count & Denominator:* Clarified that 18 multi-report complaints in `test.csv` (across 7 groups, yielding 15 positive pairs) serve as 18 individual retrieval queries against 181 candidate complaints (excluding self). Denominator for Hit@$k$ and MRR is strictly 18 queries.
2. **Clustering Evaluation Audit:**
   - *Finding:* Clustering was **never rerun on `test.csv`**. The reported 21 clusters, 87 noise points, and 0.4274 non-noise silhouette were copied from Phase 7 validation results ($N=183$).
   - *Correction:* In accordance with evaluation integrity rules, test clustering metrics are explicitly labeled as **N/A (Exploratory validation metric only; not evaluated on test set to prevent exploratory data snooping)**.
3. **Safety Override Guarantee Audit:**
   - *Finding:* Claiming "100% safety override recall" or "100% emergency detection" implies a universal real-world guarantee that a 55-term regex keyword scanner cannot provide.
   - *Correction:* Replaced universal claims with the audited wording: *"All explicitly constructed safety scenarios in the current rule-based test suite triggered the expected override. This does not establish universal real-world emergency detection."* Mandatory human review is strictly retained for all safety-flagged tickets.
4. **Classification Verification:**
   - Re-verified that exactly 182 test records were evaluated on `models/e2.joblib`, exactly 180 were correct (98.90% Accuracy, 0.9882 Macro-F1), and confidence threshold $\theta = 0.60$ was pre-fixed in Decision D-012 during Phase 4.
5. **External Dataset Provenance:**
   - Re-verified `sanchit-19/university-students-complaints` (Md. Al Amin, CC-BY-4.0, 332 records). Confirmed strict quarantine from synthetic models and test splits, and disclosed the 73.8% CSE department skew.

**Status:** Final

---

*Last updated: 2026-11-01 — Decision D-017 recorded (Final Evaluation Integrity Audit Completed)*




