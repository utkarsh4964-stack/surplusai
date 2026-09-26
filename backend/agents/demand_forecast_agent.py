"""
Demand Forecasting Agent
------------------------
Predicts near-term food demand and expected surplus for an institution
(institutional kitchen or food processing unit) using historical
consumption/production records.

Plugs into the shared-state pipeline the same way as the other agents:
    state = demand_forecast_agent(state)

Expected input in state:
    state["institution"] = {
        "id": str,
        "type": "kitchen" | "processing_unit",
        "capacity_kg": float,
        "historical_records": [
            {"date": "2026-09-01", "produced_kg": 120, "consumed_kg": 95},
            ...
        ]
    }

Adds to state:
    state["forecast"] = {
        "predicted_demand_kg": float,
        "predicted_surplus_kg": float,
        "confidence": float,        # 0-1, based on data volume + variance
        "trend": "rising" | "falling" | "stable",
        "method": "exp_smoothing"
    }

No external ML dependency required — uses exponential smoothing so it
runs anywhere. Swap `_exponential_smoothing` for Prophet/LSTM later
without touching the interface.
"""

from __future__ import annotations
from typing import Any


ALPHA = 0.4  # smoothing factor; higher = more weight on recent data
MIN_RECORDS_FOR_CONFIDENCE = 7


def _exponential_smoothing(series: list[float], alpha: float = ALPHA) -> float:
    if not series:
        return 0.0
    level = series[0]
    for value in series[1:]:
        level = alpha * value + (1 - alpha) * level
    return level


def _trend(series: list[float]) -> str:
    if len(series) < 2:
        return "stable"
    delta = series[-1] - series[0]
    span = max(abs(series[0]), 1e-6)
    pct_change = delta / span
    if pct_change > 0.1:
        return "rising"
    if pct_change < -0.1:
        return "falling"
    return "stable"


def _confidence(n_records: int, series: list[float]) -> float:
    if n_records == 0:
        return 0.0
    volume_score = min(n_records / MIN_RECORDS_FOR_CONFIDENCE, 1.0)
    if len(series) > 1:
        mean = sum(series) / len(series)
        variance = sum((x - mean) ** 2 for x in series) / len(series)
        stability_score = 1.0 / (1.0 + (variance ** 0.5) / (mean + 1e-6))
    else:
        stability_score = 0.5
    return round(0.6 * volume_score + 0.4 * stability_score, 2)


def demand_forecast_agent(state: dict[str, Any]) -> dict[str, Any]:
    institution = state.get("institution", {})
    records = institution.get("historical_records", [])

    produced = [r.get("produced_kg", 0.0) for r in records]
    consumed = [r.get("consumed_kg", 0.0) for r in records]

    predicted_demand = round(_exponential_smoothing(consumed), 2)
    predicted_production = round(_exponential_smoothing(produced), 2)
    predicted_surplus = max(round(predicted_production - predicted_demand, 2), 0.0)

    state["forecast"] = {
        "predicted_demand_kg": predicted_demand,
        "predicted_surplus_kg": predicted_surplus,
        "confidence": _confidence(len(records), consumed),
        "trend": _trend(consumed),
        "method": "exp_smoothing",
    }
    return state


if __name__ == "__main__":
    demo_state = {
        "institution": {
            "id": "inst-001",
            "type": "kitchen",
            "capacity_kg": 500,
            "historical_records": [
                {"date": "2026-09-20", "produced_kg": 300, "consumed_kg": 260},
                {"date": "2026-09-21", "produced_kg": 310, "consumed_kg": 255},
                {"date": "2026-09-22", "produced_kg": 305, "consumed_kg": 270},
                {"date": "2026-09-23", "produced_kg": 320, "consumed_kg": 265},
                {"date": "2026-09-24", "produced_kg": 315, "consumed_kg": 280},
                {"date": "2026-09-25", "produced_kg": 330, "consumed_kg": 275},
                {"date": "2026-09-26", "produced_kg": 325, "consumed_kg": 290},
            ],
        }
    }
    result = demand_forecast_agent(demo_state)
    print(result["forecast"])
