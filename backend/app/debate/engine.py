"""DebateEngine: orchestrates the four agents across structured rounds.

One user turn runs:
    analyst(user move) -> opponent rebuttal -> analyst(opponent move)
    -> fact-checker(both) -> scoreboard update
"""
from __future__ import annotations

from ..agents import analyst, fact_checker, judge, opponent, side_switch
from ..llm import get_llm_client
from ..llm.client import LLMClient
from ..memory.store import MemoryStore
from ..security import scan_injection, wrap_untrusted
from .models import (
    ClaimCheck,
    Fallacy,
    MoveAnalysis,
    ReportCard,
    RoundScore,
    TurnResult,
    Verdict,
)


class UnknownSessionError(KeyError):
    """Raised when a session id isn't in the store. Distinct from bugs."""


MAX_ROUNDS = 12


def _to_analysis(d: dict) -> MoveAnalysis:
    return MoveAnalysis(
        fallacies=[Fallacy(**f) for f in d.get("fallacies", [])],
        score=d.get("score", 6.0),
        score_reason=d.get("score_reason", ""),
        strongest_point=d.get("strongest_point", ""),
        weakest_point=d.get("weakest_point", ""),
    )


class DebateEngine:
    def __init__(self, llm: LLMClient | None = None, store: MemoryStore | None = None):
        self.llm = llm or get_llm_client()
        self.store = store or MemoryStore()
        # Per-session Tavily result cache: (session_id -> {claim_key: result}).
        # Same claim is never searched twice within a debate.
        self._claim_cache: dict[str, dict] = {}

    # ---- sessions ----

    def create_session(self, motion: str, persona: str, difficulty: str,
                       lang: str = "en"):
        return self.store.create(motion, persona, difficulty, lang)

    def get_state(self, session_id: str) -> dict | None:
        s = self.store.get(session_id)
        if not s:
            return None
        return {
            "id": s.id, "motion": s.motion, "persona": s.persona,
            "difficulty": s.difficulty, "finished": s.finished,
            "rounds": s.rounds,
            "flips": s.flips,
            "scoreboard": self._scoreboard(s),
        }

    # ---- turns ----

    def user_move(self, session_id: str, text: str) -> TurnResult:
        s = self.store.get(session_id)
        if not s:
            raise UnknownSessionError(f"unknown session {session_id}")
        if s.finished:
            raise ValueError("debate already finished")
        round_no = len(s.rounds) + 1
        if round_no > MAX_ROUNDS:
            raise ValueError(
                f"debate is capped at {MAX_ROUNDS} rounds — call the judge")
        history = [
            {"role": "user", "text": r["user_move"]}
            for r in s.rounds
        ] + [
            {"role": "opponent", "text": r["opponent_move"]}
            for r in s.rounds
        ]

        notices: list[str] = []
        degraded = False

        # Prompt-injection defense: scan the raw move, then wrap it as
        # untrusted data for every agent call below. A detected attempt is
        # called as a foul by the referee and costs the user points.
        injection_hits = scan_injection(text)
        safe_text = wrap_untrusted(text) if injection_hits else text

        user_a = _to_analysis(analyst.analyze_move(
            self.llm, move=safe_text, side="user", motion=s.motion,
            lang=s.lang))
        if injection_hits:
            user_a.fallacies.append(Fallacy(
                type="prompt_injection",
                explanation=(
                    "Move contains instruction-like text aimed at the AI "
                    f"({', '.join(injection_hits)}). Treated as debate "
                    "content, not instructions — the attempt was ignored."
                ),
                fix="Argue the motion itself. Instructions to the AI are "
                    "never part of a debate move.",
            ))
            user_a.score = max(1.0, user_a.score - 2.0)
            notices.append(
                "Prompt-injection attempt detected and neutralized — "
                "scored as a foul.")

        opp = opponent.generate_move(
            self.llm, motion=s.motion, persona=s.persona,
            difficulty=s.difficulty, round_no=round_no,
            user_move=safe_text, history=history, lang=s.lang)
        opp_a = _to_analysis(analyst.analyze_move(
            self.llm, move=opp["move"], side="opponent", motion=s.motion,
            lang=s.lang))

        cache = self._claim_cache.setdefault(session_id, {})
        fc_user = fact_checker.check_move(self.llm, move=safe_text, side="user",
                                          cache=cache, lang=s.lang)
        fc_opp = fact_checker.check_move(self.llm, move=opp["move"],
                                         side="opponent", cache=cache,
                                         lang=s.lang)
        if fc_user.get("degraded") or fc_opp.get("degraded"):
            degraded = True
            notices.append(
                "Evidence checks fell back to the cached corpus — "
                "live search hit its rate limit.")
        all_checks = fc_user["checks"] + fc_opp["checks"]
        v = sum(1 for c in all_checks if c["verdict"] == "verified")
        d = sum(1 for c in all_checks if c["verdict"] == "disputed")
        u = sum(1 for c in all_checks if c["verdict"] == "unverifiable")
        hygiene = f"{len(all_checks)} claims · {v} verified · {d} disputed · {u} unverifiable"

        round_data = {
            "round": round_no,
            "user_move": text,
            "user_score": user_a.score,
            "user_fallacies": [f.model_dump() for f in user_a.fallacies],
            "opponent_move": opp["move"],
            "opponent_score": opp_a.score,
            "checks_total": len(all_checks),
            "checks_verified": v,
        }
        self.store.append_round(session_id, round_data)

        return TurnResult(
            round_no=round_no,
            user_move=text,
            user_analysis=user_a,
            opponent_move=opp["move"],
            opponent_analysis=opp_a,
            hygiene=hygiene,
            claim_checks=[ClaimCheck(**c) for c in all_checks],
            degraded=degraded,
            notices=notices,
        )

    # ---- side-switch ----

    def flip_sides(self, session_id: str) -> dict:
        """The twist: argue the USER's position better than they did, then
        show where their own case was weak. Optional trigger — button or
        auto-suggest after round 2."""
        s = self.store.get(session_id)
        if not s:
            raise UnknownSessionError(f"unknown session {session_id}")
        if s.finished:
            raise ValueError("debate already finished")
        if not s.rounds:
            raise ValueError("play at least one round before flipping sides")
        user_moves = [r["user_move"] for r in s.rounds]
        flip = side_switch.flip_sides(
            self.llm, motion=s.motion, user_moves=user_moves, persona=s.persona,
            lang=s.lang)
        flip_data = {
            "after_round": len(s.rounds),
            "flipped_move": flip["flipped_move"],
            "claims": flip["claims"],
            "gap_note": flip["gap_note"],
        }
        self.store.append_flip(session_id, flip_data)
        return flip_data

    # ---- verdict ----

    def end_debate(self, session_id: str) -> Verdict:
        s = self.store.get(session_id)
        if not s:
            raise UnknownSessionError(f"unknown session {session_id}")
        if not s.rounds:
            raise ValueError("no rounds played yet")
        j = judge.judge_debate(
            self.llm, motion=s.motion, persona=s.persona, rounds=s.rounds,
            lang=s.lang)
        self.store.finish(session_id)
        self._claim_cache.pop(session_id, None)  # free the per-debate cache
        rc = j["report_card"]
        return Verdict(
            rounds=[RoundScore(**r) for r in j["rounds"]],
            user_total=j["user_total"],
            opponent_total=j["opponent_total"],
            winner=j["winner"],
            summary=j["summary"],
            report_card=ReportCard(**rc),
        )

    # ---- scoreboard ----

    @staticmethod
    def _scoreboard(s) -> dict:
        rounds = [
            {"round": r["round"], "user_score": r["user_score"],
             "opponent_score": r["opponent_score"]}
            for r in s.rounds
        ]
        return {
            "rounds": rounds,
            "user_total": round(sum(r["user_score"] for r in s.rounds), 1),
            "opponent_total": round(sum(r["opponent_score"] for r in s.rounds), 1),
        }
