# SurplusAI — AI Workforce for Food Rescue

**Submission build.** Real backend, real scoring logic, live frontend — not a client-side mock.

---

## 1. What it does

Restaurant submits surplus food (type, quantity, pickup deadline, optional photo) → a 7-agent
pipeline verifies it, predicts urgency, scores every NGO in range on a weighted formula, assigns
a volunteer with a real ETA, notifies all three parties, and updates a live impact dashboard.
One donation, zero manual coordination.

## 2. Architecture

```
Restaurant Portal (frontend/index.html)
        │  POST /donate  { food_type, quantity, pickup_time, image_base64, force_reject }
        ▼
FastAPI backend (backend/main.py)
        │
        ▼
Orchestrator (backend/orchestrator.py)
   runs 7 agents sequentially, threading one shared state dict
        │
        ├─▶ Donation Agent    — parses submission into structured record, mints ticket ID
        ├─▶ Quality Agent     — freshness heuristic from photo signal + category risk
        │        └─(fail)──▶ pipeline halts, ticket marked "rejected"
        ├─▶ Expiry Agent      — shelf-life estimate from category + pickup hour
        ├─▶ Matching Agent    — weighted score across all NGOs, ranks + picks winner
        ├─▶ Route Agent       — assigns volunteer, computes ETA (distance/speed × traffic)
        ├─▶ Notification Agent— builds per-stakeholder notification payloads
        └─▶ Impact Agent      — converts to meals/people/waste/CO2, updates running totals
        │
        ▼
Full trace + result returned as one JSON response
        │
        ▼
Frontend replays the trace as an animated "live" pipeline,
updates Admin Command Center, NGO feed, Volunteer feed
```

Each agent is a plain Python function that takes the shared state dict and returns it —
structured so it maps directly onto a LangGraph `StateGraph` (nodes + conditional edges) if you
want to swap in real LangGraph later. See the NOTE at the bottom of `orchestrator.py`.

## 3. Tech stack

| Layer      | Choice                          | Why |
|------------|----------------------------------|-----|
| Backend    | FastAPI + Pydantic                | Fast to stand up, auto-generates OpenAPI docs at `/docs`, matches your existing FastAPI stack |
| Agents     | Plain Python modules, no framework lock-in | Real logic, zero LLM-call latency risk during a live demo |
| Data       | JSON files (`ngos.json`, `volunteers.json`) | Swap for Postgres/SQLite with zero code change to agent logic |
| Frontend   | Single-file HTML/CSS/JS, no build step | Opens directly in a browser, nothing to `npm install` before judging |
| State      | In-memory per session (`impact_agent.py`) | Fine for a demo; swap for a DB for persistence |

## 4. What's real vs. what's a documented placeholder

Be upfront about this with judges — it's a strength, not a weakness, if you can point to exactly
where the swap-in happens.

**Real, deterministic logic (not random):**
- Matching Agent: actual weighted formula — `0.35×need_match + 0.30×proximity + 0.20×capacity_fit + 0.15×urgency_bonus` — scored against every NGO, fully explainable per donation.
- Route Agent: real ETA math (`distance / speed × traffic multiplier`), traffic multiplier is rush-hour-aware, not random.
- Expiry Agent: rule table by food category + evening-pickup penalty.
- Impact Agent: documented conversion factors (people/meal, kg/meal, CO2/kg waste) — all stated in the docstring, not hidden.

**Documented placeholders, with the swap-in point marked in code:**
- Quality Agent uses a heuristic (photo present? file size plausible? category risk) instead of a real vision model. `quality_agent.py` has a NOTE showing exactly where to drop in an Anthropic vision API call.
- Donation Agent does direct field parsing instead of LLM-based free-text extraction. `donation_agent.py` has the equivalent NOTE.
- Notifications are logged, not actually sent (no Twilio/SMS wiring). The exact payload each channel would receive is already built in `notification_agent.py`.

## 5. Running it

**Backend:**
```bash
cd backend
pip install -r requirements.txt --break-system-packages   # or use a venv
uvicorn main:app --reload --port 8000
```
Confirm it's up: `curl http://127.0.0.1:8000/health` → `{"status":"ok"}`
Interactive API docs: `http://127.0.0.1:8000/docs`

**Frontend:**
Open `frontend/index.html` directly in a browser (double-click, or `open frontend/index.html`).
The top-right connection indicator turns green once it reaches the backend. No build step.

## 6. API reference

| Endpoint         | Method | Body                                                              | Returns |
|-------------------|--------|--------------------------------------------------------------------|---------|
| `/donate`          | POST   | `{food_type, quantity, pickup_time, force_reject, image_base64}` | Full pipeline trace + result |
| `/impact`           | GET    | —                                                                  | Running session totals |
| `/ngos`              | GET    | —                                                                  | NGO dataset (for map) |
| `/health`             | GET    | —                                                                  | Liveness check |

Example:
```bash
curl -X POST http://127.0.0.1:8000/donate \
  -H "Content-Type: application/json" \
  -d '{"food_type":"Veg Thali","quantity":40,"pickup_time":"22:00","force_reject":false}'
```

## 7. Demo script (~90 seconds)

1. **Restaurant tab** — fill in 40 × Veg Thali, pickup 22:00, upload a photo. Click **Donate**.
2. Watch the manifest-style pipeline animate through all 7 agents in real time — this is a live API call, not a canned sequence.
3. When the Decision Timeline reveals, point at the score breakdown: *"AI didn't just pick the closest NGO — it weighed need, proximity, capacity, and urgency, and here's the exact math."*
4. Check the **Force quality rejection** box, resubmit — show the pipeline halting cleanly at the Quality Agent, ticket marked rejected, no downstream agents run.
5. **Admin tab** — point at the live map (route lit up to the winning NGO), impact counters ticking up, agent status lights.
6. Close on the architecture: *"Every score, every ETA, every rejection you just saw came from a real FastAPI backend running 7 independent agents — not a mock."*

## 8. Known gaps (say these proactively if asked)

- No real vision model wired in yet for the Quality Agent — heuristic only, swap-in point is documented in code.
- No persistent DB — impact totals reset when the backend restarts.
- No fallback NGO tier if every NGO in range is at capacity — matching always picks the best of what's available, doesn't yet handle "no NGO can take it."
- Volunteer assignment always picks the fastest available volunteer, not the nearest — fine for 3 volunteers, needs real geolocation at scale.

## 9. File structure

```
surplusai/
├── backend/
│   ├── main.py                 # FastAPI app, endpoints
│   ├── orchestrator.py         # runs the 7-agent pipeline
│   ├── requirements.txt
│   ├── agents/
│   │   ├── state.py            # shared state shape + trace logging
│   │   ├── donation_agent.py
│   │   ├── quality_agent.py
│   │   ├── expiry_agent.py
│   │   ├── matching_agent.py
│   │   ├── routing_agent.py
│   │   ├── notification_agent.py
│   │   └── impact_agent.py
│   └── data/
│       ├── ngos.json
│       └── volunteers.json
└── frontend/
    └── index.html              # calls the backend API, no build step
```
