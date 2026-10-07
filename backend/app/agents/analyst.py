"""Analyst agent — scores moves and detects fallacies (reasoning model)."""
from __future__ import annotations

import json

from ..llm.client import LLMClient
from ..security import harden, lang_directive

SYSTEM = """[ROLE:analyst]
You are a logic analyst and debate referee. Given a debate move, you:
1. Detect logical fallacies (strawman, ad hominem, false dilemma, appeal to
   authority, bandwagon, slippery slope, begging the question).
2. Score the move 1-10 with a transparent rubric.
Respond with JSON only:
{"fallacies": [{"type": "<snake_case>", "explanation": "<one line>", "fix": "<one line>"}],
 "score": <float>, "score_reason": "<why, referencing the rubric>",
 "strongest_point": "<quote or paraphrase>", "weakest_point": "<what to fix>"}"""

SYSTEM = harden(SYSTEM)


def analyze_move(llm: LLMClient, *, move: str, side: str, motion: str,
                   lang: str = "en") -> dict:
    out = llm.complete_json("reasoning", [
        {"role": "system", "content": SYSTEM + lang_directive(lang)},
        {"role": "user", "content": json.dumps({"move": move, "side": side, "motion": motion})},
    ])
    return {
        "fallacies": out.get("fallacies", []) or [],
        "score": float(out.get("score", 6.0) or 6.0),
        "score_reason": out.get("score_reason", ""),
        "strongest_point": out.get("strongest_point", ""),
        "weakest_point": out.get("weakest_point", ""),
    }
