# Rochondra

**Rochondra is born from an observation**
([logbook](https://medium.com/@rochondra.lab/information-asymmetry-and-conflicts-of-interest-the-ambiguous-role-of-analysts-in-the-ico-c969af990ab7)):
in an unregulated market, the whitepaper is often the only substantial document
a project publishes before it asks for money, and almost nobody reads it
properly. Not retail investors, who lack the time and the expertise, and not the
analysts they defer to, who mostly skip it and judge projects on team and
community instead. The document is not silent, though.
[Research](https://medium.com/@rochondra.lab/decoding-whitepapers-what-academic-research-reveals-about-crypto-project-quality-4e7c8f842570)
finds real signal in its length, its readability, its errors, and in the
intensity of its positive tone, which correlates negatively with how the project
later performs. Rochondra measures those signals, so that whitepapers sharing no
common format can still be compared side by side.

Concretely it is a pipeline you run yourself: give it a PDF, get back Markdown,
readability metrics, a reconstructed table of contents, and the tone and summary
of every section. It covers the Documentation pillar of a five-pillar evaluation
framework (team, technology and code, tokenomics, documentation, community). It
outputs raw measurements and a document's position within the corpus, never a
score or a rating, and it is still under active construction.

```
PDF upload
  ├── 01 Extract    PDF → Markdown, optionally describing each image with a vision model
  ├── 02 Structure  word and sentence counts, Gunning Fog, Flesch reading ease
  ├── 03 TOC        headings: native PDF outline → visual heuristics → LLM arbitration
  └── 04 Semantic   per-section sentiment (FinBERT) + summary (DistilBART)
```

A FastAPI service does the work; a Streamlit front end drives it over HTTP.
State is split across MinIO (artifacts), Redis (staging) and PostgreSQL
(durable facts), with Ollama used for the two jobs that need a language model.

| Layer | Tech |
|---|---|
| API | FastAPI + Uvicorn, Starlette `SessionMiddleware` |
| UI | Streamlit |
| PDF extraction | PyMuPDF / pymupdf4llm |
| NLP | FinBERT (sentiment) · DistilBART (summarization) |
| LLM (TOC arbitration, image description) | Ollama, local daemon or hosted |
| Object storage | MinIO: `temp-bucket`, `documents-bucket` |
| Staging state | Redis |
| Durable storage | PostgreSQL (SQLAlchemy 2 + psycopg 3) |
| Packaging | uv, Python 3.12 |

## Project documents

This README covers how to run the code. Why the project is shaped this way is
written up separately:

- **[Project brief](docs/project-brief.md)**: the problem, the approach, the
  scope, the planned outputs and the questions still open.
- **[Decision log](docs/decision-log.md)**: the decisions that shaped the
  project, each with the alternatives ruled out and the cost accepted. Where the
  code does not yet follow a decision, the entry says so.
- **Roadmap**: to follow.

## Quickstart

You need **Docker** (Postgres, Redis and MinIO run as containers) and
**[uv](https://docs.astral.sh/uv/)**. You also need **Ollama**, either a local
daemon with the configured model pulled, or an API key for a hosted one; see
[Ollama routing](#ollama-routing) for which of the two you end up using.

```bash
git clone https://github.com/Haszb/Rochondra.git
cd Rochondra

cp .env.example .env    # then fill in the secrets
uv sync                 # installs exactly what uv.lock pins
./scripts/dev.sh        # containers + API, one command
```

`dev.sh` brings the three containers up, waits until each reports healthy (the
API touches MinIO in its startup hook, so launching before then is a race), and
runs uvicorn in the foreground. Arguments are forwarded:
`./scripts/dev.sh --port 8080`.

The Streamlit UI is not part of that; run it in a second terminal:

```bash
uv run streamlit run ui/app.py
```

| Service | URL |
|---|---|
| API | <http://127.0.0.1:8000>, interactive docs at `/docs` |
| UI | <http://localhost:8501> |
| MinIO console | <http://localhost:9001> |

Ctrl-C stops the API and leaves the containers up. `docker compose down` stops
them; `docker compose down -v` also wipes their data, and the schema is
recreated on the next boot.

Two things about `uv` are worth knowing: `uv sync` installs the exact versions
pinned in `uv.lock`, and mixing `pip install` into that environment will
desynchronise it. Postgres tables are created on API startup via
`Base.metadata.create_all()`; MinIO buckets are created on first use.

## How it works

Every stage is a `POST` under `/api/whitepaper`. A document is identified by a
UUID minted at extraction time and kept in the session cookie, so the stages
after `/extract` take no identifier at all, which also means the client has to
carry the cookie (the Streamlit UI keeps a `requests.Session` for exactly this).

| Endpoint | Takes | Returns |
|---|---|---|
| `POST /extract` | `file`, `extract_images`, `save_markdown`, `project_name` | `doc_uuid`, `markdown_content` |
| `POST /structural_analysis` | `include_images_stats` | `metrics` |
| `POST /toc_extraction` | none | `toc_content` |
| `POST /sentiment_analysis` | none | `analyses`, keyed by section title |
| `POST /resume` | `?uuid=` (optional) | `available_uuids`, and binds `uuid` to the session |
| `POST /finalize` | `?uuid=` (fallback only) | `action`, plus what was persisted or deleted |

`GET /` is a health check.

### Where a document lives

Each storage layer has one role, and the boundaries are deliberate:

- **MinIO** holds artifacts: `pdf/{uuid}.pdf`, `markdown/{uuid}.md`,
  `images/{uuid}/…`, `toc/{uuid}.json`, `analysis/{uuid}.json`. They sit in
  `temp-bucket` while the document is being worked on.
- **Redis** holds the staging state: `metadata:{uuid}` plus one key per
  completed stage.
- **PostgreSQL** holds durable facts, and is written by `/finalize` alone.

`/finalize` is the transition between temporary and permanent. The
`save_markdown` toggle chosen back at `/extract` decides which way it goes:
**save** writes the Postgres rows and moves the artifacts to
`documents-bucket`, **delete** discards the staged artifacts. Either way the
document's Redis keys are dropped and the session is cleared.

Because that save branch reads the structural metrics back out of Redis, the
staging keys are written with **no TTL** on purpose. They previously inherited
the one-hour default, which meant any document finalized an hour after its
analysis, or resumed from an earlier day, failed. The cost of that choice is
that abandoned documents leave their keys and artifacts behind; reclaiming them
is left to a scheduled job that does not exist yet.

`/resume` is the way back into a document you did not finalize: it lists the
staged UUIDs, and binds one to your session so you can pick up mid-pipeline
instead of re-uploading.

### Re-running a stage

The TOC and semantic stages check the object store first and return
`toc/{uuid}.json` or `analysis/{uuid}.json` if it is already there, so
re-running them on the same document costs nothing. The flip side is that a
change to their logic has no visible effect until that object is deleted.
Structural metrics are always recomputed.

## Configuration

Settings are split in two: `config.toml` holds everything non-secret and is
committed, `.env` holds the secrets and is not. `core_shared/config.py` is the
only module that reads either.

### One knob for the whole deployment

Every service URL is derived from `[global].main_url` plus that service's port,
so moving the project to another machine is a one-line change:

```toml
[global]
main_url = "http://localhost"   # scheme + host, no port, no trailing slash
```

| Derived value | Built as |
|---|---|
| `API_URL` | `{main_url}:{api.port}{api.prefix}` |
| `UI_URL` | `{main_url}:{ui.port}` |
| `PostgresConfig.URL` | `{driver}://{user}:{password}@{host}:{postgres.port}/{database}` |
| `RedisConfig.URL` | `redis://{host}:{redis.port}/{redis.db}` |
| `MinioConfig.ENDPOINT` | `{host}:{minio.port}` |
| `OllamaConfig.URL` | `{main_url}:{ollama.port}`, the local daemon only |

When one service does not live with the others, a managed database for instance, set
`POSTGRES_HOST`, `REDIS_HOST`, `MINIO_HOST` or `OLLAMA_HOST` in `.env` to
override just that one. Everything else keeps following `main_url`.

Beyond hosts and ports, `config.toml` carries the bucket names, the Redis
default TTL, SQL echo logging, the upload size cap, and the model ids for
Ollama, FinBERT and DistilBART.

### Secrets

`.env.example` is the template; copy it to `.env` and fill it in.

| Variable | Used for |
|---|---|
| `POSTGRES_USER`, `POSTGRES_PASSWORD` | Postgres, and substituted into `docker-compose.yml` |
| `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY` | MinIO, likewise |
| `REDIS_PASSWORD` | Redis. Empty for the dev container, which has none |
| `SESSION_SECRET_KEY` | signs the session cookie |
| `OLLAMA_API_KEY` | hosted Ollama models only; see below |

The Postgres and MinIO credentials are read by both the application and
`docker-compose.yml`, so they are defined once. A real environment variable
always beats the file, which is what you want when a platform injects them.

### Ollama routing

Which endpoint an LLM call reaches is decided by the **model name**, not by a
setting of its own:

| Model name | Endpoint | Requires |
|---|---|---|
| contains `cloud`, e.g. `gemma4:31b-cloud` | `https://ollama.com` | `OLLAMA_API_KEY` |
| anything else, e.g. `qwen3.5:latest` | the local daemon | the daemon running, `ollama pull` done |

So `[whitepaper].model` and `[whitepaper].vision_model` are the only things to
change to move a job between the two, and the chat and vision jobs may sit on
different endpoints.

The two worlds genuinely do not overlap. While the local daemon is signed in
through the CLI it will proxy hosted models for you, but it authenticates with
its own credentials and ignores a bearer token. Sending an API key to
`localhost:11434` returns 401. Once the daemon is signed out, hosted models are
reachable only at the cloud URL, and only with the key.

## Layout

```
api/            FastAPI app, the six endpoints, response schemas
core_shared/    config.py (all settings) · llm.py (Ollama client, routed per model)
db/             cache/ Redis · object_store/ MinIO + key layouts · sql/ models, repositories
modules/        the analysis itself: extraction, structure, TOC, sentiment
ui/             Streamlit app and its pages
scripts/dev.sh  containers + API in one command
docs/           project brief and decision log
```

Both `db/` and `modules/` are organised by domain. Only `whitepaper` is
implemented; the `tokenomics` and `social_media` modules under `db/` are empty
placeholders reserved for later.

## History

Rochondra began as a different project: predicting the price of Bitcoin from its
own history. A data pipeline was built on the Binance API, followed by
exploratory analysis, then SimpleRNN, LSTM and GRU models tested in a multi-step
setup where each prediction feeds the next instead of being corrected by the real
value. That last choice is what made the result legible. Trained on log returns,
the models converge to a flat line at zero, which is what a network looks like
when it has learned nothing.

The conclusion was that price is an output variable, the consequence of forces
that no univariate series contains. If the timing of a market cannot be
predicted, then the choice of what to hold becomes the variable that matters,
which moves the problem from assisted trading to assisted investment. So the
work turned from modelling the output to measuring the inputs: the digital
traces a project leaves as it is built, grouped into five pillars covering team,
technology and code, tokenomics, documentation and community.

The whitepaper was implemented first, because it gathers the technical, economic
and marketing vision of a project into a single document, and because it is
costly for a weak project to fake. This repository is the result. The full
reasoning is public in the logbook:
[building a compass](https://medium.com/@rochondra.lab/building-a-compass-to-explore-the-cryptoverse-cdbc100a499e),
[a new direction](https://medium.com/@rochondra.lab/a-new-direction-89003b3017d9),
[what to expect next](https://medium.com/@rochondra.lab/quick-presentation-of-what-to-expect-next-ce1027b7ad33),
[decoding whitepapers](https://medium.com/@rochondra.lab/decoding-whitepapers-what-academic-research-reveals-about-crypto-project-quality-4e7c8f842570),
and [the role of analysts](https://medium.com/@rochondra.lab/information-asymmetry-and-conflicts-of-interest-the-ambiguous-role-of-analysts-in-the-ico-c969af990ab7).
The decisions taken since then, starting with this one, are recorded in the
[decision log](docs/decision-log.md).

## Current limitations

Points where the code lags a recorded decision are flagged as *Current gap* in
the [decision log](docs/decision-log.md). The practical ones:

- **Startup is slow.** FinBERT and DistilBART are instantiated at import time,
  about 1.5 GB, downloaded once and then cached under `~/.cache/huggingface`.
  Under `--reload` the cost is paid twice, by the reloader parent and the server
  child, and it is paid even for the stages that never touch the models. Moving
  them behind a lazy accessor is planned.
- **The UI lags the API.** It has no Finalize control, so documents processed
  through Streamlit stay staged in `temp-bucket` until finalized elsewhere, for
  instance via `/docs`.
- **Only structural metrics reach Postgres.** TOC and sentiment results live as
  JSON in the object store. `fact_sentiment`, `fact_ner` and `fact_reference`
  exist with only their keys, awaiting a fixed analysis template that will let
  whitepapers be compared on identical axes.
- **No garbage collection** for documents that are never finalized.
- **No test suite** yet.
- `storage/` and `data/` hold artifacts from before the migration to
  MinIO/Postgres/Redis. Both are untracked and nothing reads them.