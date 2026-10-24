import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.triage import triage_complaint


def load_complaints(data_path: Path) -> List[dict]:
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_existing_results(output_path: Path) -> Dict[str, dict]:
    """Load existing results to enable caching / resuming."""
    if not output_path.exists():
        return {}
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return {item["id"]: item for item in data if "id" in item}
    except Exception as e:
        print(f"[Warning] Failed to load existing cache from {output_path}: {e}")
    return {}


def save_results(results: List[dict], output_path: Path) -> None:
    """Save results atomically to JSON."""
    temp_path = output_path.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    temp_path.replace(output_path)


def run_pipeline(
    input_file: str = "data/complaints.json",
    output_file: str = "results.json",
    backend: str = None,
    rate_limit_delay: float = 1.0,
    force: bool = False,
    max_items: int = None,
) -> List[dict]:
    data_path = PROJECT_ROOT / input_file
    output_path = PROJECT_ROOT / output_file

    complaints = load_complaints(data_path)
    if max_items:
        complaints = complaints[:max_items]

    cache = {} if force else load_existing_results(output_path)
    print(f"Loaded {len(complaints)} complaints from {input_file}.")
    if cache:
        print(f"Found {len(cache)} cached items in {output_file}.")

    results = []
    processed_count = 0
    cached_count = 0

    for idx, c in enumerate(complaints, start=1):
        cid = c.get("id")
        text = c.get("text", "")
        photo_path = c.get("photo_path")

        # Check cache
        if not force and cid in cache:
            results.append(cache[cid])
            cached_count += 1
            continue

        print(f"[{idx}/{len(complaints)}] Triaging {cid} ({c.get('language', 'unknown')})...")
        resolved_photo = str(PROJECT_ROOT / photo_path) if photo_path else None
        
        triage_output = triage_complaint(
            complaint=text,
            photo_path=resolved_photo,
            backend=backend,
        )

        # Merge original complaint fields with triage output
        merged = dict(c)
        merged.update({
            "category": triage_output.get("category"),
            "department": triage_output.get("department"),
            "urgency": triage_output.get("urgency"),
            "urgency_reason": triage_output.get("urgency_reason"),
            "location": triage_output.get("location"),
            "summary": triage_output.get("summary"),
            "photo_severity": triage_output.get("photo_severity"),
        })

        results.append(merged)
        cache[cid] = merged
        processed_count += 1

        # Periodically update output file
        save_results(list(cache.values()), output_path)

        if rate_limit_delay > 0:
            time.sleep(rate_limit_delay)

    all_results = list(cache.values())

    # Step: Cluster complaints using semantic deduplication
    try:
        from backend.cluster import cluster_complaints
        print("\n[Clustering] Running semantic deduplication clustering (bge-m3 + HDBSCAN)...")
        all_results = cluster_complaints(all_results)
    except Exception as e:
        print(f"[Error] Clustering step failed: {e}")
        raise

    save_results(all_results, output_path)
    print(f"\nPipeline finished. Total: {len(results)} | Cached: {cached_count} | Newly Processed: {processed_count}")
    print(f"Results saved to {output_path}")
    return all_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run civic complaint triage pipeline.")
    parser.add_argument("--input", default="data/complaints.json", help="Path to input complaints JSON.")
    parser.add_argument("--output", default="results.json", help="Path to output results JSON.")
    parser.add_argument("--backend", default=None, help="LLM backend: 'gemini' or 'ollama'.")
    parser.add_argument("--delay", type=float, default=1.0, help="Rate limit delay in seconds.")
    parser.add_argument("--force", action="store_true", help="Ignore cache and re-process all.")
    parser.add_argument("--limit", type=int, default=None, help="Max items to process.")
    args = parser.parse_args()

    run_pipeline(
        input_file=args.input,
        output_file=args.output,
        backend=args.backend,
        rate_limit_delay=args.delay,
        force=args.force,
        max_items=args.limit,
    )
