"""Judge agent — impartial end-of-debate scorecard + report card (reasoning model)."""
from __future__ import annotations

import json

from ..llm.client import LLMClient
from ..security import harden, lang_directive

SYSTEM = """[ROLE:judge]
You are an impartial debate judge. Given the full round history (scores,
fallacies, evidence hygiene per round), you produce:
1. A round-by-round scorecard with a one-line note per round.
2. Totals and a winner ("user", "opponent", or "draw").
3. A report card for the USER: fallacy profile (counts by type), evidence
   hygiene ratio, strongest/weakest round, and up to 3 concrete tips.
Respond with JSON only:
{"rounds": [{"round": 1, "user_score": 0, "opponent_score": 0, "note": ""}],
 "user_total": 0, "opponent_total": 0, "winner": "user|opponent|draw",
 "summary": "<one paragraph>",
 "report_card": {"fallacy_profile": {"strawman": 0}, "evidence_hygiene": 0.0,
                 "strongest_round": 1, "weakest_round": 1, "tips": ["..."]}}"""

SYSTEM = harden(SYSTEM)


def judge_debate(llm: LLMClient, *, motion: str, persona: str,
                 rounds: list[dict], lang: str = "en") -> dict:
    out = llm.complete_json("reasoning", [
        {"role": "system", "content": SYSTEM + lang_directive(lang)},
        {"role": "user", "content": json.dumps(
            {"motion": motion, "persona": persona, "rounds": rounds})},
    ])
    rc = out.get("report_card", {}) or {}
    return {
        "rounds": out.get("rounds", []) or [],
        "user_total": out.get("user_total", 0),
        "opponent_total": out.get("opponent_total", 0),
        "winner": out.get("winner", "draw"),
        "summary": out.get("summary", ""),
        "report_card": {
            "fallacy_profile": rc.get("fallacy_profile", {}) or {},
            "evidence_hygiene": rc.get("evidence_hygiene", 1.0),
            "strongest_round": rc.get("strongest_round"),
            "weakest_round": rc.get("weakest_round"),
            "tips": rc.get("tips", []) or [],
        },
    }
