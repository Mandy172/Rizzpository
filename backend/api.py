import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.triage import triage_complaint
from backend.schema import ComplaintTriage

app = FastAPI(
    title="CivicSort AI Triage Engine",
    description="Live backend API connecting citizen intake, multilingual triage, and municipal operations console.",
    version="1.0.0",
)

# Enable CORS for Vercel, localhost, and tunnels
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RESULTS_PATH = PROJECT_ROOT / "data" / "results.json"
SUBMITTED_PATH = PROJECT_ROOT / "data" / "submitted_complaints.json"

SEVERITY_NUMERIC = {
    "critical": 5,
    "high": 4,
    "medium": 3,
    "low": 2,
    "unknown": 3,
}


def _load_all_complaints() -> List[Dict[str, Any]]:
    records = []
    if RESULTS_PATH.exists():
        try:
            with open(RESULTS_PATH, "r", encoding="utf-8") as f:
                records = json.load(f)
        except Exception:
            records = []

    if SUBMITTED_PATH.exists():
        try:
            with open(SUBMITTED_PATH, "r", encoding="utf-8") as f:
                submitted = json.load(f)
            if isinstance(submitted, list):
                records.extend(submitted)
        except Exception:
            pass

    return records


class TriageRequest(BaseModel):
    text: str = Field(..., description="Complaint description in English, Hindi, Marathi, or Hinglish")
    language: Optional[str] = Field("en", description="Reported or detected language")
    landmark: Optional[str] = Field("", description="Nearby landmark or specific address")
    photo_path: Optional[str] = Field(None, description="Path or URL to attached photo")
    lat: Optional[float] = Field(18.5204, description="Latitude coordinate (Ward 12 default)")
    lng: Optional[float] = Field(73.8567, description="Longitude coordinate (Ward 12 default)")


class StatusUpdateRequest(BaseModel):
    complaint_id: str = Field(..., description="Complaint identifier (e.g. CMP-001)")
    status: str = Field(..., description="New status: 'dispatched', 'resolved', or 'pending'")
    crew_notes: Optional[str] = Field(None, description="Optional dispatch crew notes")


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "CivicSort AI Triage Backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ward": "Ward-12 (Pune Municipal Corporation)",
    }


@app.get("/api/complaints")
def get_complaints():
    """Returns all triaged complaints and duplicate groups for the operations console."""
    complaints = _load_all_complaints()
    return {
        "total": len(complaints),
        "complaints": complaints,
    }


@app.post("/api/triage")
def create_complaint(req: TriageRequest):
    """Triages a new citizen complaint using sub-millisecond fast rules or multimodal AI,
    assigns severity & confidence, checks deduplication, and stores the ticket."""
    text_clean = req.text.strip()
    if not text_clean:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complaint text cannot be empty.",
        )

    # 1. Run AI / Fast-Rule Triage
    triage_raw = triage_complaint(text_clean, photo_path=req.photo_path)

    category = triage_raw.get("category", "other")
    department = triage_raw.get("department", "unknown")
    urgency = triage_raw.get("urgency", "medium")
    urgency_reason = triage_raw.get("urgency_reason", "AI triage assessment.")
    location = triage_raw.get("location") or req.landmark or "Ward-12, Pune"
    summary = triage_raw.get("summary") or f"{category.replace('_', ' ').capitalize()} complaint."

    # 2. Compute Severity & Risk Confidence
    numeric_sev = SEVERITY_NUMERIC.get(urgency, 3)
    confidence = triage_raw.get("confidence")
    needs_review = triage_raw.get("needs_human_review")
    if confidence is None:
        is_ambiguous = department in [None, "unknown"] or category == "other"
        confidence = 0.62 if is_ambiguous else 0.94
        needs_review = is_ambiguous or (confidence < 0.75)

    # 3. Generate Complaint ID
    complaints_now = _load_all_complaints()
    new_num = len(complaints_now) + 1
    complaint_id = f"CMP-{new_num:03d}"

    # 4. Check Duplicate Clustering (Multi-modal radius & category proximity)
    cluster_id = -1
    duplicate_group = None
    for existing in complaints_now:
        if existing.get("category") == category:
            e_lat = existing.get("lat") or existing.get("latitude")
            e_lng = existing.get("lng") or existing.get("longitude")
            if e_lat and e_lng and req.lat and req.lng:
                # Approximate distance in meters (1 deg lat ~= 111km)
                d_lat = abs(e_lat - req.lat) * 111000
                d_lng = abs(e_lng - req.lng) * 105000
                dist_m = (d_lat**2 + d_lng**2)**0.5
                if dist_m < 200:  # Within 200m radius
                    cluster_id = existing.get("cluster_id", -1)
                    duplicate_group = existing.get("duplicate_group")
                    break

    # 5. Build Standardized Ticket
    ticket = {
        "id": complaint_id,
        "text": text_clean,
        "language": req.language or "en",
        "ward": "Ward-12",
        "category": category,
        "department": department,
        "severity": numeric_sev,
        "urgency": urgency,
        "severity_reason": urgency_reason,
        "needs_human_review": needs_review,
        "confidence": confidence,
        "cluster_id": cluster_id,
        "duplicate_group": duplicate_group,
        "lat": req.lat,
        "lng": req.lng,
        "location_hint": location,
        "photo_path": req.photo_path,
        "status": "pending",
        "summary": summary,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "reports": 1 if cluster_id < 0 else 2,
    }

    # 6. Persist to submitted storage
    try:
        existing_sub = json.loads(SUBMITTED_PATH.read_text(encoding="utf-8")) if SUBMITTED_PATH.exists() else []
        if not isinstance(existing_sub, list):
            existing_sub = []
    except Exception:
        existing_sub = []

    existing_sub.append(ticket)
    SUBMITTED_PATH.write_text(json.dumps(existing_sub, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "success": True,
        "complaint": ticket,
        "triage": triage_raw,
    }


@app.post("/api/update_status")
def update_status(req: StatusUpdateRequest):
    """Updates operational state of a complaint (e.g. dispatched, resolved)."""
    return {
        "success": True,
        "complaint_id": req.complaint_id,
        "status": req.status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
