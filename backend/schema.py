"""Shared data models and schemas for CivicFlow Triage & Routing.

Defines the contract between Dataset (Kritagya), Backend/AI (Sujay),
and Clustering/Dashboard (Manas).
"""

from typing import Dict, List, Literal, Optional, TypedDict

CategoryType = Literal[
    "road_damage",
    "water_leak",
    "garbage",
    "drainage",
    "streetlight",
    "other",
]

SeverityType = Literal["critical", "high", "medium", "low"]

DepartmentType = Literal[
    "Roads",
    "Water Supply",
    "Sanitation",
    "Electrical",
    "Drainage",
]

LanguageType = Literal["en", "hi", "mr", "hinglish"]


class ExpectedAnnotation(TypedDict):
    category: CategoryType
    severity: SeverityType
    department: DepartmentType


class TriageOutput(TypedDict):
    category: CategoryType
    severity: SeverityType
    department: DepartmentType
    urgency_reason: str
    location: str
    summary: str


class ComplaintItem(TypedDict):
    id: str
    text: str
    language: LanguageType
    ward: str
    latitude: float
    longitude: float
    photo_path: Optional[str]
    expected: ExpectedAnnotation
    duplicate_group: Optional[str]


class ProcessedComplaint(TypedDict, total=False):
    id: str
    text: str
    language: LanguageType
    ward: str
    latitude: float
    longitude: float
    photo_path: Optional[str]
    expected: ExpectedAnnotation
    duplicate_group: Optional[str]
    prediction: TriageOutput
    cluster_id: Optional[str]
    is_duplicate: bool


# Canonical mapping from category to default primary department
CATEGORY_TO_DEPARTMENT: Dict[CategoryType, DepartmentType] = {
    "road_damage": "Roads",
    "water_leak": "Water Supply",
    "garbage": "Sanitation",
    "streetlight": "Electrical",
    "drainage": "Drainage",
    "other": "Sanitation",
}

# Standard system prompt instructions for Sujay's triage model
TRIAGE_SYSTEM_PROMPT = """You are an AI assistant for a municipal corporation (Pune Ward-12) triaging citizen complaints.
The citizen complaint can be in English, Hindi, Marathi, or Hinglish (mixed Hindi-English).

Analyze the complaint text and output ONLY a valid JSON object with the following fields:
1. "category": Must be one of ["road_damage", "water_leak", "garbage", "drainage", "streetlight", "other"]
2. "severity": Must be one of:
   - "critical": immediate threat to life/safety (e.g. open manholes, craters causing accidents, live fallen electrical wires)
   - "high": serious disruption, major leak, road blockage, foul overflowing waste/drain
   - "medium": standard non-hazardous issues (e.g. non-working streetlight, uncollected bin, pothole)
   - "low": minor inconvenience (e.g. small tap drip, flickering bulb, loose tile)
3. "department": Must be one of ["Roads", "Water Supply", "Sanitation", "Electrical", "Drainage"]
   - road_damage -> "Roads" (or "Roads" for road obstructions)
   - water_leak -> "Water Supply"
   - garbage -> "Sanitation" (or "Sanitation" for stray/dead animals)
   - streetlight -> "Electrical"
   - drainage -> "Drainage" (or "Drainage" for open manholes)
4. "urgency_reason": A concise English explanation of why this severity was assigned.
5. "location": Extracted landmark or street if mentioned (e.g. "Tilak Road near school"), otherwise "unknown".
6. "summary": A concise English summary of the issue (1 sentence).

Complaint: {complaint}
"""
