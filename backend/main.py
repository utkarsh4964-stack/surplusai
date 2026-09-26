"""
SurplusAI backend - FastAPI app.

Run:
    pip install -r requirements.txt --break-system-packages
    uvicorn main:app --reload --port 8000

Endpoints:
    POST /donate                                   -> runs the full 7-agent pipeline, returns trace + result
    GET  /impact                                     -> running session totals (for the Admin dashboard)
    GET  /ngos                                         -> raw NGO dataset (for the Admin map)
    GET  /institutions                                   -> registered institutions (kitchens / processing units)
    GET  /forecast/{institution_id}                        -> demand/surplus forecast for one institution
    GET  /processing/status/{institution_id}                 -> IoT/sensor anomaly + efficiency status
    GET  /sustainability/report/{institution_id}?donation_kg=  -> ESG-style sustainability report
    GET  /health                                                 -> liveness check
"""

import base64
import json
import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from orchestrator import (
    run_pipeline,
    run_forecast_only,
    run_processing_check,
    run_sustainability_report,
)
from agents.impact_agent import get_totals
from agents.matching_agent import _load_ngos

app = FastAPI(title="SurplusAI Backend", version="0.2.0")

# demo-mode CORS: wide open so the static frontend file can call the API
# from a file:// origin. Tighten this before any real deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

with open(os.path.join(_DATA_DIR, "institutions.json")) as f:
    _INSTITUTIONS = {i["id"]: i for i in json.load(f)}

with open(os.path.join(_DATA_DIR, "sensor_stream.json")) as f:
    _SENSOR_STREAM = json.load(f)


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
        image_base64=req.image_base64,
    )
    return result


@app.get("/institutions")
def institutions():
    return list(_INSTITUTIONS.values())


@app.get("/forecast/{institution_id}")
def forecast(institution_id: str):
    institution = _INSTITUTIONS.get(institution_id)
    if not institution:
        raise HTTPException(404, "institution not found")
    return run_forecast_only(institution)["forecast"]


@app.get("/processing/status/{institution_id}")
def processing_status(institution_id: str):
    institution = _INSTITUTIONS.get(institution_id)
    if not institution:
        raise HTTPException(404, "institution not found")
    readings = _SENSOR_STREAM.get(institution_id, [])
    return run_processing_check(institution, readings)["processing_flags"]


@app.get("/sustainability/report/{institution_id}")
def sustainability_report(institution_id: str, donation_kg: float = 0.0):
    institution = _INSTITUTIONS.get(institution_id)
    if not institution:
        raise HTTPException(404, "institution not found")
    readings = _SENSOR_STREAM.get(institution_id, [])
    return run_sustainability_report(institution, readings, donation_kg)["sustainability_report"]
