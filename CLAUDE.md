# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
uv sync                                 # install exactly what uv.lock pins — never mix in pip
./scripts/dev.sh                        # docker compose up --wait, then uvicorn api.main:app --reload
./scripts/dev.sh --port 8080            # extra args are forwarded to uvicorn
uv run streamlit run ui/app.py          # the UI, in a second terminal (dev.sh does not start it)
docker compose down                     # stop containers, keep data
docker compose down -v                  # wipe data; the schema is recreated on next API boot
```

There is no test suite, no linter and no formatter configured — `pyproject.toml`
declares runtime dependencies only. `test.ipynb` is a gitignored scratch
notebook, not a test.

Ollama is not containerised: it must already be running, or the configured
model must be a `*-cloud` one with `OLLAMA_API_KEY` set in `.env`.

## Architecture

A FastAPI service plus a separate Streamlit front end that talks to it over
HTTP. Four analysis stages turn an uploaded whitepaper PDF into Markdown,
readability metrics, a table of contents and per-section sentiment/summaries.
`README.md` is accurate and current for usage; this file covers what only
reading several source files would tell you.

### The three storage layers each have one job

- **MinIO** holds artifacts. `temp-bucket` while a document is staged,
  `documents-bucket` after it is saved. Every key layout lives in
  `db/object_store/whitepaper.py` and nowhere else: `pdf/{uuid}.pdf`,
  `markdown/{uuid}.md`, `images/{uuid}/…`, `toc/{uuid}.json`,
  `analysis/{uuid}.json`.
- **Redis** holds the staging registry: `metadata:{uuid}` plus one key per
  completed stage. These are written with `ttl=None` on purpose — `/finalize`
  reads `structural_analysis:{uuid}` back, so an expiry would break the save
  branch. `/finalize` is what deletes them.
- **Postgres** holds durable facts, written only by `/finalize`'s save branch.

Do not blur these roles: no recomputing a stage to work around a missing key,
no cross-reading one layer to repair another. `/finalize` is the single
temp→durable transition.

### Session-carried UUID

A UUID v4 is minted at `/extract` and stored in the Starlette session, so
`/structural_analysis`, `/toc_extraction` and `/sentiment_analysis` take no
identifier at all — `_get_current_uuid` raises 400 when the session is empty.
`/resume` binds an already-staged UUID to the session instead of re-uploading.
`/finalize` deliberately prefers the session UUID over its `uuid` query
parameter; that is intended, not a bug. The Streamlit UI keeps a
`requests.Session` in `st.session_state` so the API's session cookie survives
between calls.

`/finalize` branches on the `marked_for_deletion` flag captured at extraction
time from the `save_markdown` toggle: save upserts Postgres and moves the
artifacts to `documents-bucket`; delete removes them from `temp-bucket`. Both
drop the four Redis keys and clear the session.

### Object-store caching will hide your changes

`WhitepaperExtractor` and `SectionAnalyzer` both check for their JSON in
`temp-bucket` (`_already_processed` / `_load`) and return it rather than
recomputing. A change to TOC or sentiment logic has no visible effect on an
already-processed document until that object is deleted — delete it, or use a
fresh upload, when testing.

### Configuration

`core_shared/config.py` is the only place that reads settings. Non-secret
values come from the committed `config.toml`, secrets and per-host overrides
from the untracked `.env`. Every service URL is derived from
`[global].main_url` plus that service's port, so relocating the stack is a
one-line change; a single service can be moved with `POSTGRES_HOST`,
`REDIS_HOST`, `MINIO_HOST` or `OLLAMA_HOST`. Settings are plain classes with
attributes evaluated at import time, not Pydantic settings objects. Add new
settings there rather than reading `os.environ` at a call site.

### Ollama access

Always call through `core_shared.llm.client`, never the module-level `ollama`
helpers, which hard-code localhost. That client routes on the model *name*: a
name containing `cloud` goes to `[ollama].cloud_url` with the API key,
everything else to the local daemon. It also strips the `Authorization` header
`ollama-python` injects from the environment before talking to the local
daemon, so the cloud key never leaks to it. Only `chat` is exposed; add other
methods there, with the same routing, if a call site needs one.

### TOC extraction is a cascade

`modules/whitepaper/Table_of_content_extractor.py` (the largest file) tries the
native PDF outline, then visual heuristics over reconstructed lines (font size
relative to the detected body size, boldness, numbering, an exclusion list for
crypto addresses and URLs), then LLM arbitration that must answer in JSON, and
finally falls back to the pure-heuristic result if the LLM call or its parse
fails. Sentiment analysis then anchors each TOC title in the Markdown by fuzzy
matching (exact → `difflib` ratio → keyword overlap, threshold 0.75) and slices
sections between consecutive anchors.

### Known state, so you don't re-report it

- FinBERT and DistilBART are instantiated at module scope in
  `sentiment_analysis.py`, and the router builds `SectionAnalyzer()` at import
  time, so ~1.5 GB loads before the API serves anything — twice under
  `--reload`.
- Abandoned documents are never garbage-collected; their artifacts and
  TTL-less Redis keys stay forever.
- The Streamlit UI has no Finalize control, so documents it processes stay in
  `temp-bucket`.
- Only structural metrics reach Postgres; `fact_sentiment`, `fact_ner` and
  `fact_reference` are key-only placeholders. `tokenomics` and `social_media`
  packages are empty placeholders too.
- `storage/` and `data/` hold pre-migration artifacts; both are untracked and
  nothing in the code reads them.

## Conventions

- Blocking work in the router goes through `asyncio.to_thread`, never directly
  on the event loop.
- Every module carries module- and function-level docstrings that explain the
  *why*, often at length. Match that density; the existing comments are the
  project's documentation. Some are in French — leave them.
- Startup failures against Postgres or MinIO warn rather than crash
  (`api/main.py` lifespan), keeping the stages that don't need them usable.
