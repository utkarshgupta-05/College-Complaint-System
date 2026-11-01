# Final Demonstration & Evaluator Walkthrough Guide

> **Document ID:** `reports/final_demo_guide.md`  
> **System:** AI-Powered College Complaint Intelligence System  
> **Release Version:** v1.0.0  
> **Target Audience:** Project Evaluators, Academic Reviewers, and Testers  
> **Evaluation Date:** November 1, 2026  

---

## 1. Quickstart: Launching the Application

Ensure you have Python 3.11+ and Node.js 18+ installed on your system.

### Step 1: Start Backend API (FastAPI)
Open a terminal in the project root:
```bash
# Activate virtual environment if configured
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate

# Start FastAPI server on port 8000
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
*Verification:* Navigate to `http://localhost:8000/docs` in your browser to inspect the interactive OpenAPI Swagger UI.

### Step 2: Start Frontend Application (React + Vite)
Open a second terminal in the project root:
```bash
cd frontend
npm install       # (Only needed on fresh clone)
npm run dev
```
*Verification:* Navigate to `http://localhost:5173` in your browser. The application loads immediately into the Student Portal.

---

## 2. Demo User Credentials & Role Switching

The top header bar provides an instantaneous **1-click Role Switcher** (`Student`, `Staff`, `Admin`) for immediate walkthrough testing without manual login forms:

| Demo Role | User ID | Username | Primary Access / View |
|---|---|---|---|
| **Student** | `STU-001` | `student1` | **Student Portal:** Complaint submission, keystroke live triage, duplicate alerts, ticket tracker. |
| **Staff** | `STAFF-001` | `staff1` | **Staff Portal:** Departmental queues, low-confidence review queue, explainability modal, priority overrides. |
| **Admin** | `ADM-001` | `admin1` | **Admin Dashboard:** Campus KPIs, category breakdown, spatial hotspots, recurring-issue clusters. |

---

## 3. Evaluator Walkthrough Scenarios

---

### Scenario 1: Real-Time AI Pre-Triage & Keystroke Debouncing
**Objective:** Observe the real-time AI classification and priority engine in action as you type.

1. Ensure the active role is set to **Student**.
2. Select Location: `Hostel Block B - Floor 2`.
3. In the **Complaint Description** box, begin typing slowly:
   > *"The ceiling fan in my room is making an unusual buzzing noise."*
4. **Observe:**
   - As soon as you exceed 10 characters, the real-time AI triage card activates below the input box.
   - **Predicted Category:** `Hostel and Accommodation` (Code: `C01`) with a calibrated confidence bar ($\approx 95\%$).
   - **Calculated Priority:** `LOW` (Base score $\approx 16.7$).
   - Notice the smoothness: keystrokes are debounced at 300 ms, avoiding network spamming. Stale requests are cancelled cleanly.

---

### Scenario 2: Acute Safety Hazard Override
**Objective:** Verify that acute physical hazards bypass standard mathematical scoring and trigger immediate escalation to `CRITICAL`.

1. Clear the description box and enter:
   > *"There is heavy smoke and fire coming out of the electrical meter box near the staircase! Emergency evacuation needed!"*
2. **Observe:**
   - **Safety Override Triggered:** The priority instantly jumps to **`CRITICAL`** highlighted in deep red.
   - **Audit Flags:** `Safety Override: Active`, `Mandatory Human Review: Required`.
   - **Keywords Detected:** `fire`, `smoke`, `evacuation`.
   - **Base Score:** Even though the calculated score is $\approx 30.0$, the policy override forces the complaint to `CRITICAL`, demonstrating the override on keyword-matched hazards. *(Note: While all test-suite scenarios triggered the override, keyword rules do not guarantee universal real-world emergency detection; mandatory human review is strictly retained).*
3. Click **Submit Complaint**.
4. The ticket is assigned ID `COMP-XXXXX` and stored in the database.

---

### Scenario 3: Real-Time Duplicate Detection
**Objective:** Verify that multi-student reports about the same incident are detected in real time.

