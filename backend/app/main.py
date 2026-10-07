"""FastAPI app wiring."""
from __future__ import annotations

import logging
import os
import re
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api.routes import router
from .config import settings

log = logging.getLogger("crossfire")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

_SESSION_RE = re.compile(r"/api/sessions/([0-9a-f]+)")

app = FastAPI(title="Crossfire", version="0.1.0",
              description="AI debate sparring gym — Phase 1 (mock backend)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_log(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    ms = (time.perf_counter() - start) * 1000
    m = _SESSION_RE.search(request.url.path)
    sid = f" session={m.group(1)[:8]}" if m else ""
    log.info("%s %s -> %s %.0fms%s",
             request.method, request.url.path,
             response.status_code, ms, sid)
    return response


app.include_router(router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok", "llm_backend": settings.llm_backend}


# ---- serve the built frontend (single-service deploy) ----
# In production the Docker image copies frontend/dist here.
STATIC_DIR = os.environ.get("CROSSFIRE_STATIC_DIR",
                            os.path.join(os.path.dirname(__file__), "..", "static"))
if os.path.isdir(STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")),
              name="assets")

    @app.get("/{path:path}")
    def spa(path: str):
        if path.startswith("api/"):
            return {"detail": "not found"}
        candidate = os.path.join(STATIC_DIR, path)
        if path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
