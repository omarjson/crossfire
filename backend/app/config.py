"""Settings — env-driven. The one-line model swap lives here."""
from __future__ import annotations

import os

from pydantic import BaseModel


class Settings(BaseModel):
    # "mock" | "tokenfactory"  <- one-line swap via env
    llm_backend: str = os.environ.get("CROSSFIRE_LLM", "mock")
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    nebius_api_key: str | None = os.environ.get("NEBIUS_API_KEY")


settings = Settings()
