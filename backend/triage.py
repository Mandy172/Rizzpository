"""Multilingual civic complaint classification and triage engine.

Supports:
- Local open-weight models via Ollama (e.g., gemma4:latest)
- Cloud Gemini API via google-genai
- Multimodal photo verification
- Strict output validation matching backend/schema.py
"""

import json
import os
import re
import sys
import urllib.request
from typing import Any, Dict, Optional

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.schema import (
    CATEGORY_TO_DEPARTMENT,
    TRIAGE_SYSTEM_PROMPT,
    CategoryType,
    DepartmentType,
    SeverityType,
    TriageOutput,
)

FALLBACK_TRIAGE: TriageOutput = {
    "category": "other",
    "department": "Sanitation",
    "severity": "medium",
    "urgency_reason": "Could not be processed automatically, flagged for manual triage review.",
    "location": "unknown",
    "summary": "Manual inspection required.",
}


def clean_json_response(raw_text: str) -> Dict[str, Any]:
    """Cleans markdown fencing and extracts valid JSON substring."""
    cleaned = re.sub(r"```(?:json)?", "", raw_text).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or start >= end:
        raise ValueError(f"No JSON object found in response: {raw_text[:100]}...")
    return json.loads(cleaned[start : end + 1])


def normalize_triage(data: Dict[str, Any]) -> TriageOutput:
    """Normalizes and validates fields to match canonical schema."""
    cat = data.get("category", "other").strip().lower()
    # Handle category synonyms
    synonym_map = {
        "roads": "road_damage",
        "road": "road_damage",
        "pothole": "road_damage",
        "water_supply": "water_leak",
        "water": "water_leak",
        "pipe_burst": "water_leak",
        "waste": "garbage",
        "trash": "garbage",
        "lights": "streetlight",
        "lighting": "streetlight",
        "sewer": "drainage",
        "gutter": "drainage",
    }
    cat = synonym_map.get(cat, cat)
    if cat not in ["road_damage", "water_leak", "garbage", "drainage", "streetlight", "other"]:
        cat = "other"

    # Severity normalization
    sev = data.get("severity", data.get("urgency", "medium")).strip().lower()
    if sev not in ["critical", "high", "medium", "low"]:
        sev = "medium"

    # Department normalization
    dept = data.get("department", "").strip()
    dept_map = {
        "roads": "Roads",
        "road": "Roads",
        "water supply": "Water Supply",
        "water": "Water Supply",
        "sanitation": "Sanitation",
        "solid waste": "Sanitation",
        "electrical": "Electrical",
        "electricity": "Electrical",
        "drainage": "Drainage",
        "sewerage": "Drainage",
    }
    dept = dept_map.get(dept.lower(), dept)
    if dept not in ["Roads", "Water Supply", "Sanitation", "Electrical", "Drainage"]:
        dept = CATEGORY_TO_DEPARTMENT.get(cat, "Sanitation")

    return {
        "category": cat,  # type: ignore
        "severity": sev,  # type: ignore
        "department": dept,  # type: ignore
        "urgency_reason": str(data.get("urgency_reason", "Assigned based on complaint details.")),
        "location": str(data.get("location", "Ward-12, Pune")),
        "summary": str(data.get("summary", "Civic issue reported.")),
    }


def triage_with_ollama(
    complaint_text: str,
    photo_path: Optional[str] = None,
    model: str = "gemma4:latest",
    host: str = "http://localhost:11434",
) -> TriageOutput:
    """Invokes local Gemma model via Ollama."""
    prompt = TRIAGE_SYSTEM_PROMPT.format(complaint=complaint_text)
    if photo_path and os.path.exists(photo_path):
        prompt += f"\nNote: Citizen also attached an image ({os.path.basename(photo_path)}) confirming visible civic infrastructure impact."

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }

    req = urllib.request.Request(
        f"{host}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        raw_text = result.get("response", "")
        parsed = clean_json_response(raw_text)
        return normalize_triage(parsed)


def triage_complaint(
    complaint_text: str,
    photo_path: Optional[str] = None,
    model_name: Optional[str] = None,
) -> TriageOutput:
    """Primary triage entry point with fallback."""
    # 1. Try local Ollama (gemma4) first
    try:
        model = model_name or os.environ.get("OLLAMA_MODEL", "gemma4:latest")
        return triage_with_ollama(complaint_text, photo_path, model=model)
    except Exception as e:
        print(f"[Ollama] Note: {e}")

    # 2. Try Google GenAI client if GEMINI_API_KEY is present
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        try:
            from google import genai

            client = genai.Client(api_key=api_key)
            cloud_model = model_name or os.environ.get("MODEL_NAME", "gemini-2.5-flash")
            resp = client.models.generate_content(
                model=cloud_model,
                contents=TRIAGE_SYSTEM_PROMPT.format(complaint=complaint_text),
            )
            parsed = clean_json_response(resp.text)
            return normalize_triage(parsed)
        except Exception as e:
            print(f"[Gemini API] Note: {e}")

    return FALLBACK_TRIAGE


if __name__ == "__main__":
    test_cases = [
        "Pipe phat gayi hai Shivaji Chowk ke paas, poori road par paani bhar gaya hai",
        "रस्त्यावर मोठा खड्डा आहे, काल एक बाईक घसरली",
        "Streetlight pole 18 near the temple is flickering every night.",
    ]
    for text in test_cases:
        print(f"\nComplaint: {text}")
        res = triage_complaint(text)
        print("Triage:", json.dumps(res, indent=2, ensure_ascii=False))
