# Dataset Card — College Complaint Intelligence System

> **Standard:** Adheres to Hugging Face / Gebru et al. Dataset Card Guidelines.  
> **Status:** Final & Verified (Phase 9 Completed)  
> **Primary File:** `data/raw/college_complaints_synthetic.csv`  
> **Processed Splits:** `data/processed/train.csv`, `val.csv`, `test.csv`  
> **Generation Script:** `src/data/generate_synthetic_data.py` (`random_seed=42`)  
> **Evaluation Date:** November 1, 2026  

---

## 1. Dataset Summary

| Field | Description / Value |
|---|---|
| **Dataset Name** | College Complaint Synthetic & Benchmarking Dataset (v1.0) |
| **Primary Authors** | Core AI Engineering System |
| **Language** | English (incorporating American, British, and Indian university campus terminology) |
| **Total Records** | **1,273 records** |
| **Splits** | **Train:** 908 rows (71.3%) \| **Val:** 183 rows (14.4%) \| **Test:** 182 rows (14.3%) |
| **Partitioning Method**| Stratified Group K-Fold (`StratifiedGroupKFold`, $k=7$, seed=42) |
| **Date Range Covered**| 2026-01-10 to 2026-10-25 (synthetic timeline) |
| **License** | Open for Academic & Educational Project Use |
| **Privacy Risk** | **Zero Real-Student PII** (100% procedurally synthesized with automated PII masking) |
| **Associated Auxiliary Dataset** | `sanchit-19/university-students-complaints` ($N=332$, CC-BY-4.0) |

---

## 2. Dataset Purpose & Motivation

Academic institutions receive thousands of unstructured student grievances annually across diverse operational domains (facilities, dining, safety, sanitation, academics). Because genuine student complaint databases contain sensitive personal identifiable information (PII), disciplinary records, and mental health references protected under FERPA and GDPR regulations, real student datasets cannot be openly published or distributed.

This dataset was procedurally engineered to:
1. Provide a realistic, controlled benchmark for evaluating multi-class natural language classification pipelines.
2. Formulate true incident clusters with multi-student reports to benchmark duplicate detection and retrieval algorithms.
3. Test rules-based prioritization and safety override circuits under acute hazard scenarios.
4. Enable reproducible unsupervised clustering and spatial hotspot analysis without compromising student privacy.

---

## 3. Dataset Structure & Schema

The processed splits (`train.csv`, `val.csv`, `test.csv`) share a uniform, standardized 11-column schema:

| Column Name | Data Type | Nullable | Description | Synthetic Example |
|---|---|---|---|---|
| `complaint_id` | String | No | Unique immutable identifier | `"SYN-00142"` |
| `complaint_text` | String | No | Free-form student grievance text | `"Water pressure in Block C 2nd floor bathroom is zero since morning."` |
| `category` | String | No | Canonical category code (`C01`–`C11`) | `"C02"` |
| `category_name` | String | No | Human-readable category title | `"Electricity and Water"` |
| `location` | String | No | Campus facility or zone | `"Hostel Block C - Floor 2"` |
| `created_at` | DateTime | No | ISO-8601 creation timestamp | `"2026-03-14 09:22:15"` |
| `status` | String | No | Lifecycle state (`submitted`, `in_progress`, `resolved`, `pending_review`) | `"submitted"` |
| `priority_label`| String | No | Categorical priority label (`low`, `medium`, `high`, `critical`) | `"high"` |
| `incident_group_id`| String | Yes | Non-null for multi-student reports of the same incident | `"INC-C02-007"` |
| `data_source` | String | No | Provenance identifier | `"synthetic"` |
| `normalized_text`| String | No | Lowercased, punctuation-cleaned text for baseline models | `"water pressure in block c 2nd floor bathroom is zero since morning"` |

---

## 4. Class Distribution & Split Disjointness

### 4.1 Class Counts Across Partitions
The dataset provides balanced representation across 11 functional campus operational areas:

| Code | Category Name | Total Count | Train Split | Validation Split | Held-Out Test Split | Class Share (%) |
|---|---|---|---|---|---|---|
| **C01** | Hostel and Accommodation | 116 | 85 | 12 | 19 | 9.11% |
| **C02** | Electricity and Water | 115 | 80 | 16 | 19 | 9.03% |
| **C03** | Internet and Network | 116 | 83 | 17 | 16 | 9.11% |
| **C04** | Mess and Food | 116 | 81 | 17 | 18 | 9.11% |
| **C05** | Academic and Examination | 115 | 82 | 15 | 18 | 9.03% |
| **C06** | Classroom and Laboratory | 117 | 83 | 19 | 15 | 9.19% |
| **C07** | Sanitation and Cleanliness | 116 | 81 | 19 | 16 | 9.11% |
| **C08** | Campus Safety | 116 | 80 | 20 | 16 | 9.11% |
| **C09** | Transportation | 116 | 83 | 18 | 15 | 9.11% |
| **C10** | Administrative Services | 115 | 83 | 17 | 15 | 9.03% |
| **C11** | Other / Unclassified | 115 | 87 | 13 | 15 | 9.03% |
| **Total**| — | **1,273** | **908 (71.3%)**| **183 (14.4%)** | **182 (14.3%)** | **100.0%** |

