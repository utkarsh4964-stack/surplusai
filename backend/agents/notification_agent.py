"""
Notification Agent
-------------------
Builds the notification set for every stakeholder. In production this
would call Twilio/SMS/WhatsApp/email APIs; here it produces the exact
payload each channel would send, which is what a real integration needs.

Handles the case where the Route Agent could not assign a volunteer
(state["routing"]["volunteer"] is None) - the restaurant and NGO still
get notified, just without pickup/ETA details.
"""

from datetime import datetime
from .state import log_step


def run(state: dict) -> dict:
    ticket_id = state["ticket_id"]
    donation = state["donation"]
    ngo = state["matching"]["winner"]
    volunteer = state["routing"]["volunteer"]
    eta = state["routing"]["eta_minutes"]

    if volunteer is None:
        notifications = {
            "restaurant": f"Ticket {ticket_id} matched to {ngo['name']}. No volunteer available yet - "
                          f"we'll notify you the moment one is assigned.",
            "volunteer": None,
            "ngo": f"Incoming: {donation['quantity']} × {donation['food_type']} from Restaurant. "
                   f"Pickup volunteer not yet assigned - please coordinate directly if urgent.",
            "sent_at": datetime.utcnow().isoformat(),
        }
        state["notifications"] = notifications
        log_step(
            state,
            agent="Notification Agent",
            detail=f"Notified Restaurant and {ngo['name']} - no volunteer available to notify yet.",
            status="warn",
            stamp="Partial",
        )
        return state

    notifications = {
        "restaurant": f"Ticket {ticket_id} matched to {ngo['name']}. {volunteer['name']} arriving for pickup.",
        "volunteer": f"New task: collect {donation['quantity']} × {donation['food_type']} and deliver to {ngo['name']}. ETA {eta} min.",
        "ngo": f"Incoming: {donation['quantity']} × {donation['food_type']} from Restaurant, arriving in ~{eta} min via {volunteer['name']}.",
        "sent_at": datetime.utcnow().isoformat(),
    }

    state["notifications"] = notifications
    log_step(
        state,
        agent="Notification Agent",
        detail=f"Notified Restaurant, {volunteer['name']}, and {ngo['name']} with pickup and delivery details.",
        status="ok",
        stamp="Sent",
    )
    return state
