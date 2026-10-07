#!/usr/bin/env python3
"""Phase 2 smoke test: full mock debate + side-switch + Tavily mock +
SQLite store + progress endpoint, end-to-end through the API.

Run from backend/:  python3 smoke.py
"""
import os
import sys
import tempfile

_tmpdb = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmpdb.close()
os.environ["CROSSFIRE_DB_PATH"] = _tmpdb.name

sys.path.insert(0, ".")

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
passed = []


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))
    passed.append(cond)
    if not cond and detail:
        print(f"       detail: {detail}")


# 1. health
r = client.get("/health")
check("health endpoint", r.status_code == 200 and r.json()["status"] == "ok",
      r.text[:120])

# 2. create session
r = client.post("/api/sessions", json={
    "motion": "AI will replace most office jobs by 2030.",
    "persona": "skeptic",
    "difficulty": "rigorous",
})
check("create session", r.status_code == 200 and "session_id" in r.json(), r.text[:120])
sid = r.json()["session_id"]

# 3. round 1 — clean, substantive move
r = client.post(f"/api/sessions/{sid}/moves", json={"text": (
    "AI automation is already replacing routine cognitive work. For example, "
    "customer support teams have shrunk because chatbots now resolve most tier-1 "
    "tickets, and studies of call centers show AI assistance raising throughput "
    "measurably. Because the economic incentive is so strong, adoption will "
    "compound across back-office roles through the decade."
)})
t1 = r.json()
check("round 1 returns turn bundle", r.status_code == 200
      and t1["opponent_move"] and t1["hygiene"], r.text[:150])
check("round 1 no fallacies on clean move",
      len(t1["user_analysis"]["fallacies"]) == 0,
      f"got {[f['type'] for f in t1['user_analysis']['fallacies']]}")
check("round 1 opponent move is substantive", len(t1["opponent_move"].split()) > 20,
      t1["opponent_move"][:80])

# 4. round 2 — deliberately fallacious move
nasty = ("So you're saying all economists are idiots who know nothing about work, "
         "either we ban AI right now or humanity is finished, everyone knows this.")
r = client.post(f"/api/sessions/{sid}/moves", json={"text": nasty})
t2 = r.json()
flagged = {f["type"] for f in t2["user_analysis"]["fallacies"]}
check("round 2 flags strawman", "strawman" in flagged, f"flagged={flagged}")
check("round 2 flags ad_hominem", "ad_hominem" in flagged, f"flagged={flagged}")
check("round 2 flags false_dilemma", "false_dilemma" in flagged, f"flagged={flagged}")
check("round 2 flags bandwagon", "bandwagon" in flagged, f"flagged={flagged}")
check("round 2 fallacy has explanation+fix",
      all(f.get("explanation") and f.get("fix") for f in t2["user_analysis"]["fallacies"]))
check("round 2 score penalized vs round 1",
      t2["user_analysis"]["score"] < t1["user_analysis"]["score"],
      f"r1={t1['user_analysis']['score']} r2={t2['user_analysis']['score']}")
check("round 2 hygiene line present", "claims" in t2["hygiene"], t2["hygiene"])
check("round 2 claim checks carry sources",
      all("sources" in c for c in t2["claim_checks"]),
      str(t2["claim_checks"])[:150])

# 5. scoreboard state
r = client.get(f"/api/sessions/{sid}")
state = r.json()
check("scoreboard has 2 rounds", len(state["scoreboard"]["rounds"]) == 2)
check("scoreboard totals consistent",
      state["scoreboard"]["user_total"] == round(
          t1["user_analysis"]["score"] + t2["user_analysis"]["score"], 1))

# 6. side-switch
r = client.post(f"/api/sessions/{sid}/flip-sides")
check("flip-sides returns 200", r.status_code == 200, r.text[:150])
flip = r.json()
check("flip has flipped_move + gap_note",
      len(flip["flipped_move"].split()) > 20 and len(flip["gap_note"]) > 20,
      flip["flipped_move"][:100])
check("flip recorded in session state",
      len(client.get(f"/api/sessions/{sid}").json()["flips"]) == 1)
# flip before any round -> 400
r2 = client.post("/api/sessions", json={
    "motion": "Universal basic income would fix poverty for good.",
    "persona": "economist", "difficulty": "friendly",
})
sid2 = r2.json()["session_id"]
r = client.post(f"/api/sessions/{sid2}/flip-sides")
check("flip with no rounds rejected", r.status_code == 400, r.text[:100])

