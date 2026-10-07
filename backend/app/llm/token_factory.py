"""TokenFactoryClient: live Nebius Token Factory inference.

OpenAI-compatible chat completions at https://api.tokenfactory.nebius.com/v1.
NOT used until CROSSFIRE_LLM=tokenfactory and NEBIUS_API_KEY is set.

Model IDs: verify against `GET /v1/models` before Phase 2 — the Nemotron 3
family names below are the documented ones; override via env if they differ:
    NEBIUS_MODEL_FAST       (default: Nemotron-3-Nano-30B — fast turns)
    NEBIUS_MODEL_REASONING  (default: Nemotron-3-Ultra-550B — deep analysis)
"""
from __future__ import annotations

import os

import httpx

from ..net import egress_proxy_url, tls_ca_bundle
from .client import Completion, LLMClient

BASE_URL = "https://api.tokenfactory.nebius.com/v1"


# Verified via GET /v1/models on 2026-10-06 (IDs are case-sensitive).
DEFAULT_MODELS = {
    "fast": os.environ.get("NEBIUS_MODEL_FAST", "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B"),
    "reasoning": os.environ.get("NEBIUS_MODEL_REASONING", "nvidia/Nemotron-3-Ultra-550b-a55b"),
}


class TokenFactoryClient(LLMClient):
    backend_name = "tokenfactory"

    def __init__(self, api_key: str | None = None, base_url: str = BASE_URL,
                 timeout: float = 120.0):
        # Lazy: a missing key must not crash the app at import/boot time.
        # The clear error surfaces only when a live call is attempted, so the
        # frontend and health checks stay up while the key is being provisioned.
        self._key = api_key or os.environ.get("NEBIUS_API_KEY")
        self._base = base_url.rstrip("/")
        self._timeout = timeout
        self._http: httpx.Client | None = None

    def _ensure_client(self) -> httpx.Client:
        if not self._key:
            raise RuntimeError(
                "TokenFactoryClient needs an API key: set NEBIUS_API_KEY "
                "(claim the $25 hackathon credit with code NEBIUS-DEVPOST-GLOBAL26)."
            )
        if self._http is None:
            # trust_env=False + explicit sanitized proxy: ambient proxy env vars
            # in sandboxed runtimes can carry raw credentials that break httpx's
            # URL parser, so we encode them ourselves instead of letting httpx
            # read the environment.
            self._http = httpx.Client(
                timeout=self._timeout, trust_env=False, proxy=egress_proxy_url(),
                verify=tls_ca_bundle(),
                headers={"Authorization": f"Bearer {self._key}",
                         "Content-Type": "application/json"},
            )
        return self._http

    def resolve_model(self, alias: str) -> str:
        """Map 'fast'/'reasoning' aliases (used by agents) to concrete model IDs."""
        return DEFAULT_MODELS.get(alias, alias)

    def list_models(self) -> list[str]:
        """GET /v1/models — run once in Phase 2 to confirm model IDs."""
        http = self._ensure_client()
        r = http.get(f"{self._base}/models")
        r.raise_for_status()
        return [m["id"] for m in r.json().get("data", [])]

    def complete(self, model, messages, *, temperature=0.7, max_tokens=4000,
                 json_mode=False) -> Completion:
        http = self._ensure_client()
        model_id = self.resolve_model(model)
        payload: dict = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        fallback = False
        try:
            r = http.post(f"{self._base}/chat/completions", json=payload)
            r.raise_for_status()
        except httpx.HTTPError:
            # Graceful degradation: if the big reasoning model fails, retry
            # once on the fast model rather than killing the debate.
            fast_id = self.resolve_model("fast")
            if model_id == fast_id:
                raise
            payload["model"] = fast_id
            r = http.post(f"{self._base}/chat/completions", json=payload)
            r.raise_for_status()
            model_id = fast_id
            fallback = True
        data = r.json()
        msg = data["choices"][0]["message"]
        # Reasoning models may put the thinking in `reasoning` and leave
        # `content` null when the token budget runs out mid-reasoning; prefer
        # content, fall back to the reasoning trace rather than empty text.
        text = msg.get("content") or msg.get("reasoning") or ""
        meta = {"usage": data.get("usage", {})}
        if fallback:
            meta["model_fallback"] = True
        return Completion(
            text=text, model=model_id, backend="tokenfactory", meta=meta,
        )
