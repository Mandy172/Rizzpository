from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


class ComplaintTriage(BaseModel):
    category: Literal[
        "roads",
        "road_damage",
        "garbage",
        "water_supply",
        "water_leak",
        "drainage",
        "streetlight",
        "other",
        "unknown",
    ] = Field(
        default="unknown",
        description="Category of the civic complaint. Use 'unknown' if unclear.",
    )
    department: str = Field(
        default="unknown",
        description="Municipal department responsible, or 'unknown'.",
    )
    urgency: Literal["high", "medium", "low", "critical"] = Field(
        default="medium",
        description="Urgency level: 'high' if danger to people or service fully down; otherwise 'medium' or 'low'.",
    )
    urgency_reason: Optional[str] = Field(
        default=None,
        description="Brief justification for the urgency rating in English.",
    )
    location: str = Field(
        default="unknown",
        description="Specific location or landmark mentioned, or 'unknown' if not specified.",
    )
    summary: str = Field(
        default="unknown",
        description="Concise 1-sentence summary in English, or 'unknown' if vague.",
    )
    photo_severity: Optional[Literal["high", "medium", "low", "none"]] = Field(
        default=None,
        description="Optional visual severity assessment from attached photo, if available.",
    )

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, v):
        if isinstance(v, str):
            clean = v.strip().lower().replace(" ", "_")
            # Normalize common synonyms to keep category standard
            if clean in ["roads", "road"]:
                return "road_damage"
            if clean in ["water_supply", "water"]:
                return "water_leak"
            return clean
        return v

    @field_validator("urgency", mode="before")
    @classmethod
    def normalize_urgency(cls, v):
        if isinstance(v, str):
            clean = v.strip().lower()
            return clean
        return v

    @field_validator("location", "summary", "department", mode="before")
    @classmethod
    def clean_text(cls, v):
        if v is None:
            return "unknown"
        if isinstance(v, str):
            cleaned = v.strip()
            return cleaned if cleaned else "unknown"
        return str(v)

    @classmethod
    def fallback(cls) -> "ComplaintTriage":
        return cls(
            category="other",
            department="unknown",
            urgency="medium",
            urgency_reason="Could not be processed automatically, needs manual review",
            location="unknown",
            summary="unknown",
            photo_severity=None,
        )
