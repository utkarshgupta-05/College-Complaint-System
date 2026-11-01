# AI-Powered College Complaint Intelligence System

> **A technically rigorous, end-to-end Machine Learning system and full-stack application for automated campus complaint triage, similarity detection, priority assessment, and recurring-issue discovery.**

[![Python Tests](https://img.shields.io/badge/Python%20Tests-128%2F128%20Passing-brightgreen)](tests/)
[![Frontend Tests](https://img.shields.io/badge/Frontend%20Tests-27%2F27%20Passing-brightgreen)](frontend/test/)
[![Test Macro-F1](https://img.shields.io/badge/Test%20Macro--F1-0.9882-blue)](reports/final_evaluation.md)
[![Held-Out Test Split](https://img.shields.io/badge/Test%20Split%20(N=182)-Quarantined%20%26%20Leakage--Free-success)](data/processed/test.csv)
[![License](https://img.shields.io/badge/License-Academic%20Open-lightgrey)](LICENSE)

---

## 1. System Overview

University campuses receive thousands of unstructured student grievances each semester regarding hostel maintenance, laboratory equipment, dining hall food quality, safety, and administrative delays. Traditional ticketing systems rely on manual triaging, leading to slow response times, missed duplicate reports, and potential delays in addressing life-safety emergencies.

This project delivers an enterprise-grade AI/ML pipeline paired with a modern web demonstration application that solves these challenges through four specialized modules:

1. **Automated Multi-Class Classification (Module A):** Maps unstructured student complaint text to 11 standardized operational categories with calibrated confidence scores.
2. **Duplicate & Related Complaint Detection (Module B):** Uses fast lexical and semantic vector retrieval to surface candidate multi-student reports about shared campus incidents.
3. **Transparent Priority Assessment (Module C):** Computes objective, auditable urgency scores ($0-100$) using linguistic cues, facility scope, ticket aging, and recurrence, backed by **hard safety override circuits** for hazardous emergencies.
4. **Recurring-Issue & Hotspot Discovery (Module D):** Applies unsupervised density-based (DBSCAN) and centroid (K-Means) clustering to identify emergent maintenance crises and geographic failure hotspots across campus.

---

## 2. Key Evaluation Results (Held-Out Test Split, $N=182$)

The system was evaluated on a quarantined, held-out test dataset ($N=182$ complaints) partitioned using `StratifiedGroupKFold` with zero cross-split leakage.

| Module / Task | Primary Model | Test Metric | Measured Value | Validation Value | Generalization Gap |
|---|---|---|---|---|---|
| **Classification (Module A)** | Calibrated Linear SVM (`models/e2.joblib`) | **Accuracy** | **98.90%** | 99.45% | $-0.55\%$ |
| | | **Macro-F1** | **0.9882** | 0.9952 | $-0.0070$ |
| | | **Weighted-F1** | **0.9889** | 0.9945 | $-0.0056$ |
| | | **Expected Calibration Error (ECE)** | **0.0825** | 0.0823 | $+0.0002$ |
| | | **Single-Sample Latency** | **0.11 ms** | 0.11 ms | $0.00\text{ ms}$ |
| **Operational Automation ($\theta = 0.60$)** | Confidence Routing Gate | **Auto-Routed Traffic** | **98.9%** | 97.8% | $+1.1\%$ |
| | | **Auto-Routing Accuracy** | **100.00%** | 100.00% | **0 misclassified routed** |
| | | **Error Recall (% Caught)** | **100.0%** | 100.0% | Both errors caught |
| **Duplicate Retrieval (Module B)** | TF-IDF Cosine Retriever (`models/e6_tfidf_retriever.joblib`) | **Hit@1 ($N=18$ queries)** | **77.78%** | 68.42% | $+9.36\%$ |
| | | **Hit@3 ($N=18$ queries)** | **100.00%** | 100.00% | $0.00\%$ |
| | | **MRR (Mean Reciprocal Rank)** | **0.8889** | 0.8333 | $+0.0556$ |
| | | **Pairwise ROC-AUC** | **0.9978** | 0.9976 | $+0.0002$ |
| | | **Pairwise F1 (Pre-Fixed $\tau=0.60$)** | **0.3182** (Rec: 93.3%) | 0.2927 (Rec: 85.7%) | $+0.0255$ |
| **Priority Rules (Module C)** | Multi-Factor Formulation + Safety Circuits | **Safety Override Trigger Rate** | **100.0%** (in test suite) | 100.0% | $0.00\%$* |
| **Recurring Discovery (Module D)** | Cosine DBSCAN ($\epsilon=0.58$, $\text{min\_samples}=3$) | **Non-Noise Silhouette** | **N/A** (Exploratory) | 0.4274 (21 clusters) | Validation only |

*\*Note on Safety Overrides: All explicitly constructed safety scenarios in the current rule-based test suite triggered the expected override. This does not establish universal real-world emergency detection. Mandatory human review is retained for all safety-flagged tickets.*  
*Full experimental results, query denominator derivations, and error analyses are documented in [reports/final_evaluation.md](reports/final_evaluation.md).*

---

## 3. System Architecture & Tech Stack

```
   ┌────────────────────────────────────────────────────────┐
   │             Client Tier (React 18 + Vite)              │
   │  Student Portal  │  Staff Queue  │  Admin Analytics    │
   └───────────────────────────┬────────────────────────────┘
                               │ HTTP / JSON (REST)
   ┌───────────────────────────▼────────────────────────────┐
   │             Backend API Tier (FastAPI Async)           │
   │  /api/auth   │   /api/complaints   │   /api/analytics  │
   └───────────────────────────┬────────────────────────────┘
                               │
   ┌───────────────────────────▼────────────────────────────┐
   │              AI / ML Inference Service Tier            │
   │  - Calibrated Linear SVM (TF-IDF Word 1-2 ngrams)      │
   │  - TF-IDF Cosine Similarity Retriever (Dynamic Index)  │
   │  - Rules-Based Multi-Factor Priority Engine            │
   │  - Spherical K-Means & Cosine DBSCAN Clustering        │
   └───────────────────────────┬────────────────────────────┘
                               │
   ┌───────────────────────────▼────────────────────────────┐
   │                  Persistence Tier                      │
   │  PostgreSQL 15+ (Production) / SQLite 3 (Testing/Dev)   │
   │  Alembic Migrations  │  Priority Override Audit Trail  │
   └────────────────────────────────────────────────────────┘
```

- **Frontend:** React 18, Vite 5.4, Lucide Icons, Vanilla CSS3 (zero heavy UI framework dependencies).
- **Backend:** FastAPI (Python 3.11+ / 3.13), Uvicorn ASGI, Pydantic v2 schemas.
- **Machine Learning:** `scikit-learn`, `joblib`, `numpy`, `pandas`, `nltk`.
- **Database & Persistence:** SQLAlchemy 2.0 ORM, Alembic schema migrations, PostgreSQL 15+ (production) with SQLite fallback for local developer testing.

---

## 4. Repository Directory Structure

```
college-complaint-intelligence/
├── backend/                  # FastAPI web server, routers, ORM models, auth
│   ├── alembic/              # Database schema migrations
│   ├── routers/              # API endpoints (auth, complaints, analytics)
│   ├── services/             # AI singleton serving service
│   ├── database.py           # Database engine & connection pooling
│   └── main.py               # Application entrypoint
│
├── frontend/                 # React 18 + Vite client application
│   ├── src/
│   │   ├── components/       # StudentPortal, StaffPortal, AdminDashboard, Modals
│   │   ├── api.js            # Axios API client
│   │   └── App.jsx           # Main view switcher & role state
│   ├── test/                 # Node.js automated frontend test suites
│   └── package.json          # Frontend dependencies
│
├── data/
│   ├── raw/                  # Source synthetic data (1,273 rows)
│   └── processed/            # Quarantined train.csv, val.csv, test.csv
│
├── models/                   # Serialized ML artifacts (.joblib)
│   ├── e2.joblib             # Primary Calibrated Linear SVM classifier
│   └── e6_tfidf_retriever.joblib # TF-IDF duplicate similarity retriever
│
├── src/                      # Core machine learning package
│   ├── classification/       # Training, inference, and evaluation
│   ├── duplicates/           # TF-IDF & embedding similarity retrievers
│   ├── prioritization/       # Canonical priority rules and safety overrides
│   ├── clustering/           # K-Means, DBSCAN, and frequency analysis
│   └── evaluation/           # Shared metrics and split leakage audits
│
├── reports/                  # Detailed evaluation reports and figures
│   ├── figures/              # Confusion matrices, threshold curves, ROC plots
│   ├── final_evaluation.md   # Phase 9 Final Comprehensive Evaluation Report
│   ├── architecture.md       # Full Technical System Architecture
│   └── final_demo_guide.md   # Step-by-Step Evaluator Walkthrough Guide
│
├── tests/                    # Pytest backend test suite (128 passing tests)
├── DATASET_CARD.md           # Dataset Card (provenance, schema, splits, ethics)
├── MODEL_CARD.md             # Model Card (Mitchell et al. standard)
├── config.yaml               # Global project configuration
└── requirements.txt          # Python dependencies
```

---

## 5. Quickstart & Installation

### Prerequisites
- Python 3.11 or higher
- Node.js 18 or higher (with npm)
- Git

### Step 1: Clone Repository & Create Virtual Environment
```bash
git clone <repository-url>
cd college-complaint-intelligence

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### Step 2: Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

---

## 6. Running the Application

### Start the Backend Server (Terminal 1)
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
*API Swagger Documentation is available at:* `http://localhost:8000/docs`

### Start the Frontend Application (Terminal 2)
```bash
cd frontend
npm run dev
```
*Web application opens at:* `http://localhost:5173`

---

## 7. Demo Roles & Instant Role Switching

The frontend includes a **1-click Role Switcher** in the top navigation bar to facilitate evaluator walkthroughs without manual logins:

| Role | Demo Username | Default Capabilities |
|---|---|---|
| **Student** | `student1` | Submit complaints, live keystroke pre-triage, view personal complaint history. |
| **Staff** | `staff1` | Triage queue, filter low-confidence tickets, update ticket statuses, inspect explainability modal, override priorities. |
| **Admin** | `admin1` | High-level campus KPIs, category distribution charts, spatial maintenance hotspots, unsupervised cluster review. |

---

## 8. Running Automated Test Suites

The codebase includes comprehensive test suites across both backend and frontend.

### Python Backend Suite (128 Tests)
```bash
# Run complete Python test suite
python -m pytest -v
```
*Covers:* Data validation, preprocessing, leakage verification, classifier inference, duplicate retrieval, priority rules, safety overrides, API routers, RBAC authorization, and database persistence across engine restarts.

### Frontend Unit & Scenario Suite (27 Tests)
```bash
npm --prefix frontend test
```
*Covers:* Safe numeric and string formatters, keystroke debouncing, race condition cancellation, error boundaries, priority override validation, and admin chart rendering.

### Production Build Verification
```bash
npm --prefix frontend run build
```
*Produces optimized static bundle in `frontend/dist/` with zero compilation errors.*

---

## 9. Key API Endpoints Reference

| Method | Endpoint | Access Role | Description |
|---|---|---|---|
| `POST` | `/api/complaints/analyze` | All | Keystroke pre-triage (category prediction, confidence, base priority, duplicate suggestions). |
| `POST` | `/api/complaints` | Student | Submit a new complaint ticket with dynamic AI index update. |
| `GET` | `/api/complaints` | Staff / Admin | Fetch complaint queue with filtering (status, priority, category, review flag). |
| `GET` | `/api/complaints/{id}` | Staff / Admin | Fetch complete ticket details including explainability signals and override history. |
| `PATCH`| `/api/complaints/{id}/status` | Staff / Admin | Update ticket lifecycle status (`submitted` $\to$ `in_progress` $\to$ `resolved`). |
| `POST` | `/api/complaints/{id}/override-priority`| Staff / Admin | Adjust ticket priority with mandatory textual justification audit log. |
| `GET` | `/api/analytics/overview` | Admin | High-level operational KPIs, category breakdown, and spatial hotspots. |
| `GET` | `/api/analytics/clusters` | Admin | Unsupervised clustering on live database complaints with trend sufficiency check. |

---

## 10. Ethical Governance & Safeguards

1. **Zero Autonomous Deletions:** Duplicate detection surfaces candidate matches as **advisory suggestions** only. The system is strictly prohibited from merging or deleting tickets automatically.
2. **Deterministic Safety Overrides:** Complaints mentioning acute hazards (fire, smoke, electric shock, structural collapse, assault, ragging) immediately bypass mathematical averaging and are escalated to `CRITICAL` priority with mandatory human review. *Audited Boundary:* All explicitly constructed safety scenarios in the current rule-based test suite triggered the expected override. This does not establish universal real-world emergency detection; mandatory human review is strictly retained for all safety-flagged tickets.
3. **Mandatory Audit Logs:** Any human priority override requires role authorization and a non-empty textual justification, recorded in an immutable audit ledger (`PRIORITY_OVERRIDES`).
4. **Zero Synthetic Analytics Fallback:** The analytics engine clusters only real database tickets and displays an honest insufficient-data state when fewer than 3 complaints exist.

---

## 11. Documentation Index

- [Final Evaluation Report](reports/final_evaluation.md) — Comprehensive empirical metrics on the held-out test split.
- [Model Card](MODEL_CARD.md) — Standardized model documentation adhering to Mitchell et al.
- [Dataset Card](DATASET_CARD.md) — Provenance, schema, group-stratified splits, and PII masking.
- [System Architecture](reports/architecture.md) — Complete software and ML architectural specification.
- [Evaluator Demo Guide](reports/final_demo_guide.md) — Step-by-step walkthrough script for testers.
- [Experiment Results CSV](reports/experiment_results.csv) — Complete raw metrics log for Experiments E1 through E10.

---

*College Complaint Intelligence System — Developed for Academic & Operational Excellence.*
