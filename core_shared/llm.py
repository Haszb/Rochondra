"""Shared Ollama access, with the endpoint chosen per model.

Ollama serves two different worlds, and which one a call belongs to is written
in the model name: a name containing ``cloud`` is one of Ollama's hosted models
and has to go to ``https://ollama.com`` with an API key, while anything else is
served by a local daemon.

They really are two endpoints rather than one endpoint with two credentials.
While the daemon is signed in through the CLI it will proxy hosted models on
your behalf, but it authenticates with its own credentials and ignores a bearer
token handed to it — sending an API key to ``localhost:11434`` returns 401. So
once the daemon is signed out, hosted models are reachable only at the cloud
URL.

Routing on the model name keeps ``[whitepaper].model`` the only thing that has
to change to move a call between the two, and lets the chat model and the
vision model sit on different endpoints if the configuration says so.
"""

import ollama

from core_shared.config import OllamaConfig


class _ModelRoutedClient:
    """Dispatches each call to whichever endpoint serves the requested model.

    Exposes only :meth:`chat`, the one method the project calls, and requires
    *model* as a keyword argument so the routing decision is always explicit.
    Anything else on :class:`ollama.Client` — ``generate``, ``embed``, ``pull``
    — is deliberately absent and raises ``AttributeError``; add it here, with
    the same routing, when a call site needs it.

    One client is built per endpoint, on first use, and reused afterwards.
    """

    def __init__(self) -> None:
        self._clients: dict[str, ollama.Client] = {}

    def _client_for(self, model: str) -> ollama.Client:
        """Return the client for *model*, creating it on first use."""
        url = OllamaConfig.CLOUD_URL if OllamaConfig.is_cloud_model(model) else OllamaConfig.URL

        if url not in self._clients:
            self._clients[url] = (
                self._build_cloud_client(model)
                if url == OllamaConfig.CLOUD_URL
                else self._build_local_client()
            )
        return self._clients[url]

    @staticmethod
    def _build_cloud_client(model: str) -> ollama.Client:
        """Build the client for Ollama's hosted models, which need the API key.

        Raises:
            RuntimeError: If no API key is configured. Without this the call
                would surface as an opaque 401.
        """
        if not OllamaConfig.API_KEY:
            raise RuntimeError(
                f"{model!r} is an Ollama cloud model, but OLLAMA_API_KEY is "
                "empty. Set it in .env, or configure a local model in "
                "config.toml under [whitepaper]."
            )
        return ollama.Client(
            host=OllamaConfig.CLOUD_URL,
            headers={"Authorization": f"Bearer {OllamaConfig.API_KEY}"},
        )

    @staticmethod
    def _build_local_client() -> ollama.Client:
        """Build the client for the local daemon, which authenticates nobody.

        The header removal is not our own key handling — it undoes the
        library's. ``ollama-python`` reads ``OLLAMA_API_KEY`` from the
        environment itself and adds an ``Authorization`` header whenever the
        caller supplied none, so passing no key is not the same as sending no
        key. Left alone, the daemon would receive the cloud credential: no harm
        on localhost, but ``main_url`` can put the daemon on another machine.
        """
        local_client = ollama.Client(host=OllamaConfig.URL)
        local_client._client.headers.pop("authorization", None)
        return local_client

    def chat(self, *, model: str, **kwargs):
        """Run a chat completion against the endpoint that serves *model*."""
        return self._client_for(model).chat(model=model, **kwargs)


client = _ModelRoutedClient()
