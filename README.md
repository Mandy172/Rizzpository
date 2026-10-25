# CivicSort

Multilingual civic complaint triage for municipal (PMC) operations.

Citizens report problems in **English, Hindi, Marathi or Hinglish** at `/report`. Each report is triaged for category, department and urgency, duplicate reports are grouped, and officers get a prioritized queue at `/` with dispatch and resolve actions.

**Team:** [Samarth G,Sujay Tudu,Manas Dhakulkar,Kritagy Gour]  
**Event:** Hacktoberfest Hack Day

## How it works

1. **Citizen portal** (`/report`, Next.js) sends the text and landmark to `POST /triage`. If the API is unreachable it falls back to local keyword rules, and those reports get `USR-` IDs.
2. **Triage** (`backend/triage.py`, `backend/fast_rules.py`): obvious cases are decided by keyword rules. Everything else goes to `gemma3:4b`, an open-weight model running locally through Ollama. Each API response includes a `source` field (`fast_rules`, `model` or `fallback`).
3. **Clustering** (`backend/cluster.py`): `bge-m3` multilingual embeddings plus cosine agglomerative clustering group duplicate reports.
4. **Human review:** a rule-based completeness score flags uncertain reports for an officer (below 0.75, or unknown department or category).
5. **Officer console** (`/`) reads `GET /complaints` and shows the queue and duplicate groups.

## Models

| Role | Model | How it runs |
|---|---|---|
| Triage | `gemma3:4b` | Ollama, local |
| Duplicate clustering | `bge-m3` | Ollama, local |

No paid API is needed. (`triage.py` also supports a Gemini backend through `LLM_BACKEND`. It is not what produced our results.)

## Run it

Requirements: Python 3.10+, Node.js, [Ollama](https://ollama.com).

    ollama pull gemma3:4b
    ollama pull bge-m3

    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    LLM_BACKEND=ollama OLLAMA_MODEL=gemma3:4b python -m uvicorn backend.api:app --host 0.0.0.0 --port 8000

In a second terminal:

    cd frontend && npm install && npm run dev

Open `http://localhost:3000/report` (citizen) and `http://localhost:3000` (officer). `POST /reset` clears live submissions between demos.

## Evaluation and honest limits

- **Clustering:** tested blind (labels not used) against human-labelled duplicates: ARI 0.84 at threshold 0.25. That threshold was tuned on the same 54 complaints, so treat it as an upper bound. Run `python -m eval.cluster_check`.
- **Triage accuracy:** `python -m eval.evaluate` scores 54/54 on our dataset. This overstates real-world accuracy, because the keyword rules were written while looking at this dataset.
- **Confidence** is a rule-based completeness score (`compute_operational_confidence` in `backend/schema.py`), not a model probability and not calibrated. A wrong but well-formed answer can still score high.
- Romanized Hinglish embeds worse than Devanagari Hindi or Marathi.
- Photo upload is accepted in the citizen portal but is not yet sent to the officer console.
- The `dashboard/` Streamlit app is an earlier prototype and is not connected to the live API.
- A hosted frontend (e.g. Vercel) has no API behind it unless one is tunnelled. The full pipeline runs locally.

## Licenses and third-party notices

- Project code: see [LICENSE](LICENSE).
- **Gemma** (`gemma3:4b`) is released by Google under the [Gemma Terms of Use](https://ai.google.dev/gemma/terms). It is open-weight, not an OSI-approved open-source license.
- **bge-m3** is published by BAAI. Check its model card for the current license.
- **Ollama** is open source (MIT).
- Sample photos: attribution is in `data/photos/`.


PPT LINK - https://drive.google.com/file/d/1F0XNTo8twnVCcCzoATdF9LqT0RMz4efj/view?usp=sharing
