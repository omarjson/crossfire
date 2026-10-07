# Crossfire — AI Debate Sparring Gym

**Nebius x NVIDIA Global AI Hackathon** · Track: Best Apps & Agents

Most AI agrees with you. Crossfire doesn't.

State a position and Crossfire takes the other side: it argues the strongest
version of the opposing case across structured rounds, calls your logical
fallacies like a referee, checks every factual claim against live web sources,
and finishes with an impartial judge's scorecard plus a personal report card on
your reasoning. Flip sides mid-debate and it will argue *your* position better
than you did — then show you where your case was weak.

## Features

- **Structured sparring rounds** — you argue, Crossfire steelmans the opposition
- **Real-time fallacy referee** — bandwagon, false dilemma, slippery slope,
  appeal to authority and more, flagged with plain-language fixes
- **Live evidence checks** — every factual claim searched against the web,
  verdicts grounded in sources with URLs
- **Side-switch training** — mid-debate, Crossfire argues your side better than
  you did, then points out the gaps in your original case
- **Impartial judge** — round-by-round scorecard, winner verdict, and a report
  card tracking your fallacy profile and evidence hygiene
- **Sparring record** — SQLite-backed longitudinal memory: debates, rounds,
  flips, recurring fallacies, and evidence-hygiene trends across sessions
- **4 personas × 3 difficulties** — The Skeptic, The Lawyer, The Contrarian,
  The Economist; Friendly / Rigorous / Hostile

## Where we used Nebius + NVIDIA

**Nebius Token Factory** is the inference backbone. Every agent call goes
through Token Factory's OpenAI-compatible API:

| Agent | Model | Why |
|---|---|---|
| Opponent | `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` | Fast, sharp rebuttals keep rounds snappy |
| Analyst (fallacy referee) | `nvidia/Nemotron-3-Ultra-550b-a55b` | Deep reasoning for precise fallacy detection + scoring |
| Judge | `nvidia/Nemotron-3-Ultra-550b-a55b` | Long-context reasoning over full debate history for fair verdicts |
| Fact-check claim extraction | `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` | Quick structured extraction before web verification |

Swap backends with one env var (see Configuration). The app also runs fully
offline on a mock backend for development.

**Tavily** powers the evidence layer: the fact-checker extracts factual claims
from each move and issues a real Tavily search per claim at runtime, returning
grounded verdicts (verified / disputed / unverifiable) with source URLs.
Keyless mode works out of the box (no API key needed); drop in
`TAVILY_API_KEY` for higher rate limits.

## Tech stack

- **Backend:** FastAPI, SQLite (WAL mode), httpx
- **Frontend:** React + Vite, self-hosted Clash Display + Satoshi type
- **AI:** NVIDIA Nemotron-3 models via Nebius Token Factory, Tavily search API

## Getting started

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev        # served at http://localhost:5173, proxies /api to :8000
```

### Configuration

| Variable | Default | Purpose |
|---|---|---|
| `CROSSFIRE_LLM` | `mock` | `mock` (offline) or `tokenfactory` (live Nebius) |
| `NEBIUS_API_KEY` | — | Token Factory key, required for live models |
| `CROSSFIRE_TAVILY` | `keyless` | `keyless` (no key, rate-limited), `mock` (offline), or `tavily` (your key) |
| `TAVILY_API_KEY` | — | Optional, for higher Tavily limits |
| `CROSSFIRE_DB_PATH` | `backend/data/crossfire.db` | SQLite sparring-record location |

Run the test suite: `cd backend && .venv/bin/python smoke.py` (52 checks).

## Project structure

```
crossfire/
├── backend/
│   ├── app/
│   │   ├── agents/        # opponent, analyst, fact-checker, judge, side-switch
│   │   ├── api/           # FastAPI routes
│   │   ├── evidence/      # Tavily client (keyless / keyed / mock)
│   │   ├── llm/           # Token Factory + mock backends
│   │   └── memory/        # SQLite sparring-record store
│   ├── requirements.txt
│   └── smoke.py
└── frontend/
    ├── public/fonts/      # self-hosted Clash Display + Satoshi
    ├── src/components/    # landing, arena, scoreboard, verdict, record
    └── src/styles.css
```

## License

MIT — see [LICENSE](LICENSE).
