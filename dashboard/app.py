import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4
import pandas as pd
import streamlit as st
import altair as alt
import pydeck as pdk

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ── Streamlit Setup ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CivicSort · Intelligent Municipal Triage",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session State for Interactive Actions ─────────────────────────────────────
if "resolved_ids" not in st.session_state:
    st.session_state.resolved_ids = set()
if "dispatched_ids" not in st.session_state:
    st.session_state.dispatched_ids = set()
if "last_submission" not in st.session_state:
    st.session_state.last_submission = None

# ── Ultra-modern CSS Styling (Zero-indent HTML blocks to prevent markdown codeblocks) ──
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

/* Apply font safely without breaking Material Icon ligatures */
html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"], p, h1, h2, h3, h4, h5, h6, input, button, select {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

#MainMenu, footer { visibility: hidden; }

/* Keep header transparent and position the sidebar open/close toggle cleanly */
header[data-testid="stHeader"] {
    background: transparent !important;
    z-index: 100 !important;
}

[data-testid="stSidebarCollapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    top: 0.8rem !important;
    left: 0.8rem !important;
}

[data-testid="stSidebarCollapsedControl"] button {
    background: #0f1930 !important;
    border: 1.5px solid #3b82f6 !important;
    border-radius: 10px !important;
    color: #ffffff !important;
    width: 2.6rem !important;
    height: 2.6rem !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-shadow: 0 4px 14px rgba(59, 130, 246, 0.4) !important;
    transition: all 0.2s ease !important;
}

[data-testid="stSidebarCollapsedControl"] button:hover {
    background: #1d4ed8 !important;
    border-color: #93c5fd !important;
    transform: scale(1.08) !important;
}

[data-testid="stSidebarCollapsedControl"] svg,
[data-testid="stSidebarCollapsedControl"] span {
    font-size: 1.4rem !important;
    width: 1.4rem !important;
    height: 1.4rem !important;
}

/* ── App Canvas ── */
[data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at 10% 20%, #0d1527 0%, #060a13 90%) !important;
    color: #e2e8f0;
}
[data-testid="block-container"] {
    padding: 1.5rem 2.2rem 3rem 2.2rem !important;
    max-width: 100% !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #090f1d !important;
    border-right: 1px solid #182642 !important;
}
[data-testid="stSidebar"] hr {
    border-color: #182642 !important;
    margin: 0.8rem 0 !important;
}

/* ── Brand Logo ── */
.brand-container {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 0.6rem 0 1rem 0;
    border-bottom: 1px solid #182642;
    margin-bottom: 1rem;
}
.brand-logo {
    width: 44px;
    height: 44px;
    background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    box-shadow: 0 8px 16px -4px rgba(59, 130, 246, 0.4);
    flex-shrink: 0;
}
.brand-title {
    font-size: 1.25rem;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: -0.02em;
    line-height: 1.1;
}
.brand-subtitle {
    font-size: 0.7rem;
    color: #64748b;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-top: 3px;
}

