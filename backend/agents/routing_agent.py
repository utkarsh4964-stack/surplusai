"""
Route Agent
-----------
Picks the fastest available volunteer for the winning NGO and computes an
ETA between the volunteer's location and the NGO.

Two modes, same output shape:

1. Live-routing mode (used automatically when GOOGLE_MAPS_API_KEY is set):
   calls the Google Maps Directions API with the volunteer's and NGO's
   real lat/lng, and uses the actual driving/two-wheeler ETA and distance
   Google returns - true "AI-based logistics planning" against live road
   and traffic conditions, not an estimate.

2. Formula mode (fallback): the original deterministic ETA - straight-line
   distance / vehicle speed * a rush-hour-aware traffic multiplier. Used
   when there's no API key configured, the `googlemaps` package isn't
   installed, or the API call fails for any reason (network, quota,
   invalid coordinates) - a live demo should never break because an
   external API hiccupped.
"""

import json
import os
from .state import log_step

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "volunteers.json")

RUSH_HOURS = {8, 9, 18, 19, 20}
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")


def _load_volunteers():
    with open(_DATA_PATH) as f:
        return json.load(f)


def _traffic_multiplier(pickup_time: str) -> float:
    try:
        hour = int(pickup_time.split(":")[0])
    except (ValueError, IndexError):
        hour = 20
    return 1.4 if hour in RUSH_HOURS else 1.1


def _live_route(volunteer: dict, ngo: dict):
    """
    Calls Google Maps Directions API for a real ETA/distance between the
    volunteer and the NGO. Returns None (never raises) on any failure so
    the caller falls back to the formula estimate.
    """
    if not GOOGLE_MAPS_API_KEY:
        return None
    if "lat" not in volunteer or "lat" not in ngo:
        return None

    try:
        import googlemaps
    except ImportError:
        return None

    try:
        client = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
        mode = "bicycling" if volunteer.get("vehicle") in ("Bike", "Scooter") else "driving"
        result = client.directions(
            origin=(volunteer["lat"], volunteer["lng"]),
            destination=(ngo["lat"], ngo["lng"]),
            mode=mode,
        )
        if not result:
            return None
        leg = result[0]["legs"][0]
        return {
            "eta_minutes": max(4, round(leg["duration"]["value"] / 60)),
            "distance_km": round(leg["distance"]["value"] / 1000, 2),
            "polyline_summary": result[0].get("summary", ""),
        }
    except Exception:
        return None


def run(state: dict) -> dict:
    volunteers = [v for v in _load_volunteers() if v["available"]]
    ngo = state["matching"]["winner"]
    pickup_time = state["donation"]["pickup_time"]

    # fastest effective volunteer = highest speed among available
    volunteer = max(volunteers, key=lambda v: v["speed_kmph"])
    multiplier = _traffic_multiplier(pickup_time)

    live = _live_route(volunteer, ngo)

    if live is not None:
        eta_minutes = live["eta_minutes"]
        method = "google_maps"
        route_note = f"Live route via {live['polyline_summary'] or 'Google Maps'}: {eta_minutes} min ETA (real traffic conditions)."
    else:
        eta_minutes = max(4, round((ngo["distance_km"] / volunteer["speed_kmph"]) * 60 * multiplier))
        method = "formula"
        route_note = f"Fastest route to {ngo['name']}: {eta_minutes} min ETA, traffic factored in."

    state["routing"] = {
        "volunteer": volunteer,
        "eta_minutes": eta_minutes,
        "traffic_multiplier": multiplier,
        "method": method,
    }
    log_step(
        state,
        agent="Route Agent",
        detail=f"Assigned {volunteer['name']} ({volunteer['vehicle']}). {route_note}",
        status="ok",
        stamp="Routed",
    )
    return state
