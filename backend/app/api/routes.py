"""REST API: sessions, moves, verdict."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..debate.engine import DebateEngine, UnknownSessionError
from ..debate.models import (
    CreateSessionRequest,
    FlipSidesResult,
    MoveRequest,
    TurnResult,
    Verdict,
)

router = APIRouter()
engine = DebateEngine()  # singleton for Phase 1 (in-memory store)


@router.post("/sessions")
def create_session(req: CreateSessionRequest):
    s = engine.create_session(req.motion, req.persona, req.difficulty, req.lang)
    return {"session_id": s.id, "motion": s.motion,
            "persona": s.persona, "difficulty": s.difficulty, "lang": s.lang}


@router.get("/sessions/{session_id}")
def get_session(session_id: str):
    state = engine.get_state(session_id)
    if not state:
        raise HTTPException(404, "unknown session")
    return state


@router.post("/sessions/{session_id}/moves", response_model=TurnResult)
def post_move(session_id: str, req: MoveRequest):
    try:
        return engine.user_move(session_id, req.text)
    except UnknownSessionError:
        raise HTTPException(404, "unknown session")
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/sessions/{session_id}/flip-sides", response_model=FlipSidesResult)
def flip_sides(session_id: str):
    """The twist: Crossfire argues YOUR side better than you did."""
    try:
        return engine.flip_sides(session_id)
    except UnknownSessionError:
        raise HTTPException(404, "unknown session")
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/sessions/{session_id}/end", response_model=Verdict)
def end_debate(session_id: str):
    try:
        return engine.end_debate(session_id)
    except UnknownSessionError:
        raise HTTPException(404, "unknown session")
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/progress")
def get_progress():
    """Longitudinal stats across all debates: fallacy profile, hygiene trend."""
    return engine.store.progress()
