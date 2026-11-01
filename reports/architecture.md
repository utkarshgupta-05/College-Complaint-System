# System Architecture & Technical Specifications

> **Document ID:** `reports/architecture.md`  
> **System:** AI-Powered College Complaint Intelligence System  
> **Release Version:** v1.0.0  
> **Author:** Core AI Architecture Team  
> **Status:** Final & Verified (Phase 9)  

---

## 1. High-Level Architecture Overview

The College Complaint Intelligence System is an end-to-end, full-stack machine learning application engineered to intake, analyze, route, prioritize, and cluster university student grievances. The architecture balances sub-millisecond AI inference with strict relational persistence, robust Role-Based Access Control (RBAC), and verifiable human-in-the-loop governance.

```mermaid
flowchart TD
    subgraph Client ["Client Tier (React 18 + Vite)"]
        SP["Student Portal (Real-Time Keystroke Triage)"]
        STP["Staff Portal (Queue Management & Deep Explainability)"]
        ADM["Admin Dashboard (Analytics, Hotspots & Clusters)"]
    end

    subgraph Gateway ["API Gateway Tier (FastAPI Async)"]
        AuthRouter["/api/auth (OAuth2 / RBAC Tokens)"]
        CompRouter["/api/complaints (Triage & Ticket CRUD)"]
        AnalytRouter["/api/analytics (KPIs, DBSCAN, K-Means)"]
    end

    subgraph AIService ["AI / ML Inference Service (Singleton)"]
        VEC["TF-IDF Vectorizer Pipeline"]
        SVM["Calibrated Linear SVM (E2 Classifier)"]
        RET["TF-IDF Cosine Similarity Retriever (E6 Dynamic)"]
        PRI["Rules-Based Prioritization Engine (P_base + Overrides)"]
        CLUST["Spherical K-Means & Cosine DBSCAN (E8 & E10)"]
    end

    subgraph DataTier ["Data & Persistence Tier"]
        PG[("PostgreSQL 15+ (Production Persistence)")]
        Alembic["Alembic Migrations"]
        AuditLog[("Priority Override & Lifecycle Audit Logs")]
    end

    SP -->|Debounced Keystroke POST /analyze| CompRouter
    SP -->|Submit Complaint POST /| CompRouter
    STP -->|Review & Override Priority| CompRouter
    ADM -->|Request Cluster Analytics| AnalytRouter
    
    CompRouter --> AIService
    AnalytRouter --> AIService
    
    AIService --> VEC
    VEC --> SVM
    VEC --> RET
    AIService --> PRI
    AIService --> CLUST

    CompRouter --> PG
    AnalytRouter --> PG
    CompRouter --> AuditLog
```

---

## 2. Component Tier Specifications

### 2.1 Frontend Tier (`frontend/`)
- **Technology Stack:** React 18.3, Vite 5.4, Lucide React icons, Vanilla CSS3.
- **Port / Host:** `http://localhost:5173` (development) / Static build via `dist/` (production).
- **Core Principles:** Zero blank screens, defensive rendering, decoupled state.
- **Key Modules & Portals:**
  1. `StudentPortal.jsx`:
     - Implements real-time, keystroke-level debounced triage preview (300 ms debounce).
     - As the student types, invokes `/api/complaints/analyze` with `AbortController` cancellation for stale in-flight requests.
     - Displays predicted category badge with calibrated confidence meter, calculated base priority score, and potential duplicate advisory warnings before submission.
  2. `StaffPortal.jsx`:
     - Triage queue featuring multi-attribute filtering (category, priority, review flags, search terms).
     - Quick-action status updates (`submitted` $\to$ `in_progress` $\to$ `resolved`).
     - Low-confidence review queue filter isolating tickets requiring human verification.
  3. `ComplaintDetailModal.jsx`:
     - Complete explainability inspection interface for staff.
     - Visualizes full multi-class softmax probability distribution across all 11 categories.
     - Breaks down priority signals (severity, safety risk, affected population, aging bonus, recurrence).
     - Interactive priority override workflow requiring mandatory non-empty justification reasons.
  4. `AdminDashboard.jsx`:
     - High-level KPIs: Total complaints, open tickets, high/critical volume, review queue count.
     - Category breakdown bar chart and spatial maintenance hotspots table.
     - Unsupervised incident clusters from live database complaints with trend sufficiency warnings.
  5. `ErrorBoundary.jsx`:
     - Top-level React error boundary intercepting unexpected render faults, preventing blank screens, and presenting clear recovery options.

### 2.2 Backend API Gateway (`backend/`)
- **Technology Stack:** FastAPI 0.115+, Uvicorn ASGI, Pydantic v2 data validation schemas.
- **Port / Host:** `http://localhost:8000`.
- **Modular Routers:**
  - `backend/routers/auth.py`: User authentication, mock token generation, user profile resolution.
  - `backend/routers/complaints.py`: Triage pre-analysis (`/analyze`), ticket submission, list filtering, status updating, priority overrides.
  - `backend/routers/analytics.py`: Operational overview KPIs, category distribution, spatial hotspots, and dynamic unsupervised clustering.

### 2.3 AI Serving Engine (`backend/services/ai_service.py`)
- **Pattern:** Thread-safe Singleton loaded once on application startup.
- **Artifacts Ingested:**
  - `models/e2.joblib`: Primary calibrated Linear SVM classifier.
  - `models/e6_tfidf_retriever.joblib`: Primary TF-IDF similarity retriever.
