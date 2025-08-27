# admin_app.py
from pathlib import Path
import json, io
import pandas as pd
import streamlit as st
from datetime import datetime
from contextlib import redirect_stdout

# Local imports
from run_etl import main as run_etl_now

SOURCES_FP = Path("configs/sources.csv")
NORMALIZED_DIR = Path("data/normalized")
RAW_HTML_DIR = Path("data/raw/html")
RAW_PDF_DIR = Path("data/raw/pdf")
CHANGELOG_FP = Path("changelog.md")

st.set_page_config(page_title="Planning ETL Admin", layout="wide")

st.title("🗂️ Planning ETL Admin")

# ---------- Helpers ----------
def read_sources() -> list[str]:
    if not SOURCES_FP.exists():
        return []
    urls = []
    for line in SOURCES_FP.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line.split(",")[0].strip())
    return urls

def write_sources(urls: list[str]):
    SOURCES_FP.parent.mkdir(parents=True, exist_ok=True)
    lines = [u.strip() for u in urls if u.strip()]
    SOURCES_FP.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

def list_normalized_records():
    NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for fp in sorted(NORMALIZED_DIR.glob("*.json")):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
            rows.append({
                "filename": fp.name,
                "source_url": data.get("source_url", ""),
                "version_date": data.get("version_date", ""),
                "extracted_at": data.get("extracted_at", ""),
                "chunks": len(data.get("chunks", [])),
                "hash": data.get("hash", "")[:12],
                "path": str(fp),
            })
        except Exception:
            rows.append({
                "filename": fp.name, "source_url": "(parse error)",
                "version_date": "", "extracted_at": "", "chunks": 0, "hash": "", "path": str(fp)
            })
    return pd.DataFrame(rows)

def tail_changelog(n=50):
    if not CHANGELOG_FP.exists():
        return "(no changelog yet)"
    lines = CHANGELOG_FP.read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[-n:])

# ---------- Sidebar ----------
with st.sidebar:
    st.header("⚙️ Actions")
    if st.button("Run ETL now", type="primary", use_container_width=True):
        # Capture stdout from run_etl.py so we can display it
        buf = io.StringIO()
        with redirect_stdout(buf):
            run_etl_now()
        st.session_state["etl_log"] = buf.getvalue()
        st.success("ETL finished. See the log in the main panel.")

    st.divider()
    st.subheader("Quick links")
    st.markdown("- `configs/sources.csv` – raw list of URLs")
    st.markdown("- `data/normalized/` – AI-ready JSON")
    st.markdown("- `changelog.md` – what changed & when")

# ---------- Manage Sources ----------
st.subheader("1) Manage monitored sites")
current_urls = read_sources()
df = pd.DataFrame({"URL": current_urls}) if current_urls else pd.DataFrame({"URL": [""]})

edited = st.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    key="sources_editor",
    help="Add, edit, or remove URLs (one per row)."
)

col1, col2 = st.columns([1,1])
with col1:
    if st.button("💾 Save URLs", use_container_width=True):
        write_sources([u for u in edited["URL"].tolist() if isinstance(u, str)])
        st.success(f"Saved {len([u for u in edited['URL'].tolist() if isinstance(u, str) and u.strip()])} URL(s) to configs/sources.csv")

with col2:
    if st.button("🔄 Refresh list", use_container_width=True):
        st.rerun()

# ---------- Run log ----------
st.subheader("2) Last ETL log (this session)")
log = st.session_state.get("etl_log", "(Run the ETL to see logs here)")
st.code(log, language="bash")

# ---------- Changelog ----------
st.subheader("3) Changelog (latest 50 lines)")
st.code(tail_changelog(50), language="markdown")

# ---------- Browse Outputs ----------
st.subheader("4) Normalized outputs")
records = list_normalized_records()
if records.empty:
    st.info("No normalized JSON yet. Add URLs and run the ETL.")
else:
    st.dataframe(records.drop(columns=["path"]), use_container_width=True, height=240)

    # Preview selected file
    filenames = records["filename"].tolist()
    choice = st.selectbox("Select a file to preview", filenames)
    if choice:
        fp = NORMALIZED_DIR / choice
        data = json.loads(fp.read_text(encoding="utf-8"))
        st.write("**Source URL:**", data.get("source_url", ""))
        st.write("**Extracted at:**", data.get("extracted_at", ""))
        st.write("**Chunks:**", len(data.get("chunks", [])))
        # Show first chunk text
        chunks = data.get("chunks", [])
        if chunks:
            st.markdown("**First chunk (preview):**")
            st.text_area("text", chunks[0].get("text", "")[:4000], height=200)
        # Full JSON (collapsible)
        with st.expander("Full JSON"):
            st.json(data)
