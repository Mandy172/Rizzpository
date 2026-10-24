import json
import os
import re

from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL_NAME = os.environ["MODEL_NAME"]

PROMPT = """You are helping a municipal office sort citizen complaints.
The complaint may be in English, Hindi, Marathi or a mix.
Return ONLY valid JSON with these keys: category, department,
urgency, urgency_reason, location, summary.
Categories: roads, garbage, water_supply, drainage, streetlight, other.
Urgency: "high" only if there is danger to people or a service is
fully down; otherwise "medium" or "low".
If information is missing, use "unknown" instead of guessing.
Write urgency_reason and summary in English.
Complaint: {complaint}"""

FALLBACK = {
    "category": "other",
    "department": "unknown",
    "urgency": "medium",
    "urgency_reason": "Could not be processed automatically, needs manual review",
    "location": "unknown",
    "summary": "unknown",
}


def parse_json(text):
    text = re.sub(r"```(?:json)?", "", text).strip()
    start, end = text.find("{"), text.rfind("}")
    return json.loads(text[start:end + 1])


def triage_complaint(complaint):
    for attempt in range(2):
        try:
            resp = client.models.generate_content(
                model=MODEL_NAME,
                contents=PROMPT.format(complaint=complaint),
            )
            return parse_json(resp.text)
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
    return FALLBACK


if __name__ == "__main__":
    tests = [
        "Pipe phat gayi hai Shivaji Chowk ke paas, poori road par paani bhar gaya hai",
        "रस्त्यावर मोठा खड्डा आहे, काल एक बाईक घसरली",
        "road bad",
    ]
    for t in tests:
        print(t)
        print(json.dumps(triage_complaint(t), indent=2, ensure_ascii=False))
        print("-" * 40)