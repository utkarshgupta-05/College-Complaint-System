import urllib.request
import ssl
import json

ctx = ssl.create_default_context()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,application/json,*/*;q=0.8'
}

urls = [
    'https://www.kaggle.com/datasets/ayushcl/college-complaint',
    'https://www.kaggle.com/datasets/sheshanksingh/complaint',
    'https://www.kaggle.com/api/v1/datasets/download/ayushcl/college-complaint',
    'https://www.kaggle.com/api/v1/datasets/download/sheshanksingh/complaint'
]

for url in urls:
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            content_type = resp.headers.get('Content-Type')
            content_length = resp.headers.get('Content-Length')
            final_url = resp.geturl()
            print(f"URL: {url}")
            print(f"  Status: {resp.status}")
            print(f"  Final URL: {final_url}")
            print(f"  Content-Type: {content_type}")
            print(f"  Content-Length: {content_length}")
            body = resp.read(2048)
            print(f"  Body Preview (first 200 bytes): {body[:200]}")
    except urllib.error.HTTPError as e:
        print(f"URL: {url} -> HTTPError {e.code}: {e.reason}")
    except Exception as e:
        print(f"URL: {url} -> Error: {type(e).__name__}: {e}")

