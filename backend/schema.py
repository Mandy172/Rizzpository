from typing import Literal, Optional, Tuple
from pydantic import BaseModel, Field, field_validator


def compute_operational_confidence(
    category: str,
    department: str,
    urgency: str = "medium",
    text: str = "",
    location: str = "",
    has_photo: bool = False,
) -> Tuple[float, bool]:
    """Calculates a calibrated composite operational confidence score (0.0 - 1.0)
    and determines whether human supervisory review is required.

    Pillars:
      1. Department Routing (+0.40 recognized, -0.20 unknown)
      2. Category Canonicality (+0.25 canonical, +0.05 other, -0.15 unknown)
      3. Lexical Evidence (+0.10 for text >= 5 words, +0.05 for >= 2 words)
      4. Landmark Specificity (+0.09 for specific non-generic location)
      5. Visual Corroboration (+0.05 for verified photo)
    """
    score = 0.10  # Base prior

    # 1. Department routing
    dept_norm = (department or "").strip().lower().replace("_", " ").replace("-", " ")
    recognized_depts = {"roads", "water supply", "sanitation", "electrical", "drainage"}
    if dept_norm in recognized_depts:
        score += 0.40
    elif dept_norm == "unknown" or not dept_norm:
        score -= 0.20
    else:
        score += 0.15

    # 2. Category canonicality
    cat_norm = (category or "").strip().lower()
    canonical_cats = {"road_damage", "roads", "water_leak", "water_supply", "garbage", "drainage", "streetlight"}
    if cat_norm in canonical_cats:
        score += 0.25
    elif cat_norm == "other":
        score += 0.05
    else:
        score -= 0.15

    # 3. Text length & lexical evidence
    words = text.strip().split()
    if len(words) >= 5:
        score += 0.10
    elif len(words) >= 2:
        score += 0.05

    # 4. Location / landmark specificity
    loc_norm = (location or "").strip().lower()
    if loc_norm and loc_norm not in ("unknown", "ward-12, pune", "pune"):
        score += 0.09

    # 5. Visual corroboration
    if has_photo:
        score += 0.05

    # Calibrate & clamp between 0.15 and 0.98
    clamped = max(0.15, min(0.98, score))
    final_conf = round(clamped, 2)

    # Operational safety cutoff at 75% or unknown department
    needs_review = final_conf < 0.75 or dept_norm in ("unknown", "") or cat_norm in ("unknown", "")

    return final_conf, needs_review


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
    confidence: Optional[float] = Field(
        default=None,
        description="Calibrated composite operational confidence score (0.0 to 1.0).",
    )
    needs_human_review: Optional[bool] = Field(
        default=None,
        description="Flag for supervisory review if confidence is low or classification ambiguous.",
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

    def populate_confidence(
        self,
        text: str = "",
        photo_path: Optional[str] = None,
    ) -> "ComplaintTriage":
        """Calculates and attaches operational confidence and review flag based on evidence completeness."""
        has_photo = bool(photo_path) or self.photo_severity not in (None, "none")
        conf, needs_rev = compute_operational_confidence(
            category=self.category,
            department=self.department,
            urgency=self.urgency,
            text=text or self.summary,
            location=self.location,
            has_photo=has_photo,
        )
        self.confidence = conf
        self.needs_human_review = needs_rev
        return self

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
            confidence=0.15,
            needs_human_review=True,
        )
