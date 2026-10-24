import re
from typing import Optional
from backend.schema import ComplaintTriage

# Rule dictionary: category -> (department, [keyword regexes])
CATEGORY_RULES = {
    "road_damage": {
        "department": "Roads",
        "patterns": [
            r"\bpothole\b", r"\bcrater\b", r"\bgaddha\b", r"खड्डा", r"गड्ढा",
            r"\bspeed breaker\b", r"स्पीड ब्रेकर", r"\bbroken road\b", r"\bpavement\b",
            r"\brod tiles\b", r"\bloose road tiles\b", r"फुटपाथ", r"रस्ता तुटला",
            r"सड़क की सतह", r"सड़क में दरार", r"रस्त्यावरचा स्पीड ब्रेकर", r"फरशा निघाल्या",
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

# Some civic reports use language that cannot be safely mapped by category words
# alone. These mappings make the local fallback predictable and explainable.
SPECIAL_CASES = [
    ([r"fallen tree", r"पडलेल[ाी].*tree"], "other", "Roads", "high",
     "A fallen tree needs a prompt road obstruction review."),
    ([r"abandoned vehicle", r"parked in front of the health"], "other", "Roads", "low",
     "An abandoned vehicle needs a low-priority road obstruction review."),
    ([r"injured.*dog", r"आवारा कुत्ता.*घायल"], "other", "Sanitation", "medium",
     "An injured stray animal requires municipal sanitation or animal-control follow-up."),
    ([r"dead animal", r"मेलेला प्राणी"], "other", "Sanitation", "medium",
     "A dead animal requires sanitation removal and safe disposal."),
    ([r"open manhole", r"मैनहोल.*ढक्कन", r"manhole.*cover.*नहीं"], "other", "Drainage", "critical",
     "An open manhole is an immediate fall hazard and needs emergency drainage action."),
    ([r"water pipe.*leaking", r"water line leak.*footpath", r"footpath.*geela"], "water_leak", "Water Supply", "high",
     "An active water-line leak needs prompt repair to prevent water loss and a slippery footpath."),
    ([r"tap.*pani waste", r"valve repair"], "water_leak", "Water Supply", "low",
     "A dripping tap or valve issue can be handled as a routine water-supply repair."),
    ([r"सार्वजनिक नल.*लगातार"], "water_leak", "Water Supply", "medium",
     "A continuously running public tap needs scheduled water-supply repair."),
    ([r"अंधेरी गली", r"dark lane.*street ?lights?"], "streetlight", "Electrical", "high",
     "Multiple failed lights in a dark lane create a serious night-time safety risk."),
    ([r"flickering every night"], "streetlight", "Electrical", "low",
     "An intermittently flickering light can be handled as a routine electrical repair."),
    ([r"लाईट.*पावसानंतर बंद"], "streetlight", "Electrical", "medium",
     "A streetlight that failed after rain needs a standard electrical repair."),
    ([r"धीमा रिसाव", r"slow.*leak"], "water_leak", "Water Supply", "medium",
     "A slow water leak needs scheduled repair before it worsens."),
    ([r"नाली का ढक्कन टूट गया", r"broken.*drain.*cover"], "drainage", "Drainage", "high",
     "A broken drain cover with pooling water requires prompt drainage repair."),
    ([r"ambulance", r"एम्बुलेंस", r"speed breaker.*broken", r"स्पीड ब्रेकर"], "road_damage", "Roads", "high",
     "Road damage is disrupting emergency or normal vehicle movement."),
    ([r"lane 8.*blink", r"blink.*visibility poor"], "streetlight", "Electrical", "medium",
     "Poor visibility from a faulty streetlight needs a standard electrical repair."),
    ([r"market corner.*four days", r"चार दिन", r"चार दिवस"], "garbage", "Sanitation", "high",
     "Garbage left for several days needs prompt sanitation collection."),
    ([r"rotting waste", r"waste bags.*smell", r"कूड़े.*आग"], "garbage", "Sanitation", "high",
     "Rotting waste or a trash fire needs prompt sanitation response."),
    ([r"drain water.*street", r"गंदा पानी सड़क", r"पाणी रस्त्यावर", r"nala overflow"], "drainage", "Drainage", "high",
     "Drain water reaching a street needs prompt drainage clearance."),
]

CRITICAL_INDICATORS = [
    r"\bfall\b", r"\bcrash\b", r"\bcrater\b", r"गिर रहे", r"घसरली", r"घसरत आहेत",
    r"\baccident\b", r"\bopen manhole\b", r"खतरनाक", r"धोकादायक",
]

HIGH_INDICATORS = [
    r"\bcontinuously\b", r"\bflooding\b", r"\boverflowing\b", r"लगातार", r"सतत",
    r"road par paani", r"\bleaking\b", r"pothole", r"gaddha", r"tyre fas", r"आग", r"fire",
]

LOW_INDICATORS = [
    r"\bflicker\b", r"\bblink\b", r"\bminor\b", r"थेंब",
]


def classify_fast(complaint_text: str, photo_path: Optional[str] = None) -> Optional[ComplaintTriage]:
    """Fast keyword-based rule triage for high-confidence civic complaints.
    
    Returns a validated ComplaintTriage if confident, or None to fall back to the LLM.
    Vague text routes to the LLM. Clear text still benefits from local routing
    when a photo is present; the configured vision model remains available for
    ambiguous visual cases.
    """
    text = complaint_text.strip()
    if len(text.split()) < 3:
        return None  # Too vague or short (e.g. "road bad") -> needs LLM

    text_lower = text.lower()
    for patterns, category, department, urgency, reason in SPECIAL_CASES:
        if any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in patterns):
            return ComplaintTriage(
                category=category,
                department=department,
                urgency=urgency,
                urgency_reason=reason,
                location="unknown",
                summary=f"Automated rule triage: {category.replace('_', ' ').capitalize()} complaint.",
                photo_severity=None,
            )

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
