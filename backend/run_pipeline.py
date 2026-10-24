"""Pipeline execution script for CivicFlow Triage & Routing.

Processes complaints from data/complaints.json through:
1. Triage Classification (Category, Severity, Department, Location, Summary)
2. Saves enriched records to results.json for the Streamlit dashboard and evaluation.

Usage:
    python3 backend/run_pipeline.py [--limit N] [--sample]
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.triage import triage_complaint


def run_pipeline(limit: int = 0, use_sample: bool = False):
    complaints_file = "data/complaints.json"
    output_file = "results.json"

    if not os.path.exists(complaints_file):
        print(f"Error: {complaints_file} not found.")
        sys.exit(1)

    with open(complaints_file, "r", encoding="utf-8") as f:
        complaints = json.load(f)

    if limit > 0:
        complaints = complaints[:limit]

    print(f"🚀 Running CivicFlow AI Pipeline on {len(complaints)} complaints...")
    start_time = time.time()
    results = []

    for i, c in enumerate(complaints):
        cid = c.get("id")
        text = c.get("text", "")
        photo = c.get("photo_path")
        lang = c.get("language")

        print(f"[{i+1}/{len(complaints)}] Processing {cid} ({lang})...", end="", flush=True)

        if use_sample:
            # Quick mock mode for instant dashboard testing
            exp = c.get("expected", {})
            pred = {
                "category": exp.get("category", "other"),
                "severity": exp.get("severity", "medium"),
                "department": exp.get("department", "Sanitation"),
                "urgency_reason": "Verified civic complaint requiring prompt municipal attention.",
                "location": "Ward-12, Pune",
                "summary": text[:80],
            }
        else:
            pred = triage_complaint(text, photo_path=photo)

        dg = c.get("duplicate_group")
        item = {
            "id": cid,
            "text": text,
            "language": lang,
            "ward": c.get("ward", "Ward-12"),
            "latitude": c.get("latitude"),
            "longitude": c.get("longitude"),
            "photo_path": photo,
            "expected": c.get("expected"),
            "duplicate_group": dg,
            "cluster_id": dg if dg else f"SINGLE-{cid}",
            "is_duplicate": dg is not None,
            "prediction": pred,
        }
        results.append(item)
        print(f" -> {pred.get('category')} | {pred.get('department')} | {pred.get('severity')}")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    elapsed = time.time() - start_time
    print(f"\n🎉 Finished in {elapsed:.2f}s! Saved {len(results)} triaged records to {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run civic complaint triage pipeline")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of complaints to process (0 for all)")
    parser.add_argument("--sample", action="store_true", help="Generate instantaneous sample output without calling LLM")
    args = parser.parse_args()

    run_pipeline(limit=args.limit, use_sample=args.sample)
