"""
Orchestrator
------------
Runs the 7 agents in sequence, threading a single state dict through each.
Structured deliberately like a LangGraph StateGraph (nodes + edges) so
swapping in real LangGraph later is a rename, not a rewrite - see NOTE
at the bottom.

Also exposes 3 lightweight, institution-level entry points used by the
demand-forecast / processing-monitor / sustainability-ESG endpoints added
for PS 26234 (institutional kitchens & food processing units). These run
on a separate, institution-scoped state shape — they do NOT feed into the
donation ticket pipeline below, since a /donate submission has no
institution_id, historical_records, or sensor_readings attached to it.
"""

from typing import Any

from agents import (
    donation_agent,
    quality_agent,
    expiry_agent,
    matching_agent,
    routing_agent,
    notification_agent,
    impact_agent,
)
from agents.state import new_ticket_state
from agents.demand_forecast_agent import demand_forecast_agent
from agents.processing_monitor_agent import processing_monitor_agent
from agents.sustainability_agent import sustainability_agent


def run_pipeline(payload: dict, has_photo: bool, image_bytes: int, force_reject: bool) -> dict:
    state = new_ticket_state(payload)

    state = donation_agent.run(state)

    state = quality_agent.run(state, has_photo=has_photo, image_bytes=image_bytes, force_reject=force_reject)
    if state["status"] == "rejected":
        return state   # edge: Quality Agent fail -> pipeline halts here

    state = expiry_agent.run(state)
    state = matching_agent.run(state)
    state = routing_agent.run(state)
    state = notification_agent.run(state)
    state = impact_agent.run(state)

    return state

# NOTE: to migrate to real LangGraph, define each agent as a node
# (`graph.add_node("quality", quality_agent.run)`), add a conditional edge
# from "quality" -> END when state["status"] == "rejected", otherwise ->
# "expiry", and chain the rest linearly. The agent functions themselves
# don't need to change since they already take/return the shared state dict.


# ---------------------------------------------------------------------------
# Institution-level entry points (PS 26234: demand forecasting, IoT/processing
# monitoring, ESG/sustainability reporting for kitchens & processing units)
# ---------------------------------------------------------------------------

def run_forecast_only(institution: dict[str, Any]) -> dict[str, Any]:
    """Used by GET /forecast/{institution_id}."""
    state: dict[str, Any] = {"institution": institution}
    state = demand_forecast_agent(state)
    return state


def run_processing_check(
    institution: dict[str, Any], sensor_readings: list[dict[str, Any]]
) -> dict[str, Any]:
    """Used by GET /processing/status/{institution_id}."""
    state: dict[str, Any] = {"institution": institution, "sensor_readings": sensor_readings}
    state = demand_forecast_agent(state)
    state = processing_monitor_agent(state)
    return state


def run_sustainability_report(
    institution: dict[str, Any],
    sensor_readings: list[dict[str, Any]],
    donation_kg: float = 0.0,
) -> dict[str, Any]:
    """Used by GET /sustainability/report/{institution_id}."""
    state: dict[str, Any] = {
        "institution": institution,
        "sensor_readings": sensor_readings,
        "donation": {"quantity_kg": donation_kg},
    }
    state = demand_forecast_agent(state)
    state = processing_monitor_agent(state)
    state = sustainability_agent(state)
    return state
