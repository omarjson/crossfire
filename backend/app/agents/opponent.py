"""Opponent agent — argues the steelmanned opposing case (fast model)."""
from __future__ import annotations

import json

from ..llm.client import LLMClient
from ..security import harden, lang_directive

PERSONAS = {
    "skeptic": "You are THE SKEPTIC. You demand evidence for everything and distrust bold claims.",
    "lawyer": "You are THE LAWYER. You cross-examine: trap contradictions, expose weak links in reasoning chains.",
    "contrarian": "You are THE CONTRARIAN. You attack premises, not conclusions — the consensus is where errors hide.",
    "economist": "You are THE ECONOMIST. Everything is a trade-off: you price costs, name losers, and trace second-order effects.",
}

SYSTEM = """[ROLE:opponent]
You are a world-class debate sparring partner. You ALWAYS argue the strongest
version of the case AGAINST the user's position (steelmanning the opposition).
Never agree with the user, never go easy — but stay substantive, never insulting.
Respond with JSON only: {{"move": "<your debate move, 3-6 sentences>", "claims": ["<factual claim 1>", ...]}}
{persona}
Difficulty: {difficulty}. Friendly spars playfully, rigorous is direct, hostile shows no mercy."""

SYSTEM = harden(SYSTEM)


def generate_move(llm: LLMClient, *, motion: str, persona: str, difficulty: str,
                  round_no: int, user_move: str, history: list[dict],
                  lang: str = "en") -> dict:
    system = SYSTEM.format(
        persona=PERSONAS.get(persona, PERSONAS["skeptic"]), difficulty=difficulty
    )
    ctx = {
        "motion": motion, "persona": persona, "difficulty": difficulty,
        "round": round_no, "user_move": user_move, "history": history[-6:],
    }
    out = llm.complete_json("fast", [
        {"role": "system", "content": system + lang_directive(lang)},
        {"role": "user", "content": json.dumps(ctx)},
    ])
    return {
        "move": out.get("move", "").strip() or "(opponent failed to respond)",
        "claims": out.get("claims", []) or [],
    }
