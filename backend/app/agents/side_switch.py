"""Side-switch agent — flips and argues the USER's position, better than the
user did, then highlights where the user's own case was weak.

This is the killer demo moment: the AI doesn't just beat you, it teaches you
by outperforming you on your own side.
"""
from __future__ import annotations

import json

from ..llm.client import LLMClient
from ..security import harden, lang_directive

SYSTEM = """[ROLE:side_switch]
You just spent several rounds arguing AGAINST the user's position. Now you
switch sides: argue FOR the user's position — and do it BETTER than the user
did. Steelman their case: the strongest, most evidence-grounded version of
their argument, in 4-7 sentences. Then, in a separate note, explain exactly
where the user's own case was weak and what your version does better
(stronger evidence, tighter logic, better structure).

Respond with JSON only:
{"flipped_move": "<your stronger version of the user's case>",
 "claims": ["<factual claim 1>", "<factual claim 2>"],
 "gap_note": "<where the user's case was weak and what yours does better>"}"""

SYSTEM = harden(SYSTEM)


def flip_sides(llm: LLMClient, *, motion: str, user_moves: list[str],
               persona: str, lang: str = "en") -> dict:
    out = llm.complete_json("fast", [
        {"role": "system", "content": SYSTEM + lang_directive(lang)},
        {"role": "user", "content": json.dumps({
            "motion": motion,
            "persona_you_were": persona,
            "user_moves_so_far": user_moves,
        })},
    ])
    return {
        "flipped_move": out.get("flipped_move", "").strip()
        or "(side-switch failed to respond)",
        "claims": out.get("claims", []) or [],
        "gap_note": out.get("gap_note", "").strip(),
    }
