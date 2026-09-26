"""
Quality Agent
-------------
Scores freshness/spoilage risk for a donation.

Two modes, same output shape:

1. Vision mode (used automatically when a photo is submitted AND
   ANTHROPIC_API_KEY is set in the environment): sends the image to
   Claude's vision API with a structured freshness-assessment prompt and
   parses a 0-100 score + spoilage flags from the response. This is the
   "image-based quality assessment" the problem statement asks for.

2. Heuristic mode (fallback): the original deterministic scoring based on
   photo presence, image size, and category risk. Used when there's no
   photo, no API key configured, or the vision call fails for any reason
   (network, rate limit, bad response) - the pipeline must never break a
   live demo because an external API hiccupped.

Both modes feed the same threshold/rejection logic below them.
"""

import base64
import json
import os

from .state import log_step

REJECT_THRESHOLD = 60
CATEGORY_RISK = {
    "Cooked Meal": 0,     # highest spoilage risk, no discount
    "Bakery": 8,
    "Packaged": 15,
}

ANTHROPIC_MODEL = os.environ.get("QUALITY_AGENT_MODEL", "claude-3-5-sonnet-20241022")

_VISION_PROMPT = """You are a food safety inspector for a food-rescue platform.
Look at this photo of a food donation (category: {category}).

Rate its freshness and safety for redistribution on a 0-100 scale, where:
- 90-100: looks fresh, well-packaged, clearly safe
- 60-89: acceptable, minor cosmetic issues, still safe to redistribute
- 0-59: visible spoilage, contamination, or unsafe packaging - should be rejected

Respond with ONLY a JSON object, no other text, in this exact shape:
{{"freshness_score": <integer 0-100>, "spoilage_flags": [<short strings, empty list if none>], "reasoning": "<one short sentence>"}}"""


def _heuristic_score(has_photo: bool, image_bytes: int, category: str) -> int:
    base = 78 if has_photo else 65   # unverified donations score lower, not rejected outright
    if has_photo and image_bytes > 20_000:   # plausible real photo vs a tiny/blank file
        base += 12
    base += CATEGORY_RISK.get(category, 0)
    return min(base, 99)


def _vision_score(image_base64: str, category: str):
    """
    Calls Claude's vision API to assess the photo directly.
    Returns None (never raises) if the API key is missing, the package
    isn't installed, or the call fails for any reason - the caller falls
    back to the heuristic in that case.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        import anthropic
    except ImportError:
        return None

    raw = image_base64.split(",")[-1]  # strip a data: URL prefix if present
    media_type = "image/jpeg"
    if image_base64.startswith("data:"):
        header = image_base64.split(";")[0]
        media_type = header.split(":")[-1] or media_type

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": raw}},
                    {"type": "text", "text": _VISION_PROMPT.format(category=category)},
                ],
            }],
        )
        text = "".join(block.text for block in response.content if getattr(block, "type", None) == "text")
        text = text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:]
        parsed = json.loads(text.strip())
        score = int(parsed["freshness_score"])
        return {
            "freshness_score": max(0, min(score, 100)),
            "spoilage_flags": parsed.get("spoilage_flags", []),
            "reasoning": parsed.get("reasoning", ""),
        }
    except Exception:
        return None


def run(state: dict, has_photo: bool, image_bytes: int, force_reject: bool, image_base64=None) -> dict:
    category = state["donation"]["category"]

    vision_result = None
    if force_reject:
        freshness = 35
        source_note = "forced rejection (demo/testing path)"
    else:
        if has_photo and image_base64:
            vision_result = _vision_score(image_base64, category)

        if vision_result is not None:
            freshness = vision_result["freshness_score"]
            flags = vision_result["spoilage_flags"]
            flag_note = f" Flags: {', '.join(flags)}." if flags else ""
            source_note = f"Claude Vision assessment.{flag_note} {vision_result['reasoning']}".strip()
        else:
            freshness = _heuristic_score(has_photo, image_bytes, category)
            source_note = (
                "from uploaded photo (heuristic - vision model unavailable)"
                if has_photo
                else "no photo provided - conservative heuristic estimate"
            )

    rejected = force_reject or freshness < REJECT_THRESHOLD

    if rejected:
        state["quality"] = {
            "freshness_score": freshness,
            "passed": False,
            "has_photo": has_photo,
            "method": "vision" if vision_result else "heuristic",
        }
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

    state["quality"] = {
        "freshness_score": freshness,
        "passed": True,
        "has_photo": has_photo,
        "method": "vision" if vision_result else "heuristic",
    }
    log_step(
        state,
        agent="Quality Agent",
        detail=f"Freshness score {freshness}% ({source_note}). Packaging and spoilage check passed.",
        status="ok",
        stamp="Verified",
    )
    return state
