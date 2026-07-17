"""
Route Agent
-----------
Picks the fastest available volunteer for the winning NGO and computes a
real ETA from distance / vehicle speed, with a deterministic traffic
multiplier derived from pickup hour (rush-hour-aware, not random).
"""

import json
import os
from .state import log_step

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "volunteers.json")

RUSH_HOURS = {8, 9, 18, 19, 20}


def _load_volunteers():
    with open(_DATA_PATH) as f:
        return json.load(f)


def _traffic_multiplier(pickup_time: str) -> float:
    try:
        hour = int(pickup_time.split(":")[0])
    except (ValueError, IndexError):
        hour = 20
    return 1.4 if hour in RUSH_HOURS else 1.1


def run(state: dict) -> dict:
    volunteers = [v for v in _load_volunteers() if v["available"]]
    ngo = state["matching"]["winner"]
    pickup_time = state["donation"]["pickup_time"]

    # fastest effective volunteer = highest speed among available
    volunteer = max(volunteers, key=lambda v: v["speed_kmph"])
    multiplier = _traffic_multiplier(pickup_time)

    eta_minutes = max(4, round((ngo["distance_km"] / volunteer["speed_kmph"]) * 60 * multiplier))

    state["routing"] = {
        "volunteer": volunteer,
        "eta_minutes": eta_minutes,
        "traffic_multiplier": multiplier,
    }
    log_step(
        state,
        agent="Route Agent",
        detail=(
            f"Assigned {volunteer['name']} ({volunteer['vehicle']}). "
            f"Fastest route to {ngo['name']}: {eta_minutes} min ETA, traffic factored in."
        ),
        status="ok",
        stamp="Routed",
    )
    return state
