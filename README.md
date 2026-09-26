# 🍲 SurplusAI
### AI Workforce for Food Rescue & Institutional Food Waste Management

> **Every meal deserves a second chance.**

SurplusAI is an autonomous multi-agent platform that rescues surplus food from restaurants, hotels, bakeries, and events, intelligently matches it with NGOs, plans deliveries, coordinates volunteers, and measures real-world impact — all with minimal human intervention.

It now also extends into **institutional kitchens and food processing units**: forecasting demand before surplus happens, monitoring storage/machine health from IoT sensor data, and generating ESG-ready sustainability reports — aligned with SIH Problem Statement **26234** (*AI-Powered Smart Food Waste Reduction and Sustainable Redistribution Ecosystem for Institutional Kitchens and Food Processing Units*).

Instead of relying on phone calls, WhatsApp groups, or manual coordination, SurplusAI uses a team of specialized AI agents that collaborate to complete the entire rescue and waste-prevention workflow.

---

# 🚨 The Problem

Every day:

- 🍽 Restaurants discard perfectly edible meals.
- 🏨 Hotels throw away buffet leftovers.
- 🥖 Bakeries dispose of unsold bread.
- 🎉 Events generate large amounts of food waste.
- 🏭 Institutional kitchens and food processing units overproduce, lose raw material, and run inefficient storage — often without knowing it until the waste is already generated.

Meanwhile:

- NGOs
- Orphanages
- Homeless shelters
- Community kitchens

struggle to provide meals because they don't know where surplus food is available.

The challenge isn't food production.

**It's coordination — and the lack of foresight to prevent the waste before it happens.**

---

# 💡 Our Solution

SurplusAI transforms food rescue into an autonomous AI workflow, and extends it upstream into prevention.

A restaurant or institution only needs to submit a donation once, or simply stay connected — everything else is handled automatically.

```text
Institution / Restaurant
      │
      ▼
🤖 AI Workforce
      │
      ▼
NGO receives food  +  Institution gets forecast, sensor alerts & ESG report
```

The AI system:

- Forecasts demand and expected surplus before it's generated
- Monitors storage and machine conditions via IoT sensor data
- Understands the donation
- Verifies food quality
- Predicts urgency
- Finds the best NGO
- Plans the fastest route
- Assigns a volunteer
- Notifies everyone
- Tracks sustainability and ESG impact

---

# 🤖 AI Workforce

SurplusAI is powered by **ten specialized AI agents** — the original seven-agent rescue pipeline, plus three new agents for institutional kitchens and food processing units.

## 📈 Demand Forecasting Agent *(new)*

Predicts near-term demand and expected surplus for an institution using historical consumption/production records (exponential smoothing).

Responsibilities:

- Forecast predicted demand and surplus (kg)
- Report forecast confidence and trend (rising / falling / stable)
- Feed downstream agents so actuals can be compared against prediction

---

## 📡 Processing Monitor Agent *(new)*

Ingests IoT/sensor telemetry from storage and machinery and flags operational inefficiencies.

Responsibilities:

- Detect storage temperature/humidity excursions
- Detect machine downtime events
- Detect excessive energy draw
- Compute overproduction relative to the forecast
- Compute a processing efficiency score
- Flag spoilage risk upstream to the Quality Agent on a storage breach

---

## 🥘 Donation Agent

Converts restaurant/institution submissions into structured donation records.

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

- Restaurant / Institution
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

Measures real-world impact for the donation-ticket pipeline.

Tracks:

- Meals rescued
- People fed
- Food waste prevented
- CO₂ emissions avoided

---

## 🌍 Sustainability / ESG Agent *(new)*

Aggregates rescue outcomes and processing efficiency into ESG-ready sustainability analytics for an institution.

Tracks:

- Meals rescued & food waste prevented (kg)
- CO₂ avoided
- Waste-prevention percentage vs. forecasted surplus
- Resource-efficiency index
- An ESG summary (Environmental / Social / Governance) exportable per institution

---

# ⚙ System Architecture

```
Institution / Restaurant Portal
        │
        ▼
FastAPI Backend
        │
        ▼
Orchestrator
        │
   ┌────┴──────────────────────────────┐
   ▼                                    │
Demand Forecast Agent ───► Donation Agent
   │                                    │
   ▼                                    ▼
Processing Monitor Agent ──────► Quality Agent
   │                                    │
   │                                    ▼
   │                              Expiry Agent
   │                                    │
   │                                    ▼
   │                             Matching Agent
   │                                    │
   │                                    ▼
   │                              Routing Agent
   │                                    │
   │                                    ▼
   │                          Notification Agent
   │                                    │
   │                                    ▼
   │                              Impact Agent
   │                                    │
   └──────────────► Sustainability / ESG Agent
                                        │
                                        ▼
                          Response + Live Dashboard
```

Every agent operates on a shared state object, making the architecture easy to extend with LangGraph. The Demand Forecast, Processing Monitor and Sustainability agents run on an **institution-scoped** state (used by `/forecast`, `/processing/status`, `/sustainability/report`), separate from the **donation-ticket** state used by `/donate` — they share the same design pattern but different inputs, since a single donation ticket has no attached institution history or live sensor feed.

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
- Exponential-smoothing demand forecasting (swappable for Prophet/LSTM)
- Rule-based IoT anomaly detection (swappable for a trained anomaly model)

