# Data Directory — College Complaint Intelligence System

> This directory holds all datasets used in the project.
> **Never commit raw complaint data to Git if it contains PII.**
> **Never commit files larger than a few MB without using Git LFS.**

---

## Directory Structure

```
data/
├── raw/        # Original, immutable source files — do not modify
├── interim/    # Partially processed files (e.g., after PII masking, before splitting)
└── processed/  # Final, model-ready datasets (train.csv, val.csv, test.csv)
```

---

## Data Dictionary

The following fields are the **intended schema**. Actual fields depend on the dataset chosen in Phase 2.

| Field | Type | Description | Example |
|---|---|---|---|
| `complaint_id` | string | Unique identifier | `COMP-2024-0001` |
| `complaint_text` | string | Free-text complaint (PII-masked) | `"The water supply in Block B has been off for 2 days."` |
| `category` | string | Category label (C01–C11) | `C02` |
| `category_name` | string | Human-readable category name | `Electricity and Water` |
| `location` | string | Campus location | `Boys Hostel Block B` |
| `created_at` | datetime (ISO 8601) | Submission timestamp | `2024-03-15T09:30:00` |
| `status` | string | Current status | `Open`, `In Progress`, `Resolved` |
| `priority_label` | string | Assigned priority (if available) | `High` |
| `incident_group_id` | string | Groups related complaints (if annotated) | `INC-2024-042` |
| `resolved_at` | datetime / null | Resolution timestamp | `2024-03-16T14:00:00` |
| `department` | string | Responsible department | `Hostel Administration` |
| `data_source` | string | Origin of the record | `real`, `public`, `synthetic` |
| `split` | string | Dataset split assignment | `train`, `val`, `test` |

---

## File Naming Convention

| File | Contents |
|---|---|
| `raw/<source_name>_raw.csv` | Original downloaded / received data |
| `interim/<source_name>_masked.csv` | PII-masked version |
| `interim/<source_name>_labeled.csv` | After category labeling |
| `processed/train.csv` | Training split |
| `processed/val.csv` | Validation split |
| `processed/test.csv` | Test split (do not touch until final evaluation) |
| `processed/data_stats.json` | Category distribution, text length stats |

---

## How to Obtain Data

Follow the strategy in order of preference (see also `DATASET_CARD.md`):

1. **Real college data:** Obtain authorization → anonymize → place in `data/raw/`.
2. **Public dataset:** Download → inspect license → place in `data/raw/`.
3. **Synthetic data:** Run `src/data/generate_synthetic.py` → output goes to `data/raw/synthetic_complaints.csv`.

Document the source, date, and license in `DATASET_CARD.md` before proceeding.

---

## .gitignore Rules for this Directory

Add the following to `.gitignore`:

```
data/raw/*.csv
data/raw/*.json
data/interim/*.csv
data/processed/*.csv
!data/raw/.gitkeep
!data/interim/.gitkeep
!data/processed/.gitkeep
```

---

*Last updated: 2026-10-29 — Phase 1 initialization.*
