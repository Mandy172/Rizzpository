import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def evaluate_results(data_file: str = "data/complaints.json", results_file: str = "results.json") -> dict:
    data_path = PROJECT_ROOT / data_file
    results_path = PROJECT_ROOT / results_file

    if not data_path.exists():
        raise FileNotFoundError(f"Dataset file not found at {data_path}")
    if not results_path.exists():
        raise FileNotFoundError(f"Results file not found at {results_path}. Run backend/run_pipeline.py first.")

    with open(data_path, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    with open(results_path, "r", encoding="utf-8") as f:
        predictions = json.load(f)

    pred_map = {item["id"]: item for item in predictions if "id" in item}

    total = len(ground_truth)
    routed_correctly = 0
    dept_correct = 0
    cat_correct = 0
    urgency_correct = 0

    language_stats = {}
    misses = []

    for item in ground_truth:
        cid = item.get("id")
        lang = item.get("language", "unknown")
        expected = item.get("expected", {})
        
        if lang not in language_stats:
            language_stats[lang] = {"total": 0, "correct": 0}
        language_stats[lang]["total"] += 1

        pred = pred_map.get(cid)
        if not pred:
            misses.append({
                "id": cid,
                "language": lang,
                "text": item.get("text", "")[:60] + "...",
                "expected": expected,
                "predicted": "MISSING_FROM_RESULTS",
                "issue": "Not processed",
            })
            continue

        exp_dept = (expected.get("department") or "").strip().lower()
        pred_dept = (pred.get("department") or "").strip().lower()

        exp_cat = (expected.get("category") or "").strip().lower()
        pred_cat = (pred.get("category") or "").strip().lower()

        exp_sev = (expected.get("severity") or "").strip().lower()
        pred_urg = (pred.get("urgency") or "").strip().lower()

        d_match = (exp_dept == pred_dept)
        c_match = (exp_cat == pred_cat)
        u_match = (exp_sev == pred_urg)

        if d_match:
            dept_correct += 1
        if c_match:
            cat_correct += 1
        if u_match:
            urgency_correct += 1

        # A complaint is considered routed correctly if its department matches
        is_routed = d_match and c_match

        if is_routed:
            routed_correctly += 1
            language_stats[lang]["correct"] += 1
        else:
            issues = []
            if not d_match:
                issues.append(f"Dept ({pred.get('department')} != {expected.get('department')})")
            if not c_match:
                issues.append(f"Cat ({pred.get('category')} != {expected.get('category')})")
            if not u_match:
                issues.append(f"Urgency ({pred.get('urgency')} != {expected.get('severity')})")

            misses.append({
                "id": cid,
                "language": lang,
                "text": item.get("text", "")[:60] + "...",
                "expected": f"dept={expected.get('department')}, cat={expected.get('category')}, sev={expected.get('severity')}",
                "predicted": f"dept={pred.get('department')}, cat={pred.get('category')}, urg={pred.get('urgency')}",
                "issue": ", ".join(issues),
            })

    print("=" * 60)
    print(f"EVALUATION SUMMARY: {routed_correctly} of {total} routed correctly")
    print("=" * 60)
    print(f"Department Accuracy: {dept_correct}/{total} ({dept_correct / total * 100:.1f}%)")
    print(f"Category Accuracy:   {cat_correct}/{total} ({cat_correct / total * 100:.1f}%)")
    print(f"Severity Match:      {urgency_correct}/{total} ({urgency_correct / total * 100:.1f}%)")
    print("\nAccuracy by Language:")
    for lang, stats in language_stats.items():
        pct = (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0
        print(f"  - {lang.upper():8s}: {stats['correct']}/{stats['total']} ({pct:.1f}%)")

    if misses:
        print("\n" + "=" * 60)
        print(f"MISSED COMPLAINTS ({len(misses)} total):")
        print("=" * 60)
        for m in misses:
            print(f"[{m['id']}] ({m['language']}) - {m['text']}")
            print(f"   Expected : {m['expected']}")
            print(f"   Predicted: {m['predicted']}")
            print(f"   Issue    : {m['issue']}\n")
    else:
        print("\nAll complaints routed perfectly!")

    return {
        "total": total,
        "routed_correctly": routed_correctly,
        "dept_accuracy": dept_correct / total,
        "cat_accuracy": cat_correct / total,
        "misses": misses,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate complaint routing accuracy against expected dataset.")
    parser.add_argument("--data", default="data/complaints.json", help="Expected dataset path")
    parser.add_argument("--results", default="results.json", help="Predictions path")
    args = parser.parse_args()

    evaluate_results(data_file=args.data, results_file=args.results)
