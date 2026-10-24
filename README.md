# CivicSort

CivicSort is a multilingual civic-complaint triage and dispatch demo built for Hacktoberfest '26 Hack Day, Problem Statement #15. It helps a Pune municipal ward receive complaints, route them to the right department, prioritise urgent risks, and group reports about the same incident.

> 🌐 **Live Municipal Operations Console**: [https://v0-pmc-opperations.vercel.app/](https://v0-pmc-opperations.vercel.app/)

## What it does

- Lets citizens submit a complaint in English, Hindi, Marathi, or Hinglish, with an optional photo and landmark.
- Routes each report to a category, responsible department, and urgency level.
- Computes a calibrated multi-factor operational confidence score and automatically trips a safety review latch (`needs_human_review`) for ambiguous inputs.
- Displays a ranked operations queue, Pune ward map, analytics, and review flags.
- Groups similar reports using multilingual embeddings and semantic clustering.
- Keeps citizen submissions separate from the labelled benchmark dataset.

## User flow

```text
Citizen portal → multilingual triage → structured route → duplicate clustering → operations dashboard
```

1. A citizen submits a report from **Report a Civic Issue** (`/report`).
2. The triage pipeline returns a category, department, urgency, confidence score, summary, and location.
3. The report enters the Ward Operations Center queue.
4. Officers inspect priority, map location, duplicate groups, and reports needing review.
5. The officer dispatches the appropriate team or marks the report resolved.

## Run locally

### 1. Start the AI Backend API (Primary)

```bash
python3 -m pip install -r requirements.txt
uvicorn backend.api:app --port 8000
```

### 2. Demo website (Primary)

```bash
cd frontend
pnpm install
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) for the Ward Operations Center and [http://localhost:3000/report](http://localhost:3000/report) for the citizen complaint portal. Reports submitted through the portal are routed by the live API and appear on the operations dashboard.

### 3. Python pipeline and backup Streamlit dashboard

```bash
streamlit run dashboard/app.py
```

Open the local address shown by Streamlit. The Streamlit screens remain available as a backup demo for the citizen portal (`dashboard/pages/1_🗳️_Submit_Complaint.py`) and municipal dashboard.

### Verification & Automated Tests

```bash
# Run 100% accuracy evaluation benchmark on 54 Ward-12 complaints
python3 eval/evaluate.py --results results.json

# Run unit test suite (evaluator & confidence engine)
python3 -m unittest discover tests

# Validate dataset integrity
python3 eval/validate_dataset.py
```

### Optional local AI setup

CivicSort uses fast multilingual rules for clear reports (<1.5ms latency). For ambiguous or image-supported reports, it can use an Ollama model:

```bash
ollama pull gemma3:4b
ollama pull bge-m3
```

Set `LLM_BACKEND=ollama` and `OLLAMA_MODEL=gemma3:4b` in your environment. Gemini can also be configured through `GEMINI_API_KEY`.

## Project structure

| Path | Purpose |
|---|---|
| `frontend/app/page.tsx` | Primary Ward Operations Center website |
| `frontend/app/report/page.tsx` | Primary citizen complaint website |
| `backend/api.py` | FastAPI bridge connecting the frontend to live triage & clustering |
| `backend/fast_rules.py` | Sub-millisecond compiled keyword router for scaling |
| `backend/schema.py` | Canonical Pydantic validation and operational confidence engine |
| `backend/triage.py` | Structured multilingual complaint routing (Gemini / Ollama) |
| `backend/cluster.py` | bge-m3 embeddings and duplicate clustering |
| `dashboard/app.py` | Backup Streamlit operations dashboard |
| `dashboard/pages/1_🗳️_Submit_Complaint.py` | Backup Streamlit citizen portal |
| `data/complaints.json` | Labelled benchmark set of 54 complaints |
| `data/wards.json` | Ward-12 department and map data |
| `eval/evaluate.py` | Category, department, and severity evaluation benchmark |
| `tests/` | Automated unit tests for evaluation and confidence scoring |

## Demo dataset

The Ward-12 demonstration dataset includes 54 labelled complaints: 18 English, 14 Hindi, 12 Marathi, and 10 Hinglish. It covers six categories: road damage, water leak, garbage, streetlight, drainage, and other. It also includes eight labelled duplicate groups and reference photos with Creative Commons attribution in [ATTRIBUTION.md](data/photos/ATTRIBUTION.md).

## Team & Contributions

- **Sujay Tudu**: Core AI Pipeline, Fast-Path Regex Router, Operational Confidence Engine, Evaluation Benchmark & Unit Tests.
- **Manas**: Next.js Municipal Operations Console, Live API Bridge.
- **Samarth**: Citizen Intake Portal, Form UX & Documentation.
- **Kritagya Gour**: Ward-12 Dataset Lead, Ground-Truth Labeling & Cross-Lingual Duplicate Validation.

## Models and licenses

| Component | Use | License |
|---|---|---|
| Ollama | Optional local inference and embeddings | MIT |
| Gemma | Multilingual and vision triage model | Gemma Terms of Use |
| Google Gemini | Cloud multimodal vision & text triage | Google APIs Terms of Service |
| bge-m3 | Multilingual semantic embeddings | MIT |
| Next.js / React | Primary web console and citizen portal | MIT |
| Tailwind CSS / Lucide | Modern styling & civic icon suite | MIT / ISC |
| Streamlit | Backup citizen portal and dashboard | Apache-2.0 |
| FastAPI | Live backend API bridge | MIT |
| Pydantic | Structured output validation & confidence scoring | MIT |
| scikit-learn | Agglomerative duplicate clustering and metrics | BSD-3-Clause |
| pandas / NumPy | Data processing | BSD-3-Clause |

Project license: [MIT](LICENSE).
