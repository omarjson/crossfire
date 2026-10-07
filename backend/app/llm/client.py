"""LLM client abstraction.

Swap between backends with one config change:
    CROSSFIRE_LLM=mock            # offline canned behavior (default)
    CROSSFIRE_LLM=tokenfactory    # live Nebius Token Factory (needs NEBIUS_API_KEY)

All agents talk to `LLMClient.complete()` and never to a concrete backend.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Completion:
    text: str
    model: str
    backend: str
    meta: dict[str, Any] = field(default_factory=dict)


class LLMClient(ABC):
    """Minimal chat-completions interface every agent uses."""

    backend_name: str = "base"

    @abstractmethod
    def complete(
        self,
        model: str,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        json_mode: bool = False,
    ) -> Completion:
        """Run a chat completion. `messages` = [{"role": ..., "content": ...}]."""
        raise NotImplementedError

    def complete_json(
        self,
        model: str,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ) -> dict[str, Any]:
        """Completion parsed as JSON. Returns {} on parse failure."""
        comp = self.complete(
            model, messages, temperature=temperature, max_tokens=max_tokens, json_mode=True
        )
        text = comp.text.strip()
        # tolerate code fences
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
