from pathlib import Path
import requests, fitz, trafilatura
from bs4 import BeautifulSoup

def fetch_url(url: str, timeout: int = 60) -> requests.Response:
    headers = {"User-Agent":"Mozilla/5.0 (compatible; planning-etl/1.0)"}
    resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
    resp.raise_for_status()
    return resp

def extract_text_html(html: str) -> str:
    extracted = trafilatura.extract(html, include_tables=False, include_formatting=True) or ""
    if extracted.strip():
        return extracted.strip()
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script","style","noscript"]):
        tag.decompose()
    text = " ".join(soup.stripped_strings)
    return text.strip()

def extract_text_pdf(path: Path) -> str:
    doc = fitz.open(str(path))
    parts = []
    for page in doc:
        parts.append(page.get_text("text"))
    return "\n".join(parts).strip()
