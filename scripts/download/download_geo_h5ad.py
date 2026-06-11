import os
import sys
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def download_with_resume(url, out_path, chunk_size=8192*1024, max_retries=20):
    """Download with resume support and exponential backoff retry."""
    session = requests.Session()
    retry = Retry(
        total=max_retries,
        backoff_factor=2,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"]
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=1, pool_maxsize=1)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    headers = {}
    existing_size = 0
    if os.path.exists(out_path):
        existing_size = os.path.getsize(out_path)
        headers["Range"] = f"bytes={existing_size}-"
        print(f"Resuming from {existing_size} bytes")

    mode = "ab" if existing_size > 0 else "wb"

    attempt = 0
    while attempt < max_retries:
        try:
            print(f"Attempt {attempt+1}/{max_retries}: GET {url}")
            with session.get(url, headers=headers, stream=True, timeout=(60, 300)) as r:
                r.raise_for_status()
                total = r.headers.get('content-length')
                if total:
                    total = int(total)
                    if existing_size > 0:
                        total += existing_size
                    print(f"Total size: {total} bytes ({total/1024**3:.2f} GB)")

                downloaded = existing_size
                with open(out_path, mode) as f:
                    for chunk in r.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total and downloaded % (100*1024*1024) < chunk_size:
                                pct = downloaded * 100 / total
                                print(f"  {downloaded}/{total} ({pct:.1f}%)")

                print(f"Download complete: {out_path} ({downloaded} bytes)")
                return True

        except (requests.exceptions.RequestException, requests.exceptions.ChunkedEncodingError) as e:
            attempt += 1
            wait = min(2 ** attempt, 120)
            print(f"Error: {e}")
            print(f"Retrying in {wait}s... (attempt {attempt}/{max_retries})")
            time.sleep(wait)
            # Update resume header
            if os.path.exists(out_path):
                existing_size = os.path.getsize(out_path)
                headers["Range"] = f"bytes={existing_size}-"
                mode = "ab"

    print(f"Failed after {max_retries} attempts")
    return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python download_geo_h5ad.py <url> <out_path>")
        sys.exit(1)

    url = sys.argv[1]
    out_path = sys.argv[2]
    success = download_with_resume(url, out_path)
    sys.exit(0 if success else 1)
