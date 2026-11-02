import os
import sys
import json
import ssl
import urllib.request
from pathlib import Path

def audit_kaggle_system():
    results = {
        "kaggle_installed": False,
        "kaggle_version": None,
        "env_vars": {},
        "config_files": {},
        "urls": {},
        "download_status": {},
        "api_authenticated": False,
        "api_auth_error": None
    }
    
    # 1. Check Python module
    try:
        import kaggle
        results["kaggle_installed"] = True
        results["kaggle_version"] = getattr(kaggle, "__version__", "unknown")
    except ImportError:
        results["kaggle_installed"] = False

    # 2. Check Environment Variables
    target_env = ["KAGGLE_USERNAME", "KAGGLE_KEY", "KAGGLE_API_TOKEN", "KAGGLE_CONFIG_DIR"]
    for var in target_env:
        val = os.environ.get(var)
        results["env_vars"][var] = bool(val)  # Never expose the actual value

    # 3. Check Credential Files
    home = Path.home()
    kaggle_dir = home / ".kaggle"
    results["config_files"]["~/.kaggle_exists"] = kaggle_dir.exists()
    results["config_files"]["kaggle.json_exists"] = (kaggle_dir / "kaggle.json").exists()
    results["config_files"]["access_token_exists"] = (kaggle_dir / "access_token").exists()

    # 4. Check Dataset URLs
    datasets = [
        {
            "id": "ayushcl/college-complaint",
            "url": "https://www.kaggle.com/datasets/ayushcl/college-complaint",
            "api_url": "https://www.kaggle.com/api/v1/datasets/download/ayushcl/college-complaint",
            "target_dir": "data/external/kaggle_college_complaint"
        },
        {
            "id": "sheshanksingh/complaint",
            "url": "https://www.kaggle.com/datasets/sheshanksingh/complaint",
            "api_url": "https://www.kaggle.com/api/v1/datasets/download/sheshanksingh/complaint",
            "target_dir": "data/external/kaggle_multilingual_complaint"
        }
    ]

    ctx = ssl.create_default_context()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }

    for d in datasets:
        d_id = d["id"]
        res = {"accessible": False, "http_status": None, "reason": None}
        
        # Ensure target dir exists
        os.makedirs(d["target_dir"], exist_ok=True)
        
        # Test HTTP
        req = urllib.request.Request(d["url"], headers=headers)
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
                res["http_status"] = resp.status
                body = resp.read(1024).decode('utf-8', errors='ignore')
                if "challengepage" in body or "recaptcha" in body:
                    res["accessible"] = False
                    res["reason"] = "Kaggle Cloudflare/reCAPTCHA challenge page intercepted. Unauthenticated automated web download blocked."
                else:
                    res["accessible"] = True
                    res["reason"] = "HTTP 200 OK."
        except urllib.error.HTTPError as e:
            res["http_status"] = e.code
            res["reason"] = f"HTTPError {e.code}: {e.reason}"
        except Exception as e:
            res["reason"] = f"{type(e).__name__}: {str(e)}"
            
        results["urls"][d_id] = res

    # 5. Check Kaggle API authentication call (handling SystemExit)
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi()
        try:
            api.authenticate()
            results["api_authenticated"] = True
        except SystemExit:
            results["api_authenticated"] = False
            results["api_auth_error"] = "SystemExit: KaggleApi requires credentials (KAGGLE_API_TOKEN or ~/.kaggle/kaggle.json)."
        except Exception as e:
            results["api_authenticated"] = False
            results["api_auth_error"] = f"{type(e).__name__}: {str(e)}"
    except SystemExit:
        results["api_authenticated"] = False
        results["api_auth_error"] = "SystemExit: KaggleApi import/init requires credentials."
    except Exception as e:
        results["api_authenticated"] = False
        results["api_auth_error"] = f"{type(e).__name__}: {str(e)}"

    print("AUDIT_RESULT_START")
    print(json.dumps(results, indent=2))
    print("AUDIT_RESULT_END")

if __name__ == "__main__":
    audit_kaggle_system()
