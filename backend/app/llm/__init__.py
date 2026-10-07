"""Backend selector — the one-line swap.

    CROSSFIRE_LLM=mock            (default) offline canned behavior
    CROSSFIRE_LLM=tokenfactory    live Nebius (needs NEBIUS_API_KEY)
"""
from __future__ import annotations

import os

from .client import LLMClient
from .mock import MockLLMClient


def get_llm_client() -> LLMClient:
    backend = os.environ.get("CROSSFIRE_LLM", "mock").lower()
    if backend == "tokenfactory":
        from .token_factory import TokenFactoryClient

        return TokenFactoryClient()
    if backend == "mock":
        return MockLLMClient()
    raise ValueError(f"Unknown CROSSFIRE_LLM backend: {backend!r} (use 'mock' or 'tokenfactory')")
