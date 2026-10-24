"""Live API for the officer console.

GET  /complaints  (and /api/complaints) -> pipeline results + live submissions, in the frontend schema
POST /triage      (and /api/triage)     -> triage one complaint, save it, re-cluster everything
POST /reset       (and /api/reset)      -> clear live submissions (for demo rehearsal)
GET  /health      (and /api/health)     -> server health check
"""
import copy
import hashlib
import json
import random
import re
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.cluster import cluster_complaints
from backend.export_dashboard import map_urgency_to_severity, normalize_department
from backend.fast_rules import classify_fast
from backend.schema import compute_operational_confidence
from backend.triage import triage_complaint

BASE_FILES = [PROJECT_ROOT / "results.json", PROJECT_ROOT / "data" / "results.json"]
LIVE_FILE = PROJECT_ROOT / "data" / "live_complaints.json"
WARDS_FILE = PROJECT_ROOT / "data" / "wards.json"

app = FastAPI(title="CivicSort API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_lock = threading.Lock()
_rows: List[Dict[str, Any]] = []


def _read(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _base_items() -> List[dict]:
    for p in BASE_FILES:
        data = _read(p, None)
        if isinstance(data, list) and data:
            return data
    return []


def _ward_center():
    w = _read(WARDS_FILE, {})
    c = w.get("center", {})
    return float(c.get("latitude", 18.5204)), float(c.get("longitude", 73.8567))


# ---- language detection (the triage output has no language field) ----
_MR = {"आहे", "आहेत", "नाही", "आणि", "मध्ये", "झाला", "झाली", "पडला", "पडली", "होत", "तुंबली"}
_HI = {"है", "हैं", "नहीं", "और", "में", "रहा", "रही", "पर", "गया", "गई"}
_ROMAN = {"hai", "hain", "nahi", "nahin", "mein", "paas", "saamne", "sadak", "gaddha", "kachra",
          "paani", "pani", "raha", "rahi", "aahe", "ahe", "aur", "gaya", "gayi", "bahut", "kal",
          "hua", "hui", "phat", "phoot", "nala", "bijli", "bimar", "bacche", "jaldi", "dono"}


def detect_language(text: str) -> str:
    clean = text.replace("।", " ")
    if re.search(r"[\u0900-\u097F]", clean):
        words = set(re.findall(r"[\u0900-\u097F]+", clean))
        return "mr" if len(words & _MR) > len(words & _HI) else "hi"
    words = {w.lower() for w in re.findall(r"[A-Za-z]+", clean)}
    return "hinglish" if words & _ROMAN else "en"


def to_row(item: dict) -> dict:
    raw_dept = (item.get("department") or "").strip()
    severity = map_urgency_to_severity(item.get("urgency"), item.get("text", ""))

    # Calibrated multi-factor operational confidence engine
    conf = item.get("confidence")
    needs_rev = item.get("needs_human_review")
    if conf is None or needs_rev is None:
        c_val, r_val = compute_operational_confidence(
            category=item.get("category", "other"),
            department=raw_dept,
            urgency=item.get("urgency", "medium"),
            text=item.get("text", ""),
            location=item.get("location", ""),
            has_photo=bool(item.get("photo_path")),
        )
        confidence = conf if conf is not None else c_val
        needs_human_review = needs_rev if needs_rev is not None else r_val
    else:
        confidence = conf
        needs_human_review = needs_rev

    loc = item.get("location")
    hint = loc if loc and str(loc).lower() != "unknown" else None
    lat = item.get("lat", item.get("latitude", 0.0))
    lng = item.get("lng", item.get("longitude", 0.0))
    return {
        "id": item.get("id"),
        "text": item.get("text", ""),
        "language": item.get("language", "en"),
        "category": item.get("category", "other"),
        "severity": severity,
        "severity_reason": item.get("urgency_reason") or item.get("summary") or "Civic issue reported.",
        "department": normalize_department(raw_dept),
        "needs_human_review": bool(needs_human_review),
        "confidence": confidence,
        "cluster_id": int(item.get("cluster_id", -1)),
        "location_hint": hint,
        "lat": float(lat or 0.0),
        "lng": float(lng or 0.0),
        "live": bool(item.get("live", False)),
    }


def _rebuild() -> None:
    """Re-cluster base + live complaints with the real bge-m3 pipeline and refresh rows."""
    global _rows
    items = copy.deepcopy(_base_items()) + copy.deepcopy(_read(LIVE_FILE, []))
    for it in items:
        it.setdefault("cluster_id", -1)
    try:
        cluster_complaints(items)
    except Exception as e:
        print(f"[api] clustering failed, keeping stored cluster ids: {e}")
    rows = [to_row(it) for it in items]
    _rows = rows


class TriageIn(BaseModel):
    text: str = Field(min_length=3, max_length=1000)
    location: str | None = Field(default=None, max_length=200)


@app.on_event("startup")
def _startup():
    with _lock:
        _rebuild()
    print(f"[api] loaded {len(_rows)} complaints")


@app.get("/health")
@app.get("/api/health")
def health():
    return {"status": "ok", "complaints": len(_rows)}


@app.get("/complaints")
@app.get("/api/complaints")
def complaints():
    return _rows


@app.post("/triage")
@app.post("/api/triage")
def triage(body: TriageIn):
    text = body.text.strip()
    started = time.time()
    source = "fast_rules" if classify_fast(text) is not None else "model"
    out = triage_complaint(text)
    if str(out.get("urgency_reason") or "").startswith("Could not be processed"):
        source = "fallback"

    with _lock:
        live = _read(LIVE_FILE, [])
        new_id = f"LIVE-{len(live) + 1:03d}"
        lat0, lng0 = _ward_center()
        rnd = random.Random(int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16))
        item = {
            "id": new_id,
            "text": text,
            "language": detect_language(text),
            "ward": "Ward-12",
            "latitude": round(lat0 + rnd.uniform(-0.01, 0.01), 5),
            "longitude": round(lng0 + rnd.uniform(-0.01, 0.01), 5),
            "category": out.get("category"),
            "department": out.get("department"),
            "urgency": out.get("urgency"),
            "urgency_reason": out.get("urgency_reason"),
            "location": (body.location or "").strip() or out.get("location"),
            "summary": out.get("summary"),
            "photo_severity": out.get("photo_severity"),
            "confidence": out.get("confidence"),
            "needs_human_review": out.get("needs_human_review"),
            "live": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        live.append(item)
        LIVE_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = LIVE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(live, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(LIVE_FILE)
        try:
            _rebuild()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"re-clustering failed: {e}")
        row = next(r for r in _rows if r["id"] == new_id)

    return {**row, "source": source, "seconds": round(time.time() - started, 1)}


@app.post("/reset")
@app.post("/api/reset")
def reset():
    with _lock:
        LIVE_FILE.unlink(missing_ok=True)
        _rebuild()
    return {"status": "reset", "complaints": len(_rows)}
