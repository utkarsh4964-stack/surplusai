"""
Shared pipeline state. Every agent receives this dict, mutates its own
section, and returns it. This is what the orchestrator threads through
the agent graph, and what gets serialized back to the frontend as the
live pipeline trace.
"""

from datetime import datetime
from typing import Any, Dict


def new_ticket_state(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "ticket_id": None,
        "input": payload,          # raw submission from Restaurant Portal
        "steps": [],                # ordered trace of what each agent did (for UI)
        "donation": {},             # Donation Agent output
        "quality": {},              # Quality Agent output
        "expiry": {},                # Expiry Agent output
        "matching": {},              # Matching Agent output
        "routing": {},                # Route Agent output
        "notifications": {},          # Notification Agent output
        "impact": {},                  # Impact Agent output
        "status": "processing",         # processing | rejected | completed
        "created_at": datetime.utcnow().isoformat(),
    }


def log_step(state: Dict[str, Any], agent: str, detail: str, status: str = "ok", stamp: str = ""):
    """Append a trace entry. status: ok | warn | fail"""
    state["steps"].append({
        "agent": agent,
        "detail": detail,
        "status": status,
        "stamp": stamp,
        "at": datetime.utcnow().isoformat(),
    })