### 4.2 Group-Aware Disjointness & Leakage Audit
To prevent artificial shortcuts in duplicate detection and classification, records sharing an `incident_group_id` were strictly assigned to the same partition using `StratifiedGroupKFold`:

| Split | Incident Groups | Multi-Report Records | Standalone Records | Total Records |
|---|---|---|---|---|
| **Train** | 35 | 92 | 816 | 908 |
| **Validation** | 8 | 19 | 164 | 183 |
| **Held-Out Test** | 7 | 18 | 164 | 182 |
| **Total** | **50** | **129** | **1,144** | **1,273** |

**Automated Leakage Audit Output (`src.data.preprocess.check_split_leakage`):**
- **Overlapping Complaint IDs:** `0`
- **Exact Text Leaks:** `0`
- **Incident Group Overlap:** `0`
- **Status:** **100% Leakage-Free Verified**

---

## 5. Data Generation & Quality Assurance

### 5.1 Procedural Generation Methodology
The dataset was generated using `src/data/generate_synthetic_data.py`:
1. **Combinatorial Syntactic Templates:** 15 distinct syntactic complaint structures per category, combining subject noun phrases, fault descriptors, temporal urgency markers, and impact qualifiers.
2. **Realistic Campus Vocabulary:** Incorporated authentic facilities terminology (e.g., LAN port, MCB trip, water purifier, mess token, sports complex, shuttle bus).
3. **Multi-Report Incident Clustering:** Procedurally spawned 50 distinct real incident groups where 2 to 4 student personas independently report the identical underlying problem from different perspectives (varying formality, sentence length, and vocabulary).
4. **Noise Injection:** Realistic orthographic variations, capitalization shifts, and minor formatting irregularities were injected across 15% of records.

### 5.2 Quality Checks Executed & Passed
- [x] Zero empty or whitespace-only texts.
- [x] Zero records shorter than 10 characters (minimum text length: 32 characters, maximum: 412 characters).
- [x] Zero duplicate complaint texts.
- [x] 100% label validity across codes `C01` through `C11`.
- [x] Strict temporal validity (all timestamps between 2026-01-10 and 2026-10-25).

### 5.3 Automated PII Sanitization
The preprocessing pipeline (`src/data/preprocess.py`) implements a rigorous regex scrubbing layer that scans for and masks synthetic PII:
- **Phone Numbers:** `\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b` $\to$ `[PHONE]`
- **Email Addresses:** `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b` $\to$ `[EMAIL]`
- **Roll / Student ID Numbers:** `\b(?:ROLL|STU|ID|REG)[-:\s]?\d{4,8}\b` $\to$ `[STUDENT_ID]`

---

## 6. Auxiliary Real-World Dataset Profile

To evaluate zero-shot domain transfer without contaminating synthetic benchmarks, the project integrated the external public dataset **`sanchit-19/university-students-complaints`** (approved under Decision **D-014**):

| Attribute | Details |
|---|---|
| **Repository URL** | [Hugging Face: sanchit-19/university-students-complaints](https://huggingface.co/datasets/sanchit-19/university-students-complaints) |
| **Original Creator**| Md. Al Amin (`alaminxpro/university-students-complaints`, ORCID: `0009-0005-5859-3093`) |
| **License** | Creative Commons Attribution 4.0 International (**CC-BY-4.0**) |
| **Record Count** | **332 rows** (`train.csv`: 273, `test.csv`: 59) |
| **Domain Scope** | Real student feedback across 6 university academic departments (73.8% CSE department skew) |
| **Category Taxonomy**| 5 Coarse Classes: `Infrastructure` (143), `Technical` (65), `Academic` (64), `Finance` (33), `Administrative` (27) |
| **Paraphrase Groups**| 186 unique incident groups (`Complaint_Group_ID`); 58 multi-complaint groups ($N=204$ rows) |
| **Usage Policy** | **Strictly quarantined from training.** Never merged into synthetic files. Used exclusively for zero-shot duplicate retrieval evaluation and out-of-domain clustering in Phase 7. |

---

## 7. Known Limitations & Usage Constraints

1. **Synthetic Grammar vs. Natural Student Text:**
   - Procedurally generated complaints exhibit higher grammatical consistency than real-world text. Natural student complaints frequently feature shorthand, emojis, and Hinglish or local campus slang.
2. **Category Coarseness:**
   - Real-world complaints may span multiple administrative domains (e.g., broken laboratory air conditioner damaging research equipment). In our primary dataset, each complaint is assigned a single primary label (`C01`–`C11`).
3. **Benchmarking Mandate:**
   - Numerical metrics obtained on this dataset (e.g., 98.90% classification accuracy) serve to validate machine learning architecture and data engineering pipelines. They must **never** be cited as empirical performance on real human student bodies.

---

*Dataset Card finalized and approved for Phase 9 submission.*
