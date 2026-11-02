from pathlib import Path

path = Path("reports/final_test_evaluation.md")
text = path.read_text(encoding="utf-8")

# 1. Update Section 1 with Historical Evaluation Reconciliation
old_sec1 = """### Strict Evaluation Integrity Protocols
1. **Zero Retraining or Post-Hoc Tuning:** The model was loaded directly from disk without modification, retraining, or threshold re-optimization.
2. **One-Time Execution:** This evaluation was executed strictly once. No iterative adjustments or parameter sweeps were performed using test signals.
3. **Data Quarantine Verification:** MD5 checksums of `train.csv` (`e8582a04a904d25403ce33fc235a588f`), `val.csv` (`8a465d4798521dd9f67133f8d0e3bf27`), and `test.csv` (`29aa41cf0c911e498b307e16a27b270a`) verify that all dataset splits remained 100% pristine throughout development.
4. **Scope Disclosure:** All metrics reported below represent performance on the procedurally generated, synthetic campus complaint benchmark. They demonstrate statistical generalization to unseen synthetic test distributions, but do **not** constitute universal proof of real-world deployment accuracy."""

new_sec1 = """### Strict Evaluation Integrity Protocols
1. **Historical Evaluation Reconciliation:** This evaluation replicates and confirms the initial held-out test evaluation conducted during Phase 9 (`reports/final_evaluation.md`). Following the Phase 9 benchmark, external data augmentation (E11) and hybrid feature engineering (E13) were explored on validation data; neither outperformed the frozen E2 baseline. The Phase 11 evaluation serves as a deterministic re-verification that `models/e2.joblib` reproduces the exact identical 98.90% Accuracy and 0.9882 Macro-F1 without drift, degradation, or leakage.
2. **Zero Retraining or Post-Hoc Tuning:** The model was loaded directly from disk without modification, retraining, or threshold re-optimization.
3. **Zero Parameter Tuning on Test Set:** No iterative adjustments or parameter sweeps were performed using test signals.
4. **Data Quarantine Verification:** MD5 checksums of `train.csv` (`e8582a04a904d25403ce33fc235a588f`), `val.csv` (`8a465d4798521dd9f67133f8d0e3bf27`), and `test.csv` (`29aa41cf0c911e498b307e16a27b270a`) verify that all dataset splits remained 100% pristine throughout development.
5. **Scope Disclosure:** All metrics reported below represent performance on the procedurally generated, synthetic campus complaint benchmark ($N = 182$). They demonstrate statistical generalization to unseen synthetic test distributions, but do **not** constitute universal proof of real-world deployment accuracy."""

# 2. Update Section 4 with Sample Size Context and Real-World Distinction
old_sec4 = """> [!IMPORTANT]
> **Safety Guarantee Clarification:**  
> While the confidence threshold achieved 100% error recall on this test set, confidence is a statistical probability estimate, **not** a deterministic mathematical guarantee. Rare out-of-distribution complaints could potentially receive high confidence. The human review gate functions as a robust defense-in-depth mechanism, but human staff oversight remains indispensable."""

new_sec4 = """> [!IMPORTANT]
> **Sample Size Context & Operational Limits:**  
> 1. **Sample Size Sensitivity ($N=182$, $N_{\\text{errors}}=2$):** The observed 100.00% auto-routing precision (180/180) and 100.0% error recall (2/2) are sample statistics measured on a small evaluation split containing exactly 2 classification errors. With $N_{\\text{errors}}=2$, perfect recall must not be interpreted as an infallible guarantee. Confidence is a calibrated statistical estimate, not a deterministic certainty.
> 2. **Synthetic Benchmark vs. Real-World Routing Reliability:** High accuracy on synthetic English complaints does not guarantee equivalent operational routing reliability in production. Real-world college complaints frequently feature colloquial Hinglish (*"paani nahi aa raha"*, *"geyser switch sparking"*), multi-intent overlaps (e.g. electrical fault inside a dining mess), ambiguous descriptions, or misidentified venues. Production deployment strictly mandates maintaining the human-in-the-loop review queue for staff oversight."""

assert old_sec1 in text, "old_sec1 not found in text"
assert old_sec4 in text, "old_sec4 not found in text"

text = text.replace(old_sec1, new_sec1)
text = text.replace(old_sec4, new_sec4)

path.write_text(text, encoding="utf-8")
print("Successfully patched reports/final_test_evaluation.md")

