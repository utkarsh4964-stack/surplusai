"""
Route Agent
-----------
Picks the best available volunteer for the winning NGO and computes an
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

Volunteer selection: picks the available volunteer with the lowest
estimated ETA to the NGO (distance / speed), not simply the volunteer
with the highest top speed - a fast rider halfway across town is often
slower door-to-door than a slower rider next door.
"""

import json
import math
import os
from .state import log_step

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "volunteers.json")

RUSH_HOURS = {8, 9, 18, 19, 20}
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")

# Vehicles that are actually human-powered - only these should ever be
# routed with Google Maps' "bicycling" mode. Motorized two-wheelers
# (Scooter, Bike meaning motorbike in this dataset's context, etc.) get
# "driving" so ETAs reflect real road/traffic speed, not cycling speed.
NON_MOTORIZED_VEHICLES = {"Cycle", "Bicycle"}


def _load_volunteers():
    with open(_DATA_PATH) as f:
        return json.load(f)


def _traffic_multiplier(pickup_time: str) -> float:
    try:
        hour = int(pickup_time.split(":")[0])
    except (ValueError, IndexError):
        hour = 20
    return 1.4 if hour in RUSH_HOURS else 1.1


def _haversine_km(lat1, lng1, lat2, lng2) -> float:
    R = 6371.0
    dlat, dlng = math.radians(lat2 - lat1), math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _pick_best_volunteer(volunteers: list, ngo: dict):
    """Choose the available volunteer with the lowest straight-line-based
    ETA to the NGO, not just the fastest vehicle. Returns None if no
    volunteer is available."""
    if not volunteers:
        return None
    if "lat" not in ngo or "lng" not in ngo:
        # no coordinates to compare against - fall back to fastest vehicle
        return max(volunteers, key=lambda v: v["speed_kmph"])

    def est_minutes(v):
        dist = _haversine_km(v["lat"], v["lng"], ngo["lat"], ngo["lng"])
        return (dist / max(v["speed_kmph"], 1)) * 60

    return min(volunteers, key=est_minutes)


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
        mode = "bicycling" if volunteer.get("vehicle") in NON_MOTORIZED_VEHICLES else "driving"
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

    volunteer = _pick_best_volunteer(volunteers, ngo)

    if volunteer is None:
        state["routing"] = {"volunteer": None, "eta_minutes": None, "method": "none"}
        log_step(
            state,
            agent="Route Agent",
            detail="No volunteers currently available - donation matched but pickup is unassigned. "
                   "Restaurant/NGO notified to arrange pickup manually.",
            status="warn",
            stamp="Unassigned",
        )
        return state

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
