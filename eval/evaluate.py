"""Evaluation benchmark script for CivicFlow Triage & Routing.

Computes precision, accuracy, and breakdown across:
- Category Classification (road_damage, water_leak, garbage, etc.)
- Department Routing (Roads, Water Supply, Sanitation, Electrical, Drainage)
- Severity Level (critical, high, medium, low)
- Language breakdown (English, Hindi, Marathi, Hinglish)
- Duplicate Group Clustering accuracy

Usage:
    python3 eval/evaluate.py [path_to_results.json]
"""

import json
import os
import sys
from collections import defaultdict


def evaluate_predictions(results_path="results.json", complaints_path="data/complaints.json"):
    if not os.path.exists(results_path):
        print(f"❌ Error: Results file '{results_path}' not found.")
        print("Please run the AI pipeline first or generate sample results.")
        return None

    with open(results_path, "r", encoding="utf-8") as f:
        results = json.load(f)

    # Load ground truth if not embedded in results
    complaints_map = {}
    if os.path.exists(complaints_path):
        with open(complaints_path, "r", encoding="utf-8") as f:
            for item in json.load(f):
                complaints_map[item["id"]] = item

    total = len(results)
    cat_correct = 0
    dept_correct = 0
    sev_correct = 0

    lang_stats = defaultdict(lambda: {"total": 0, "cat_ok": 0, "dept_ok": 0, "sev_ok": 0})
    cat_stats = defaultdict(lambda: {"total": 0, "correct": 0})
    mismatches = []

    for item in results:
        cid = item.get("id")
        gt = item.get("expected") or (complaints_map.get(cid, {}).get("expected", {}))
        pred = item.get("prediction", {})
        lang = item.get("language") or complaints_map.get(cid, {}).get("language", "unknown")
        text = item.get("text") or complaints_map.get(cid, {}).get("text", "")

        if not gt or not pred:
            continue

        exp_cat = gt.get("category")
        exp_dept = gt.get("department")
        exp_sev = gt.get("severity")

        pred_cat = pred.get("category")
        pred_dept = pred.get("department")
        pred_sev = pred.get("severity")

        # Counts
        lang_stats[lang]["total"] += 1
        cat_stats[exp_cat]["total"] += 1

        is_cat_ok = pred_cat == exp_cat
        is_dept_ok = pred_dept == exp_dept
        is_sev_ok = pred_sev == exp_sev

        if is_cat_ok:
            cat_correct += 1
            lang_stats[lang]["cat_ok"] += 1
            cat_stats[exp_cat]["correct"] += 1

        if is_dept_ok:
            dept_correct += 1
            lang_stats[lang]["dept_ok"] += 1

        if is_sev_ok:
            sev_correct += 1
            lang_stats[lang]["sev_ok"] += 1

        if not (is_cat_ok and is_dept_ok):
            mismatches.append({
                "id": cid,
                "lang": lang,
                "text": text[:60] + "...",
                "exp_cat": exp_cat,
                "pred_cat": pred_cat,
                "exp_dept": exp_dept,
                "pred_dept": pred_dept,
                "exp_sev": exp_sev,
                "pred_sev": pred_sev,
            })

    # Print summary
    print("\n" + "=" * 65)
    print("🎯 CIVICFLOW TRIAGE & ROUTING EVALUATION REPORT")
    print("=" * 65)
    print(f"Total Evaluated: {total}")
    print(f"Category Accuracy:    {cat_correct}/{total} ({cat_correct/total*100:.1f}%)")
    print(f"Department Accuracy:  {dept_correct}/{total} ({dept_correct/total*100:.1f}%)")
    print(f"Severity Accuracy:    {sev_correct}/{total} ({sev_correct/total*100:.1f}%)")

    print("\n🌐 LANGUAGE BREAKDOWN:")
    print(f"{'Language':<12} {'Count':<8} {'Category Acc':<16} {'Dept Acc':<16} {'Severity Acc'}")
    print("-" * 65)
    for lang, s in sorted(lang_stats.items()):
        cnt = s["total"]
        c_acc = f"{s['cat_ok']}/{cnt} ({s['cat_ok']/cnt*100:.0f}%)"
        d_acc = f"{s['dept_ok']}/{cnt} ({s['dept_ok']/cnt*100:.0f}%)"
        s_acc = f"{s['sev_ok']}/{cnt} ({s['sev_ok']/cnt*100:.0f}%)"
        print(f"{lang:<12} {cnt:<8} {c_acc:<16} {d_acc:<16} {s_acc}")

    print("\n📁 CATEGORY ACCURACY:")
    for cat, s in sorted(cat_stats.items()):
        cnt = s["total"]
        acc = f"{s['correct']}/{cnt} ({s['correct']/cnt*100:.0f}%)"
        print(f"  - {cat:<15}: {acc}")

    # Check Duplicate Groups clustering if cluster_id present
    dup_cluster_checks = defaultdict(set)
    for item in results:
        dg = item.get("duplicate_group") or complaints_map.get(item.get("id"), {}).get("duplicate_group")
        cid = item.get("id")
        clust = item.get("cluster_id")
        if dg and clust:
            dup_cluster_checks[dg].add(clust)

    if dup_cluster_checks:
        print("\n🔁 DUPLICATE CLUSTER RECALL:")
        clean_groups = 0
        for dg, clusters in dup_cluster_checks.items():
            is_single = len(clusters) == 1
            if is_single:
                clean_groups += 1
            print(f"  - {dg}: grouped into {len(clusters)} cluster(s) -> {'✅ Grouped Together' if is_single else '⚠️ Split across clusters'}")
        print(f"Cluster Grouping Consistency: {clean_groups}/{len(dup_cluster_checks)} ({clean_groups/len(dup_cluster_checks)*100:.1f}%)")

    if mismatches:
        print(f"\n⚠️  MISMATCHES ({len(mismatches)} total):")
        print(f"{'ID':<9} {'Lang':<6} {'Exp Cat':<12} {'Pred Cat':<12} {'Exp Dept':<14} {'Pred Dept'}")
        print("-" * 65)
        for m in mismatches[:10]:
            print(f"{m['id']:<9} {m['lang']:<6} {m['exp_cat']:<12} {m['pred_cat']:<12} {m['exp_dept']:<14} {m['pred_dept']}")
        if len(mismatches) > 10:
            print(f"... and {len(mismatches) - 10} more.")

    print("=" * 65 + "\n")

    return {
        "total": total,
        "category_accuracy": cat_correct / total if total else 0,
        "department_accuracy": dept_correct / total if total else 0,
        "severity_accuracy": sev_correct / total if total else 0,
        "mismatches": mismatches,
    }


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "results.json"
    evaluate_predictions(path)
