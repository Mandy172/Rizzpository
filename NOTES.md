# Test notes — CivicFlow Triage & Routing

Dataset & Testing Lead: **Kritagya Gour**

---

## 1. Dataset Overview

- **Total Complaints:** 54 complaints strictly scoped around Pune Ward-12 (`18.5158` to `18.5261` N, `73.8519` to `73.8601` E).
- **Language Distribution:**
  - English (`en`): 18 complaints
  - Hindi (`hi`): 14 complaints
  - Marathi (`mr`): 12 complaints
  - Hinglish (`hinglish`): 10 complaints
- **Duplicate Groups:** 8 distinct groups (`DUP-01` through `DUP-08`) testing cross-lingual duplicate reporting (e.g., `DUP-01` water leak reported in EN, HI, MR).
- **Photos:** 6 reference images with open Creative Commons licenses tracked in [ATTRIBUTION.md](file:///Users/kritagyagour/Documents/Codex/2026-10-24/wha/work/Rizzpository/data/photos/ATTRIBUTION.md).
- **Automated Validation:** Passes `python3 eval/validate_dataset.py` with 0 errors and 0 warnings.

---

## 2. Cross-Team Schema Alignment (Kritagya ↔ Sujay ↔ Manas)

To prevent breaking bugs between dataset ground truth, AI triage, and dashboard integration, canonical definitions are locked in [backend/schema.py](file:///Users/kritagyagour/Documents/Codex/2026-10-24/wha/work/Rizzpository/backend/schema.py):

| Field | Canonical Values | Notes |
| --- | --- | --- |
| `category` | `road_damage`, `water_leak`, `garbage`, `drainage`, `streetlight`, `other` | Aligned with `data/wards.json` handles |
| `severity` | `critical`, `high`, `medium`, `low` | `critical` reserved for direct safety hazard |
| `department` | `Roads`, `Water Supply`, `Sanitation`, `Electrical`, `Drainage` | Exact matching ward department names |
| `duplicate_group` | `DUP-01` to `DUP-08` or `null` | Used for evaluating deduplication clustering |

---

## 3. Manual Testing Checklist

- [x] **Dataset Integrity:** Validated format, coordinate boundaries, and schema types (`eval/validate_dataset.py`).
- [x] **English Triage:** CMP-001 routes to `water_leak`, `high`, `Water Supply`.
- [x] **Hindi Triage:** CMP-020 routes to `road_damage`, `critical`/`high`, `Roads` (verified with `gemma4:latest`).
- [x] **Marathi Triage:** CMP-033 routes to `water_leak`, `high`, `Water Supply`.
- [x] **Hinglish Triage:** CMP-047 routes to `road_damage`, `high`, `Roads`.
- [x] **Cross-Lingual Duplicates:** `DUP-01`, `DUP-02`, `DUP-03` contain matching issues across languages.
- [x] **Ward-12 Geo-coordinates:** Verified all 54 pins fall within Ward-12 boundary (18.515 to 18.526 N, 73.851 to 73.860 E).
- [x] **Missing Photo Graceful Degradation:** Triage works seamlessly when `photo_path` is null.
- [x] **Baseline Results Generation:** `eval/generate_mock_results.py` generates `results.json` unblocking Manas for dashboard development.

---

## 4. Key Test Observations & Ambiguous Cases

| Complaint ID | Language | Description | Expected Category / Dept / Severity | Observed Model Behavior | Resolution & Advice |
| --- | --- | --- | --- | --- | --- |
| `CMP-006` | en | Large fallen tree blocking road | `other` / `Roads` / `high` | Tree is obstruction, not road surface damage | `Roads` department correctly configured to handle road obstructions |
| `CMP-015` | en | Abandoned vehicle outside health center | `other` / `Roads` / `low` | Parking / obstruction issue | Handled by `Roads` ward team |
| `CMP-029` | hi | Stray injured dog in park | `other` / `Sanitation` / `medium` | Animal control / civic sanitation | Routed to `Sanitation` |
| `CMP-043` | mr | Dead animal near bus depot | `other` / `Sanitation` / `medium` | Carcass removal | Routed to `Sanitation` |
| `CMP-053` | hinglish | Open manhole cover on footpath | `other` / `Drainage` / `critical` | Missing cover over sewer | Handled by `Drainage`, severity flagged `critical` due to fatal fall hazard |
| `DUP-01` | Multi (EN, HI, MR) | Tilak Road water leak outside school | 4 reports (`CMP-001`, `CMP-013`, `CMP-019`, `CMP-033`) | Grouped into single issue cluster | Dedup radius threshold should be ~150m with `water_leak` category match |

---

## 5. Verification Tools

- **Validate Dataset:**
  ```bash
  python3 eval/validate_dataset.py
  ```
- **Generate Baseline Results (for dashboard testing):**
  ```bash
  python3 eval/generate_mock_results.py
  ```
- **Run Benchmark Evaluation:**
  ```bash
  python3 eval/evaluate.py results.json
  ```
