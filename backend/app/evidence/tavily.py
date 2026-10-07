"""Tavily web-search client for evidence grounding.

Swap with one config change:
    CROSSFIRE_TAVILY=keyless  (default) real results, no key needed (rate-limited)
    CROSSFIRE_TAVILY=mock     canned results, offline
    CROSSFIRE_TAVILY=tavily   live Tavily API with your own key (TAVILY_API_KEY),
                             higher limits + full endpoints

The live paths are the stackable "$3k Best Use of Tavily" bonus: the
fact-checker makes a real runtime Tavily call per claim.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import httpx

from ..net import egress_proxy_url, tls_ca_bundle

TAVILY_URL = "https://api.tavily.com/search"


@dataclass
class SearchResult:
    title: str
    url: str
    content: str
    score: float = 0.0


class TavilyClientBase(ABC):
    backend_name: str = "base"

    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        raise NotImplementedError


class TavilyClient(TavilyClientBase):
    """Live Tavily search API."""

    backend_name = "tavily"

    def __init__(self, api_key: str | None = None, timeout: float = 30.0):
        key = api_key or os.environ.get("TAVILY_API_KEY")
        if not key:
            raise RuntimeError(
                "TavilyClient needs an API key: set TAVILY_API_KEY "
                "(free tier at tavily.com, or via the Nebius Builders Program)."
            )
        self._key = key
        self._http = httpx.Client(
            timeout=timeout, trust_env=False, proxy=egress_proxy_url(),
            verify=tls_ca_bundle(),
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"},
        )

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        r = self._http.post(TAVILY_URL, json={
            "query": query,
            "search_depth": "basic",
            "max_results": max_results,
            "include_answer": False,
            "include_raw_content": False,
        })
        r.raise_for_status()
        out = []
        for item in r.json().get("results", [])[:max_results]:
            out.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                content=(item.get("content", "") or "")[:600],
                score=float(item.get("score", 0.0) or 0.0),
            ))
        return out


class KeylessTavilyClient(TavilyClientBase):
    """Real Tavily results with no API key (official SDK keyless mode).

    Rate-limited by Tavily; search() and extract() only. Good enough for
    the demo and development — drop in TAVILY_API_KEY for higher limits.
    """

    backend_name = "keyless"

    def __init__(self):
        from tavily import TavilyClient as _SDK
        self._sdk = _SDK()  # no args -> keyless mode

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        from tavily import TavilyKeylessLimitError
        try:
            resp = self._sdk.search(query, max_results=max_results)
        except TavilyKeylessLimitError as e:
            raise RuntimeError(
                f"Tavily keyless rate limit reached ({e}); set TAVILY_API_KEY "
                "for higher limits."
            ) from e
        out = []
        for item in (resp.get("results") or [])[:max_results]:
            out.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                content=(item.get("content", "") or "")[:600],
                score=float(item.get("score", 0.0) or 0.0),
            ))
        return out


class MockTavilyClient(TavilyClientBase):
    """Canned results so the pipeline runs offline and tests stay green."""

    backend_name = "mock"

    _CANNED = [
        ("mckinsey", SearchResult(
            title="McKinsey — The state of AI in 2025",
            url="https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai",
            content="Survey data on enterprise AI adoption rates and reported impact across functions.",
            score=0.92)),
        ("automation", SearchResult(
            title="McKinsey Global Institute — A future that works: automation",
            url="https://www.mckinsey.com/featured-insights/digital-disruption/harnessing-automation-for-a-future-that-works",
            content="Analysis of technically automatable activities by occupation; less than 5% of occupations fully automatable, ~60% with at least 30% automatable activities.",
            score=0.88)),
        ("default", SearchResult(
            title="Mock evidence corpus",
            url="https://example.com/mock-evidence",
            content="Mock mode: no live web access. Verdicts below are heuristic placeholders, not real verification.",
            score=0.5)),
    ]

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        q = query.lower()
        hits = [r for key, r in self._CANNED if key != "default" and key in q]
        if not hits:
            hits = [r for key, r in self._CANNED if key == "default"]
        return hits[:max_results]


def get_tavily_client() -> TavilyClientBase:
    backend = os.environ.get("CROSSFIRE_TAVILY", "keyless").lower()
    if backend == "keyless":
        return KeylessTavilyClient()
    if backend == "tavily":
        return TavilyClient()
    if backend == "mock":
        return MockTavilyClient()
    raise ValueError(
        f"Unknown CROSSFIRE_TAVILY backend: {backend!r} (use 'keyless', 'mock' or 'tavily')"
    )
