"""
Donation Agent
--------------
Takes the raw restaurant submission (free-form-ish fields from the form)
and normalizes it into a structured donation record: food type, quantity,
category, pickup deadline. Also mints the ticket ID.

In a fuller build this is where an LLM call would parse unstructured text
like "40 veg thalis, pickup before 10 PM" into these same fields. The
schema below is what that call would need to return, so swapping in a
real LLM parser later is a drop-in change (see NOTE at bottom).
"""

import itertools
from datetime import datetime
from .state import log_step

_ticket_counter = itertools.count(1001)

CATEGORY_MAP = {
    "Veg Thali": "Cooked Meal",
    "Rice Bowl": "Cooked Meal",
    "Mixed Meal": "Cooked Meal",
    "Roti / Chapati": "Cooked Meal",
    "Bakery Items": "Bakery",
    "Packaged Snacks": "Packaged",
}


def run(state: dict) -> dict:
    payload = state["input"]

    food_type = payload.get("food_type", "Mixed Meal")
    quantity = max(1, int(payload.get("quantity", 1)))
    pickup_time = payload.get("pickup_time", "22:00")
    category = CATEGORY_MAP.get(food_type, "Cooked Meal")

    ticket_id = f"TCK-{next(_ticket_counter)}"

    state["ticket_id"] = ticket_id
    state["donation"] = {
        "food_type": food_type,
        "quantity": quantity,
        "category": category,
        "pickup_time": pickup_time,
    }

    log_step(
        state,
        agent="Donation Agent",
        detail=f"Parsed submission → {quantity} × {food_type}. Category: {category}. "
               f"Pickup before {pickup_time}. Ticket {ticket_id} opened.",
        status="ok",
        stamp="Logged",
    )
    return state

# NOTE: to swap in a real LLM-based parser, replace the direct field reads
# above with a call to the Anthropic API using a prompt like:
#   "Extract food_type, quantity, pickup_time from: {raw_text}. Return JSON."
# and validate the result against CATEGORY_MAP before continuing.