## Data

- JSON datasets
- In-memory session state
- Mock IoT sensor stream (`sensor_stream.json`) for demo purposes

Future upgrades:

- PostgreSQL
- LangGraph
- Vision Models
- LLM-powered extraction
- Real IoT sensor integration (MQTT/HTTP ingestion)
- Time-series forecasting models (Prophet, LSTM)

---

# 📁 Project Structure

```
surplusai/

├── backend/
│   ├── main.py
│   ├── orchestrator.py
│   ├── agents/
│   │   ├── demand_forecast_agent.py
│   │   ├── donation_agent.py
│   │   ├── processing_monitor_agent.py
│   │   ├── quality_agent.py
│   │   ├── expiry_agent.py
│   │   ├── matching_agent.py
│   │   ├── routing_agent.py
│   │   ├── notification_agent.py
│   │   ├── impact_agent.py
│   │   ├── sustainability_agent.py
│   │   └── state.py
│   └── data/
│       ├── ngos.json
│       ├── volunteers.json
│       ├── institutions.json
│       └── sensor_stream.json
│
└── frontend/
    ├── index.html
    ├── app.js
    └── style.css
```

---

# 🌐 REST API

## POST /donate

Creates a new donation and executes the complete 7-agent rescue pipeline.

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

## GET /institutions

Returns registered institutions (kitchens and food processing units).

---

## GET /forecast/{institution_id}

Returns the demand/surplus forecast for one institution.

Example response:

```json
{
  "predicted_demand_kg": 279.27,
  "predicted_surplus_kg": 42.39,
  "confidence": 0.98,
  "trend": "rising",
  "method": "exp_smoothing"
}
```

---

## GET /processing/status/{institution_id}

Returns IoT/sensor anomaly flags and processing efficiency for one institution.

Example response:

```json
{
  "storage_excursions": 1,
  "machine_downtime_events": 1,
  "energy_alerts": 0,
  "overproduction_kg": 45.73,
  "total_energy_kwh": 36.5,
  "efficiency_score": 0.82
}
```

---

## GET /sustainability/report/{institution_id}?donation_kg=

Returns an ESG-style sustainability report for one institution.

Example response:

```json
{
  "meals_rescued": 100,
  "food_waste_prevented_kg": 40,
  "co2_avoided_kg": 100.0,
  "waste_prevention_pct": 94.4,
  "resource_efficiency_index": 0.71,
  "esg_summary": {
    "environmental": "...",
    "social": "...",
    "governance": "..."
  }
}
```

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

No build step required. Includes an "🏭 Institutions" tab alongside Donor / NGO Partner / Volunteer / Impact Center.

---

# 🎬 Demo Flow

**Rescue pipeline:**

1. Restaurant/institution submits surplus food.
2. Donation enters the AI workflow.
3. Seven AI agents execute sequentially.
4. NGO is selected using weighted scoring.
5. Volunteer receives assignment.
6. Dashboard updates in real time.
7. Impact metrics increase.

**Institution dashboard:**

1. Select an institution (kitchen or processing unit).
2. Demand Forecasting Agent predicts upcoming surplus.
3. Processing Monitor Agent reports live sensor status and efficiency.
4. Sustainability Agent generates an ESG report for the cycle.

Total demo time:

**~90 seconds** (rescue pipeline) **+ ~30 seconds** (institution dashboard)

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

The selected NGO isn't simply the closest—it is the best overall match. Forecasts, processing flags, and ESG scores are similarly broken down into their component metrics rather than returned as opaque numbers.

---

# ✅ Alignment with PS 26234

| PS 26234 requirement | SurplusAI component |
|---|---|
| Predict food demand and surplus in real time | Demand Forecasting Agent |
| Identify items nearing expiry/quality deterioration | Quality Agent + Expiry Prediction Agent |
| Connect surplus food with NGOs/food banks/shelters | Matching Agent |
| Optimize transportation and delivery routes | Route Planning Agent |
| Monitor processing efficiency, storage, operational performance | Processing Monitor Agent |
| Detect overproduction, raw material loss, downtime, energy usage | Processing Monitor Agent |
| Generate sustainability/ESG analytics | Sustainability / ESG Agent |
| Support data-driven production planning | Demand Forecasting Agent + institution dashboard |

---

# 🔮 Future Roadmap

- LangGraph orchestration
- Vision AI for food inspection
- LLM-based donation extraction
- Google Maps routing
- WhatsApp notifications
- PostgreSQL persistence
- Real-time volunteer tracking
- Real IoT sensor integration (current version uses a mock stream)
- Time-series forecasting models (Prophet, LSTM) in place of exponential smoothing
- CSR/ESG analytics dashboard export (PDF)
- Government food rescue integration

---

# 🌍 Impact

Every successful donation, and every institution using the forecast/processing/sustainability tools, contributes to:

- Reducing food waste before and after it's generated
- Feeding vulnerable communities
- Lowering greenhouse gas emissions
- Improving coordination between food donors and NGOs
- Helping institutional kitchens and food processing units plan production and meet ESG goals

SurplusAI demonstrates how autonomous AI systems can solve meaningful real-world problems through explainable, collaborative decision-making — from the moment food is planned, to the moment it's rescued.

---

**Every meal deserves a second chance.**
