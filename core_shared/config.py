import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import toml as tomllib  # type: ignore[no-redef]


# ---------------------------------------------------------------------------
# Configuration file
# ---------------------------------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent.parent
TOML_PATH = ROOT_DIR / "config.toml"

if not TOML_PATH.exists():
    raise FileNotFoundError(f"Global configuration file not found at: {TOML_PATH}")

with open(TOML_PATH, "rb") as f:
    _config_data = tomllib.load(f)

STORAGE_ROOT = ROOT_DIR / _config_data["global"]["storage_base_dir"]


# ---------------------------------------------------------------------------
# Module configurations
# ---------------------------------------------------------------------------

class WhitepaperConfig:
    """Configuration hub for the Whitepaper module."""

    _wp = _config_data["whitepaper"]

    PDF_DIR = STORAGE_ROOT / _wp["pdf_subdir"]
    MD_DIR = STORAGE_ROOT / _wp["markdown_subdir"]
    IMG_DIR = STORAGE_ROOT / _wp["images_subdir"]
    REGISTRY_PATH = STORAGE_ROOT / "index_registry.csv"
    TOCS_DIR = STORAGE_ROOT / _wp["tocs_subdir"]
    ANALYSIS_DIR: Path = STORAGE_ROOT / "analyses"
    LLM_MODEL = _config_data["whitepaper"]["model"]
    LLM_MODEL_VISION = _config_data["whitepaper"]["vision_model"]


class TokenomicsConfig:
    """Configuration hub for the Tokenomics module."""

    pass


# ---------------------------------------------------------------------------
# Storage initialisation
# ---------------------------------------------------------------------------

def init_storage_directories() -> None:
    """Create all storage directories if they do not already exist."""
    directories = [
        WhitepaperConfig.PDF_DIR,
        WhitepaperConfig.MD_DIR,
        WhitepaperConfig.IMG_DIR,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Network
# ---------------------------------------------------------------------------

_api = _config_data["api"]
_ui = _config_data["ui"]

API_HOST = _api["host"]
API_PORT = int(_api["port"])
API_URL = f"http://{API_HOST}:{API_PORT}/api"

UI_HOST = _ui["host"]
UI_PORT = int(_ui["port"])