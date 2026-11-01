# Exploratory Data Analysis Report

**Dataset:** `data/raw/college_complaints_synthetic.csv`  
**Data Source:** `synthetic` (explicitly tagged for pipeline development)  
**Total Records:** 1273  
**Date Range:** 2026-01-11 04:05:22 to 2026-10-26 22:45:05  
**Language:** English  

---

## 1. Dataset Integrity & Missing Values

| Column | Missing Count | Data Type | Notes |
|---|---|---|---|
| `complaint_id` | 0 (0.0%) | object | Clean (0 missing) |
| `complaint_text` | 0 (0.0%) | object | Clean (0 missing) |
| `category` | 0 (0.0%) | object | Clean (0 missing) |
| `category_name` | 0 (0.0%) | object | Clean (0 missing) |
| `location` | 0 (0.0%) | object | Clean (0 missing) |
| `created_at` | 0 (0.0%) | object | Clean (0 missing) |
| `status` | 0 (0.0%) | object | Clean (0 missing) |
| `priority_label` | 0 (0.0%) | object | Clean (0 missing) |
| `incident_group_id` | 1157 (90.9%) | object | Nullable field |
| `data_source` | 0 (0.0%) | object | Clean (0 missing) |

- **Null texts:** 0 (all complaints contain valid text)
- **Min length check:** All texts >= 10 characters (min observed: 78 chars)
- **Max length observed:** 318 characters (54 words)
- **Median length:** 182 characters (28 words)

---

## 2. Category Distribution

All 11 categories defined in `config.yaml` are populated with balanced representation (each >= 115 records):

| Code | Category Name | Count | Percentage |
|---|---|---|---|
| `C01` | Hostel and Accommodation | 116 | 9.1% |
| `C02` | Electricity and Water | 115 | 9.0% |
| `C03` | Internet and Network | 116 | 9.1% |
| `C04` | Mess and Food | 116 | 9.1% |
| `C05` | Academic and Examination | 115 | 9.0% |
| `C06` | Classroom and Laboratory | 117 | 9.2% |
| `C07` | Sanitation and Cleanliness | 116 | 9.1% |
| `C08` | Campus Safety | 116 | 9.1% |
| `C09` | Transportation | 116 | 9.1% |
| `C10` | Administrative Services | 115 | 9.0% |
| `C11` | Other / Unclassified | 115 | 9.0% |

- **Imbalance ratio:** Max count = 117, Min count = 115 (ratio: 1.02). The dataset is approximately balanced, preventing degenerate majority-class bias during baseline training.

---

## 3. Priority & Safety Escalation Breakdown

| Priority Level | Count | Share | Description |
|---|---|---|---|
| `Medium` | 476 | 37.4% | Standard issue |
| `Low` | 360 | 28.3% | Standard issue |
| `Critical` | 239 | 18.8% | Safety-critical override cases |
| `High` | 198 | 15.6% | Standard issue |

- **Safety Critical Incidents:** 239 complaints contain severe safety cues (fire hazards, gas leaks, electrical sparking, structural hazards, assaults). These are designated for immediate human escalation.

---

## 4. Multi-Report Incident Groups (Duplicates / Related Incidents)

- **Total Grouped Incident Clusters:** 47 distinct incidents
- **Total Multi-Report Records:** 116 (9.1%)
- **Standalone Records:** 1157 (90.9%)
- **Cluster Sizes:** 2 to 3 related complaints per incident group with varying student perspectives, wording, and timestamps.
- **Leakage Prevention:** Group-aware stratified splitting ensures that all members of an incident group remain strictly within the same data split (train, val, or test).

---

## 5. Visual Artifacts Produced

The following publication-grade charts have been generated and saved:
1. `reports/figures/class_distribution.png`: Category frequency comparison.
2. `reports/figures/text_length_distribution.png`: Word count distribution and boxplots by category.
3. `reports/figures/priority_distribution.png`: Breakdown of severity/priority levels.
4. `reports/figures/top_keywords_per_category.png`: Top bigram frequencies across representative categories.

---

## 6. Key Findings for Modeling

1. **Vocabulary Diversity:** Text lengths range naturally from concise reports (e.g. 8-15 words) to multi-sentence complaints with context and past escalation history (up to 90 words).
2. **Ambiguity Handling:** Cross-domain complaints (e.g., mess hygiene leading to health center visits) are captured in C11 and multi-topic scenarios, ensuring the classifier must learn nuanced distinctions rather than trivial keyword matches.
3. **Data Leakage Protected:** Near-duplicate and related incident complaints are partitioned with zero group leakage across splits.
