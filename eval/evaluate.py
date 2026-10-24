import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Documented conversion mapping for dashboard exports (1-5 numeric scale -> urgency label)
NUMERIC_SEVERITY_TO_URGENCY: Dict[int, str] = {
    1: "low",       # 1 – Cosmetic
    2: "low",       # 2 – Minor
    3: "medium",    # 3 – Inconvenient
    4: "high",      # 4 – Serious
    5: "critical",  # 5 – Danger
}


def normalize_department(val: Any) -> str:
    """Normalize department name handling case, whitespace, underscores, and hyphens.

    Examples:
      'Water Supply'     -> 'water_supply'
      'water_supply'     -> 'water_supply'
      'water-supply'     -> 'water_supply'
      '  Water   Supply' -> 'water_supply'
      'ROADS'            -> 'roads'
      None / ''          -> 'unknown'
    """
    if val is None:
        return "unknown"
    s = str(val).strip().lower()
    if not s:
        return "unknown"
    return re.sub(r"[\s\-_]+", "_", s)


def normalize_category(val: Any) -> str:
    """Normalize category label consistent with backend.schema.ComplaintTriage.

    Handles case, whitespace, underscores, hyphens, and canonical synonyms:
      'roads', 'road'        -> 'road_damage'
      'water_supply', 'water'-> 'water_leak'
      None / ''              -> 'unknown'
    """
    if val is None:
        return "unknown"
    s = str(val).strip().lower()
    if not s:
        return "unknown"
    s = re.sub(r"[\s\-_]+", "_", s)
    if s in ("roads", "road"):
        return "road_damage"
    if s in ("water_supply", "water"):
        return "water_leak"
    return s


def normalize_urgency(val: Any, allow_numeric_conversion: bool = True) -> Tuple[str, bool]:
    """Normalize urgency/severity label.

    Returns:
      Tuple of (normalized_string_label, is_numeric_converted)

    String labels: 'low', 'medium', 'high', 'critical'
    Numeric labels: 1-5 converted via NUMERIC_SEVERITY_TO_URGENCY if allowed.
    """
    if val is None:
        return "unknown", False

    # Check for direct integer/float severity (from dashboard export)
    if isinstance(val, (int, float)):
        int_val = int(val)
        if allow_numeric_conversion and int_val in NUMERIC_SEVERITY_TO_URGENCY:
            return NUMERIC_SEVERITY_TO_URGENCY[int_val], True
        return "unknown", False

    s = str(val).strip().lower()
    if not s:
        return "unknown", False

    # Check for string digit (e.g. "4")
    if s.isdigit():
        int_val = int(s)
        if allow_numeric_conversion and int_val in NUMERIC_SEVERITY_TO_URGENCY:
            return NUMERIC_SEVERITY_TO_URGENCY[int_val], True
        return "unknown", False

    return s, False


def extract_prediction_fields(
    pred: Optional[dict],
    allow_numeric_conversion: bool = True,
) -> Tuple[Optional[str], Optional[str], Optional[str], bool]:
    """Extract (department, category, urgency, is_numeric_converted) from a prediction item.

    Safely handles both root-level fields and nested 'prediction' objects without crashing.
    Prioritizes original model output format ('urgency').
    """
    if not pred or not isinstance(pred, dict):
        return None, None, None, False

    # Department
    dept = pred.get("department")
    if dept is None and isinstance(pred.get("prediction"), dict):
        dept = pred["prediction"].get("department")

    # Category
    cat = pred.get("category")
    if cat is None and isinstance(pred.get("prediction"), dict):
        cat = pred["prediction"].get("category")

    # Urgency (primary model output format)
    urgency = pred.get("urgency")
    is_numeric = False

    # Fallback to nested prediction if root urgency is absent
    if urgency is None and isinstance(pred.get("prediction"), dict):
        nested_urg = pred["prediction"].get("urgency") or pred["prediction"].get("severity")
        if nested_urg is not None:
            urgency = nested_urg

    # Fallback to root severity if urgency is absent (e.g. dashboard exports)
    if urgency is None and "severity" in pred:
        urgency = pred["severity"]

    norm_urg, is_numeric = normalize_urgency(urgency, allow_numeric_conversion=allow_numeric_conversion)
    return dept, cat, norm_urg, is_numeric


