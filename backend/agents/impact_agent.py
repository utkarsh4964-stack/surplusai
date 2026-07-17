"""
Impact Agent
------------
Converts a completed donation into impact metrics and folds them into a
running session total (in-memory; swap for a DB in production).

Conversion assumptions (documented, not hidden):
- people_fed = meals * 0.5   (avg 2 meals per person served across a day)
- waste_kg   = meals * 0.3   (avg plate weight per meal)
- co2_kg     = waste_kg * 2.5 (emissions factor for landfilled food waste)
"""

from .state import log_step

PEOPLE_PER_MEAL = 0.5
KG_PER_MEAL = 0.3
CO2_PER_KG_WASTE = 2.5

# in-memory running totals for the demo session
_session_totals = {"meals": 0, "people": 0, "waste_kg": 0.0, "co2_kg": 0.0, "donations": 0}


def get_totals() -> dict:
    return dict(_session_totals)


def run(state: dict) -> dict:
    quantity = state["donation"]["quantity"]

    people_fed = round(quantity * PEOPLE_PER_MEAL)
    waste_kg = round(quantity * KG_PER_MEAL, 1)
    co2_kg = round(waste_kg * CO2_PER_KG_WASTE, 1)

    _session_totals["meals"] += quantity
    _session_totals["people"] += people_fed
    _session_totals["waste_kg"] = round(_session_totals["waste_kg"] + waste_kg, 1)
    _session_totals["co2_kg"] = round(_session_totals["co2_kg"] + co2_kg, 1)
    _session_totals["donations"] += 1

    state["impact"] = {
        "meals": quantity,
        "people_fed": people_fed,
        "waste_kg": waste_kg,
        "co2_kg": co2_kg,
        "session_totals": get_totals(),
    }
    state["status"] = "completed"

    log_step(
        state,
        agent="Impact Agent",
        detail=(
            f"Dashboard updated: {quantity} meals rescued, {people_fed} people fed, "
            f"{waste_kg} kg waste prevented, {co2_kg} kg CO2 avoided."
        ),
        status="ok",
        stamp="Complete",
    )
    return state