1. Keep the role as **Student**.
2. Enter Location: `Hostel Block B - Floor 2`.
3. Enter Description:
   > *"Heavy smoke coming from electrical meter room near stairs, please call fire brigade."*
4. **Observe:**
   - The **Potential Similar Complaints** advisory box appears below the input.
   - The complaint you submitted in Scenario 2 is retrieved with high similarity ($>0.75$).
   - The advisory card informs the student that this incident is already under active review, reducing redundant submissions while preserving the student's right to submit if they wish.

---

### Scenario 4: Staff Triage & Deep Explainability Modal
**Objective:** Review incoming complaints as an authorized staff member and inspect model explainability.

1. Click **Staff** in the top header role switcher. The interface switches to the **Staff Portal**.
2. **Explore the Queue:**
   - Notice the ticket submitted in Scenario 2 appears at the top of the queue with badge `CRITICAL` and `Needs Review`.
   - Filter by status, priority, or category using the dropdown selectors.
   - Toggle the **"Needs Human Review Only"** checkbox to filter for low-confidence or safety-flagged complaints.
3. Click **Inspect & Review** on any complaint row.
4. **The Explainability Modal opens:**
   - **Softmax Probability Distribution:** A clean horizontal bar chart displaying probabilities across all 11 categories (e.g. `C02: 94.2%`, `C01: 2.1%`, `C06: 1.5%`).
   - **Priority Signal Breakdown:** Displays exact numerical sub-scores for *Language Severity*, *Safety Risk*, *Affected Population*, *Waiting Time Escalation*, and *Recurrence*.

---

### Scenario 5: Staff Priority Override with Immutable Audit Trail
**Objective:** Test human governance by adjusting a complaint's priority and logging justification.

1. Inside the **Complaint Detail Modal**, locate the **Adjust Priority (Staff Override)** section.
2. Select a new priority from the dropdown (e.g., change `CRITICAL` to `HIGH` if verified as a small false alarm, or escalate `LOW` to `HIGH`).
3. Try clicking **Apply Override** with an empty reason field.
   - **Observe:** The UI and backend block the submission with an alert: *"A clear justification reason is required for staff overrides."*
4. Type a valid reason:
   > *"Inspected by electrician; minor fuse burnt out, no active fire hazard. Work order issued."*
5. Click **Apply Override**.
6. **Observe:** The modal updates, the badge displays `HIGH [OVERRIDDEN]`, and an immutable audit entry is appended to the database audit table.

---

### Scenario 6: Admin Dashboard & Live Analytics
**Objective:** Inspect executive-level metrics and verified cluster discovery.

1. Click **Admin** in the header role switcher.
2. **Inspect High-Level KPIs:**
   - Total Complaints Count, Open Tickets, Critical Issues, Low-Confidence Review Count.
3. **Inspect Category Breakdown Chart:**
   - Dynamic bar chart showing real complaint counts and percentages across all 11 categories.
4. **Inspect Spatial Hotspots Table:**
   - Ranks campus facilities by complaint density (e.g., `Hostel Block B`, `Mess Hall 1`).
5. **Inspect Recurring Incident Clusters:**
   - If the database has $\ge 3$ complaints, unsupervised TF-IDF K-Means groups related complaints into semantic clusters.
   - If fewer than 3 complaints exist, notice the **honest insufficient-data state**: the system displays *"Insufficient live complaints to discover statistical clusters"* rather than faking synthetic data.

---

## 7. Edge Cases & Resilience Verifications

1. **Short / Empty Complaints:**
   - Type `"hi"` into the student portal. Notice the character counter indicates `(2/10 chars)` and the AI engine waits safely without firing premature requests.
2. **Network Interruption / Graceful Degradation:**
   - If the backend is temporarily paused, the frontend displays clear inline status notices rather than crashing or freezing.
3. **Rapid Typing / Race Condition Stress Test:**
   - Rapidly paste and delete text fragments. The `AbortController` hook cancels in-flight network requests, ensuring only the final keystroke's prediction renders.

---

*Demo walkthrough verified complete and ready for evaluation.*

