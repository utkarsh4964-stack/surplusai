"""
Processing Monitor Agent
------------------------
Consumes IoT/sensor telemetry from a food processing unit or kitchen
storage area and flags operational inefficiencies: storage temperature
excursions, machine downtime, excessive energy draw, and overproduction
relative to the Demand Forecasting Agent's prediction.

    state = processing_monitor_agent(state)

Expected input in state:
    state["sensor_readings"] = [
        {
            "timestamp": "2026-09-27T09:00:00",
            "storage_temp_c": 6.2,
            "storage_humidity_pct": 55,
            "machine_status": "running" | "idle" | "down",
            "energy_kwh": 12.4
        },
        ...
    ]
    state["thresholds"] = {          # optional, sane defaults used otherwise
        "max_storage_temp_c": 8.0,
        "max_humidity_pct": 70,
        "max_energy_kwh_per_reading": 15.0
    }
    state["forecast"]["predicted_production_kg"]  # optional, from demand_forecast_agent

Adds to state:
    state["processing_flags"] = {
        "storage_excursions": int,
        "machine_downtime_events": int,
        "energy_alerts": int,
        "overproduction_kg": float,
        "efficiency_score": float   # 0-1, higher is better
    }
"""

from __future__ import annotations
from typing import Any

DEFAULT_THRESHOLDS = {
    "max_storage_temp_c": 8.0,
    "max_humidity_pct": 70,
    "max_energy_kwh_per_reading": 15.0,
}


def processing_monitor_agent(state: dict[str, Any]) -> dict[str, Any]:
    readings = state.get("sensor_readings", [])
    thresholds = {**DEFAULT_THRESHOLDS, **state.get("thresholds", {})}

    storage_excursions = 0
    machine_downtime_events = 0
    energy_alerts = 0
    total_energy = 0.0

    for r in readings:
        if r.get("storage_temp_c", 0) > thresholds["max_storage_temp_c"]:
            storage_excursions += 1
        if r.get("storage_humidity_pct", 0) > thresholds["max_humidity_pct"]:
            storage_excursions += 1
        if r.get("machine_status") == "down":
            machine_downtime_events += 1
        energy = r.get("energy_kwh", 0.0)
        total_energy += energy
        if energy > thresholds["max_energy_kwh_per_reading"]:
            energy_alerts += 1

    actual_production = state.get("institution", {}).get("historical_records", [])
    actual_today = actual_production[-1]["produced_kg"] if actual_production else 0.0
    predicted = state.get("forecast", {}).get("predicted_demand_kg", 0.0)
    overproduction_kg = max(round(actual_today - predicted, 2), 0.0)

    n_readings = max(len(readings), 1)
    penalty = (
        (storage_excursions * 0.05)
        + (machine_downtime_events * 0.08)
        + (energy_alerts * 0.03)
        + (min(overproduction_kg / 100.0, 1.0) * 0.1)
    )
    efficiency_score = round(max(1.0 - min(penalty, 1.0), 0.0), 2)

    state["processing_flags"] = {
        "storage_excursions": storage_excursions,
        "machine_downtime_events": machine_downtime_events,
        "energy_alerts": energy_alerts,
        "overproduction_kg": overproduction_kg,
        "total_energy_kwh": round(total_energy, 2),
        "efficiency_score": efficiency_score,
    }

    # Feed spoilage-risk signal downstream to the Quality Agent
    if storage_excursions > 0:
        state["quality_risk_flag"] = "storage_temperature_breach"

    return state


if __name__ == "__main__":
    demo_state = {
        "institution": {"historical_records": [{"produced_kg": 340}]},
        "forecast": {"predicted_demand_kg": 280},
        "sensor_readings": [
            {"storage_temp_c": 5.1, "storage_humidity_pct": 60, "machine_status": "running", "energy_kwh": 11},
            {"storage_temp_c": 9.4, "storage_humidity_pct": 65, "machine_status": "running", "energy_kwh": 13},
            {"storage_temp_c": 6.0, "storage_humidity_pct": 58, "machine_status": "down", "energy_kwh": 0},
        ],
    }
    result = processing_monitor_agent(demo_state)
    print(result["processing_flags"], result.get("quality_risk_flag"))
