"""MockLLMClient: offline, deterministic debate behavior.

Dispatches on a [ROLE:...] marker in the system prompt. The user message is
expected to carry a JSON context blob (each agent documents its schema).
Returns JSON text the agents parse via `complete_json`.
"""
from __future__ import annotations

import json
import random
import re
from typing import Any

from .client import Completion, LLMClient

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "be",
    "been", "being", "to", "of", "in", "on", "for", "with", "as", "by",
    "at", "from", "that", "this", "it", "its", "they", "them", "their",
    "you", "your", "we", "our", "i", "my", "me", "he", "she", "his",
    "her", "not", "no", "yes", "if", "then", "than", "so", "such",
    "will", "would", "can", "could", "should", "just", "very", "more",
    "most", "all", "any", "some", "do", "does", "did", "have", "has",
    "had", "about", "into", "over", "after", "before", "because", "what",
    "which", "who", "whom", "when", "where", "why", "how",
}

FALLACIES: list[dict[str, Any]] = [
    {
        "type": "strawman",
        "patterns": [
            r"\bso you'?re saying\b",
            r"\bbasically,? you'?re (saying|claiming|arguing)\b",
            r"\byou (just )?think (all|every)\b",
        ],
        "explanation": "Strawman: you restated the other side's position in a weaker, distorted form instead of engaging with what was actually said.",
        "fix": "Quote the actual claim back, then attack that — steelman it first, then dismantle the strong version.",
    },
    {
        "type": "ad_hominem",
        "patterns": [
            r"\b(idiot|idiots|stupid|dumb|moron|morons|clueless|ignorant)\b",
            r"\bpeople like you\b",
        ],
        "explanation": "Ad hominem: you attacked the person instead of the argument. Even if they're wrong about everything else, the claim stands or falls on its own merits.",
        "fix": "Drop the personal jab and name the specific premise you dispute and why.",
    },
    {
        "type": "false_dilemma",
        "patterns": [
            r"\beither\b.{0,80}\bor\b",
            r"\bno other choice\b",
            r"\bonly two options\b",
        ],
        "explanation": "False dilemma: you presented two options as if they're the only ones, hiding the middle ground.",
        "fix": "Name a third option explicitly — regulation, gradual adoption, hybrid approaches — then argue why your preferred one still wins.",
    },
    {
        "type": "appeal_to_authority",
        "patterns": [
            r"\bexperts say\b",
            r"\bscientists (say|agree)\b",
            r"\bstudies show\b",
        ],
        "explanation": "Appeal to unnamed authority: 'experts say' without naming who or citing what. Authority without evidence is just a rumor with a suit on.",
        "fix": "Name the expert or study, or drop the appeal and argue from evidence directly.",
    },
    {
        "type": "bandwagon",
        "patterns": [
            r"\beveryone (knows|agrees|thinks|understands)\b",
            r"\bit'?s (just )?common sense\b",
        ],
        "explanation": "Bandwagon: popularity isn't proof. Everyone once 'knew' the sun orbited the earth.",
        "fix": "Replace the crowd with a reason — why is it true, not how many believe it?",
    },
]

TONE = {
    "friendly": {"open": "Fair point —", "jab": "though I'd push back gently:"},
    "rigorous": {"open": "Let's test that.", "jab": "Here's the problem:"},
    "hostile": {"open": "That won't survive contact with scrutiny.", "jab": "Let me dismantle it:"},
}

OPENERS = {
    "skeptic": [
        "{open} Your claim about {motion_short} is bold. {jab} extraordinary claims need evidence, and so far I see assertion, not proof. What would you accept as a falsifying test of your own position?",
        "{open} Before we go further: define your terms. What exactly counts as '{kw1}' here? Vague claims about {motion_short} collapse the moment you pin them down.",
    ],
    "lawyer": [
        "{open} Let's examine what your position on {motion_short} actually commits you to. If {kw1} is true as you claim, then you must also accept its logical consequences — including the ones you haven't mentioned. Are you prepared to defend those too?",
        "{open} You assert {kw1} leads to your conclusion about {motion_short}. Walk me through the chain, link by link. One weak link breaks the whole case — and I intend to find it.",
    ],
    "contrarian": [
        "{open} Everyone assumes your take on {motion_short} is obviously right. {jab} the consensus is usually where the interesting errors hide. Your premise about {kw1} — why should I grant it? What if it's backwards?",
        "{open} Let me attack the foundation, not the paint. Your argument about {motion_short} rests on {kw1} being true and {kw2} mattering. I dispute both. Defend the premises before the conclusion.",
    ],
    "economist": [
        "{open} Everything is a trade-off. Your position on {motion_short} names the benefits of {kw1} — now price the costs. Who pays, how much, and why is it worth it?",
        "{open} Consider incentives. If you're right about {motion_short}, who benefits from {kw1} and who gets hurt? Arguments that ignore the losers are marketing, not reasoning.",
    ],
}

