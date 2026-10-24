# Civic Complaint Triage
Built at Hacktoberfest 26 Hack Day (NST.ADYPU · NSTSDC, Pune, 24--25
Oct 2026) for Problem Statement #15: Civic Complaint Triage and
Routing.

Municipal portals receive thousands of free-text complaints (potholes,
garbage, water leaks) that staff sort by hand. Citizens write in
English, Hindi, Marathi or Hinglish, urgent cases sit in the same queue
as trivial ones, and the same issue is reported again and again.

This project helps municipal teams sort, prioritize and route incoming
complaints quickly, and spot repeated complaints about the same issue,
using an Ollama model that runs locally.
What it does
- Accepts a complaint as free text (English, Hindi, Marathi,
  Hinglish), with an optional photo and location.
- Classifies each complaint into a category, a severity and
  the department that should handle it.
- Groups duplicate complaints about the same issue so officers see
  one problem with many reports.
- Shows everything on a dashboard with a Ward-12 map.
- A missing photo never blocks text triage.
- Complaint text is processed by a local Ollama model, so it is
  not sent to a cloud AI service.
How it works
Complaint (text + optional photo + location)
        │
        ▼
  FastAPI backend ──► Ollama (local model) ──► category, severity, department (JSON)
        │
        ▼
  Duplicate grouping (clustering)
        │
        ▼
  Streamlit dashboard: triage table, duplicate groups, Ward-12 map
Models and Licenses
  Component        Used for               License
  Ollama       Local AI inference     MIT
  ollama-python    Python client          MIT
  FastAPI          Backend API            MIT
  Uvicorn          API server             BSD-3-Clause
  Pydantic         Data validation        MIT
  Streamlit        Dashboard              Apache-2.0
  pydeck           Ward map               BSD-3-Clause
  HDBSCAN          Duplicate grouping     BSD-3-Clause
  scikit-learn     Clustering utilities   BSD-3-Clause
  pandas / NumPy   Data handling          BSD-3-Clause
  Pillow           Photo handling         HPND

Project License: MIT
