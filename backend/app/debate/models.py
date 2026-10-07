"""Pydantic models for the debate API."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Persona = Literal["skeptic", "lawyer", "contrarian", "economist"]
Difficulty = Literal["friendly", "rigorous", "hostile"]


class CreateSessionRequest(BaseModel):
    motion: str = Field(min_length=10, max_length=500)
    persona: Persona = "skeptic"
    difficulty: Difficulty = "rigorous"
    lang: str = Field(default="en", pattern="^(en|ar)$")


class MoveRequest(BaseModel):
    text: str = Field(min_length=5, max_length=2000)


class Fallacy(BaseModel):
    type: str
    explanation: str
    fix: str


class ClaimCheck(BaseModel):
    claim: str
    verdict: str
    note: str
    sources: list[str] = []


class MoveAnalysis(BaseModel):
    fallacies: list[Fallacy] = []
    score: float
    score_reason: str = ""
    strongest_point: str = ""
    weakest_point: str = ""


class TurnResult(BaseModel):
    round_no: int
    user_move: str
    user_analysis: MoveAnalysis
    opponent_move: str
    opponent_analysis: MoveAnalysis
    hygiene: str
    claim_checks: list[ClaimCheck] = []
    degraded: bool = False
    notices: list[str] = []


class RoundScore(BaseModel):
    round: int
    user_score: float
    opponent_score: float
    note: str = ""


class FlipSidesResult(BaseModel):
    after_round: int
    flipped_move: str
    claims: list[str] = []
    gap_note: str = ""


class ReportCard(BaseModel):
    fallacy_profile: dict[str, int] = {}
    evidence_hygiene: float = 1.0
    strongest_round: int | None = None
    weakest_round: int | None = None
    tips: list[str] = []


class Verdict(BaseModel):
    rounds: list[RoundScore] = []
    user_total: float
    opponent_total: float
    winner: str
    summary: str = ""
    report_card: ReportCard
