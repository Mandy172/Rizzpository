import base64
import json
import os
import re
from typing import Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types
import requests

from backend.schema import ComplaintTriage

load_dotenv()

# Configuration from environment
LLM_BACKEND = os.environ.get("LLM_BACKEND", "gemini").lower()
MODEL_NAME = os.environ.get("MODEL_NAME", "gemma-4-26b-a4b-it")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:4b")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

BASE_SYSTEM_INSTRUCTIONS = """You are an AI assistant helping a municipal ward office triage citizen complaints.
Complaints can be in English, Hindi, Marathi, or Hinglish.

Your task is to analyze the complaint and return ONLY a valid raw JSON object (no extra commentary, no markdown codeblocks) matching this specification:

Keys:
- "category": Choose one of: "road_damage", "water_leak", "garbage", "streetlight", "drainage", "other".
- "department": The responsible municipal department: "Roads", "Water Supply", "Sanitation", "Electrical", "Drainage". If completely undetermined, use "unknown".
- "urgency": Choose one of:
  - "critical": Immediate danger to life or severe hazard (e.g., open manhole, deep road crater causing crashes, live electrical wire).
  - "high": Major service disruption, active flooding, leaking water main, rotting waste pile.
  - "medium": Normal civic maintenance issue (e.g., uncollected bin, clogged drain without flooding, non-working light).
  - "low": Minor repair, slow drip, flickering light, cosmetic issue.
- "urgency_reason": A concise 1-sentence explanation in English justifying the urgency level.
- "location": Specific landmark, street, chowk, or ward mentioned in the complaint. If no location is mentioned, return "unknown". NEVER invent or guess a location.
- "summary": A concise 1-sentence English summary of the issue. If the complaint is vague (e.g. "road bad"), return "unknown".
- "photo_severity": If an image/photo is provided, evaluate visual severity: one of "high", "medium", "low", "none". If no image is provided, use null.
"""


def get_gemini_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set. Please check your .env file.")
    return genai.Client(api_key=api_key)


def parse_json(text: str) -> dict:
    """Extract and parse JSON from the model response."""
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError(f"Could not find valid JSON object in output: {text}")
    return json.loads(cleaned[start:end + 1])


def _call_gemini(complaint: str, photo_path: Optional[str] = None) -> str:
    client = get_gemini_client()
    prompt_text = f"{BASE_SYSTEM_INSTRUCTIONS}\n\nComplaint: {complaint}"
    contents = [prompt_text]

    if photo_path and os.path.isfile(photo_path):
        mime_type = "image/png" if photo_path.lower().endswith(".png") else "image/jpeg"
        with open(photo_path, "rb") as img_f:
            img_bytes = img_f.read()
        contents.append(types.Part.from_bytes(data=img_bytes, mime_type=mime_type))

    resp = client.models.generate_content(
        model=MODEL_NAME,
        contents=contents,
    )
    return resp.text


def _call_ollama(complaint: str, photo_path: Optional[str] = None) -> str:
    prompt_text = f"{BASE_SYSTEM_INSTRUCTIONS}\n\nComplaint: {complaint}"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt_text,
        "stream": False,
        "format": "json",
    }

    if photo_path and os.path.isfile(photo_path):
        with open(photo_path, "rb") as img_f:
            b64_img = base64.b64encode(img_f.read()).decode("utf-8")
        payload["images"] = [b64_img]

    url = f"{OLLAMA_HOST.rstrip('/')}/api/generate"
    response = requests.post(url, json=payload, timeout=60)
    response.raise_for_status()
    data = response.json()
    return data.get("response", "")


def triage_complaint(
    complaint: str,
    photo_path: Optional[str] = None,
    backend: Optional[str] = None,
) -> dict:
    """Triage a civic complaint into structured JSON validated by ComplaintTriage.
    
    Supports switchable backends: 'gemini' or 'ollama' (via LLM_BACKEND env or parameter).
    Retries once on failure and falls back to ComplaintTriage.fallback() if both attempts fail.
    """
    chosen_backend = (backend or os.environ.get("LLM_BACKEND", LLM_BACKEND)).lower()

    for attempt in range(2):
        try:
            if chosen_backend == "ollama":
                raw_text = _call_ollama(complaint, photo_path=photo_path)
            else:
                raw_text = _call_gemini(complaint, photo_path=photo_path)

            raw_data = parse_json(raw_text)
            validated = ComplaintTriage.model_validate(raw_data)
            return validated.model_dump()
        except Exception as e:
            print(f"[triage_complaint] Attempt {attempt + 1} with backend '{chosen_backend}' failed: {e}")

    return ComplaintTriage.fallback().model_dump()


if __name__ == "__main__":
    tests = [
        ("Pipe phat gayi hai Shivaji Chowk ke paas, poori road par paani bhar gaya hai", None),
        ("रस्त्यावर मोठा खड्डा आहे, काल एक बाईक घसरली", None),
        ("road bad", None),
        ("Water is leaking continuously near the school gate on Tilak Road.", "data/photos/water-leak.jpg"),
    ]
    for text, photo in tests:
        print(f"\nComplaint: {text}")
        if photo:
            print(f"Photo: {photo}")
        result = triage_complaint(text, photo_path=photo)
        print(json.dumps(result, indent=2, ensure_ascii=False))
