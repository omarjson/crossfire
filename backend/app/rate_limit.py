"""In-memory per-IP sliding-window rate limit for debate creation.

Why: the public demo has no throttling; every new debate fires paid
Nebius + Tavily calls. 10 debates/hour per IP is generous for real
viewers and stops scripted credit-burn.

Reversible: delete the add_middleware line in main.py and redeploy.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

WINDOW_SECONDS = 3600          # 1 hour
MAX_SESSIONS_PER_WINDOW = 10   # debates started per IP per hour

_hits: dict[str, deque[float]] = defaultdict(deque)


def _client_ip(request: Request) -> str:
    # Caddy reverse-proxies to uvicorn and sets X-Forwarded-For.
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class DebateRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "POST" and request.url.path == "/api/sessions":
            ip = _client_ip(request)
            now = time.time()
            q = _hits[ip]
            while q and now - q[0] > WINDOW_SECONDS:
                q.popleft()
            if len(q) >= MAX_SESSIONS_PER_WINDOW:
                return JSONResponse(
                    {"detail": "Too many debates started — try again in a bit."},
                    status_code=429,
                )
            q.append(now)
        return await call_next(request)
