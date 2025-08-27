from pathlib import Path
from utils import now_iso, sha256_text, safe_id_from_url, ensure_dirs, is_pdf_response, write_changelog_line, run_cmd
from extractor import fetch_url, extract_text_html, extract_text_pdf
from normalizer import normalize_record
import json

def read_sources(fp: Path) -> list[str]:
    urls = []
    for line in fp.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line.split(",")[0].strip())
    return urls

def save_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    ensure_dirs()
    sources_fp = Path("configs/sources.csv")
    if not sources_fp.exists():
        raise SystemExit("configs/sources.csv not found. Please create it and add URLs.")
    urls = read_sources(sources_fp)
    if not urls:
        print("No URLs found in configs/sources.csv")
        return

    for url in urls:
        print(f"Processing: {url}")
        fetched_at = now_iso()
        resp = fetch_url(url)
        title = ""
        text = ""

        if is_pdf_response(resp):
            sid = safe_id_from_url(url)
            raw_pdf = Path(f"data/raw/pdf/{sid}.pdf")
            raw_pdf.write_bytes(resp.content)
            text = extract_text_pdf(raw_pdf)
            if len(text) < 400:
                print("PDF text appears short; attempting OCR pass...")
                ocr_pdf = raw_pdf.with_suffix(".ocr.pdf")
                code, out, err = run_cmd(["ocrmypdf", "--skip-text", str(raw_pdf), str(ocr_pdf)])
                if code == 0 and ocr_pdf.exists():
                    text = extract_text_pdf(ocr_pdf)
                else:
                    print("OCR not available or failed; continuing without OCR.")
        else:
            sid = safe_id_from_url(url)
            raw_html = Path(f"data/raw/html/{sid}.html")
            raw_html.write_bytes(resp.content)
            text = extract_text_html(resp.text)
            try:
                tstart = resp.text.lower().find("<title>")
                tend = resp.text.lower().find("</title>")
                if tstart != -1 and tend != -1 and tend > tstart:
                    title = resp.text[tstart+7:tend].strip()
            except Exception:
                pass

        if not text.strip():
            print(f"Warning: extracted empty text for {url}")
            continue

        norm = normalize_record(url, title, text, fetched_at)
        norm["id"] = f"{sid}-{fetched_at[:10]}"
        norm["hash"] = sha256_text(norm["content_clean"])
        for i, ch in enumerate(norm["chunks"], 1):
            ch["chunk_id"] = f"{sid}-{i:03d}"

        current_fp = Path(f"data/normalized/{sid}.json")
        previous_hash = None
        if current_fp.exists():
            try:
                prev = json.loads(current_fp.read_text(encoding="utf-8"))
                previous_hash = prev.get("hash")
            except Exception:
                pass

        if previous_hash != norm["hash"]:
            save_json(current_fp, norm)
            write_changelog_line(f"Updated: {url}")
        else:
            print("No change detected.")

    print("Done.")

if __name__ == "__main__":
    main()
