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


# ---------------------------------------------------------------------------
# Module configurations
# ---------------------------------------------------------------------------

class WhitepaperConfig:
    """Configuration hub for the Whitepaper module."""

    LLM_MODEL = _config_data["whitepaper"]["model"]
    LLM_MODEL_VISION = _config_data["whitepaper"]["vision_model"]


class TokenomicsConfig:
    """Configuration hub for the Tokenomics module."""

    pass


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