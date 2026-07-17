"""
Orchestrator
------------
Runs the 7 agents in sequence, threading a single state dict through each.
Structured deliberately like a LangGraph StateGraph (nodes + edges) so
swapping in real LangGraph later is a rename, not a rewrite - see NOTE
at the bottom.
"""

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
