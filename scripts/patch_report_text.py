"""Patch diagnostic explanation in reports/final_test_evaluation.md."""
with open("reports/final_test_evaluation.md", "r", encoding="utf-8") as f:
    text = f.read()

target = """#### Misclassification Case: `SYN-00196`
- **True Category:** `C06` (Classroom and Laboratory)
- **Predicted Category:** `C07` (Sanitation and Cleanliness)
- **Model Confidence:** `0.4052`
- **Complaint Text:**
  > *"Digital oscilloscope and function generators in Sports Complex - Indoor Badminton Court are faulty and displaying distorted signals. When approached, staff told us that spare parts have not been sanctioned yet."*
- **Operational Triage:** Routed to **Human Review** (Confidence $< 0.60$).
- **Diagnostic Reason:** 
  Multi-intent lexical competition between venue and service tokens.

#### Misclassification Case: `SYN-00326`
- **True Category:** `C06` (Classroom and Laboratory)
- **Predicted Category:** `C07` (Sanitation and Cleanliness)
- **Model Confidence:** `0.2075`
- **Complaint Text:**
  > *"Digital oscilloscope and function generators in Hostel Block A - Floor 3 are faulty and displaying distorted signals. Mid-semester exams are ongoing and this disturbance is making it very difficult to concentrate. Please fix this on priority."*
- **Operational Triage:** Routed to **Human Review** (Confidence $< 0.60$).
- **Diagnostic Reason:** 
  Multi-intent lexical competition between venue and service tokens."""

replacement = """#### Misclassification Case: `SYN-00196`
- **True Category:** `C06` (Classroom and Laboratory)
- **Predicted Category:** `C07` (Sanitation and Cleanliness)
- **Model Confidence:** `0.4052`
- **Complaint Text:**
  > *"Digital oscilloscope and function generators in Sports Complex - Indoor Badminton Court are faulty and displaying distorted signals. When approached, staff told us that spare parts have not been sanctioned yet."*
- **Operational Triage:** Routed to **Human Review** (Confidence $< 0.60$).
- **Diagnostic Reason:** 
  Lexical sparsity of laboratory apparatus unigrams (`oscilloscope`, `function generator`), combined with an anomalous synthetic venue pairing (`Sports Complex - Indoor Badminton Court`). Background tokens (`spare parts`, `approached staff`) and diffuse location weights led the model to predict C07 with low confidence ($0.4052$). Safely routed to human review.

#### Misclassification Case: `SYN-00326`
- **True Category:** `C06` (Classroom and Laboratory)
- **Predicted Category:** `C07` (Sanitation and Cleanliness)
- **Model Confidence:** `0.2075`
- **Complaint Text:**
  > *"Digital oscilloscope and function generators in Hostel Block A - Floor 3 are faulty and displaying distorted signals. Mid-semester exams are ongoing and this disturbance is making it very difficult to concentrate. Please fix this on priority."*
- **Operational Triage:** Routed to **Human Review** (Confidence $< 0.60$).
- **Diagnostic Reason:** 
  Identical technical vocabulary sparsity on `oscilloscope` combined with a residential hostel location (`Hostel Block A - Floor 3`) and exam context (`Mid-semester exams ongoing`). The classifier produced very low confidence ($0.2075$), correctly triggering the human review safety gate."""

if target in text:
    new_text = text.replace(target, replacement)
    with open("reports/final_test_evaluation.md", "w", encoding="utf-8") as f:
        f.write(new_text)
    print("Patched reports/final_test_evaluation.md successfully.")
else:
    print("Target not found. Normalizing line endings...")
    text_norm = text.replace("\r\n", "\n")
    target_norm = target.replace("\r\n", "\n")
    replacement_norm = replacement.replace("\r\n", "\n")
    if target_norm in text_norm:
        new_text = text_norm.replace(target_norm, replacement_norm)
        with open("reports/final_test_evaluation.md", "w", encoding="utf-8") as f:
            f.write(new_text)
        print("Patched reports/final_test_evaluation.md with normalized line endings.")
    else:
        print("Target still not found!")

