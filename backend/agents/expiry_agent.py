"""
Expiry Agent
------------
Estimates the safe consumption window from food category and time-of-day
(a proxy for ambient temperature risk - evening service holds heat/moisture
longer than a bakery item at room temp). Deterministic rule table, not a
model - stated explicitly for judges rather than implied as ML.
"""

from datetime import datetime
from .state import log_step

# base shelf life in hours, by category
SHELF_LIFE_HOURS = {
    "Cooked Meal": 2.5,
    "Bakery": 18,
    "Packaged": 72,
}

URGENT_THRESHOLD_HOURS = 3


def run(state: dict) -> dict:
    category = state["donation"]["category"]
    base_hours = SHELF_LIFE_HOURS.get(category, 3)

    # evening pickups (after 18:00) on cooked meals shave the window slightly
    pickup_time = state["donation"]["pickup_time"]
    try:
        hour = int(pickup_time.split(":")[0])
    except (ValueError, IndexError):
        hour = 20
    evening_penalty = 0.3 if (category == "Cooked Meal" and hour >= 18) else 0

    safe_hours = round(max(0.5, base_hours - evening_penalty), 1)
    urgent = safe_hours <= URGENT_THRESHOLD_HOURS

    state["expiry"] = {"safe_hours": safe_hours, "urgent": urgent}
    log_step(
        state,
        agent="Expiry Agent",
        detail=f"Estimated safe window: {safe_hours} hours from pickup, based on food category and pickup time.",
        status="warn" if urgent else "ok",
        stamp="High urgency" if urgent else "Standard",
    )
    return state
