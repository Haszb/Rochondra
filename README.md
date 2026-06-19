```markdown
# Rochondra

> Crypto whitepaper analysis pipeline — PDF ingestion, structural metrics, TOC extraction, and per-section NLP (sentiment + summarization).

---

## Stack

| Layer | Tech |
|---|---|
| API | FastAPI + Uvicorn |
| UI | Streamlit |
| PDF extraction | PyMuPDF / pymupdf4llm |
| NLP | FinBERT (sentiment) · DistilBART (summarization) |
| LLM arbitration | Ollama (Gemma) |
| Session | Starlette `SessionMiddleware` |
| Package manager | uv |

---gemma4:31b-cloud

## Prerequisites

**Ollama** must be running locally with the required models pulled and logged for access of the cloud models (by default):

```bash
ollama pull "your_model" # default model : gemma4:31b-cloud
```

Ollama must be reachable at its default address (`http://localhost:11434`) before starting the API.

---

## Installation

```bash
git clone https://github.com/your-handle/rochondra.git
cd rochondra

uv sync
```

> A `requirements.txt` is provided for reference, but `uv` is the recommended installer.  
> Do **not** mix `pip install` and `uv sync` in the same environment.

---

## Configuration

The `config.toml` at the project root is the single source of configuration:

```toml
[global]
environment      = "development"
storage_base_dir = "storage"

[api]
host = "127.0.0.1"
port = 8000

[ui]
host = "127.0.0.1"
port = 8501

[whitepaper]
pdf_subdir      = "pdfs"
markdown_subdir = "markdowns"
images_subdir   = "images"
tocs_subdir     = "tocs"
model           = "gemma4:31b-cloud"
vision_model    = "gemma4:31b-cloud"

[tokenomics]
# Reserved for future use.

[social_media]
# Reserved for future use.
```

Storage directories are created automatically on first run under `storage/`.

---

## Running

Open two terminals from the project root.

**Terminal 1 — API:**
```bash
uv run uvicorn api.main:app --reload
```

**Terminal 2 — UI:**
```bash
uv run streamlit run ui/app.py
```

The UI is then available at `http://localhost:8501`.

---

## Pipeline

```
PDF upload
    └── 01 Extract    — PDF → Markdown (+ optional image description via Ollama vision)
    └── 02 Structure  — word count, readability scores (Gunning Fog, Flesch)
    └── 03 TOC        — heading extraction: native PDF TOC → visual heuristics → LLM fallback
    └── 04 Semantic   — per-section sentiment (FinBERT) + summary (DistilBART)
```

Results are cached by UUID — re-running any step on the same document is instantaneous.

---

## Project structure

```
rochondra/
├── api/
│   ├── main.py
│   ├── routers/
│   │   └── whitepaper_router.py
│   └── schemas.py
├── core_shared/
│   └── config.py
├── modules/
│   └── whitepaper/
│       ├── extractor.py
│       ├── structural_analysis.py
│       ├── Table_of_content_extractor.py
│       └── sentiment_analysis.py
├── ui/
│   ├── app.py
│   └── pages/
│       └── whitepaper_ui.py
├── config.toml
└── requirements.txt
```

---

## Notes

- First run of the semantic analysis step will be slow — FinBERT and DistilBART are loaded into memory on import and released cleanly on shutdown.
- The CSV registry under `storage/` is a temporary persistence layer; a proper database backend is planned.
- `tokenomics` and `social_media` modules are reserved for future development.
```