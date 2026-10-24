"""
Citizen Complaint Portal — CivicSort
======================================
A clean, mobile-friendly intake form where citizens can report civic issues
in English, Hindi, Marathi, or Hinglish.

Submitted complaints are triaged by CivicSort and appear in the Ward
Operations Center dashboard.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from typing import Optional

import streamlit as st

# ── Path setup ────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Report a Civic Issue · CivicSort",
    page_icon="🗳️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background-color: #0f172a !important;
    color: #e2e8f0 !important;
}

#MainMenu, footer { visibility: hidden; }

[data-testid="stAppViewContainer"] { background: #0f172a !important; }
[data-testid="stSidebar"] { background: #0f172a !important; }

.portal-hero {
    text-align: center;
    padding: 2.5rem 1rem 1.5rem 1rem;
}
.portal-hero h1 {
    font-size: 2.2rem;
    font-weight: 900;
    color: #ffffff;
    letter-spacing: -0.03em;
    margin: 0 0 0.5rem 0;
}
.portal-hero p {
    color: #94a3b8;
    font-size: 1rem;
    margin: 0;
}
.lang-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    margin: 2px;
    background: #1e293b;
    color: #94a3b8;
    border: 1px solid #334155;
}
.result-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 1.5rem;
    margin-top: 1.5rem;
}
.result-card h3 {
    color: #10b981;
    font-size: 1.1rem;
    font-weight: 800;
    margin: 0 0 1rem 0;
}
.result-row {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem 0;
    border-bottom: 1px solid #334155;
    font-size: 0.9rem;
}
.result-row:last-child { border-bottom: none; }
.result-label { color: #64748b; }
.result-value { color: #f1f5f9; font-weight: 600; }
.sev-critical { color: #ef4444 !important; }
.sev-high     { color: #f97316 !important; }
.sev-medium   { color: #eab308 !important; }
.sev-low      { color: #22c55e !important; }

div[data-testid="stTextArea"] textarea {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    color: #f1f5f9 !important;
    border-radius: 10px !important;
    font-size: 1rem !important;
}
div[data-testid="stTextArea"] textarea:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
}
div[data-testid="stTextInput"] input {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    color: #f1f5f9 !important;
    border-radius: 10px !important;
}
div[data-testid="stSelectbox"] > div {
    background: #1e293b !important;
    border-radius: 10px !important;
}
div[data-testid="stFileUploader"] {
    background: #1e293b !important;
    border: 1.5px dashed #334155 !important;
    border-radius: 10px !important;
}
div[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    padding: 0.75rem !important;
    width: 100% !important;
    border: none !important;
    transition: all 0.2s ease !important;
}
div[data-testid="stFormSubmitButton"] button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(99,102,241,0.35) !important;
}
label[data-testid="stWidgetLabel"] p {
    color: #94a3b8 !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}
.st-expander {
    background: #1e293b !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
}
</style>""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
SUBMITTED_PATH = PROJECT_ROOT / "data" / "submitted_complaints.json"
UPLOAD_DIR     = PROJECT_ROOT / "data" / "uploads"

LANG_OPTIONS = {
    "en":       "🇬🇧  English",
    "hi":       "🇮🇳  Hindi (हिन्दी)",
    "mr":       "🌟  Marathi (मराठी)",
    "hinglish": "🤝  Hinglish (Hindi + English)",
}

CATEGORY_ICONS = {
    "road_damage":  "🛣️",
    "water_leak":   "💧",
    "garbage":      "🗑️",
    "drainage":     "🌊",
    "streetlight":  "💡",
    "other":        "📋",
}

DEPT_CONTACTS = {
    "Roads":         "roads@civicflow.demo",
    "Water Supply":  "water@civicflow.demo",
    "Sanitation":    "sanitation@civicflow.demo",
    "Electrical":    "electrical@civicflow.demo",
    "Drainage":      "drainage@civicflow.demo",
}

EXAMPLE_COMPLAINTS = {
    "-- Write your own complaint --": "",
    "💧 Water Leak (Hinglish)": "School ke paas pipe phoot gaya hai, road par pani bhar raha hai.",
    "🛣️ Pothole (Hindi)": "बस स्टॉप के सामने बड़ा गड्ढा है, बाइक वाले गिर रहे हैं।",
    "🗑️ Garbage (Marathi)": "मार्केटच्या कोपऱ्यात चार दिवसांपासून कचरा उचललेला नाही.",
    "💡 Streetlight (English)": "Streetlight near the park entrance has been broken for a week.",
    "🌊 Blocked Drain (Hinglish)": "Nala overflow ho raha hai near the clinic, road par pani hai.",
    "⚠️ Open Manhole (Hinglish)": "Footpath pe open manhole cover nahi hai, bachche wahan se jaate hain.",
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def save_uploaded_photo(uploaded_file) -> Optional[str]:
    if uploaded_file is None:
        return None
    ext = Path(uploaded_file.name).suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png"}:
        return None
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    fname = f"citizen-{uuid4().hex[:10]}{ext}"
    dest = UPLOAD_DIR / fname
    dest.write_bytes(uploaded_file.getbuffer())
    return str((UPLOAD_DIR / fname).relative_to(PROJECT_ROOT))


def run_triage(text: str, photo_rel_path: Optional[str]) -> dict:
    from backend.triage import triage_complaint
    abs_photo = str(PROJECT_ROOT / photo_rel_path) if photo_rel_path else None
    return triage_complaint(text, photo_path=abs_photo)


def persist_report(report: dict):
    try:
        existing = json.loads(SUBMITTED_PATH.read_text(encoding="utf-8")) if SUBMITTED_PATH.exists() else []
        existing = existing if isinstance(existing, list) else []
    except (json.JSONDecodeError, OSError):
        existing = []
    existing.append(report)
    SUBMITTED_PATH.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")


def build_report(text: str, language: str, landmark: str, photo_rel: Optional[str], triage: dict) -> dict:
    sev_map = {"low": 2, "medium": 3, "high": 4, "critical": 5}
    return {
        "id":              f"USR-{uuid4().hex[:7].upper()}",
        "text":            text.strip(),
        "language":        language,
        "ward":            "Ward-12",
        "category":        triage.get("category", "other"),
        "department":      triage.get("department", "Sanitation"),
        "severity":        sev_map.get(triage.get("urgency", "medium"), 3),
        "urgency":         triage.get("urgency", "medium"),
        "severity_reason": triage.get("urgency_reason", "AI triage assessment."),
        "needs_human_review": triage.get("category") == "other" or triage.get("department") == "unknown",
        "confidence":      0.93 if triage.get("department") not in [None, "unknown"] else 0.62,
        "cluster_id":      -1,
        "duplicate_group": None,
        "lat":             18.5204,
        "lng":             73.8567,
        "location_hint":   landmark.strip() or triage.get("location", "Ward-12, Pune"),
        "photo_path":      photo_rel,
        "reports":         1,
        "submitted_at":    datetime.now(timezone.utc).isoformat(),
    }

# ── Session state ─────────────────────────────────────────────────────────────
if "portal_result" not in st.session_state:
    st.session_state.portal_result = None
if "portal_submitted" not in st.session_state:
    st.session_state.portal_submitted = False

# ── Hero header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="portal-hero">
    <h1>🏙️ Report a Civic Issue</h1>
    <p>Pune Municipal Corporation · Ward 12 · Multilingual AI-assisted routing</p>
    <div style="margin-top:0.8rem;">
        <span class="lang-badge">🇬🇧 English</span>
        <span class="lang-badge">🇮🇳 हिन्दी</span>
        <span class="lang-badge">🌟 मराठी</span>
        <span class="lang-badge">🤝 Hinglish</span>
    </div>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── Success banner (after submission) ────────────────────────────────────────
if st.session_state.portal_submitted and st.session_state.portal_result:
    r = st.session_state.portal_result
    urg = r.get("urgency", "medium")
    sev_class = f"sev-{urg}"
    cat = r.get("category", "other")
    cat_icon = CATEGORY_ICONS.get(cat, "📋")
    dept = r.get("department", "Sanitation")
    dept_email = DEPT_CONTACTS.get(dept, "civic@pune.gov.in")

    st.markdown(f"""
