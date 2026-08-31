"""Shared Ollama client, configured from ``config.toml`` and ``.env``.

The ``ollama`` package defaults to ``http://localhost:11434`` when used through
its module-level helpers, which makes the host impossible to configure. Going
through this client instead means the host follows ``main_url`` like every
other service, and an API key can be supplied without touching call sites.
"""

import ollama

from core_shared.config import OllamaConfig

_headers = (
    {"Authorization": f"Bearer {OllamaConfig.API_KEY}"} if OllamaConfig.API_KEY else {}
)

client = ollama.Client(host=OllamaConfig.URL, headers=_headers)
