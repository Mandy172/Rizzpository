import re
from typing import Optional, Tuple
from backend.schema import ComplaintTriage

# Rule dictionary: category -> (department, [keyword regexes])
CATEGORY_RULES = {
    "road_damage": {
        "department": "Roads",
        "patterns": [
            r"\bpothole\b", r"\bcrater\b", r"\bgaddha\b", r"खड्डा", r"गड्ढा",
            r"\bspeed breaker\b", r"स्पीड ब्रेकर", r"\bbroken road\b", r"\bpavement\b",
            r"\brod tiles\b", r"\bloose road tiles\b", r"फुटपाथ", r"रस्ता तुटला",
        ],
    },
    "water_leak": {
        "department": "Water Supply",
        "patterns": [
            r"\bpipe burst\b", r"\bwater leak\b", r"\bleaking water\b", r"\bwater line\b",
            r"pipe phat", r"pipe phoot", r"पानी की पाइप", r"पाण्याची पाईप", r"गळत आहे",
            r"रिसाव", r"सार्वजनिक नल", r"पाण्याचा व्हॉल्व", r"\bwater is leaking\b",
        ],
    },
    "garbage": {
        "department": "Sanitation",
        "patterns": [
            r"\bgarbage\b", r"\btrash\b", r"\bdumpster\b", r"\bwaste bags\b", r"\bcommunity bin\b",
            r"\bkachra\b", r"कचरा", r"कूड़ा", r"डस्टबिन", r"दुर्गंधी", r"smell", r"waste",
        ],
    },
    "drainage": {
        "department": "Drainage",
        "patterns": [
            r"\bdrain\b", r"\bgutter\b", r"\bdrainage\b", r"\bstorm drain\b", r"\bsewage\b",
            r"\bnala\b", r"नाली जाम", r"नाली", r"गटार", r"गटाराची जाळी", r"तुंबली",
        ],
    },
    "streetlight": {
        "department": "Electrical",
        "patterns": [
            r"\bstreetlight\b", r"\bstreet light\b", r"\blamp\b", r"स्ट्रीट लाइट", r"स्ट्रीट लाईट",
            r"\bflickering\b", r"\bblink\b", r"अंधेरी गली", r"लाईट बंद",
        ],
    },
}

CRITICAL_INDICATORS = [
    r"\bfall\b", r"\bcrash\b", r"\bcrater\b", r"गिर रहे", r"घसरली", r"\baccident\b",
    r"\bfas gaya\b", r"\bdangerous\b", r"खतरनाक", r"धोकादायक", r"\bmanhole\b",
]

HIGH_INDICATORS = [
    r"\bcontinuously\b", r"\bflooding\b", r"\boverflowing\b", r"लगातार", r"सतत",
    r"road par paani", r"rot", r"smell", r"आग", r"fire",
]

LOW_INDICATORS = [
    r"\bslow\b", r"\bflicker\b", r"\bblink\b", r"\bminor\b", r"धीमा", r"थेंब",
]


def classify_fast(complaint_text: str, photo_path: Optional[str] = None) -> Optional[ComplaintTriage]:
    """Fast keyword-based rule triage for high-confidence civic complaints.
    
    Returns a validated ComplaintTriage if confident, or None to fall back to the LLM.
    Photos and vague text always route to the LLM.
    """
    if photo_path:
        return None  # Needs vision model

    text = complaint_text.strip()
    if len(text.split()) < 3:
        return None  # Too vague or short (e.g. "road bad") -> needs LLM

    text_lower = text.lower()
    matches = []

    for cat, meta in CATEGORY_RULES.items():
        score = sum(1 for p in meta["patterns"] if re.search(p, text_lower, re.IGNORECASE))
        if score > 0:
            matches.append((cat, meta["department"], score))

    if len(matches) != 1:
        # Ambiguous or no clear keyword match -> fall back to LLM
        return None

    cat, dept, _ = matches[0]

    # Urgency estimation
    if any(re.search(p, text_lower, re.IGNORECASE) for p in CRITICAL_INDICATORS):
        urgency = "critical"
        urgency_reason = "Flagged critical due to high-risk hazards or active accidents mentioned in text."
    elif any(re.search(p, text_lower, re.IGNORECASE) for p in HIGH_INDICATORS):
        urgency = "high"
        urgency_reason = "Flagged high urgency due to continuous leak, major disruption, or public hazard."
    elif any(re.search(p, text_lower, re.IGNORECASE) for p in LOW_INDICATORS):
        urgency = "low"
        urgency_reason = "Flagged low urgency for minor repair or intermittent civic issue."
    else:
        urgency = "medium"
        urgency_reason = "Standard civic maintenance issue routed via rule triage."

    # Location extraction heuristic (e.g. "near X", "outside X", "ke paas", "जवळ")
    loc_match = re.search(
        r"(?:near|outside|at|in front of|ke paas|के पास|जवळ|समोर)\s+([A-Za-z0-9\s\-]+?)(?:[.,]|$)",
        text,
        re.IGNORECASE,
    )
    location = loc_match.group(1).strip() if loc_match else "unknown"

    return ComplaintTriage(
        category=cat,
        department=dept,
        urgency=urgency,
        urgency_reason=urgency_reason,
        location=location,
        summary=f"Automated rule triage: {cat.replace('_', ' ').capitalize()} complaint.",
        photo_severity=None,
    )
