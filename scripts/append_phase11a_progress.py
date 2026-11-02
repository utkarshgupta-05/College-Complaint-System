from pathlib import Path

path = Path("docs/implementation-progress.md")
text = path.read_text(encoding="utf-8").rstrip()

if "*Last updated:" in text:
    text = text[:text.rfind("---")].rstrip()

entry = """

---

## Phase 11A — Final Taxonomy and Evaluation Integrity Audit

**Overall Status:** ✅ Verified Complete (Decision D-024 Recorded; Canonical Taxonomy Locked; Evaluation History Reconciled)

| Task | Acceptance Criteria | Status | Evidence |
|---|---|---|---|
| Canonical taxonomy verification | Audit category code-name-department mapping across all layers | ✅ Verified Complete | All datasets, models, backend, frontend, and reports confirmed 100% compliant |
| Taxonomy reference module | Create canonical immutable source of truth | ✅ Verified Complete | `src/taxonomy.py` defining CANONICAL_TAXONOMY, CATEGORY_DEPARTMENTS, CATEGORY_DESCRIPTIONS |
| Backend service connection | Connect ai_service to canonical taxonomy module | ✅ Verified Complete | `backend/services/ai_service.py` imports directly from `src.taxonomy` |
| Evaluation history reconciliation | Reconcile Phase 9 and Phase 11 test evaluation timeline | ✅ Verified Complete | Documented Phase 9 as initial test run and Phase 11 as deterministic re-verification |
| Claim governance | Add sample size context ($N_{\\text{errors}}=2$) and benchmark limits | ✅ Verified Complete | `reports/final_test_evaluation.md` and `MODEL_CARD.md` updated with tempered claims |
| Automated regression tests | Authored tests verifying taxonomy across datasets, model, and frontend | ✅ Verified Complete | `tests/test_taxonomy.py` (7 tests, all PASSED) |
| Full test suite verification | Verify entire test suite passes without regressions | ✅ Verified Complete | 135 / 135 tests passing in ~23s |
| Audit report delivery | Generate comprehensive Phase 11A audit report | ✅ Verified Complete | `reports/phase11a_integrity_audit.md` |

---

*Last updated: 2026-11-01 — Phase 11A Final Taxonomy & Evaluation Integrity Audit Completed (Decision D-024 recorded; 135/135 Tests Passing)*
"""

path.write_text(text + entry + "\n", encoding="utf-8")
print("Successfully updated docs/implementation-progress.md")