REBUTTALS = {
    "skeptic": [
        "{open} You mention {kw1}, but that's an anecdote wearing a lab coat. {jab} one vivid example proves nothing about {motion_short} in general. Show me the base rate.",
        "{open} '{kw2}' is doing a lot of heavy lifting in that move. {jab} define it precisely, or your argument about {motion_short} is built on fog.",
    ],
    "lawyer": [
        "{open} You just conceded more than you realize. If {kw1} is as you describe, then your earlier claim about {motion_short} contradicts it. Which one are you abandoning?",
        "{open} Let's hold that statement up to the light: '{kw2}'. {jab} under cross-examination, does it mean what you need it to mean, or only what you said?",
    ],
    "contrarian": [
        "{open} You're polishing the conclusion while the premises rot. {jab} {kw1} doesn't imply what you think it implies about {motion_short} — correlation dressed as causation.",
        "{open} Flip it: what evidence would change your mind about {motion_short}? If the answer is 'nothing,' you're not reasoning about {kw1} — you're preaching.",
    ],
    "economist": [
        "{open} You priced the benefits of {kw1} at zero cost. {jab} nothing is free — apply your own logic about {motion_short} to the downside case and tell me the net.",
        "{open} Second-order effects, please. If {kw1} happens as you say, what happens next? And after that? Arguments about {motion_short} that stop at step one are incomplete.",
    ],
}

TIPS = {
    "strawman": "Steel-man before you attack: restate the strongest version of the opposing case, then dismantle that.",
    "ad_hominem": "Argue against claims, not people — your strongest moves never needed the insult.",
    "false_dilemma": "Always name the third option explicitly before choosing between two.",
    "appeal_to_authority": "Cite the study or drop the appeal — argue from evidence, not from lab coats.",
    "bandwagon": "Replace 'everyone knows' with one concrete reason.",
}


def keywords(text: str, n: int = 3) -> list[str]:
    words = re.findall(r"[a-zA-Z]{4,}", text.lower())
    freq: dict[str, int] = {}
    for w in words:
        if w not in STOPWORDS:
            freq[w] = freq.get(w, 0) + 1
    ranked = sorted(freq, key=lambda w: (-freq[w], w))
    out = ranked[:n]
    while len(out) < n:
        out.append("the claim")
    return out


def shorten_motion(motion: str, n: int = 8) -> str:
    words = motion.split()
    s = " ".join(words[:n])
    return s + ("…" if len(words) > n else "")


def detect_fallacies(text: str) -> list[dict[str, str]]:
    found = []
    for f in FALLACIES:
        for pat in f["patterns"]:
            if re.search(pat, text, re.IGNORECASE):
                found.append(
                    {"type": f["type"], "explanation": f["explanation"], "fix": f["fix"]}
                )
                break
    return found


def score_move(text: str, fallacy_count: int) -> tuple[float, str]:
    words = len(text.split())
    score = 6.0 + min(words / 60.0, 2.0)
    evidence_words = ("because", "for example", "for instance", "data", "study",
                      "research", "evidence", "specifically")
    if any(w in text.lower() for w in evidence_words):
        score += 0.5
    score -= 1.5 * fallacy_count
    score = max(1.0, min(10.0, score))
    score = round(score, 1)
    reasons = []
    if words >= 60:
        reasons.append("substantive length")
    if fallacy_count:
        reasons.append(f"{fallacy_count} fallac{'y' if fallacy_count == 1 else 'ies'} detected (-1.5 each)")
    if any(w in text.lower() for w in evidence_words):
        reasons.append("grounds claims in reasons/evidence (+0.5)")
    if not reasons:
        reasons.append("clear but thin — add evidence or a concrete example")
    return score, "; ".join(reasons)


