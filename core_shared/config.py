"""Single source of configuration for the whole project.

Values come from two places:

* ``config.toml`` — non-secret settings, committed to the repository.
* ``.env``        — secrets and per-host overrides, never committed.

Every service URL is derived from ``[global].main_url`` plus that service's
port, so relocating the project to another machine is a one-line change. When a
service does not live alongside the others (a managed database, say), set the
matching ``*_HOST`` variable in ``.env`` to override just that one.
"""

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

if sys.version_info >= (3, 11):
    import tomllib
else:
    import toml as tomllib  # type: ignore[no-redef]


# ---------------------------------------------------------------------------
# Configuration files
# ---------------------------------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent.parent
TOML_PATH = ROOT_DIR / "config.toml"

if not TOML_PATH.exists():
    raise FileNotFoundError(f"Global configuration file not found at: {TOML_PATH}")

with open(TOML_PATH, "rb") as f:
    _config_data = tomllib.load(f)

# override=False so a real environment variable always beats the .env file,
# which is what you want when deploying with env vars injected by the platform.
load_dotenv(ROOT_DIR / ".env", override=False)

_global = _config_data["global"]
_api = _config_data["api"]
_ui = _config_data["ui"]
_postgres = _config_data["postgres"]
_redis = _config_data["redis"]
_minio = _config_data["minio"]
_ollama = _config_data["ollama"]


# ---------------------------------------------------------------------------
# The single deployment knob
# ---------------------------------------------------------------------------

ENVIRONMENT = _global["environment"]

#: Scheme + host, without a port — e.g. ``http://localhost``. Change this one
#: value to point the whole project at another machine.
MAIN_URL = _global["main_url"].rstrip("/")

#: Bare hostname extracted from :data:`MAIN_URL`, for drivers that take a host
#: rather than a URL (psycopg, redis-py, minio).
MAIN_HOST = urlparse(MAIN_URL).hostname or "localhost"


def _host_for(service: str) -> str:
    """Return the host for *service*, honouring a ``<SERVICE>_HOST`` override.

    Falls back to :data:`MAIN_HOST` so that, by default, everything is assumed
    to live on the same machine.
    """
    return os.getenv(f"{service.upper()}_HOST") or MAIN_HOST


def _url_for(port: int, host: str | None = None) -> str:
    """Build a service URL the same way everywhere: ``{scheme}://{host}:{port}``."""
    scheme = urlparse(MAIN_URL).scheme or "http"
    return f"{scheme}://{host or MAIN_HOST}:{port}"


# ---------------------------------------------------------------------------
# Application services
# ---------------------------------------------------------------------------

API_PORT = int(_api["port"])
API_PREFIX = _api["prefix"]
API_HOST = _host_for("api")
API_URL = f"{_url_for(API_PORT, API_HOST)}{API_PREFIX}"

UI_PORT = int(_ui["port"])
UI_HOST = _host_for("ui")
UI_URL = _url_for(UI_PORT, UI_HOST)


# ---------------------------------------------------------------------------
# Datastores
# ---------------------------------------------------------------------------

class PostgresConfig:
    """PostgreSQL connection settings. Credentials come from ``.env``."""

    HOST = _host_for("postgres")
    PORT = int(_postgres["port"])
    DATABASE = _postgres["database"]
    DRIVER = _postgres["driver"]
    ECHO_SQL = bool(_postgres["echo_sql"])

    USER = os.getenv("POSTGRES_USER", "rochondra")
    PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

    #: SQLAlchemy DSN, assembled from the pieces above.
    URL = f"{DRIVER}://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"


class RedisConfig:
    """Redis connection settings."""

    HOST = _host_for("redis")
    PORT = int(_redis["port"])
    DB = int(_redis["db"])
    DEFAULT_TTL_SECONDS = int(_redis["default_ttl_seconds"])

    PASSWORD = os.getenv("REDIS_PASSWORD") or None

    URL = f"redis://{HOST}:{PORT}/{DB}"


class MinioConfig:
    """MinIO / S3 connection settings. Credentials come from ``.env``."""

    HOST = _host_for("minio")
    PORT = int(_minio["port"])
    CONSOLE_PORT = int(_minio["console_port"])
    SECURE = bool(_minio["secure"])

    TEMP_BUCKET = _minio["temp_bucket"]
    DOCUMENTS_BUCKET = _minio["documents_bucket"]

    ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "rochondra")
    SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "")

    #: The MinIO SDK takes ``host:port`` without a scheme; ``SECURE`` carries it.
    ENDPOINT = f"{HOST}:{PORT}"
    CONSOLE_URL = _url_for(CONSOLE_PORT, HOST)


class OllamaConfig:
    """Ollama connection settings."""

    HOST = _host_for("ollama")
    PORT = int(_ollama["port"])
    URL = _url_for(PORT, HOST)

    API_KEY = os.getenv("OLLAMA_API_KEY") or None


# ---------------------------------------------------------------------------
# Module configurations
# ---------------------------------------------------------------------------

class WhitepaperConfig:
    """Configuration hub for the Whitepaper module."""

    LLM_MODEL = _config_data["whitepaper"]["model"]
    LLM_MODEL_VISION = _config_data["whitepaper"]["vision_model"]
    SENTIMENT_MODEL = _config_data["whitepaper"]["sentiment_model"]
    SUMMARIZER_MODEL = _config_data["whitepaper"]["summarizer_model"]
    MAX_UPLOAD_BYTES = int(_config_data["whitepaper"]["max_upload_mb"]) * 1024 * 1024


class TokenomicsConfig:
    """Configuration hub for the Tokenomics module."""

    pass


# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------

#: Signing key for the Starlette session cookie. Must be set in production;
#: the development fallback is deliberately obvious.
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "dev-only-insecure-key")
