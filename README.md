# CivicSort

CivicSort is a multilingual civic-complaint triage and dispatch demo built for Hacktoberfest '26 Hack Day, Problem Statement #15. It helps a Pune municipal ward receive complaints, route them to the right department, prioritise urgent risks, and group reports about the same incident.

## What it does

- Lets citizens submit a complaint in English, Hindi, Marathi, or Hinglish, with an optional photo and landmark.
- Routes each report to a category, responsible department, and urgency level.
- Displays a ranked operations queue, Pune ward map, analytics, and review flags.
- Groups similar reports using multilingual embeddings and density-based clustering.
- Keeps citizen submissions separate from the labelled benchmark dataset.

## User flow

```text
Citizen portal → multilingual triage → structured route → duplicate clustering → operations dashboard
```

1. A citizen submits a report from **Report a Civic Issue**.
2. The triage pipeline returns a category, department, urgency, summary, and location.
3. The report enters the Ward Operations Center queue.
4. Officers inspect priority, map location, duplicate groups, and reports needing review.
5. The officer dispatches the appropriate team or marks the report resolved.

## Run locally

```bash
python3 -m pip install -r requirements.txt
streamlit run dashboard/app.py
```

Open the local address shown by Streamlit. Use the **Report a Civic Issue** page in the sidebar for the citizen portal, and **Ward Operations Center** for the municipal dashboard.

### Optional local AI setup

CivicSort uses fast multilingual rules for clear reports. For ambiguous or image-supported reports, it can use an Ollama model:

```bash
ollama pull gemma4:latest
ollama pull bge-m3
```

Set `LLM_BACKEND=ollama` and `OLLAMA_MODEL=gemma4:latest` in your environment before launching Streamlit. Gemini can also be configured through `GEMINI_API_KEY`.

## Project structure

| Path | Purpose |
|---|---|
| `dashboard/app.py` | Municipal operations dashboard |
| `dashboard/pages/1_🗳️_Submit_Complaint.py` | Citizen complaint portal |
| `backend/triage.py` | Structured multilingual complaint routing |
| `backend/cluster.py` | bge-m3 embeddings and HDBSCAN duplicate clustering |
| `data/complaints.json` | Labelled benchmark set of 54 complaints |
| `data/wards.json` | Ward-12 department and map data |
| `eval/evaluate.py` | Category, department, and severity evaluation |

## Demo dataset

The Ward-12 demonstration dataset includes 54 labelled complaints: 18 English, 14 Hindi, 12 Marathi, and 10 Hinglish. It covers six categories: road damage, water leak, garbage, streetlight, drainage, and other. It also includes eight labelled duplicate groups and optional reference photos with attribution.

## Models and licenses

| Component | Use | License |
|---|---|---|
| Ollama | Optional local inference and embeddings | MIT |
| Gemma | Optional multilingual and vision triage model | Gemma Terms of Use |
| bge-m3 | Multilingual semantic embeddings | MIT |
| Streamlit | Citizen portal and dashboard | Apache-2.0 |
| Pydantic | Structured output validation | MIT |
| HDBSCAN | Duplicate clustering | BSD-3-Clause |
| scikit-learn | Clustering fallback and metrics | BSD-3-Clause |
| pandas / NumPy | Data processing | BSD-3-Clause |

Project license: [MIT](LICENSE).
