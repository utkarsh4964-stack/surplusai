"""
SurplusAI backend - FastAPI app.

Run:
    pip install -r requirements.txt --break-system-packages
    uvicorn main:app --reload --port 8000

Endpoints:
    POST /donate          -> runs the full 7-agent pipeline, returns trace + result
    GET  /impact           -> running session totals (for the Admin dashboard)
    GET  /ngos               -> raw NGO dataset (for the Admin map)
    GET  /health               -> liveness check
"""

import base64
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from orchestrator import run_pipeline
from agents.impact_agent import get_totals
from agents.matching_agent import _load_ngos

app = FastAPI(title="SurplusAI Backend", version="0.1.0")

# demo-mode CORS: wide open so the static frontend file can call the API
# from a file:// origin. Tighten this before any real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class DonationRequest(BaseModel):
    food_type: str
    quantity: int
    pickup_time: str
    force_reject: bool = False
    image_base64: Optional[str] = None   # optional data URL or raw base64


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ngos")
def ngos():
    return _load_ngos()


@app.get("/impact")
def impact():
    return get_totals()


@app.post("/donate")
def donate(req: DonationRequest):
    has_photo = bool(req.image_base64)
    image_bytes = 0
    if has_photo:
        raw = req.image_base64.split(",")[-1]   # strip data: URL prefix if present
        try:
            image_bytes = len(base64.b64decode(raw))
        except Exception:
            image_bytes = 0

    payload = {
        "food_type": req.food_type,
        "quantity": req.quantity,
        "pickup_time": req.pickup_time,
    }

    result = run_pipeline(
        payload=payload,
        has_photo=has_photo,
        image_bytes=image_bytes,
        force_reject=req.force_reject,
    )
    return result
