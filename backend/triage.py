import json
import os
import re
from typing import Optional

from dotenv import load_dotenv
from google import genai

from backend.schema import ComplaintTriage

load_dotenv()

MODEL_NAME = os.environ.get("MODEL_NAME", "gemma-4-26b-a4b-it")

PROMPT = """You are an AI assistant helping a municipal ward office triage citizen complaints.
Complaints can be in English, Hindi, Marathi, or Hinglish.

Your task is to analyze the complaint and return ONLY a valid raw JSON object (no extra commentary, no markdown codeblocks) matching this specification:

Keys:
- "category": Choose one of: "road_damage", "water_leak", "garbage", "streetlight", "drainage", "other".
- "department": The responsible municipal department: "Roads", "Water Supply", "Sanitation", "Electrical", "Drainage". If completely undetermined, use "unknown".
- "urgency": Choose one of:
  - "critical": Immediate danger to life or severe hazard (e.g., open manhole, deep road crater causing crashes, live wires).
  - "high": Major service disruption, active flooding, leaking water main, rotting waste pile.
  - "medium": Normal civic maintenance issue (e.g., uncollected bin, clogged drain without flooding, non-working light).
  - "low": Minor repair, slow drip, flickering light, cosmetic issue.
- "urgency_reason": A concise 1-sentence explanation in English justifying the urgency level.
- "location": Specific landmark, street, chowk, or ward mentioned in the complaint. If no location is mentioned, return "unknown". NEVER invent or guess a location.
- "summary": A concise 1-sentence English summary of the issue. If the complaint is vague (e.g. "road bad"), return "unknown".

Complaint: {complaint}
"""


def get_client() -> genai.Client:
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


def triage_complaint(complaint: str, photo_path: Optional[str] = None) -> dict:
    """Triage a civic complaint text into structured JSON validated by ComplaintTriage.
    
    Retries once on failure and falls back to a safe default if parsing/validation fails.
    """
    for attempt in range(2):
        try:
            client = get_client()
            resp = client.models.generate_content(
                model=MODEL_NAME,
                contents=PROMPT.format(complaint=complaint),
            )
            raw_data = parse_json(resp.text)
            validated = ComplaintTriage.model_validate(raw_data)
            return validated.model_dump()
        except Exception as e:
            print(f"[triage_complaint] Attempt {attempt + 1} failed: {e}")
    
    return ComplaintTriage.fallback().model_dump()


if __name__ == "__main__":
    tests = [
        "Pipe phat gayi hai Shivaji Chowk ke paas, poori road par paani bhar gaya hai",
        "रस्त्यावर मोठा खड्डा आहे, काल एक बाईक घसरली",
        "road bad",
        "The streetlight at the public park entrance has been off all week.",
    ]
    for t in tests:
        print(f"\nComplaint: {t}")
        result = triage_complaint(t)
        print(json.dumps(result, indent=2, ensure_ascii=False))
