# 🍲 SurplusAI
### AI Workforce for Food Rescue

> **Every meal deserves a second chance.**

SurplusAI is an autonomous multi-agent platform that rescues surplus food from restaurants, hotels, bakeries, and events, intelligently matches it with NGOs, plans deliveries, coordinates volunteers, and measures real-world impact—all with minimal human intervention.

Instead of relying on phone calls, WhatsApp groups, or manual coordination, SurplusAI uses a team of specialized AI agents that collaborate to complete the entire rescue workflow.

---

# 🚨 The Problem

Every day:

- 🍽 Restaurants discard perfectly edible meals.
- 🏨 Hotels throw away buffet leftovers.
- 🥖 Bakeries dispose of unsold bread.
- 🎉 Events generate large amounts of food waste.

Meanwhile:

- NGOs
- Orphanages
- Homeless shelters
- Community kitchens

struggle to provide meals because they don't know where surplus food is available.

The challenge isn't food production.

**It's coordination.**

---

# 💡 Our Solution

SurplusAI transforms food rescue into an autonomous AI workflow.

A restaurant only needs to submit a donation once.

Everything else is handled automatically.

```text
Restaurant
      │
      ▼
🤖 AI Workforce
      │
      ▼
NGO receives food
```

The AI system:

- Understands the donation
- Verifies food quality
- Predicts urgency
- Finds the best NGO
- Plans the fastest route
- Assigns a volunteer
- Notifies everyone
- Tracks social impact

---

# 🤖 AI Workforce

SurplusAI is powered by seven specialized AI agents.

## 🥘 Donation Agent

Converts restaurant submissions into structured donation records.

Responsibilities:

- Extract food information
- Generate donation ID
- Normalize quantities
- Prepare shared state

---

## 👁 Food Quality Agent

Evaluates whether the donation is safe.

Current implementation:

- Freshness heuristic
- Food category risk
- Photo availability

Future:

- Vision LLM integration
- Food detection
- Spoilage classification

---

## ⏳ Expiry Prediction Agent

Predicts remaining safe consumption time using:

- Food category
- Pickup deadline
- Shelf-life rules

---

## 🎯 Matching Agent

Ranks every NGO using an explainable weighted scoring algorithm.

Current scoring:

```
Final Score =
0.35 × Need Match
+ 0.30 × Proximity
+ 0.20 × Capacity Fit
+ 0.15 × Urgency
```

The highest scoring NGO is selected.

Every decision is explainable.

---

## 🚗 Route Planning Agent

Assigns the most suitable volunteer.

Calculates:

- Estimated travel time
- Distance
- Traffic multiplier
- Route information

---

## 📢 Notification Agent

Generates personalized notifications for:

- Restaurant
- NGO
- Volunteer

Current implementation logs payloads.

Can later integrate:

- WhatsApp
- SMS
- Email
- Push notifications

---

## 📊 Impact Agent

Measures real-world impact.

Tracks:

- Meals rescued
- People fed
- Food waste prevented
- CO₂ emissions avoided

---

# ⚙ System Architecture

```
Restaurant Portal
        │
        ▼
FastAPI Backend
        │
        ▼
Orchestrator
        │
        ▼
Donation Agent
        │
        ▼
Quality Agent
        │
        ▼
Expiry Agent
        │
        ▼
Matching Agent
        │
        ▼
Routing Agent
        │
        ▼
Notification Agent
        │
        ▼
Impact Agent
        │
        ▼
Response + Live Dashboard
```

Every agent operates on a shared state object, making the architecture easy to extend with LangGraph.

---

# 🏗 Tech Stack

## Frontend

- HTML
- CSS
- JavaScript

## Backend

- FastAPI
- Pydantic
- Python

## AI

- Modular Agent Architecture
- Shared Agent State
- Explainable Decision Logic

## Data

- JSON datasets
- In-memory session state

Future upgrades:

- PostgreSQL
- LangGraph
- Vision Models
- LLM-powered extraction

---

# 📁 Project Structure

```
surplusai/

├── backend/
│   ├── main.py
│   ├── orchestrator.py
│   ├── agents/
│   │   ├── donation_agent.py
│   │   ├── quality_agent.py
│   │   ├── expiry_agent.py
│   │   ├── matching_agent.py
│   │   ├── routing_agent.py
│   │   ├── notification_agent.py
│   │   ├── impact_agent.py
│   │   └── state.py
│   └── data/
│       ├── ngos.json
│       └── volunteers.json
│
└── frontend/
    └── index.html
```

---

# 🌐 REST API

## POST /donate

Creates a new donation and executes the complete AI workflow.

Example:

```json
{
  "food_type": "Veg Thali",
  "quantity": 40,
  "pickup_time": "22:00"
}
```

Returns:

- Donation result
- Agent trace
- Selected NGO
- Volunteer assignment
- ETA
- Impact metrics

---

## GET /impact

Returns platform impact statistics.

---

## GET /ngos

Returns registered NGOs.

---

## GET /health

Health check endpoint.

---

# 🚀 Running the Project

## Backend

```bash
cd backend

pip install -r requirements.txt

uvicorn main:app --reload
```

Backend:

```
http://localhost:8000
```

Swagger Docs:

```
http://localhost:8000/docs
```

---

## Frontend

Open:

```
frontend/index.html
```

No build step required.

---

# 🎬 Demo Flow

1. Restaurant submits surplus food.
2. Donation enters the AI workflow.
3. Seven AI agents execute sequentially.
4. NGO is selected using weighted scoring.
5. Volunteer receives assignment.
6. Dashboard updates in real time.
7. Impact metrics increase.

Total demo time:

**~90 seconds**

---

# 📊 Explainable AI

Unlike traditional matching systems, every decision made by SurplusAI is transparent.

Example:

```
Need Match        0.91
Proximity         0.82
Capacity Fit      0.75
Urgency Bonus     0.93

Final Score       0.87
```

The selected NGO isn't simply the closest—it is the best overall match.

---

# 🔮 Future Roadmap

- LangGraph orchestration
- Vision AI for food inspection
- LLM-based donation extraction
- Google Maps routing
- WhatsApp notifications
- PostgreSQL persistence
- Real-time volunteer tracking
- IoT temperature sensors
- CSR analytics dashboard
- Government food rescue integration

---

# 🌍 Impact

Every successful donation contributes to:

- Reducing food waste
- Feeding vulnerable communities
- Lowering greenhouse gas emissions
- Improving coordination between food donors and NGOs

SurplusAI demonstrates how autonomous AI systems can solve meaningful real-world problems through explainable, collaborative decision-making.

---

# 👥 Team

Built for **HackAgentAIx** as an exploration of autonomous multi-agent systems for social impact.

**Every meal deserves a second chance.**