/* ── KPI Cards ── */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 14px;
    margin-bottom: 1.4rem;
}
.kpi-card {
    background: #0c1426;
    border: 1px solid #1a2947;
    border-radius: 14px;
    padding: 1rem 1.2rem;
    position: relative;
    overflow: hidden;
    transition: all 0.25s ease;
}
.kpi-card:hover {
    border-color: #3b82f6;
    transform: translateY(-2px);
    box-shadow: 0 10px 25px -5px rgba(12, 20, 38, 0.8);
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #3b82f6, #8b5cf6);
    opacity: 0.8;
}
.kpi-title {
    font-size: 0.72rem;
    font-weight: 700;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.kpi-value {
    font-size: 1.9rem;
    font-weight: 800;
    color: #f8fafc;
    margin: 0.35rem 0 0.1rem 0;
    letter-spacing: -0.02em;
}
.kpi-sub {
    font-size: 0.72rem;
    color: #64748b;
    font-weight: 500;
}

/* ── Section Titles ── */
.section-title {
    font-size: 0.8rem;
    font-weight: 700;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin: 0 0 0.75rem 0;
}

/* ── Complaint Card ── */
.complaint-box {
    background: #0c1426;
    border: 1px solid #1a2947;
    border-radius: 12px;
    padding: 1.1rem 1.25rem 0.9rem 1.25rem;
    margin-bottom: 0.4rem;
    transition: all 0.2s ease;
}
.complaint-box:hover {
    border-color: #3b82f6;
    background: #0f1930;
}
.complaint-text {
    font-size: 0.94rem;
    color: #f1f5f9;
    font-weight: 500;
    line-height: 1.55;
    margin: 0.7rem 0;
}
.tag {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 9px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.02em;
}
.tag-prio { background: #1e1b4b; color: #a5b4fc; border: 1px solid #312e81; }
.tag-cat  { background: #0f2447; color: #93c5fd; border: 1px solid #1d4ed8; }
.tag-dept { background: #064e3b; color: #6ee7b7; border: 1px solid #047857; }
.tag-lang { background: #1e293b; color: #cbd5e1; border: 1px solid #334155; }
.tag-rev-yes { background: #450a0a; color: #fca5a5; border: 1px solid #991b1b; }
.tag-rev-no  { background: #064e3b; color: #6ee7b7; border: 1px solid #047857; }

/* ── Live Pulse Indicator ── */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: rgba(34, 197, 94, 0.12);
    border: 1px solid rgba(34, 197, 94, 0.35);
    color: #4ade80;
    padding: 4px 11px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 700;
}
.pulse-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #22c55e;
    box-shadow: 0 0 10px #22c55e;
    animation: pulseGlow 1.8s infinite;
}
@keyframes pulseGlow {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.3; transform: scale(0.85); }
}

/* ── Tabs Styling ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: transparent;
    border-bottom: 1px solid #1a2947;
    padding-bottom: 4px;
    margin-bottom: 1.2rem;
}
.stTabs [data-baseweb="tab"] {
    background: #0c1426;
    border: 1px solid #1a2947;
    border-radius: 10px;
    color: #94a3b8;
    padding: 8px 18px;
    font-size: 0.85rem;
    font-weight: 700;
    transition: all 0.2s;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #f8fafc;
    border-color: #3b82f6;
}
.stTabs [aria-selected="true"] {
    background: #1e3a8a !important;
    border-color: #3b82f6 !important;
    color: #ffffff !important;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

/* ── Streamlit Form Controls ── */
[data-testid="stTextInput"] input {
    background: #0c1426 !important;
    border: 1px solid #1a2947 !important;
    border-radius: 10px !important;
    color: #f1f5f9 !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: #3b82f6 !important;
}
</style>""", unsafe_allow_html=True)


# ── Data Loading & Fallback Safety ───────────────────────────────────────────
@st.cache_data
def load_data():
    results_path = PROJECT_ROOT / "data" / "results.json"
    if not results_path.exists():
        results_path = PROJECT_ROOT / "results.json"
    if not results_path.exists():
        st.error(f"Cannot find results.json at {results_path}")
        return pd.DataFrame()

    with open(results_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    # Citizen reports are stored outside the seed dataset so a demo submission
    # remains visible after a browser refresh without modifying benchmark data.
    submitted_path = PROJECT_ROOT / "data" / "submitted_complaints.json"
    if submitted_path.exists():
        try:
            with open(submitted_path, "r", encoding="utf-8") as submitted_file:
                submitted_records = json.load(submitted_file)
            if isinstance(submitted_records, list):
                records.extend(submitted_records)
        except (json.JSONDecodeError, OSError):
            pass

    df = pd.DataFrame(records)

    # Normalize coordinate column names
    if "lat" not in df.columns and "latitude" in df.columns:
        df["lat"] = df["latitude"]
    if "lng" not in df.columns and "longitude" in df.columns:
        df["lng"] = df["longitude"]

    # Normalize column names across various teammate conventions
    if "urgency" in df.columns and "severity" not in df.columns:
        u_map = {"critical": 5, "high": 4, "medium": 3, "low": 2}
        df["severity"] = df["urgency"].map(u_map).fillna(3).astype(int)
    if "severity" not in df.columns:
        df["severity"] = 3
    if "cluster_id" not in df.columns:
        df["cluster_id"] = -1

    # The bundled Ward-12 demonstration results retain their validated
    # duplicate-group labels. Use those stable IDs for the dashboard while
    # newly submitted reports remain unclustered until the next pipeline run.
    if "duplicate_group" in df.columns:
        known_groups = df["duplicate_group"].dropna().astype(str)
        if not known_groups.empty:
            group_ids = {
                group: index + 1
                for index, group in enumerate(sorted(known_groups.unique()))
            }
            df["cluster_id"] = df["duplicate_group"].map(group_ids).fillna(-1).astype(int)
    if "needs_human_review" not in df.columns:
        df["needs_human_review"] = False
    if "language" not in df.columns:
        df["language"] = "en"
    if "department" not in df.columns:
        df["department"] = "other"
    if "confidence" not in df.columns:
        df["confidence"] = 0.88

    # Calculate cluster sizes (reports count)
    valid_clusters = df[df.cluster_id >= 0]
    sizes = valid_clusters.groupby("cluster_id").size() if not valid_clusters.empty else pd.Series(dtype=int)
    df["reports"] = df.cluster_id.map(sizes).fillna(1).astype(int)

    # Priority Score Formula: Severity * 10 + Duplicate Reports * 3
    df["priority"] = (df["severity"] * 10) + (df["reports"] * 3)

    return df


def save_uploaded_photo(uploaded_file) -> Optional[str]:
    """Save an optional image locally so the vision-capable triage path can read it."""
    if uploaded_file is None:
        return None

    extension = Path(uploaded_file.name).suffix.lower()
    if extension not in {".jpg", ".jpeg", ".png"}:
        return None

    upload_dir = PROJECT_ROOT / "data" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"report-{uuid4().hex[:12]}{extension}"
    photo_path = upload_dir / filename
    photo_path.write_bytes(uploaded_file.getbuffer())
    return str(photo_path.relative_to(PROJECT_ROOT))


def submit_complaint(text: str, language: str, landmark: str, uploaded_file) -> dict:
    """Run the existing triage model and persist one citizen report for the dashboard."""
    from backend.triage import triage_complaint

    relative_photo_path = save_uploaded_photo(uploaded_file)
    absolute_photo_path = (
        str(PROJECT_ROOT / relative_photo_path) if relative_photo_path else None
    )
    triage = triage_complaint(text, photo_path=absolute_photo_path)

    urgency_to_severity = {"low": 2, "medium": 3, "high": 4, "critical": 5}
    ward_center = {"lat": 18.5204, "lng": 73.8567}
    report = {
        "id": f"USR-{uuid4().hex[:7].upper()}",
        "text": text.strip(),
        "language": language,
        "ward": "Ward-12",
        "category": triage["category"],
        "department": triage["department"],
        "severity": urgency_to_severity.get(triage["urgency"], 3),
        "urgency": triage["urgency"],
        "severity_reason": triage.get("urgency_reason") or "Assessed by the CivicSort triage model.",
        "needs_human_review": triage["category"] == "other" or triage["department"] == "unknown",
        "confidence": 0.92 if triage["department"] != "unknown" else 0.60,
        "cluster_id": -1,
        "duplicate_group": None,
        "lat": ward_center["lat"],
        "lng": ward_center["lng"],
        "location_hint": landmark.strip() or triage.get("location", "unknown"),
        "photo_path": relative_photo_path,
        "reports": 1,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }

    submitted_path = PROJECT_ROOT / "data" / "submitted_complaints.json"
    try:
        previous = json.loads(submitted_path.read_text(encoding="utf-8")) if submitted_path.exists() else []
        previous = previous if isinstance(previous, list) else []
    except (json.JSONDecodeError, OSError):
        previous = []
    previous.append(report)
    submitted_path.write_text(json.dumps(previous, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


df_all = load_data()
if df_all.empty:
    st.stop()

# ── Color Definitions ─────────────────────────────────────────────────────────
SEV_MAP = {
    1: {"name": "Cosmetic", "bg": "#064e3b", "color": "#6ee7b7", "rgb": [34, 197, 94]},
    2: {"name": "Minor", "bg": "#713f12", "color": "#fde68a", "rgb": [234, 179, 8]},
    3: {"name": "Inconvenient", "bg": "#78350f", "color": "#fcd34d", "rgb": [202, 138, 4]},
    4: {"name": "Serious Hazard", "bg": "#7f1d1d", "color": "#fca5a5", "rgb": [239, 68, 68]},
    5: {"name": "Critical Danger", "bg": "#4c0519", "color": "#fda4af", "rgb": [153, 27, 27]},
}

LANG_FLAGS = {
    "en": "🇬🇧 English",
    "hi": "🇮🇳 Hindi",
    "mr": "🚩 Marathi",
    "hinglish": "🔀 Hinglish",
    "other": "🌐 Other",
}

# ── Sidebar Navigation & Filters ──────────────────────────────────────────────
with st.sidebar:
    # App Logo
    st.markdown("""<div class="brand-container">
<div class="brand-logo">🏙️</div>
<div>
<div class="brand-title">CivicSort</div>
<div class="brand-subtitle">Pune Municipal Corporation</div>
</div>
</div>""", unsafe_allow_html=True)

    st.markdown("""<div style="margin-bottom: 1rem;">
<span class="status-pill"><span class="pulse-dot"></span>PMC Ward Live Engine</span>
</div>""", unsafe_allow_html=True)

    st.markdown("### 🎛️ Intelligent Filters")

    # Search Box
    search_query = st.text_input(
        "Search complaints",
        placeholder="Search keywords (e.g., 'gaddha', 'leak')...",
        label_visibility="collapsed",
    )

    # Language Filter
    available_langs = sorted(df_all["language"].unique())
    lang_labels = [LANG_FLAGS.get(l, l) for l in available_langs]
    selected_lang_labels = st.multiselect(
        "🌐 Language",
        options=lang_labels,
        default=lang_labels,
    )
    selected_langs = [l for l in available_langs if LANG_FLAGS.get(l, l) in selected_lang_labels]

    # Category Filter
    all_categories = sorted(df_all["category"].unique())
    cat_display_map = {c: c.replace("_", " ").title() for c in all_categories}
    selected_cats = st.multiselect(
        "📂 Category",
        options=all_categories,
        default=all_categories,
        format_func=lambda c: cat_display_map.get(c, c),
    )

    # Department Filter
    all_depts = sorted(df_all["department"].unique())
    selected_depts = st.multiselect(
        "🏛️ Department",
        options=all_depts,
        default=all_depts,
        format_func=lambda d: d.replace("_", " ").title(),
    )

    # Severity Slider
    st.markdown("---")
    min_severity = st.slider("⚡ Minimum Severity Level", 1, 5, 1)

    # Operational Toggles
    st.markdown("### 🎯 Quick Filters")
    flag_review = st.toggle("⚠️ Only Needs Human Review", value=False)
    flag_duplicates = st.toggle("🔗 Only Duplicate Clusters", value=False)
    flag_unresolved = st.toggle("⏳ Only Pending Dispatches", value=False)

    st.markdown("---")
    # Severity Legend
    st.markdown("### 🎨 Severity Legend")
    for sev_num, info in SEV_MAP.items():
        st.markdown(
            f"""<div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;">
<div style="width:12px;height:12px;border-radius:4px;background:{info["color"]};"></div>
<span style="font-size:0.78rem;color:#cbd5e1;font-weight:600;">Level {sev_num} — {info["name"]}</span>
</div>""",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.caption("CivicSort AI Pipeline · Multilingual Triage · PMC Demo 2026")


# ── Filter Data ───────────────────────────────────────────────────────────────
mask = (
    df_all["language"].isin(selected_langs)
    & df_all["category"].isin(selected_cats)
    & df_all["department"].isin(selected_depts)
    & (df_all["severity"] >= min_severity)
)

if search_query.strip():
    mask = mask & df_all["text"].str.contains(search_query.strip(), case=False, na=False)

if flag_review:
    mask = mask & df_all["needs_human_review"]

if flag_duplicates:
    mask = mask & (df_all["cluster_id"] >= 0) & (df_all["reports"] > 1)

filtered_df = df_all[mask].copy()

if flag_unresolved:
    filtered_df = filtered_df[~filtered_df["id"].isin(st.session_state.resolved_ids)]


# ── Header Banner ─────────────────────────────────────────────────────────────
header_col1, header_col2 = st.columns([3, 1])
with header_col1:
    st.markdown("""<div style="display:flex;align-items:center;gap:12px;margin-bottom:0.2rem;">
<h1 style="font-size:2.1rem;font-weight:900;color:#ffffff;letter-spacing:-0.03em;margin:0;">
Civic Complaint Triage & Dispatch
</h1>
</div>
<p style="color:#94a3b8;font-size:0.88rem;margin:0 0 1.2rem 0;">
Automated multilingual complaint routing, severity scoring, and duplicate clustering for Pune Municipal Corporation.
</p>""", unsafe_allow_html=True)

with header_col2:
    st.markdown("<div style='text-align:right;'>", unsafe_allow_html=True)
    if st.button("🔄 Reset All Filters", width="stretch"):
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# ── Main Tabs ────────────────────────────────────────────────────────────────
tab_ops, tab_submit, tab_clusters = st.tabs([
    "📊 Ward Operations Center",
    "📝 Report a Civic Issue",
    "🔗 Duplicate Cluster Analytics",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: OPERATIONS CENTER
# ══════════════════════════════════════════════════════════════════════════════
with tab_ops:
    # ── KPI Cards ─────────────────────────────────────────────────────────────
    n_complaints = len(filtered_df)
    n_groups = int(filtered_df[filtered_df.cluster_id >= 0]["cluster_id"].nunique())
    n_critical = int((filtered_df.severity >= 4).sum())
    n_review = int(filtered_df.needs_human_review.sum())
    avg_confidence = f"{filtered_df['confidence'].mean() * 100:.0f}%" if n_complaints > 0 else "N/A"

    kpi_html = f"""<div class="kpi-grid">
<div class="kpi-card">
<div class="kpi-title">📋 Active Queue</div>
<div class="kpi-value">{n_complaints}</div>
<div class="kpi-sub">{len(st.session_state.resolved_ids)} resolved in session</div>
</div>
<div class="kpi-card">
<div class="kpi-title">🔗 Duplicate Groups</div>
<div class="kpi-value">{n_groups}</div>
<div class="kpi-sub">Clustered by bge-m3 + HDBSCAN</div>
</div>
<div class="kpi-card">
<div class="kpi-title">⚡ Severe Hazards</div>
<div class="kpi-value" style="color:#f87171;">{n_critical}</div>
<div class="kpi-sub">Priority 4 & 5 immediate danger</div>
</div>
<div class="kpi-card">
<div class="kpi-title">👁️ Human Review</div>
<div class="kpi-value" style="color:#fbbf24;">{n_review}</div>
<div class="kpi-sub">Ambiguous or mixed input</div>
</div>
<div class="kpi-card">
<div class="kpi-title">🎯 AI Confidence</div>
<div class="kpi-value" style="color:#38bdf8;">{avg_confidence}</div>
<div class="kpi-sub">Mean semantic certainty</div>
</div>
</div>"""
    st.markdown(kpi_html, unsafe_allow_html=True)

    # ── Charts Row ────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">📈 Real-time Analytics</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)

    chart_theme = {
        "background": "#0c1426",
        "axisX": {
            "labelColor": "#94a3b8", "labelFontSize": 11, "labelAngle": 0,
            "tickColor": "#1a2947", "gridColor": "#0c1426", "domainColor": "#1a2947",
            "titleColor": "#64748b"
        },
        "axisY": {
            "labelColor": "#94a3b8", "labelFontSize": 10,
            "gridColor": "#162238", "domainColor": "#1a2947",
            "tickColor": "#1a2947", "titleColor": "#64748b"
        },
        "view": {"stroke": "transparent"},
    }

    with c1:
        st.caption("**Complaints by Category**")
        if not filtered_df.empty:
            cat_counts = filtered_df["category"].value_counts().reset_index()
            cat_counts.columns = ["category", "count"]
            cat_counts["label"] = cat_counts["category"].str.replace("_", " ").str.title()
            ch_cat = (
                alt.Chart(cat_counts)
                .mark_bar(color="#3b82f6", cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
                .encode(
                    x=alt.X("label:N", sort="-y", title=None, axis=alt.Axis(labelAngle=0, labelLimit=85)),
                    y=alt.Y("count:Q", title=None, axis=alt.Axis(tickMinStep=1)),
                    tooltip=["label:N", "count:Q"],
                )
                .properties(height=170)
                .configure(**chart_theme)
            )
            st.altair_chart(ch_cat, use_container_width=True)
        else:
            st.info("No data")

    with c2:
        st.caption("**Severity Distribution**")
        if not filtered_df.empty:
            sev_counts = filtered_df["severity"].value_counts().sort_index().reset_index()
            sev_counts.columns = ["severity", "count"]
            sev_counts["color"] = sev_counts["severity"].map(lambda s: SEV_MAP.get(s, {}).get("color", "#94a3b8"))
            sev_counts["name"] = sev_counts["severity"].map(lambda s: f"L{s} {SEV_MAP.get(s, {}).get('name', '')}")
            ch_sev = (
                alt.Chart(sev_counts)
                .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
                .encode(
                    x=alt.X("name:N", sort=None, title=None, axis=alt.Axis(labelAngle=0, labelLimit=90)),
                    y=alt.Y("count:Q", title=None, axis=alt.Axis(tickMinStep=1)),
                    color=alt.Color("color:N", scale=None),
                    tooltip=["name:N", "count:Q"],
                )
                .properties(height=170)
                .configure(**chart_theme)
            )
            st.altair_chart(ch_sev, use_container_width=True)
        else:
            st.info("No data")

    with c3:
        st.caption("**Departmental Workload**")
        if not filtered_df.empty:
            dept_counts = filtered_df["department"].value_counts().reset_index()
            dept_counts.columns = ["department", "count"]
            dept_counts["label"] = dept_counts["department"].str.replace("_", " ").str.title()
            ch_dept = (
                alt.Chart(dept_counts)
                .mark_bar(color="#10b981", cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
                .encode(
                    x=alt.X("label:N", sort="-y", title=None, axis=alt.Axis(labelAngle=0, labelLimit=85)),
                    y=alt.Y("count:Q", title=None, axis=alt.Axis(tickMinStep=1)),
                    tooltip=["label:N", "count:Q"],
                )
                .properties(height=170)
                .configure(**chart_theme)
            )
            st.altair_chart(ch_dept, use_container_width=True)
        else:
            st.info("No data")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Main Two-Column Layout ────────────────────────────────────────────────
    col_queue, col_map = st.columns([3, 2], gap="large")

    with col_queue:
        # Sorting Controls
        sub_c1, sub_c2 = st.columns([2, 1])
        with sub_c1:
            st.markdown(f'<div class="section-title">📋 Priority Queue ({len(filtered_df)} items)</div>', unsafe_allow_html=True)
        with sub_c2:
            sort_opt = st.selectbox(
                "Sort",
                ["Priority (High → Low)", "Severity (High → Low)", "Reports Count", "Newest"],
                label_visibility="collapsed",
            )

        # Apply Sort
        if sort_opt == "Priority (High → Low)":
            display_df = filtered_df.sort_values("priority", ascending=False)
        elif sort_opt == "Severity (High → Low)":
            display_df = filtered_df.sort_values(["severity", "priority"], ascending=False)
        elif sort_opt == "Reports Count":
            display_df = filtered_df.sort_values("reports", ascending=False)
        else:
            display_df = filtered_df

        if display_df.empty:
            st.info("No complaints match your active filter criteria.")
        else:
            for _, row in display_df.iterrows():
                cid = row["id"]
                is_resolved = cid in st.session_state.resolved_ids
                is_dispatched = cid in st.session_state.dispatched_ids

                sev_val = int(row["severity"])
                sev_info = SEV_MAP.get(sev_val, SEV_MAP[3])
                cat_name = str(row["category"]).replace("_", " ").title()
                dept_name = str(row["department"]).replace("_", " ").title()
                lang_tag = LANG_FLAGS.get(str(row["language"]), str(row["language"]))

                cluster_badge = (
                    f'<span class="tag" style="background:#1e1b4b;color:#c7d2fe;border:1px solid #4338ca;">🔗 Group #{int(row["cluster_id"])} ({int(row["reports"])} reports)</span>'
                    if row["cluster_id"] >= 0 and row["reports"] > 1
                    else '<span class="tag" style="background:#0f172a;color:#64748b;border:1px solid #1e293b;">Single Report</span>'
                )

                review_badge = (
                    '<span class="tag tag-rev-yes">⚠️ Needs Review</span>'
                    if row["needs_human_review"]
                    else '<span class="tag tag-rev-no">✓ Auto-Approved</span>'
                )

                status_label = ""
                if is_resolved:
                    status_label = '<span class="tag" style="background:#064e3b;color:#a7f3d0;border:1px solid #059669;">✅ RESOLVED</span>'
                elif is_dispatched:
                    status_label = '<span class="tag" style="background:#1e3a8a;color:#93c5fd;border:1px solid #2563eb;">🚀 CREW DISPATCHED</span>'

                # Formatted Card HTML with zero-indent lines to avoid markdown codeblock bugs
                card_html = f"""<div class="complaint-box" style="{'border-color:#10b981;opacity:0.75;' if is_resolved else ''}">
<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;margin-bottom:8px;">
<div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">
<span class="tag tag-prio">Priority {int(row["priority"])}</span>
<span class="tag" style="background:{sev_info['bg']};color:{sev_info['color']};border:1px solid {sev_info['color']}55;">Level {sev_val} · {sev_info['name']}</span>
<span class="tag tag-cat">{cat_name}</span>
<span class="tag tag-dept">{dept_name}</span>
{cluster_badge}
{review_badge}
{status_label}
</div>
<span style="font-size:0.75rem;color:#64748b;font-weight:600;">{cid} · {lang_tag}</span>
</div>
<div class="complaint-text">{row["text"]}</div>
<div style="font-size:0.78rem;color:#94a3b8;display:flex;justify-content:space-between;align-items:center;margin-top:6px;">
<span><b style="color:#cbd5e1;">Justification:</b> {row.get("severity_reason", "Assessed by civic model")}</span>
<span style="color:#64748b;">Confidence: {int(row.get("confidence", 0.85) * 100)}%</span>
</div>
</div>"""
                st.markdown(card_html, unsafe_allow_html=True)

                # Interactive Quick-Action buttons
                act1, act2, act3 = st.columns([1, 1, 3])
                with act1:
                    if not is_dispatched and not is_resolved:
                        if st.button("🚀 Dispatch", key=f"disp_{cid}"):
                            st.session_state.dispatched_ids.add(cid)
                            st.toast(f"Crew dispatched for {cid} ({dept_name})!", icon="🚀")
                            st.rerun()
                with act2:
                    if not is_resolved:
                        if st.button("✅ Resolve", key=f"res_{cid}"):
                            st.session_state.resolved_ids.add(cid)
                            st.toast(f"Complaint {cid} marked as Resolved!", icon="✅")
                            st.rerun()
                st.markdown("<div style='margin-bottom:0.4rem;'></div>", unsafe_allow_html=True)

    with col_map:
        st.markdown('<div class="section-title">🗺️ Geo-Spatial Incident Map · Pune</div>', unsafe_allow_html=True)

        map_data = filtered_df.rename(columns={"lng": "lon"})[["lat", "lon", "severity", "category", "text", "id"]].dropna().copy()

        if not map_data.empty:
            map_data["color"] = map_data["severity"].map(lambda s: SEV_MAP.get(int(s), {}).get("rgb", [234, 179, 8]))
            map_data["radius"] = map_data["severity"].map(lambda s: 120 + (int(s) * 60))

            layer = pdk.Layer(
                "ScatterplotLayer",
                data=map_data,
                get_position="[lon, lat]",
                get_fill_color="color",
                get_line_color=[255, 255, 255, 80],
                get_radius="radius",
                radius_min_pixels=8,
                radius_max_pixels=28,
                stroked=True,
                line_width_min_pixels=1.5,
                pickable=True,
                opacity=0.88,
            )

            view_state = pdk.ViewState(
                latitude=float(map_data["lat"].mean()),
                longitude=float(map_data["lon"].mean()),
                zoom=11.2,
                pitch=20,
            )

            map_tooltip = {
                "html": (
                    "<div style='font-family:Plus Jakarta Sans,sans-serif;font-size:12px;"
                    "background:#090f1d;color:#e2e8f0;padding:10px 14px;border-radius:10px;"
                    "border:1px solid #1a2947;box-shadow:0 8px 20px rgba(0,0,0,0.7);max-width:260px;'>"
                    "<div style='color:#38bdf8;font-weight:700;margin-bottom:3px;'>{id} · {category}</div>"
                    "<div style='margin-bottom:6px;line-height:1.4;'>{text}</div>"
                    "<div style='color:#f87171;font-weight:700;'>Severity Level: {severity}</div>"
                    "</div>"
                ),
                "style": {"backgroundColor": "transparent", "border": "none"},
            }

            st.pydeck_chart(
                pdk.Deck(
                    layers=[layer],
                    initial_view_state=view_state,
                    tooltip=map_tooltip,
                    map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
                ),
                height=380,
            )
        else:
            st.info("No geospatial data for current filters.")

        # Duplicate Groups Spotlight
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">🔗 Top Duplicate Incident Clusters</div>', unsafe_allow_html=True)

        clustered_only = filtered_df[filtered_df.cluster_id >= 0]
        if not clustered_only.empty:
            grp_stats = (
                clustered_only.groupby("cluster_id")
                .agg(
                    reports=("id", "count"),
                    category=("category", "first"),
                    department=("department", "first"),
                    max_sev=("severity", "max"),
                )
                .sort_values(["reports", "max_sev"], ascending=False)
                .head(6)
                .reset_index()
            )

            for _, g in grp_stats.iterrows():
                sev_i = SEV_MAP.get(int(g["max_sev"]), SEV_MAP[3])
                cat_n = str(g["category"]).replace("_", " ").title()
                dept_n = str(g["department"]).replace("_", " ").title()

                group_html = f"""<div style="background:#0c1426;border:1px solid #1a2947;border-radius:10px;padding:0.75rem 1rem;margin-bottom:0.5rem;display:flex;justify-content:space-between;align-items:center;">
<div>
<div style="display:flex;align-items:center;gap:6px;">
<span style="font-weight:800;color:#818cf8;font-size:0.85rem;">Group #{int(g["cluster_id"])}</span>
<span class="tag tag-cat">{cat_n}</span>
<span class="tag tag-dept">{dept_n}</span>
</div>
<div style="color:#64748b;font-size:0.75rem;margin-top:3px;">
Municipal savings: merged {int(g["reports"])} tickets into 1 crew dispatch
</div>
</div>
<div style="text-align:right;">
<div style="font-size:1.15rem;font-weight:800;color:#38bdf8;">{int(g["reports"])}×</div>
<span style="font-size:0.7rem;color:{sev_i['color']};font-weight:700;">Sev {int(g['max_sev'])}</span>
</div>
</div>"""
                st.markdown(group_html, unsafe_allow_html=True)
        else:
            st.caption("No multi-report clusters found in current filter.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: CITIZEN COMPLAINT INTAKE
# ══════════════════════════════════════════════════════════════════════════════
with tab_submit:
    st.markdown("""<div style="margin-bottom:1.2rem;">
<h3 style="font-size:1.3rem;font-weight:800;color:#ffffff;margin:0 0 0.3rem 0;">
📝 Report a Civic Issue
</h3>
<p style="color:#94a3b8;font-size:0.9rem;margin:0;">
Describe the problem in English, Hindi, Marathi, or Hinglish. CivicSort will route it to the right municipal department.
</p>
</div>""", unsafe_allow_html=True)

    form_col, guide_col = st.columns([3, 2], gap="large")
    with form_col:
        with st.form("citizen_complaint_form", clear_on_submit=True):
            complaint_text = st.text_area(
                "What is the civic issue?",
                placeholder="Example: School ke paas pipe phoot gaya hai aur road par pani aa raha hai.",
                height=150,
                max_chars=1200,
            )
            field_left, field_right = st.columns(2)
            with field_left:
                complaint_language = st.selectbox(
                    "Complaint language",
                    options=["en", "hi", "mr", "hinglish"],
                    format_func=lambda code: LANG_FLAGS[code],
                )
            with field_right:
                landmark = st.text_input(
                    "Nearest landmark (optional)",
                    placeholder="e.g. Tilak Road school gate",
                )
            photo = st.file_uploader(
                "Attach a photo (optional)",
                type=["jpg", "jpeg", "png"],
                help="A photo can help the vision-enabled triage path assess unclear reports.",
            )
            submitted = st.form_submit_button("🚀 Submit complaint for triage", use_container_width=True)

        if submitted:
            if len(complaint_text.strip()) < 8:
                st.error("Please describe the issue in at least a few words.")
            else:
                with st.spinner("Classifying and routing your complaint..."):
                    try:
                        report = submit_complaint(
                            complaint_text,
                            complaint_language,
                            landmark,
                            photo,
                        )
                        st.session_state.last_submission = report
                        load_data.clear()
                        st.toast(
                            f"Complaint {report['id']} routed to {report['department']}.",
                            icon="✅",
                        )
                        # Run once more so the Operations Center immediately
                        # reads the persisted report and updates its queue.
                        st.rerun()
                    except Exception as exc:
                        st.error(f"The complaint could not be processed: {exc}")

    with guide_col:
        st.markdown("""<div class="complaint-box">
<div class="section-title">What happens next?</div>
<div style="color:#cbd5e1;line-height:1.7;font-size:0.9rem;">
1. CivicSort identifies the issue category.<br>
2. It assigns the responsible department.<br>
3. It estimates urgency from low to critical.<br>
4. The report appears in the operations queue.<br>
5. Unclear reports are marked for human review.
</div>
</div>""", unsafe_allow_html=True)
        st.caption("For this Ward-12 demo, submitted reports appear at the ward centre on the map. A production version can use GPS or geocoding.")

    if st.session_state.last_submission:
        report = st.session_state.last_submission
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Latest routing result")
        result_a, result_b, result_c, result_d = st.columns(4)
        result_a.metric("Category", str(report["category"]).replace("_", " ").title())
        result_b.metric("Department", report["department"])
        result_c.metric("Urgency", str(report["urgency"]).title())
        result_d.metric("Report ID", report["id"])
        st.caption(report["severity_reason"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: DUPLICATE CLUSTER DEEP-DIVE
# ══════════════════════════════════════════════════════════════════════════════
with tab_clusters:
    st.markdown("""<div style="margin-bottom:1.2rem;">
<h3 style="font-size:1.3rem;font-weight:800;color:#ffffff;margin:0 0 0.3rem 0;">
🔗 bge-m3 + HDBSCAN Semantic Deduplication
</h3>
<p style="color:#94a3b8;font-size:0.85rem;margin:0;">
How our multilingual embeddings merge separate citizen reports about the same incident into a single unified ticket.
</p>
</div>""", unsafe_allow_html=True)

    c_clusters = df_all[df_all.cluster_id >= 0]["cluster_id"].unique()
    if len(c_clusters) > 0:
        for cid in sorted(c_clusters):
            group_items = df_all[df_all.cluster_id == cid]
            if len(group_items) < 2:
                continue

            first = group_items.iloc[0]
            cat_n = str(first["category"]).replace("_", " ").title()
            dept_n = str(first["department"]).replace("_", " ").title()

            st.markdown(f"""<div style="background:#0c1426;border:1px solid #1a2947;border-radius:12px;padding:1rem 1.25rem;margin-bottom:1rem;">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.6rem;">
<div style="display:flex;align-items:center;gap:8px;">
<span style="font-weight:800;color:#818cf8;font-size:1rem;">Cluster #{cid}</span>
<span class="tag tag-cat">{cat_n}</span>
<span class="tag tag-dept">{dept_n}</span>
</div>
<span style="font-size:0.85rem;color:#38bdf8;font-weight:700;">{len(group_items)} Citizen Reports Merged</span>
</div>""", unsafe_allow_html=True)

            for _, item in group_items.iterrows():
                lang_tag = LANG_FLAGS.get(str(item["language"]), str(item["language"]))
                st.markdown(f"""<div style="background:#080f1e;border-left:3px solid #3b82f6;padding:8px 12px;margin:5px 0;border-radius:4px;">
<div style="font-size:0.75rem;color:#64748b;margin-bottom:2px;">Report ID: <b>{item['id']}</b> ({lang_tag})</div>
<div style="color:#cbd5e1;font-size:0.88rem;">"{item['text']}"</div>
</div>""", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Run clustering first using `python -m backend.cluster` to generate semantic clusters.")
