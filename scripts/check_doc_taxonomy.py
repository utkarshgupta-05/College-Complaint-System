import os

files_to_check = [
    "reports/final_evaluation.md",
    "reports/final_project_report.md",
    "reports/final_test_evaluation.md",
    "MODEL_CARD.md",
    "DATASET_CARD.md",
    "README.md"
]

for f in files_to_check:
    if os.path.exists(f):
        print(f"=== {f} ===")
        with open(f, "r", encoding="utf-8") as fp:
            for i, line in enumerate(fp):
                if any(c in line for c in ["C01", "C02", "C03", "C04", "C10", "C11"]) and any(w in line for w in ["Hostel", "Electricity", "Internet", "Mess", "Administrative", "Other", "Civil", "Electrical", "Canteen", "Power"]):
                    print(f"  Line {i+1}: {line.strip()[:100]}")