- **Dynamic Online Indexing:**
  - When a student submits a new complaint, `AIService.index_complaint(cid, text, metadata)` vectorizes the text and appends it to the in-memory candidate matrix.
  - Subsequent submissions immediately match against freshly submitted tickets in real time without requiring offline index rebuilds.
- **Latency Benchmarks:**
  - Single complaint classification: **$0.11\text{ ms}$**.
  - Candidate similarity retrieval ($N=1,200$ corpus): **$2.13\text{ ms}$**.
  - Total end-to-end `/api/complaints/analyze` response time: **$<15\text{ ms}$**.

---

## 3. Data Tier & Relational Schema

### 3.1 Database Architecture
- **Production Engine:** PostgreSQL 15+ (`postgresql+psycopg2://user:password@localhost:5432/complaints_db`).
- **Testing & Local Fallback:** SQLite 3 (`sqlite:///./complaints.db`).
- **Production Safeguard:** In `backend/config.py`, when `ENV=production`, the application strictly prohibits SQLite connections and enforces PostgreSQL.

### 3.2 Entity-Relationship Model

```mermaid
erDiagram
    USERS ||--o{ COMPLAINTS : submits
    USERS ||--o{ PRIORITY_OVERRIDES : authorises
    COMPLAINTS ||--o{ PRIORITY_OVERRIDES : audited_by
    COMPLAINTS ||--o{ STATUS_HISTORY : logs

    USERS {
        string id PK
        string username
        string role "student | staff | admin"
        string full_name
        string department
    }

    COMPLAINTS {
        string complaint_id PK
        string student_id FK
        text complaint_text
        string category "C01..C11"
        string category_name
        float confidence
        string priority "CRITICAL | HIGH | MEDIUM | LOW"
        float priority_score
        boolean safety_flag
        boolean safety_override
        boolean needs_human_review
        string location
        string status "submitted | in_progress | resolved"
        string incident_group_id
        datetime created_at
        datetime updated_at
    }

    PRIORITY_OVERRIDES {
        int id PK
        string complaint_id FK
        string staff_id FK
        string old_priority
        string new_priority
        text reason
        datetime created_at
    }

    STATUS_HISTORY {
        int id PK
        string complaint_id FK
        string staff_id FK
        string old_status
        string new_status
        datetime created_at
    }
```

---

## 4. End-to-End Request Lifecycles

### 4.1 Keystroke Pre-Triage Analysis Flow
1. Student types into description field in `StudentPortal.jsx`.
2. Debounce hook delays execution for 300 ms after the last keypress.
3. If length $\ge 10$ characters, sends `POST /api/complaints/analyze` with `{ text, location }`.
4. `ai_service.py` executes:
   - Text preprocessing and normalization.
   - `e2.predict_proba()` calculates softmax category distribution and identifies top category + confidence score.
   - `rules.assess_priority()` calculates base numerical score and checks for safety keyword triggers.
   - `e6.find_similar()` retrieves top-3 candidates with similarity $\ge 0.50$.
5. Backend returns Pydantic `ComplaintAnalysisResponse`.
6. Frontend updates category pill, confidence meter, priority badge, and duplicate suggestions box without re-rendering the entire form.

### 4.2 Ticket Submission & Dynamic Indexing Flow
1. Student clicks "Submit Complaint".
2. `POST /api/complaints` validates payload and inserts record into `COMPLAINTS` table in database.
3. `ai_service.index_complaint()` dynamically computes the new TF-IDF vector and updates the in-memory matrix.
4. Database commits transaction and returns newly created complaint ID (`COMP-XXXXX`).

### 4.3 Human-in-the-Loop Priority Override Flow
1. Staff member opens `ComplaintDetailModal.jsx` and selects a new priority level.
2. Staff enters non-empty justification reason (required by UI and validated by backend).
3. `POST /api/complaints/{id}/override-priority` executes:
   - Validates user role is `staff` or `admin` (HTTP 403 otherwise).
   - Updates `priority` in `COMPLAINTS` table.
   - Inserts audit record into `PRIORITY_OVERRIDES` table.
4. UI notifies staff and updates badge with `[OVERRIDDEN]` tag.

---

## 5. Security & Role-Based Access Control (RBAC)

The system enforces three strict privilege tiers:

| Role | Capabilities | Protected Endpoints |
|---|---|---|
| **Student** (`student`) | Submit complaints, run pre-triage `/analyze`, view personal complaint tracking | `/api/complaints/analyze`, `POST /api/complaints`, `GET /api/complaints/my` |
| **Staff** (`staff`) | View all complaints, filter low-confidence queue, update ticket status, apply priority overrides, inspect explainability | `PATCH /api/complaints/{id}/status`, `POST /api/complaints/{id}/override-priority` |
| **Admin** (`admin`) | All staff capabilities + access high-level analytics overview, view spatial hotspots, inspect recurring-issue clusters | `GET /api/analytics/overview`, `GET /api/analytics/clusters` |

---

## 6. Zero Synthetic Fallback Policy

To ensure absolute academic integrity and prevent misleading administrators:
- The `/api/analytics/clusters` endpoint executes clustering **strictly on live database records**.
- If fewer than 3 complaints exist in the live database, the endpoint returns an empty array `[]` with status `"insufficient_data"`.
- Synthetic or validation-corpus clusters are **never** injected or presented as live campus issues.

---

*System Architecture verified complete and active.*

