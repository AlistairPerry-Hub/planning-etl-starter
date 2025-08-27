# Planning ETL Starter (Victoria)

This repository fetches a list of planning pages/PDFs you provide, extracts text,
normalizes it to JSON, chunks it for AI retrieval, and keeps a daily change log.

## Quick Start
1. Open `configs/sources.csv` and paste the URLs you want to monitor (one per line).
2. Run locally or in GitHub Codespaces:
   - `python -m pip install -r requirements.txt`
   - `python run_etl.py`
3. Check outputs under `data/normalized/` and `changelog.md`.
4. Push this repo to GitHub. GitHub Actions runs **daily at 07:00 Melbourne** (21:00 UTC).

Notes:
- Scanned PDFs: the Action tries OCR (`ocrmypdf` + `tesseract`).
- It only commits when there are changes.
