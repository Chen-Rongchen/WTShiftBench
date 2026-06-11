import os
import sys
import time
import socks
import socket
import urllib.request

# Configure SOCKS5 proxy
socks.set_default_proxy(socks.SOCKS5, "10.10.10.215", 7897)
socket.socket = socks.socksocket

def download_with_resume(url, out_path, chunk_size=8192*1024, max_retries=10):
    headers = {}
    existing_size = 0
    if os.path.exists(out_path):
        existing_size = os.path.getsize(out_path)
        headers["Range"] = f"bytes={existing_size}-"
        print(f"Resuming from {existing_size} bytes")

    attempt = 0
    while attempt < max_retries:
        try:
            print(f"Attempt {attempt+1}/{max_retries}")
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=300) as response:
                total = response.headers.get('Content-Length')
                if total:
                    total = int(total)
                    if existing_size > 0:
                        total += existing_size
                    print(f"Total: {total} bytes ({total/1024**3:.2f} GB)")

                mode = "ab" if existing_size > 0 else "wb"
                downloaded = existing_size
                with open(out_path, mode) as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total and downloaded % (50*1024*1024) < chunk_size:
                            pct = downloaded * 100 / total
                            print(f"  {downloaded}/{total} ({pct:.1f}%)")

                print(f"Complete: {downloaded} bytes")
                return True
        except Exception as e:
            attempt += 1
            wait = min(2 ** attempt, 60)
            print(f"Error: {e}")
            print(f"Retry in {wait}s...")
            time.sleep(wait)
            if os.path.exists(out_path):
                existing_size = os.path.getsize(out_path)
                headers["Range"] = f"bytes={existing_size}-"

    print("Failed")
    return False

if __name__ == "__main__":
    url = sys.argv[1]
    out_path = sys.argv[2]
    success = download_with_resume(url, out_path)
    sys.exit(0 if success else 1)
