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
| LLM (TOC arbitration, image description) | Ollama, local daemon or hosted |
| Object storage | MinIO (`temp-bucket`, `documents-bucket`) |
| Cache / staging metadata | Redis |
| Durable storage | PostgreSQL (SQLAlchemy 2 + psycopg 3) |
| Session | Starlette `SessionMiddleware` |
| Package manager | uv |

---

## Prerequisites

**Docker** — Postgres, Redis and MinIO run as containers, defined in `docker-compose.yml`.

**Ollama** serves the pipeline's two LLM jobs — table-of-contents arbitration
and image description. Which endpoint a call reaches is decided by the *model
name*, so moving a job between local and hosted is a one-line edit in
`config.toml`:

| Model name | Endpoint | Requires |
|---|---|---|
| contains `cloud` — e.g. `gemma4:31b-cloud` | `https://ollama.com` | `OLLAMA_API_KEY` in `.env` |
| anything else — e.g. `qwen3.5:latest` | the local daemon, `{main_url}:11434` | the daemon running, model pulled |

```bash
ollama pull "your_model"   # local models only
```

The two worlds do not overlap: a CLI login does not authenticate a call made to
`ollama.com`, and an API key is useless against the local daemon, which signs in
with its own credentials and answers 401 to a bearer token. `[whitepaper].model`
and `[whitepaper].vision_model` choose which world each job uses, and the two
may differ.

---

## Installation

```bash
git clone https://github.com/your-handle/rochondra.git
cd rochondra

uv sync
```

`uv sync` installs the exact versions pinned in `uv.lock`. Do **not** mix
`pip install` and `uv sync` in the same environment.

---

## Running

Everything except the UI starts with one command:

```bash
./scripts/dev.sh
```

This brings up the three containers, waits until each reports healthy, then runs
the API in the foreground. Arguments are forwarded to uvicorn
(`./scripts/dev.sh --port 8080`).

| Service | URL |
|---|---|
| API | http://127.0.0.1:8000 — interactive docs at `/docs` |
| MinIO console | http://localhost:9001 |

Ctrl-C stops the API and leaves the containers running. To stop them:

```bash
docker compose down        # keep data
docker compose down -v     # wipe data (the schema is recreated on next boot)
```

**Streamlit UI** — not started by `dev.sh`; run it in a second terminal:

```bash
uv run streamlit run ui/app.py     # http://localhost:8501
```

> The UI currently lags the API: it has no Finalize step, so documents it
> processes stay staged in `temp-bucket` until finalized elsewhere (e.g. via
> `/docs`).

---

## Configuration

Configuration is split in two: `config.toml` holds everything non-secret and is
committed; `.env` holds secrets and is not. Copy `.env.example` to `.env` to get
started.

### The single deployment knob

Every service URL is derived from `[global].main_url` plus that service's port,
so pointing the project at another machine is a one-line change:

```toml
[global]
main_url = "http://localhost"   # scheme + host, no port
```

| Derived value | Built as |
|---|---|
| `API_URL` | `{main_url}:{api.port}{api.prefix}` |
| `UI_URL` | `{main_url}:{ui.port}` |
| `PostgresConfig.URL` | `{driver}://{user}:{password}@{host}:{postgres.port}/{database}` |
| `RedisConfig.URL` | `redis://{host}:{redis.port}/{redis.db}` |
| `MinioConfig.ENDPOINT` | `{host}:{minio.port}` |
| `OllamaConfig.URL` | `{main_url}:{ollama.port}` — the local daemon; hosted models use `[ollama].cloud_url` instead |

When one service does not live with the others — a managed database, say — set
the matching `POSTGRES_HOST`, `REDIS_HOST`, `MINIO_HOST` or `OLLAMA_HOST` in
`.env` to override just that one. Everything else keeps following `main_url`.

### config.toml

Sections: `[global]`, `[api]`, `[ui]`, `[postgres]`, `[redis]`, `[minio]`,
`[ollama]`, `[whitepaper]`. Beyond hosts and ports this covers the bucket names,
the Redis default TTL, SQL echo logging, the upload size cap, Ollama's cloud
URL, and the model ids for the Ollama chat and vision jobs, FinBERT and
DistilBART.

