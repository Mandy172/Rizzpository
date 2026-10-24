"""Generates an initial results.json based on data/complaints.json.

Allows Manas (Dashboard & Integration) to build and test the Streamlit UI
immediately without waiting for the live LLM inference loop.
"""

import json

REASONS = {
    "road_damage": "Potholes and broken road surfaces pose immediate accident hazards for two-wheelers and pedestrians.",
    "water_leak": "Continuous pipe leakage leads to potable water wastage and flooding of pedestrian footpaths.",
    "garbage": "Uncollected decomposing waste causes public health concerns, foul stench, and attracts stray animals.",
    "streetlight": "Dark corridors and faulty streetlights create safety hazards and poor visibility at night.",
    "drainage": "Blocked gutters and missing manhole covers cause sewage overflow and severe accident risks.",
    "other": "Road obstruction or civic hazard requiring municipal inspection.",
}


def generate_baseline():
    with open("data/complaints.json", "r", encoding="utf-8") as f:
        complaints = json.load(f)

    results = []
    for c in complaints:
        exp = c["expected"]
        cat = exp["category"]
        sev = exp["severity"]
        dept = exp["department"]
        dg = c.get("duplicate_group")

        item = {
            "id": c["id"],
            "text": c["text"],
            "language": c["language"],
            "ward": c["ward"],
            "latitude": c["latitude"],
            "longitude": c["longitude"],
            "photo_path": c.get("photo_path"),
            "expected": exp,
            "duplicate_group": dg,
            "cluster_id": dg if dg else f"SINGLE-{c['id']}",
            "is_duplicate": dg is not None,
            "prediction": {
                "category": cat,
                "severity": sev,
                "department": dept,
                "urgency_reason": REASONS.get(cat, "Needs municipal inspection and resolution."),
                "location": "Ward-12, Pune",
                "summary": c["text"][:80],
            },
        }
        results.append(item)

    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"✅ Generated baseline results.json with {len(results)} items.")


if __name__ == "__main__":
    generate_baseline()
