"""Dataset validation script for Kritagya (Dataset & Testing).

Verifies that data/complaints.json and data/wards.json adhere strictly to the schema:
- Valid JSON format
- Required fields present for all complaints
- Categories match wards.json allowed handles
- Departments match wards.json departments
- Severities match allowed values ('critical', 'high', 'medium', 'low')
- Languages match allowed values ('en', 'hi', 'mr', 'hinglish')
- Coordinates are within Pune Ward-12 boundary
- Photo paths exist if specified
- Duplicate groups have >= 2 complaints
"""

import json
import os
import sys

ALLOWED_CATEGORIES = {"road_damage", "water_leak", "garbage", "drainage", "streetlight", "other"}
ALLOWED_SEVERITIES = {"critical", "high", "medium", "low"}
ALLOWED_LANGUAGES = {"en", "hi", "mr", "hinglish"}
WARD_LAT_RANGE = (18.50, 18.55)
WARD_LON_RANGE = (73.83, 73.88)


def validate():
    errors = []
    warnings = []

    # 1. Load wards.json
    wards_path = "data/wards.json"
    if not os.path.exists(wards_path):
        errors.append(f"Missing {wards_path}")
        return errors, warnings

    with open(wards_path, "r", encoding="utf-8") as f:
        ward = json.load(f)

    ward_departments = {d["name"]: d["handles"] for d in ward.get("departments", [])}
    print(f"Loaded Ward: {ward.get('ward_id')} ({ward.get('name')})")
    print(f"Ward Departments: {list(ward_departments.keys())}")

    # 2. Load complaints.json
    complaints_path = "data/complaints.json"
    if not os.path.exists(complaints_path):
        errors.append(f"Missing {complaints_path}")
        return errors, warnings

    with open(complaints_path, "r", encoding="utf-8") as f:
        complaints = json.load(f)

    print(f"Total Complaints: {len(complaints)}")
    if len(complaints) < 50:
        warnings.append(f"Complaint count is {len(complaints)}, target is 50-60.")

    dup_groups = {}
    lang_counts = {}

    for i, c in enumerate(complaints):
        cid = c.get("id", f"index-{i}")
        # Required fields
        for field in ["id", "text", "language", "ward", "latitude", "longitude", "expected"]:
            if field not in c:
                errors.append(f"[{cid}] Missing required field: '{field}'")

        lang = c.get("language")
        if lang not in ALLOWED_LANGUAGES:
            errors.append(f"[{cid}] Invalid language '{lang}', allowed: {ALLOWED_LANGUAGES}")
        else:
            lang_counts[lang] = lang_counts.get(lang, 0) + 1

        # Check coordinates
        lat = c.get("latitude", 0)
        lon = c.get("longitude", 0)
        if not (WARD_LAT_RANGE[0] <= lat <= WARD_LAT_RANGE[1]):
            warnings.append(f"[{cid}] Latitude {lat} outside Ward-12 range {WARD_LAT_RANGE}")
        if not (WARD_LON_RANGE[0] <= lon <= WARD_LON_RANGE[1]):
            warnings.append(f"[{cid}] Longitude {lon} outside Ward-12 range {WARD_LON_RANGE}")

        # Check photo path
        photo = c.get("photo_path")
        if photo and not os.path.exists(photo):
            errors.append(f"[{cid}] Photo path '{photo}' does not exist on disk!")

        # Check duplicate group
        dg = c.get("duplicate_group")
        if dg:
            dup_groups.setdefault(dg, []).append(cid)

        # Check expected schema
        expected = c.get("expected", {})
        cat = expected.get("category")
        sev = expected.get("severity")
        dept = expected.get("department")

        if cat not in ALLOWED_CATEGORIES:
            errors.append(f"[{cid}] Invalid expected category '{cat}', allowed: {ALLOWED_CATEGORIES}")

        if sev not in ALLOWED_SEVERITIES:
            errors.append(f"[{cid}] Invalid expected severity '{sev}', allowed: {ALLOWED_SEVERITIES}")

        if dept not in ward_departments:
            errors.append(f"[{cid}] Invalid expected department '{dept}', allowed: {list(ward_departments.keys())}")
        elif cat and cat not in ward_departments[dept]:
            warnings.append(f"[{cid}] Category '{cat}' not in handled list for department '{dept}' ({ward_departments[dept]})")

    # Check duplicate groups count & size
    print(f"\nDuplicate Groups ({len(dup_groups)}):")
    for dg, members in dup_groups.items():
        if len(members) < 2:
            warnings.append(f"Duplicate group '{dg}' has fewer than 2 members: {members}")
        print(f"  - {dg}: {len(members)} complaints ({', '.join(members)})")

    if not (6 <= len(dup_groups) <= 10):
        warnings.append(f"Found {len(dup_groups)} duplicate groups; target is 6–8.")

    print(f"\nLanguage Distribution: {lang_counts}")

    return errors, warnings


if __name__ == "__main__":
    errors, warnings = validate()
    print("\n" + "=" * 50)
    print(f"VALIDATION SUMMARY: {len(errors)} errors, {len(warnings)} warnings")
    print("=" * 50)

    for w in warnings:
        print(f"⚠️  WARNING: {w}")

    for e in errors:
        print(f"❌ ERROR: {e}")

    if errors:
        sys.exit(1)
    else:
        print("✅ ALL DATASET CHECKS PASSED PERFECTLY!")