# 7. end debate -> verdict
r = client.post(f"/api/sessions/{sid}/end")
v = r.json()
check("verdict returned", r.status_code == 200 and v["winner"] in ("user", "opponent", "draw"),
      r.text[:150])
check("verdict has round scorecard", len(v["rounds"]) == 2)
check("report card has fallacy profile",
      v["report_card"]["fallacy_profile"].get("strawman", 0) >= 1,
      str(v["report_card"]["fallacy_profile"]))
check("report card has tips", len(v["report_card"]["tips"]) > 0)

# 8. progress endpoint (SQLite longitudinal stats)
r = client.get("/api/progress")
p = r.json()
check("progress endpoint", r.status_code == 200 and p["debates"] >= 2, r.text[:150])
check("progress counts rounds", p["total_rounds"] >= 2, str(p["total_rounds"]))
check("progress counts flips", p["total_flips"] >= 1, str(p["total_flips"]))
check("progress fallacy profile has strawman",
      p["fallacy_profile"].get("strawman", 0) >= 1, str(p["fallacy_profile"]))
check("progress hygiene trend present",
      len(p["hygiene_by_debate"]) >= 1 and "hygiene" in p["hygiene_by_debate"][0])

# 9. LLM backend swap is one env change
from app.llm import get_llm_client
from app.llm.mock import MockLLMClient
check("default backend is mock", isinstance(get_llm_client(), MockLLMClient))
os.environ["CROSSFIRE_LLM"] = "bogus"
try:
    get_llm_client()
    check("unknown backend raises", False)
except ValueError:
    check("unknown backend raises", True)
finally:
    del os.environ["CROSSFIRE_LLM"]

# 10. Tavily client swap
from app.evidence.tavily import (
    KeylessTavilyClient, MockTavilyClient, TavilyClient, get_tavily_client,
)
check("default tavily backend is keyless", isinstance(get_tavily_client(), KeylessTavilyClient))
os.environ["CROSSFIRE_TAVILY"] = "mock"
res = get_tavily_client().search("AI automation jobs report")
check("mock tavily returns results", len(res) > 0 and res[0].url.startswith("http"),
      str(res[0].url)[:80])
del os.environ["CROSSFIRE_TAVILY"]
os.environ["CROSSFIRE_TAVILY"] = "bogus"
try:
    get_tavily_client()
    check("unknown tavily backend raises", False)
except ValueError:
    check("unknown tavily backend raises", True)
finally:
    del os.environ["CROSSFIRE_TAVILY"]
try:
    TavilyClient(api_key=None)
    # only reaches here if TAVILY_API_KEY happens to be set in env
    check("tavily without key raises", "TAVILY_API_KEY" in os.environ)
except RuntimeError:
    check("tavily without key raises", True)
# fact-checker wires tavily evidence through (mock-backed)
from app.agents import fact_checker
fc = fact_checker.check_move(
    MockLLMClient(),
    move="A 2023 McKinsey report estimated that 30% of admin tasks are automatable.",
    side="user",
)
check("fact-checker extracts + verifies with sources",
      len(fc["checks"]) > 0 and all("sources" in c for c in fc["checks"]),
      str(fc["checks"])[:200])
check("fact-checker summary line", "claims" in fc["summary"], fc["summary"])

# 11. TokenFactoryClient constructs the right request shape (no network)
from unittest.mock import patch
from app.llm.token_factory import TokenFactoryClient
tf = TokenFactoryClient(api_key="test-key")
tf._ensure_client()  # build the httpx client (lazy since the no-key boot fix)
with patch.object(tf._http, "post") as fake_post:
    fake_post.return_value.json.return_value = {
        "choices": [{"message": {"content": '{"ok": true}'}}], "usage": {}}
    fake_post.return_value.raise_for_status.return_value = None
    comp = tf.complete("fast", [{"role": "user", "content": "hi"}], json_mode=True)
    _, kwargs = fake_post.call_args
    body = kwargs["json"]
    check("tokenfactory uses bearer auth",
          tf._http.headers["Authorization"] == "Bearer test-key")
    check("tokenfactory posts to chat/completions",
          fake_post.call_args[0][0].endswith("/chat/completions"))
    check("tokenfactory json_mode sets response_format",
          body.get("response_format") == {"type": "json_object"})
    check("tokenfactory returns Completion", comp.text == '{"ok": true}'
          and comp.backend == "tokenfactory")
    check("tokenfactory fast alias is verified model id",
          tf.resolve_model("fast") == "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B")

