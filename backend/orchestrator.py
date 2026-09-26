"""
Orchestrator
------------
Runs the full SurplusAI agent pipeline over a shared state dict.

Assumes each existing agent module exposes a function named
`<name>_agent(state: dict) -> dict`, matching the pattern used by the
new agents (demand_forecast_agent, processing_monitor_agent,
sustainability_agent). If your existing agents export differently named
functions (e.g. `run()` or a class), rename the imports below to match —
only the import lines and the calls in run_pipeline() need adjusting.
"""

from __future__ import annotations
from typing import Any

from agents.demand_forecast_agent import demand_forecast_agent
from agents.donation_agent import donation_agent
from agents.processing_monitor_agent import processing_monitor_agent
from agents.quality_agent import quality_agent
from agents.expiry_agent import expiry_agent
from agents.matching_agent import matching_agent
from agents.routing_agent import routing_agent
from agents.notification_agent import notification_agent
from agents.sustainability_agent import sustainability_agent  # replaces impact_agent


def run_pipeline(initial_state: dict[str, Any]) -> dict[str, Any]:
    """
    Executes all agents in sequence on a shared state dict, mutating and
    passing it forward. Each stage's output becomes the next stage's input.
    """
    state = initial_state

    # 1. Forecast expected demand/surplus for the institution before
    #    processing this donation, so downstream agents can compare
    #    actuals against prediction.
    state = demand_forecast_agent(state)

    # 2. Normalize the incoming donation into a structured record.
    state = donation_agent(state)

    # 3. Pull in IoT/sensor telemetry and flag storage/machine issues.
    #    Sets state["quality_risk_flag"] if a storage temperature
    #    breach occurred, which quality_agent should check.
    state = processing_monitor_agent(state)

    # 4. Assess food safety/freshness (vision + heuristic), now aware
    #    of any processing-side risk flags.
    state = quality_agent(state)

    # 5. Predict remaining safe consumption window.
    state = expiry_agent(state)

    # 6. Score and select the best-matching NGO.
    state = matching_agent(state)

    # 7. Plan pickup/delivery logistics.
    state = routing_agent(state)

    # 8. Notify restaurant/institution, NGO, and volunteer.
    state = notification_agent(state)

    # 9. Compute sustainability/ESG metrics for this cycle
    #    (replaces the old impact_agent step).
    state = sustainability_agent(state)

    return state


def run_forecast_only(institution: dict[str, Any]) -> dict[str, Any]:
    """Lightweight path for the /forecast/{id} endpoint — no donation yet."""
    state = {"institution": institution}
    state = demand_forecast_agent(state)
    return state


def run_processing_check(
    institution: dict[str, Any], sensor_readings: list[dict[str, Any]]
) -> dict[str, Any]:
    """Lightweight path for /processing/status/{id}."""
    state = {"institution": institution, "sensor_readings": sensor_readings}
    state = demand_forecast_agent(state)
    state = processing_monitor_agent(state)
    return state


def run_sustainability_report(
    institution: dict[str, Any],
    sensor_readings: list[dict[str, Any]],
    donation_kg: float = 0.0,
) -> dict[str, Any]:
    """Lightweight path for /sustainability/report/{id}."""
    state = {
        "institution": institution,
        "sensor_readings": sensor_readings,
        "donation": {"quantity_kg": donation_kg},
    }
    state = demand_forecast_agent(state)
    state = processing_monitor_agent(state)
    state = sustainability_agent(state)
    return state