<div class="result-card">
    <h3>✅ Complaint Registered & Routed!</h3>
    <div class="result-row">
        <span class="result-label">Complaint ID</span>
        <span class="result-value">{r['id']}</span>
    </div>
    <div class="result-row">
        <span class="result-label">Category</span>
        <span class="result-value">{cat_icon} {cat.replace('_', ' ').title()}</span>
    </div>
    <div class="result-row">
        <span class="result-label">Routed To</span>
        <span class="result-value">🏛️ {dept} ({dept_email})</span>
    </div>
    <div class="result-row">
        <span class="result-label">Urgency</span>
        <span class="result-value {sev_class}">{urg.upper()}</span>
    </div>
    <div class="result-row">
        <span class="result-label">AI Summary</span>
        <span class="result-value" style="max-width:65%;text-align:right;">{r.get('severity_reason', '')}</span>
    </div>
    <div class="result-row">
        <span class="result-label">Location Hint</span>
        <span class="result-value">{r.get('location_hint', 'Ward-12, Pune')}</span>
    </div>
</div>
""", unsafe_allow_html=True)

    if st.button("📋 Submit Another Complaint", use_container_width=True):
        st.session_state.portal_result = None
        st.session_state.portal_submitted = False
        st.rerun()

    st.stop()

# ── Complaint form ────────────────────────────────────────────────────────────
# Quick example picker
example_pick = st.selectbox(
    "💡 Try an example complaint:",
    options=list(EXAMPLE_COMPLAINTS.keys()),
)
prefill = EXAMPLE_COMPLAINTS[example_pick]

with st.form("citizen_portal_form", clear_on_submit=False):
    complaint_text = st.text_area(
        "Describe the civic issue *",
        value=prefill,
        placeholder="Type your complaint here in any language — English, Hindi, Marathi or Hinglish...",
        height=160,
        max_chars=1200,
    )

    col_lang, col_landmark = st.columns(2)
    with col_lang:
        language = st.selectbox(
            "Language of complaint",
            options=list(LANG_OPTIONS.keys()),
            format_func=lambda k: LANG_OPTIONS[k],
        )
    with col_landmark:
        landmark = st.text_input(
            "Nearest landmark (optional)",
            placeholder="e.g. Tilak Road school gate",
        )

    photo = st.file_uploader(
        "📷  Attach a photo (optional — JPG or PNG)",
        type=["jpg", "jpeg", "png"],
        help="A photo helps the vision model verify the severity of your report.",
    )

    if photo:
        st.image(photo, caption="Preview", width=260)

    submit_btn = st.form_submit_button(
        "🚀  Submit & Route Complaint",
        use_container_width=True,
    )

if submit_btn:
    text = complaint_text.strip()
    if len(text) < 8:
        st.error("⚠️ Please describe the issue in at least a few words.")
    else:
        with st.spinner("🤖 CivicSort AI is reading your complaint..."):
            try:
                photo_rel = save_uploaded_photo(photo)
                triage    = run_triage(text, photo_rel)
                report    = build_report(text, language, landmark, photo_rel, triage)
                persist_report(report)
                st.session_state.portal_result    = report
                st.session_state.portal_submitted = True
                st.rerun()
            except Exception as e:
                st.error(f"❌ Could not process complaint: {e}")
                st.info("If you use local AI, make sure Ollama and the configured model are running.")

# ── Info expander ─────────────────────────────────────────────────────────────
st.divider()
with st.expander("ℹ️ How does this work?", expanded=False):
    st.markdown("""
**CivicSort** first uses multilingual routing rules for clear reports. It can use a configured AI model through Ollama or Gemini for ambiguous and photo-supported reports.

When you submit a complaint:
1. **Language Handling** — Works in English, Hindi, Marathi, and Hinglish.
2. **Category Classification** — Roads, Water Supply, Garbage, Drainage, Streetlight, or Other.
3. **Urgency Assessment** — Critical / High / Medium / Low based on danger signals in the text.
4. **Department Routing** — Automatically assigned to the correct municipal ward department.
5. **Photo Support** — If you attach a photo, the configured vision-capable model can assess unclear reports.
6. **Operations Queue** — Your report appears in the Ward-12 queue, where duplicate clustering groups similar incidents.

Your complaint instantly appears in the **Ward Operations Center** dashboard.
    """)

st.caption("CivicSort · Pune Municipal Corporation Demo · Problem Statement #15 · Open-source under MIT License")
