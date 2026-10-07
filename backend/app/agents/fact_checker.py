"""Fact-checker agent — verifies factual claims against web evidence.

Pipeline: extract claims (fast LLM) -> Tavily search per claim ->
verdicts grounded in the retrieved snippets (fast LLM).

Tavily backend swaps with CROSSFIRE_TAVILY (mock default, tavily live).
The live path is the runtime Tavily call behind the "$3k Best Use of
Tavily" bonus.
"""
from __future__ import annotations

import json

from ..evidence.tavily import TavilyClientBase, get_tavily_client
from ..llm.client import LLMClient
from ..security import harden, lang_directive

EXTRACT_SYSTEM = """[ROLE:fact_checker]
Extract the factual claims from a debate move — statements that could be
checked against real-world data (statistics, named reports, historical facts).
Skip opinions, rhetorical questions, and pure argumentation.
Respond with JSON only: {"claims": ["<claim 1>", "<claim 2>"]}"""

VERIFY_SYSTEM = """[ROLE:fact_checker]
You are given factual claims plus web evidence retrieved for each. For every
claim return a verdict grounded ONLY in the evidence shown:
- "verified": evidence directly supports the claim
- "disputed": evidence contradicts or seriously qualifies it
- "unverifiable": evidence is thin, mock/placeholder, or off-topic
Cite which sources you used by URL.
Respond with JSON only:
{"checks": [{"claim": "<claim>", "verdict": "<verified|disputed|unverifiable>",
             "note": "<one line, grounded in the evidence>",
             "sources": ["<url 1>", "<url 2>"]}]}"""

EXTRACT_SYSTEM = harden(EXTRACT_SYSTEM)
VERIFY_SYSTEM = harden(VERIFY_SYSTEM)

MAX_CLAIMS_PER_MOVE = 4


class TavilyRateLimited(RuntimeError):
    """Keyless Tavily hit its rate cap mid-debate."""


def _evidence_block(claim: str, tavily: TavilyClientBase,
                    cache: dict | None = None) -> tuple[str, list[str], bool]:
    """Returns (evidence_text, urls, degraded). Results are cached per
    normalized claim text so the same claim is never searched twice."""
    key = " ".join(claim.lower().split())
    if cache is not None and key in cache:
        return cache[key]
    degraded = False
    try:
        results = tavily.search(claim, max_results=3)
    except RuntimeError as e:
        if "rate limit" in str(e).lower():
            # Keyless cap reached: fall back to the mock corpus for this
            # claim and flag it, instead of dying mid-debate.
            from ..evidence.tavily import MockTavilyClient
            results = MockTavilyClient().search(claim, max_results=3)
            degraded = True
        else:
            results = []
    except Exception:
        results = []
    if not results:
        out: tuple[str, list[str], bool] = ("No evidence retrieved.", [], degraded)
    else:
        lines = [f"- {r.title} ({r.url}): {r.content}" for r in results]
        out = ("\n".join(lines), [r.url for r in results], degraded)
    if cache is not None:
        cache[key] = out
    return out


def check_move(llm: LLMClient, *, move: str, side: str,
               tavily: TavilyClientBase | None = None,
               cache: dict | None = None, lang: str = "en") -> dict:
    tavily = tavily or get_tavily_client()

    extracted = llm.complete_json("fast", [
        {"role": "system", "content": EXTRACT_SYSTEM + lang_directive(lang)},
        {"role": "user", "content": json.dumps({"move": move, "side": side})},
    ])
    claims = (extracted.get("claims", []) or [])[:MAX_CLAIMS_PER_MOVE]
    if not claims:
        return {"checks": [], "summary": "0 claims · 0 verified · 0 disputed · 0 unverifiable",
                "degraded": False}

    evidence: dict[str, tuple[str, list[str]]] = {}
    degraded = False
    for claim in claims:
        text, urls, deg = _evidence_block(claim, tavily, cache)
        evidence[claim] = (text, urls)
        degraded = degraded or deg

    bundle = "\n\n".join(
        f"CLAIM: {c}\nEVIDENCE:\n{evidence[c][0]}" for c in claims
    )
    out = llm.complete_json("fast", [
        {"role": "system", "content": VERIFY_SYSTEM},
        {"role": "user", "content": bundle},
    ])
    checks = out.get("checks", []) or []
    # backfill sources from retrieval when the model omits them
    for ch in checks:
        if not ch.get("sources"):
            ch["sources"] = evidence.get(ch.get("claim", ""), ("", []))[1][:2]

    v = sum(1 for c in checks if c["verdict"] == "verified")
    d = sum(1 for c in checks if c["verdict"] == "disputed")
    u = sum(1 for c in checks if c["verdict"] == "unverifiable")
    return {
        "checks": checks,
        "summary": f"{len(checks)} claims · {v} verified · {d} disputed · {u} unverifiable",
        "tavily_backend": tavily.backend_name,
        "degraded": degraded,
    }
