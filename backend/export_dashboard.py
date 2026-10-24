import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def map_urgency_to_severity(urgency: Optional[str], text: str = "") -> int:
    """Map string urgency level to dashboard's 1-5 integer severity scale.
    
    Dashboard Scale:
      1 - Cosmetic
      2 - Minor
      3 - Inconvenient
      4 - Serious
      5 - Danger
    """
    if not urgency:
        return 2

    u = urgency.strip().lower()
    if u == "critical":
        return 5
    elif u == "high":
        return 4
    elif u == "medium":
        return 3
    elif u == "low":
        # If text is extremely short / vague ("road bad"), treat as 1 (cosmetic/vague)
        if len(text.strip().split()) <= 2:
            return 1
        return 2
    return 2


def parse_cluster_id(duplicate_group: Optional[str], group_id_map: Dict[str, int]) -> int:
    """Map duplicate_group to an integer cluster_id (>= 0 for duplicates, -1 for unique)."""
    if not duplicate_group or duplicate_group == "None":
        return -1

    # If format is DUP-01, DUP-02, etc., extract the integer directly
    match = re.search(r"DUP-(\d+)", str(duplicate_group))
    if match:
        return int(match.group(1))

    # Fallback to mapping unique string identifiers to incremental integers
    if duplicate_group not in group_id_map:
        group_id_map[duplicate_group] = len(group_id_map) + 1
    return group_id_map[duplicate_group]


def normalize_department(dept: Optional[str]) -> str:
    """Normalize department names to lowercase snake_case to match data/results.json convention.
    
    e.g. 'Water Supply' -> 'water_supply', 'Roads' -> 'roads'
    """
    if not dept:
        return "other"
    d = dept.strip().lower().replace(" ", "_")
    if d == "unknown":
        return "other"
    return d


def export_for_dashboard(
    input_file: str = "results.json",
    output_file: str = "data/results_real.json",
) -> List[Dict[str, Any]]:
    input_path = PROJECT_ROOT / input_file
    output_path = PROJECT_ROOT / output_file

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    group_id_map: Dict[str, int] = {}
    exported = []

    for item in data:
        raw_dept = (item.get("department") or "").strip()
        is_unknown_dept = (raw_dept.lower() == "unknown")
        
        # Determine needs_human_review: department 'unknown' or category 'unknown'
        needs_human_review = is_unknown_dept or (item.get("category") == "unknown")

        text = item.get("text", "")
        urgency = item.get("urgency")
        severity = map_urgency_to_severity(urgency, text=text)

        # Confidence heuristic (not in root results.json, guessed for dashboard)
        if needs_human_review:
            confidence = 0.35
        elif severity >= 4:
            confidence = 0.92
        else:
            confidence = 0.88

        # Cluster ID from duplicate_group
        cluster_id = parse_cluster_id(item.get("duplicate_group"), group_id_map)

        # Department format: lowercase snake_case (e.g. 'water_supply', 'roads')
        department = normalize_department(raw_dept)

        # Location hint (if present and known)
        loc = item.get("location")
        location_hint = loc if loc and loc.lower() != "unknown" else None

        row: Dict[str, Any] = {
            "id": item.get("id"),
            "text": text,
            "language": item.get("language", "en"),
            "category": item.get("category", "other"),
            "severity": severity,
            "severity_reason": item.get("urgency_reason") or item.get("summary") or "Civic maintenance issue reported.",
            "department": department,
            "needs_human_review": bool(needs_human_review),
            "confidence": confidence,
            "cluster_id": cluster_id,
            "lat": float(item.get("latitude", 0.0)),
            "lng": float(item.get("longitude", 0.0)),
        }

        if location_hint:
            row["location_hint"] = location_hint

        exported.append(row)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(exported, f, indent=2, ensure_ascii=False)

    print(f"Exported {len(exported)} records to {output_path}")
    print(f"  - Needs Review: {sum(1 for r in exported if r['needs_human_review'])}")
    print(f"  - Grouped Items (cluster_id >= 0): {sum(1 for r in exported if r['cluster_id'] >= 0)}")
    print(f"  - Unique Items (cluster_id == -1): {sum(1 for r in exported if r['cluster_id'] == -1)}")
    return exported


if __name__ == "__main__":
    export_for_dashboard()
