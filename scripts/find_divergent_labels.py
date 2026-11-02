import os

patterns = ["Civil, Water", "Electrical & Power", "IT & Network Services", "Canteen, Mess & Food"]
for root, dirs, files in os.walk("."):
    if any(x in root for x in [".git", "node_modules", ".gemini", "venv", "__pycache__"]):
        continue
    for f in files:
        path = os.path.join(root, f)
        try:
            with open(path, "r", encoding="utf-8") as fp:
                text = fp.read()
                for p in patterns:
                    if p in text:
                        print(f"Found '{p}' in {path}")
                        break
        except Exception:
            pass