### .env

```ini
POSTGRES_USER=          MINIO_ACCESS_KEY=       SESSION_SECRET_KEY=
POSTGRES_PASSWORD=      MINIO_SECRET_KEY=       REDIS_PASSWORD=
                                                OLLAMA_API_KEY=
```

`OLLAMA_API_KEY` is needed only once a model whose name contains `cloud` is
configured; purely local setups can leave it empty.
`docker-compose.yml` substitutes the Postgres and MinIO credentials from this
same file, so they are defined once. A real environment variable always wins
over the file, which is what you want when a deployment platform injects them.

Postgres tables are created automatically on API startup via
`Base.metadata.create_all()` in the FastAPI `lifespan` hook. MinIO buckets are
created on first use.

---

## Pipeline

```
PDF upload
    └── 01 Extract    — PDF → Markdown (+ optional image description via Ollama vision)
    └── 02 Structure  — word count, readability scores (Gunning Fog, Flesch)
    └── 03 TOC        — heading extraction: native PDF TOC → visual heuristics → LLM fallback
    └── 04 Semantic   — per-section sentiment (FinBERT) + summary (DistilBART)
```

Each stage is a `POST` under `/api/whitepaper`. A document is identified by a
UUID minted at extraction time and held in the session, so later stages take no
identifier. Intermediate results are staged in `temp-bucket` and mirrored into
Redis. The TOC and semantic stages return their stored JSON rather than
recomputing when `toc/{uuid}.json` or `analysis/{uuid}.json` already exists, so
re-running them on the same document is instantaneous — delete that object to
force a fresh run. Structural metrics are always recomputed.

Two endpoints manage a document's lifecycle:

- **`/resume`** — lists staged UUIDs; with `?uuid=` binds one to the session,
  skipping a fresh upload.
- **`/finalize`** — closes the document. The `save_markdown` toggle chosen at
  extraction time decides the branch: **save** writes rows to Postgres and moves
  artifacts to `documents-bucket`; **delete** discards the staged artifacts.
  Both clear the document's Redis keys and the session.

Until a document is finalized, its artifacts and all four of its uuid-scoped
Redis keys stay in place. Those keys are written without a TTL deliberately:
`/finalize`'s save branch reads the structural metrics back out of Redis, so an
expiry would make any document finalized more than an hour after its analysis —
or resumed from an earlier day — fail. Reclaiming what abandoned documents leave
behind is left to a future scheduled job; there is no garbage collection today.

---

## Project structure

```
rochondra/
├── api/
│   ├── main.py                 app, lifespan, session middleware, custom OpenAPI
│   ├── routers/
│   │   └── whitepaper_router.py
│   └── schemas.py
├── core_shared/
│   ├── config.py               config.toml + .env -> all URLs and settings
│   └── llm.py                  Ollama client, routed per model name
├── db/
│   ├── cache/client.py         Redis helpers
│   ├── object_store/           MinIO client + per-domain helpers
│   │   ├── client.py
│   │   └── whitepaper.py
│   └── sql/                    SQLAlchemy engine, models, repositories
│       ├── base.py
│       └── whitepaper/
│           ├── models.py
│           └── repository.py
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
├── scripts/
│   └── dev.sh                  containers + API in one command
├── docker-compose.yml          postgres · redis · minio
├── config.toml                 non-secret settings (committed)
└── .env                        secrets (not committed; see .env.example)
```

---

## Notes

- The first API start is slow: FinBERT and DistilBART are loaded at import time
  (~1.5 GB), downloaded once and then cached under `~/.cache/huggingface`. Under
  `--reload` the cost is paid twice, by the reloader parent and by the server
  child, and it is paid even for the stages that never touch the models.
- Only structural metrics reach Postgres today. TOC and sentiment results are
  stored as JSON in the object store; `fact_sentiment`, `fact_ner` and
  `fact_reference` are placeholder tables whose columns are still to be defined.
- The `storage/` directory holds legacy artifacts from before the migration to
  MinIO/Postgres/Redis. Nothing reads or writes it any more.
- `tokenomics` and `social_media` are reserved for future development.
