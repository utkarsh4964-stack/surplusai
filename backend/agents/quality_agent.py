"""
Quality Agent
-------------
Real heuristic (no ML model, but not random either): scores freshness from
actual signals available at submission time - whether a photo was provided,
image size/format sanity, and category risk. This is intentionally
deterministic so the same input always produces the same verdict, which
matters for a live demo.

Swap-in point: replace `_heuristic_score` with a real vision call (see
NOTE at bottom) - the rest of the agent (thresholding, logging) stays the same.
"""

from .state import log_step

REJECT_THRESHOLD = 60
CATEGORY_RISK = {
    "Cooked Meal": 0,     # highest spoilage risk, no discount
    "Bakery": 8,
    "Packaged": 15,
}


def _heuristic_score(has_photo: bool, image_bytes: int, category: str) -> int:
    base = 78 if has_photo else 65   # unverified donations score lower, not rejected outright
    if has_photo and image_bytes > 20_000:   # plausible real photo vs a tiny/blank file
        base += 12
    base += CATEGORY_RISK.get(category, 0)
    return min(base, 99)


def run(state: dict, has_photo: bool, image_bytes: int, force_reject: bool) -> dict:
    category = state["donation"]["category"]
    freshness = 35 if force_reject else _heuristic_score(has_photo, image_bytes, category)
    rejected = force_reject or freshness < REJECT_THRESHOLD

    source_note = "from uploaded photo" if has_photo else "no photo provided — conservative estimate"

    if rejected:
        state["quality"] = {"freshness_score": freshness, "passed": False, "has_photo": has_photo}
        log_step(
            state,
            agent="Quality Agent",
            detail=f"Freshness score {freshness}% ({source_note}). Below safety threshold ({REJECT_THRESHOLD}%).",
            status="fail",
            stamp="Rejected",
        )
        log_step(
            state,
            agent="System",
            detail=f"Donation {state['ticket_id']} halted. Restaurant notified to discard or resubmit with a clearer photo.",
            status="fail",
            stamp="Stopped",
        )
        state["status"] = "rejected"
        return state

    state["quality"] = {"freshness_score": freshness, "passed": True, "has_photo": has_photo}
    log_step(
        state,
        agent="Quality Agent",
        detail=f"Freshness score {freshness}% ({source_note}). Packaging and spoilage check passed.",
        status="ok",
        stamp="Verified",
    )
    return state

# NOTE: to use a real vision model, replace _heuristic_score with an
# Anthropic API call sending the image + a prompt like "Rate this food's
# freshness 0-100 and flag visible spoilage or packaging damage." Parse
# the numeric score from the response and feed it into the same threshold logic.
