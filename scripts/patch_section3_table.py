"""Patch Section 3 of reports/final_test_evaluation.md to match classification report."""
with open("reports/final_test_evaluation.md", "r", encoding="utf-8") as f:
    text = f.read()

target = """| Code | Category Name | Support | Precision | Recall | F1 Score | Generalization Note |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **C01** | Hostel and Accommodation | 19 | 0.9500 | 1.0000 | **0.9744** | 1 FP from C07 residential corridor issue |
| **C02** | Electricity and Water | 19 | 0.9500 | 1.0000 | **0.9744** | 1 FP from C06 lab electrical surge issue |
| **C03** | Internet and Network | 16 | 1.0000 | 1.0000 | **1.0000** | Perfect 100% precision & recall |
| **C04** | Mess and Food | 18 | 1.0000 | 1.0000 | **1.0000** | Perfect 100% precision & recall |
| **C05** | Academic and Examination | 18 | 1.0000 | 1.0000 | **1.0000** | Perfect 100% precision & recall |
| **C06** | Classroom and Laboratory | 15 | 1.0000 | 0.9333 | **0.9655** | 1 FN (missed surge complaint $\\to$ C02) |
| **C07** | Sanitation and Cleanliness | 16 | 1.0000 | 0.9375 | **0.9677** | 1 FN (missed hostel corridor $\\to$ C01) |
| **C08** | Campus Safety | 16 | 1.0000 | 1.0000 | **1.0000** | Perfect 100% precision & recall |
| **C09** | Transportation | 15 | 1.0000 | 1.0000 | **1.0000** | Perfect 100% precision & recall |
| **C10** | Administrative Services | 15 | 1.0000 | 1.0000 | **1.0000** | Perfect 100% precision & recall |
| **C11** | Other / Unclassified | 15 | 1.0000 | 1.0000 | **1.0000** | Perfect 100% precision & recall |
| **Total / Macro** | — | **182** | **0.9892** | **0.9885** | **0.9882** | **9 out of 11 categories at 1.0000 F1** |"""

replacement = """| Code | Category Name | Support | Precision | Recall | F1 Score | Generalization Note |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **C01** | Hostel and Accommodation | 19 | 1.0000 | 1.0000 | **1.0000** | Perfect 100% precision & recall |
| **C02** | Electricity and Water | 19 | 1.0000 | 1.0000 | **1.0000** | Perfect 100% precision & recall |
| **C03** | Internet and Network | 16 | 1.0000 | 1.0000 | **1.0000** | Perfect 100% precision & recall |
| **C04** | Mess and Food | 18 | 1.0000 | 1.0000 | **1.0000** | Perfect 100% precision & recall |
| **C05** | Academic and Examination | 18 | 1.0000 | 1.0000 | **1.0000** | Perfect 100% precision & recall |
| **C06** | Classroom and Laboratory | 15 | 1.0000 | 0.8667 | **0.9286** | 2 FNs (oscilloscope apparatus $\\to$ C07) |
| **C07** | Sanitation and Cleanliness | 16 | 0.8889 | 1.0000 | **0.9412** | 2 FPs from C06 apparatus complaints |
| **C08** | Campus Safety | 16 | 1.0000 | 1.0000 | **1.0000** | Perfect 100% precision & recall |
| **C09** | Transportation | 15 | 1.0000 | 1.0000 | **1.0000** | Perfect 100% precision & recall |
| **C10** | Administrative Services | 15 | 1.0000 | 1.0000 | **1.0000** | Perfect 100% precision & recall |
| **C11** | Other / Unclassified | 15 | 1.0000 | 1.0000 | **1.0000** | Perfect 100% precision & recall |
| **Total / Macro** | — | **182** | **0.9899** | **0.9879** | **0.9882** | **9 out of 11 categories at 1.0000 F1** |"""

text_norm = text.replace("\r\n", "\n")
target_norm = target.replace("\r\n", "\n")
replacement_norm = replacement.replace("\r\n", "\n")

if target_norm in text_norm:
    new_text = text_norm.replace(target_norm, replacement_norm)
    with open("reports/final_test_evaluation.md", "w", encoding="utf-8") as f:
        f.write(new_text)
    print("Replaced successfully.")
else:
    print("Target not found!")