# 12. SQLite persistence across store instances (same file)
from app.memory.store import MemoryStore
s2 = MemoryStore(path=_tmpdb.name).get(sid)
check("sqlite persists rounds across instances",
      s2 is not None and len(s2.rounds) == 2, str(len(s2.rounds) if s2 else 0))
check("sqlite persists flips across instances",
      s2 is not None and len(s2.flips) == 1)

# 13. SQLite WAL mode + integrity check
import sqlite3
conn = sqlite3.connect(_tmpdb.name)
mode = conn.execute("PRAGMA journal_mode;").fetchone()[0]
check("sqlite runs in WAL mode", mode.lower() == "wal", mode)
integ = conn.execute("PRAGMA integrity_check;").fetchone()[0]
check("sqlite integrity check ok", integ == "ok", str(integ)[:60])
conn.close()

# 14. Round cap: 13th move rejected
r = client.post("/api/sessions", json={
    "motion": "This is a motion long enough to pass validation here.",
    "persona": "skeptic", "difficulty": "friendly",
})
cap_sid = r.json()["session_id"]
# temporarily lower the cap for a fast test
import app.debate.engine as eng_mod
old_cap, eng_mod.MAX_ROUNDS = eng_mod.MAX_ROUNDS, 2
try:
    for i in range(2):
        rr = client.post(f"/api/sessions/{cap_sid}/moves",
                         json={"text": f"Test move number {i} with enough words to pass validation."})
        assert rr.status_code == 200, rr.text[:150]
    rr = client.post(f"/api/sessions/{cap_sid}/moves",
                     json={"text": "This third move should be rejected by the round cap."})
    check("round cap rejects excess moves", rr.status_code == 400 and "capped" in rr.text,
          rr.text[:120])
finally:
    eng_mod.MAX_ROUNDS = old_cap

# 15. TurnResult carries degraded/notices fields
check("turn bundle has degraded flag", "degraded" in t1 and t1["degraded"] is False)
check("turn bundle has notices list", "notices" in t1 and isinstance(t1["notices"], list))

# 16. Ultra -> Nano fallback on HTTP error (mocked transport)
import httpx
from app.llm.token_factory import TokenFactoryClient
calls = []
def flaky_handler(request):
    calls.append(request.url.path)
    body = httpx.Response(200, json={
        "choices": [{"message": {"content": '{"ok": true}'}}], "usage": {}})
    if len(calls) == 1:
        return httpx.Response(500, json={"error": "boom"})
    return body
tf2 = TokenFactoryClient(api_key="test-key")
tf2._http = httpx.Client(transport=httpx.MockTransport(flaky_handler), timeout=10,
                         headers={"Authorization": "Bearer test-key"})
comp2 = tf2.complete("reasoning", [{"role": "user", "content": "hi"}])
check("ultra failure falls back to nano", comp2.meta.get("model_fallback") is True
      and len(calls) == 2, f"calls={len(calls)}")
check("fallback keeps working result", comp2.text == '{"ok": true}')

# 17. Tavily claim cache: same claim searched once per debate
from app.evidence.tavily import MockTavilyClient
from app.agents import fact_checker
searches = []
class CountingMock(MockTavilyClient):
    def search(self, query, max_results=5):
        searches.append(query)
        return super().search(query, max_results)
from app.llm.mock import MockLLMClient
mlm = MockLLMClient()
cm = CountingMock()
cache = {}
fact_checker.check_move(mlm, move="Studies show AI adoption rose 40 percent across sectors last year.",
                        side="user", tavily=cm, cache=cache)
n1 = len(searches)
fact_checker.check_move(mlm, move="Studies show AI adoption rose 40 percent across sectors last year.",
                        side="user", tavily=cm, cache=cache)
n2 = len(searches)
check("tavily cache avoids repeat searches", n1 > 0 and n2 == n1,
      f"searches: {n1} then {n2}")

# 18. Keyless rate-limit falls back to mock (degraded flag)
class RateLimitedMock(MockTavilyClient):
    backend_name = "keyless"
    def search(self, query, max_results=5):
        raise RuntimeError("Tavily keyless rate limit reached (demo)")
res = fact_checker.check_move(mlm, move="A 2023 report found 30 percent of admin tasks are automatable.",
                              side="user", tavily=RateLimitedMock(), cache={})
check("rate limit degrades gracefully", res.get("degraded") is True)

print()
if all(passed):
    print(f"ALL {len(passed)} CHECKS PASSED")
else:
    print(f"{sum(passed)}/{len(passed)} passed — FAILURES ABOVE")
    sys.exit(1)