class MockLLMClient(LLMClient):
    backend_name = "mock"

    def __init__(self, seed: int = 42):
        self._rng = random.Random(seed)

    def complete(self, model, messages, *, temperature=0.7, max_tokens=4000, json_mode=False):
        system = ""
        user_text = ""
        for m in messages:
            if m["role"] == "system":
                system += m["content"] + "\n"
            elif m["role"] == "user":
                user_text = m["content"]
        role = "opponent"
        for candidate in ("opponent", "analyst", "fact_checker", "judge", "side_switch"):
            if f"[ROLE:{candidate}]" in system:
                role = candidate
                break
        try:
            ctx = json.loads(user_text)
        except (json.JSONDecodeError, TypeError):
            ctx = {"text": user_text}
        handler = {
            "opponent": self._opponent,
            "analyst": self._analyst,
            "fact_checker": self._fact_checker,
            "judge": self._judge,
            "side_switch": self._side_switch,
        }[role]
        payload = handler(ctx)
        return Completion(text=json.dumps(payload), model=model, backend="mock")

    # ---- handlers ----

    def _opponent(self, ctx: dict) -> dict:
        motion = ctx.get("motion", "the motion")
        persona = ctx.get("persona", "skeptic")
        difficulty = ctx.get("difficulty", "rigorous")
        round_no = int(ctx.get("round", 1))
        user_move = ctx.get("user_move", "")
        kws = keywords(user_move or motion)
        tone = TONE.get(difficulty, TONE["rigorous"])
        pool = OPENERS if round_no == 1 else REBUTTALS
        templates = pool.get(persona, pool["skeptic"])
        template = self._rng.choice(templates)
        move = template.format(
            open=tone["open"], jab=tone["jab"],
            motion_short=shorten_motion(motion),
            kw1=kws[0], kw2=kws[1],
        )
        claims = [s.strip() for s in re.split(r"(?<=[.!?])\s+", move) if len(s.split()) > 6][:3]
        return {"move": move, "claims": claims}

    def _analyst(self, ctx: dict) -> dict:
        move = ctx.get("move", "")
        fallacies = detect_fallacies(move)
        score, reason = score_move(move, len(fallacies))
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", move) if s.strip()]
        strongest = sentences[0][:160] if sentences else ""
        weakest = (
            f"Contains {fallacies[0]['type'].replace('_', ' ')} — {fallacies[0]['explanation'][:120]}"
            if fallacies else "No major weakness detected in this move."
        )
        return {
            "fallacies": fallacies,
            "score": score,
            "score_reason": reason,
            "strongest_point": strongest,
            "weakest_point": weakest,
        }

    def _fact_checker(self, ctx: dict) -> dict:
        # Two modes: claim extraction (plain move blob) vs verdict rendering
        # (bundle with CLAIM:/EVIDENCE: sections).
        text = ctx.get("text", "") or ctx.get("move", "")
        if "CLAIM:" in text and "EVIDENCE:" in text:
            return self._fact_verify(text)
        return self._fact_extract(ctx.get("move", text))

    @staticmethod
    def _sentences(move: str) -> list[str]:
        return [s.strip() for s in re.split(r"(?<=[.!?])\s+", move)
                if len(s.split()) > 5]

    def _fact_extract(self, move: str) -> dict:
        sentences = self._sentences(move)
        claims = []
        for s in sentences[:6]:
            low = s.lower()
            factual = (bool(re.search(r"\d", s)) or
                       any(p in low for p in ("studies show", "research shows",
                                              "experts say", "scientists agree",
                                              "report", "data", "percent", "%")))
            if factual:
                claims.append(s[:200])
        return {"claims": claims[:4]}

    def _fact_verify(self, bundle: str) -> dict:
        import re as _re
        claims = _re.findall(r"CLAIM:\s*(.+?)\nEVIDENCE:", bundle)
        urls = _re.findall(r"\((https?://[^)]+)\)", bundle)
        mock_evidence = "mock-evidence" in bundle or "example.com" in bundle
        checks = []
        for claim in claims[:4]:
            low = claim.lower()
            has_number = bool(_re.search(r"\d", claim))
            appeals = any(p in low for p in ("studies show", "research shows",
                                            "experts say", "scientists agree"))
            if mock_evidence:
                verdict, note = "unverifiable", "Mock mode: no live web access — verdict is a placeholder."
            elif has_number:
                verdict, note = "disputed", "Specific figure cited without a checkable source in the evidence."
            elif appeals:
                verdict, note = "unverifiable", "Appeal to unnamed authority — evidence names no source."
            else:
                verdict, note = "verified", "No conflicting evidence in the retrieved snippets."
            checks.append({"claim": claim[:200], "verdict": verdict, "note": note,
                           "sources": urls[:2]})
        v = sum(1 for c in checks if c["verdict"] == "verified")
        d = sum(1 for c in checks if c["verdict"] == "disputed")
        u = sum(1 for c in checks if c["verdict"] == "unverifiable")
        return {
            "checks": checks,
            "summary": f"{len(checks)} claims · {v} verified · {d} disputed · {u} unverifiable",
            "mock_note": "Mock mode: heuristics only. Live Tavily verification when CROSSFIRE_TAVILY=tavily.",
        }

    def _side_switch(self, ctx: dict) -> dict:
        motion = ctx.get("motion", "the motion")
        user_moves = ctx.get("user_moves_so_far", []) or []
        kws = keywords(" ".join(user_moves) or motion)
        flipped = (
            f"Here's your case, done properly. On {shorten_motion(motion)}: the core "
            f"mechanism is {kws[0]} compounding over time — early adopters capture "
            f"outsized gains, which funds the next wave of {kws[1]}, which lowers costs "
            f"for everyone else. That's not speculation, it's the standard diffusion "
            f"pattern: the economic incentive ({kws[2]}) is strong enough that even "
            f"partial adoption reshapes the landscape. Your version gestured at this; "
            f"the steelmanned version names the mechanism, the incentive, and the "
            f"historical pattern in one chain."
        )
        return {
            "flipped_move": flipped,
            "claims": [
                "Early adopters of automation capture outsized gains that fund further adoption.",
                "Technology diffusion follows an S-curve pattern driven by falling costs.",
            ],
            "gap_note": (
                "Your moves leaned on assertion ('it keeps getting smarter') without naming "
                "a mechanism. The flipped version wins by (1) naming the compounding mechanism, "
                "(2) citing the diffusion pattern, and (3) chaining incentive → adoption → "
                "cost decline. Borrow that structure: mechanism first, examples second."
            ),
        }

    def _judge(self, ctx: dict) -> dict:
        rounds = ctx.get("rounds", [])
        user_total = round(sum(r.get("user_score", 0) for r in rounds), 1)
        opp_total = round(sum(r.get("opponent_score", 0) for r in rounds), 1)
        if user_total > opp_total:
            winner = "user"
        elif opp_total > user_total:
            winner = "opponent"
        else:
            winner = "draw"
        round_notes = []
        for r in rounds:
            us, os = r.get("user_score", 0), r.get("opponent_score", 0)
            edge = "User takes the round." if us > os else ("Opponent takes the round." if os > us else "Round tied.")
            nf = len(r.get("user_fallacies", []))
            extra = f" {nf} fallac{'y' if nf == 1 else 'ies'} flagged on the user's side." if nf else ""
            round_notes.append({"round": r.get("round"), "user_score": us,
                                "opponent_score": os, "note": edge + extra})
        fall_counts: dict[str, int] = {}
        for r in rounds:
            for f in r.get("user_fallacies", []):
                t = f.get("type", "unknown")
                fall_counts[t] = fall_counts.get(t, 0) + 1
        total_checks = sum(r.get("checks_total", 0) for r in rounds)
        total_verified = sum(r.get("checks_verified", 0) for r in rounds)
        hygiene = round(total_verified / total_checks, 2) if total_checks else 1.0
        user_scores = [(r.get("user_score", 0), r.get("round")) for r in rounds]
        tips = [TIPS[t] for t in fall_counts if t in TIPS]
        if not tips:
            tips = ["Vary your evidence: mix data, examples, and first principles across rounds."]
        tips = tips[:3]
        return {
            "rounds": round_notes,
            "user_total": user_total,
            "opponent_total": opp_total,
            "winner": winner,
            "summary": (
                f"After {len(rounds)} round{'s' if len(rounds) != 1 else ''}: "
                f"user {user_total} — opponent {opp_total}. "
                + (f"{winner.title()} wins the debate." if winner != "draw" else "Dead heat — nobody lands a decisive blow.")
            ),
            "report_card": {
                "fallacy_profile": fall_counts,
                "evidence_hygiene": hygiene,
                "strongest_round": max(user_scores)[1] if user_scores else None,
                "weakest_round": min(user_scores)[1] if user_scores else None,
                "tips": tips,
            },
        }
