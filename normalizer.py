import re

def estimate_tokens(s: str) -> int:
    return max(1, int(len(s)/4))

def chunk_text(text: str, max_tokens: int = 700) -> list:
    max_chars = max_tokens*4
    chunks, buf, size = [], [], 0
    for para in text.split("\n\n"):
        if size + len(para) > max_chars and buf:
            chunks.append("\n\n".join(buf).strip())
            buf, size = [], 0
        buf.append(para)
        size += len(para)
    if buf:
        chunks.append("\n\n".join(buf).strip())
    return chunks

def normalize_record(url: str, title: str, text: str, fetched_at_iso: str) -> dict:
    m = re.search(r"\b(\d{2}\.\d{2})(?:-([0-9]+))?\b", text)
    clause = m.group(1) if m else None
    section = f"{m.group(1)}-{m.group(2)}" if (m and m.group(2)) else clause

    chunks = chunk_text(text, max_tokens=700)
    return {
        "id": None,
        "doc_type": "document",
        "jurisdiction": "VIC",
        "scheme": "planning",
        "clause": clause,
        "section": section,
        "title": title or "",
        "version_date": fetched_at_iso[:10],
        "source_url": url,
        "content_raw": text,
        "content_clean": text,
        "markdown": None,
        "html": None,
        "chunks": [{"chunk_id": None, "text": c, "token_estimate": estimate_tokens(c)} for c in chunks],
        "citations": [],
        "hash": None,
        "extracted_at": fetched_at_iso,
        "license": "",
        "notes": ""
    }
