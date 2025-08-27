import hashlib, subprocess
from datetime import datetime, timezone
from urllib.parse import urlparse
from pathlib import Path
from typing import Tuple

def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def safe_id_from_url(url: str) -> str:
    p = urlparse(url)
    safe = (p.netloc + p.path).strip("/").replace("/", "_").replace(".", "_")
    if not safe:
        import re as _re
        safe = _re.sub(r'[^a-zA-Z0-9]+', '_', url)[:50]
    return safe

def ensure_dirs():
    Path("data/raw/html").mkdir(parents=True, exist_ok=True)
    Path("data/raw/pdf").mkdir(parents=True, exist_ok=True)
    Path("data/normalized").mkdir(parents=True, exist_ok=True)

def is_pdf_response(resp) -> bool:
    ctype = resp.headers.get("Content-Type", "").lower()
    return "pdf" in ctype or resp.url.lower().endswith(".pdf")

def write_changelog_line(msg: str):
    Path("changelog.md").touch(exist_ok=True)
    with open("changelog.md", "a", encoding="utf-8") as f:
        f.write(f"- {now_iso()} — {msg}\n")

def run_cmd(cmd:list) -> Tuple[int,str,str]:
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        return p.returncode, p.stdout, p.stderr
    except Exception as e:
        return 1, "", str(e)
