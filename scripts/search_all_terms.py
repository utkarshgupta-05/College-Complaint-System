import os

terms = [
    "Electrical & Power", "Civil, Water", "IT & Network", 
    "Academic & Faculty", "Classroom & Lab", "Sanitation, Cleanliness", 
    "Security, Safety", "Transport & Bus", "Canteen, Mess", 
    "Administrative & Financial", "Hostel & Housing",
    "Hostel & Accommodation", "Electricity & Water", "Internet & Network"
]

for root, dirs, files in os.walk("."):
    if any(x in root for x in [".git", "node_modules", ".gemini", "venv", "__pycache__"]):
        continue
    for f in files:
        if f.endswith((".md", ".json", ".csv", ".py", ".html")):
            path = os.path.join(root, f)
            try:
                with open(path, "r", encoding="utf-8") as fp:
                    text = fp.read()
                    matches = [t for t in terms if t in text]
                    if matches:
                        print(f"{path}: {matches}")
            except Exception:
                pass