def evaluate_results(
    data_file: str = "data/complaints.json",
    results_file: str = "results.json",
    allow_numeric_conversion: bool = True,
    verbose: bool = True,
) -> dict:
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

    # Allow predictions to be either a list of items or an id-keyed dict
    if isinstance(predictions, list):
        pred_map = {item.get("id"): item for item in predictions if isinstance(item, dict) and "id" in item}
    elif isinstance(predictions, dict):
        pred_map = predictions
    else:
        pred_map = {}

    total = len(ground_truth)
    missing_count = 0
    dept_correct = 0
    cat_correct = 0
    urgency_correct = 0
    routed_correctly = 0

    language_stats: Dict[str, Dict[str, int]] = {}
    dept_errors: List[dict] = []
    cat_errors: List[dict] = []
    urgency_errors: List[dict] = []
    routing_errors: List[dict] = []
    numeric_conversion_applied = False

    for item in ground_truth:
        cid = item.get("id", "UNKNOWN_ID")
        lang = item.get("language", "unknown")
        text = item.get("text", "")
        expected = item.get("expected") or {}

        if lang not in language_stats:
            language_stats[lang] = {
                "total": 0,
                "routed_correct": 0,
                "dept_correct": 0,
                "cat_correct": 0,
                "urgency_correct": 0,
            }
        language_stats[lang]["total"] += 1

        pred = pred_map.get(cid)
        if pred is None:
            missing_count += 1
            exp_dept = normalize_department(expected.get("department"))
            exp_cat = normalize_category(expected.get("category"))
            exp_urg, _ = normalize_urgency(expected.get("severity"), allow_numeric_conversion=False)

            err_info = {
                "id": cid,
                "language": lang,
                "expected": f"dept={exp_dept}, cat={exp_cat}, urg={exp_urg}",
                "predicted": "<missing>",
                "text": text,
            }
            dept_errors.append(err_info)
            cat_errors.append(err_info)
            urgency_errors.append(err_info)
            routing_errors.append(err_info)
            continue

        raw_pred_dept, raw_pred_cat, norm_pred_urg, used_numeric = extract_prediction_fields(
            pred, allow_numeric_conversion=allow_numeric_conversion
        )
        if used_numeric:
            numeric_conversion_applied = True

        exp_dept = normalize_department(expected.get("department"))
        pred_dept = normalize_department(raw_pred_dept)

        exp_cat = normalize_category(expected.get("category"))
        pred_cat = normalize_category(raw_pred_cat)

        exp_urg, _ = normalize_urgency(expected.get("severity"), allow_numeric_conversion=False)
        pred_urg = norm_pred_urg

        # Independent metric evaluations
        d_match = (exp_dept == pred_dept)
        c_match = (exp_cat == pred_cat)
        u_match = (exp_urg == pred_urg)
        is_routed = d_match and c_match

        if d_match:
            dept_correct += 1
            language_stats[lang]["dept_correct"] += 1
        else:
            dept_errors.append({
                "id": cid,
                "language": lang,
                "expected": exp_dept,
                "predicted": pred_dept,
                "text": text,
            })

        if c_match:
            cat_correct += 1
            language_stats[lang]["cat_correct"] += 1
        else:
            cat_errors.append({
                "id": cid,
                "language": lang,
                "expected": exp_cat,
                "predicted": pred_cat,
                "text": text,
            })

        if u_match:
            urgency_correct += 1
            language_stats[lang]["urgency_correct"] += 1
        else:
            urgency_errors.append({
                "id": cid,
                "language": lang,
                "expected": exp_urg,
                "predicted": pred_urg,
                "text": text,
            })

        if is_routed:
            routed_correctly += 1
            language_stats[lang]["routed_correct"] += 1
        else:
            routing_errors.append({
                "id": cid,
                "language": lang,
                "expected": f"dept={exp_dept}, cat={exp_cat}",
                "predicted": f"dept={pred_dept}, cat={pred_cat}",
                "text": text,
            })

    dept_acc = (dept_correct / total * 100) if total > 0 else 0.0
    cat_acc = (cat_correct / total * 100) if total > 0 else 0.0
    urg_acc = (urgency_correct / total * 100) if total > 0 else 0.0
    route_acc = (routed_correctly / total * 100) if total > 0 else 0.0

    if verbose:
        print("=" * 60)
        print("EVALUATION BENCHMARK")
        print("=" * 60)
        print(f"Total Complaints:    {total}")
        print(f"Predictions Found:   {total - missing_count} (Missing: {missing_count})")
        if numeric_conversion_applied:
            print("[Notice] Converted numeric severity (1-5) via NUMERIC_SEVERITY_TO_URGENCY mapping.")
        print("-" * 60)
        print("ACCURACY METRICS:")
        print(f"  - Department Accuracy:       {dept_correct}/{total} ({dept_acc:.1f}%)")
        print(f"  - Category Accuracy:         {cat_correct}/{total} ({cat_acc:.1f}%)")
        print(f"  - Urgency/Severity Accuracy: {urgency_correct}/{total} ({urg_acc:.1f}%)")
        print(f"  - Combined Routing Accuracy: {routed_correctly}/{total} ({route_acc:.1f}%) [Dept AND Category]")
        print("-" * 60)
        print("COMBINED ROUTING BY LANGUAGE:")
        for lang, stats in language_stats.items():
            pct = (stats["routed_correct"] / stats["total"] * 100) if stats["total"] > 0 else 0.0
            print(f"  - {lang.upper():8s}: {stats['routed_correct']}/{stats['total']} ({pct:.1f}%)")

        # 1. Department errors
        print("\n" + "=" * 60)
        print(f"DEPARTMENT ERRORS ({len(dept_errors)} total):")
        print("=" * 60)
        if dept_errors:
            for err in dept_errors:
                t_snippet = err['text'][:65] + ("..." if len(err['text']) > 65 else "")
                print(f"[{err['id']}] ({err['language']})")
                print(f"   Expected : {err['expected']}")
                print(f"   Predicted: {err['predicted']}")
                print(f"   Text     : {t_snippet}\n")
        else:
            print("None (100% department accuracy)\n")

        # 2. Category errors
        print("=" * 60)
        print(f"CATEGORY ERRORS ({len(cat_errors)} total):")
        print("=" * 60)
        if cat_errors:
            for err in cat_errors:
                t_snippet = err['text'][:65] + ("..." if len(err['text']) > 65 else "")
                print(f"[{err['id']}] ({err['language']})")
                print(f"   Expected : {err['expected']}")
                print(f"   Predicted: {err['predicted']}")
                print(f"   Text     : {t_snippet}\n")
        else:
            print("None (100% category accuracy)\n")

        # 3. Urgency / Severity errors
        print("=" * 60)
        print(f"URGENCY / SEVERITY ERRORS ({len(urgency_errors)} total):")
        print("=" * 60)
        if urgency_errors:
            for err in urgency_errors:
                t_snippet = err['text'][:65] + ("..." if len(err['text']) > 65 else "")
                print(f"[{err['id']}] ({err['language']})")
                print(f"   Expected : {err['expected']}")
                print(f"   Predicted: {err['predicted']}")
                print(f"   Text     : {t_snippet}\n")
        else:
            print("None (100% urgency accuracy)\n")

    return {
        "total": total,
        "missing_count": missing_count,
        "dept_correct": dept_correct,
        "dept_accuracy": dept_correct / total if total > 0 else 0.0,
        "cat_correct": cat_correct,
        "cat_accuracy": cat_correct / total if total > 0 else 0.0,
        "urgency_correct": urgency_correct,
        "urgency_accuracy": urgency_correct / total if total > 0 else 0.0,
        "routed_correctly": routed_correctly,
        "routing_accuracy": routed_correctly / total if total > 0 else 0.0,
        "language_stats": language_stats,
        "dept_errors": dept_errors,
        "cat_errors": cat_errors,
        "urgency_errors": urgency_errors,
        "routing_errors": routing_errors,
        "misses": routing_errors,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate complaint routing accuracy against expected dataset.")
    parser.add_argument("--data", default="data/complaints.json", help="Expected dataset path")
    parser.add_argument("--results", default="results.json", help="Predictions path")
    parser.add_argument(
        "--strict-urgency",
        action="store_true",
        help="Disallow numeric severity (1-5) auto-conversion to string urgency labels.",
    )
    args = parser.parse_args()

    evaluate_results(
        data_file=args.data,
        results_file=args.results,
        allow_numeric_conversion=not args.strict_urgency,
    )
