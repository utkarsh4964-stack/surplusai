"""
Sustainability / ESG Agent (replaces impact_agent.py)
------------------------------------------------------
Aggregates rescue outcomes and processing efficiency into sustainability
analytics: waste-prevention rate, CO2 avoided, resource-efficiency index,
and an ESG-style compliance summary institutions can export.

    state = sustainability_agent(state)

Expected input in state (populated upstream by earlier agents):
    state["donation"]           = {"quantity_kg": float, ...}
    state["forecast"]           = {"predicted_surplus_kg": float, ...}
    state["processing_flags"]   = {"efficiency_score": float, "overproduction_kg": float, ...}
    state["matching"]           = {"ngo_id": str, ...}   # optional

Adds to state:
    state["sustainability_report"] = {
        "meals_rescued": int,
        "food_waste_prevented_kg": float,
        "co2_avoided_kg": float,
        "waste_prevention_pct": float,
        "resource_efficiency_index": float,   # 0-1
        "esg_summary": {
            "environmental": str,
            "social": str,
            "governance": str,
        }
    }

Constants below are standard food-rescue estimation factors used across
similar platforms (kg food -> meals, kg food -> CO2e); swap for
verified LCA figures if the institution provides its own.
"""

from __future__ import annotations
from typing import Any

KG_PER_MEAL = 0.4          # avg meal weight
CO2E_PER_KG_FOOD = 2.5     # kg CO2e avoided per kg food diverted from landfill


def sustainability_agent(state: dict[str, Any]) -> dict[str, Any]:
    donation_kg = state.get("donation", {}).get("quantity_kg", 0.0)
    predicted_surplus = state.get("forecast", {}).get("predicted_surplus_kg", 0.0)
    efficiency_score = state.get("processing_flags", {}).get("efficiency_score", 1.0)
    overproduction_kg = state.get("processing_flags", {}).get("overproduction_kg", 0.0)

    meals_rescued = int(donation_kg / KG_PER_MEAL) if donation_kg else 0
    co2_avoided = round(donation_kg * CO2E_PER_KG_FOOD, 2)

    denom = predicted_surplus if predicted_surplus > 0 else max(donation_kg, 1.0)
    waste_prevention_pct = round(min(donation_kg / denom, 1.0) * 100, 1)

    resource_efficiency_index = round(
        (0.6 * efficiency_score) + (0.4 * (1 - min(overproduction_kg / 100.0, 1.0))), 2
    )

    esg_summary = {
        "environmental": f"{co2_avoided} kg CO2e avoided; "
                          f"{round(donation_kg, 1)} kg food diverted from landfill.",
        "social": f"~{meals_rescued} meals made available to NGOs/shelters this cycle.",
        "governance": f"Resource efficiency index {resource_efficiency_index} "
                      f"(processing efficiency {efficiency_score}, "
                      f"overproduction {overproduction_kg} kg).",
    }

    state["sustainability_report"] = {
        "meals_rescued": meals_rescued,
        "food_waste_prevented_kg": round(donation_kg, 2),
        "co2_avoided_kg": co2_avoided,
        "waste_prevention_pct": waste_prevention_pct,
        "resource_efficiency_index": resource_efficiency_index,
        "esg_summary": esg_summary,
    }
    return state


if __name__ == "__main__":
    demo_state = {
        "donation": {"quantity_kg": 40},
        "forecast": {"predicted_surplus_kg": 45},
        "processing_flags": {"efficiency_score": 0.85, "overproduction_kg": 10},
    }
    result = sustainability_agent(demo_state)
    print(result["sustainability_report"])
