import json
import pandas as pd
import streamlit as st
import altair as alt
import pydeck as pdk

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CivicSort · Triage Dashboard",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ---- fonts & base ---- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ---- hide default streamlit chrome ---- */
#MainMenu, footer, header { visibility: hidden; }

/* ---- sidebar ---- */
[data-testid="stSidebar"] {
    background: #0f172a;
    border-right: 1px solid #1e293b;
}
[data-testid="stSidebar"] * { color: #cbd5e1 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #f1f5f9 !important; }

/* ---- main background ---- */
[data-testid="stAppViewContainer"] {
    background: #0f172a;
}
[data-testid="block-container"] {
    padding: 2rem 2.5rem 2rem 2.5rem;
}

/* ---- metric cards ---- */
[data-testid="metric-container"] {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
}
[data-testid="metric-container"] label {
    color: #94a3b8 !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #f1f5f9 !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
}

/* ---- section headers ---- */
.section-header {
    font-size: 1rem;
    font-weight: 700;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin: 0 0 0.75rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #1e293b;
}

/* ---- dataframe ---- */
[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
}

/* ---- severity badge helper classes (used in HTML) ---- */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.04em;
}
.sev-1  { background:#14532d; color:#86efac; }
.sev-2  { background:#713f12; color:#fde68a; }
.sev-3  { background:#78350f; color:#fcd34d; }
.sev-4  { background:#7f1d1d; color:#fca5a5; }
.sev-5  { background:#4c0519; color:#fda4af; }
.cat-badge { background:#1e293b; color:#e2e8f0; border:1px solid #334155; }
.dept-badge { background:#0f2447; color:#93c5fd; border:1px solid #1e40af; }
.review-yes { background:#431407; color:#fca5a5; }
.review-no  { background:#134e4a; color:#6ee7b7; }

/* ---- complaint card ---- */
.complaint-card {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.6rem;
    transition: border-color 0.2s;
}
.complaint-card:hover { border-color: #475569; }
.complaint-text {
    color: #e2e8f0;
    font-size: 0.9rem;
    margin: 0.4rem 0 0.6rem 0;
    line-height: 1.5;
}
.complaint-meta {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    align-items: center;
}
.priority-pill {
    background: #312e81;
    color: #a5b4fc;
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 0.72rem;
    font-weight: 700;
}
.cluster-pill {
    background: #1e293b;
    color: #64748b;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 0.72rem;
}

/* ---- page title ---- */
.page-title {
    font-size: 1.85rem;
    font-weight: 800;
    color: #f1f5f9;
    letter-spacing: -0.02em;
    margin: 0;
}
.page-sub {
    color: #64748b;
    font-size: 0.85rem;
    margin-top: 2px;
    margin-bottom: 1.5rem;
}
.live-dot {
    display: inline-block;
    width: 8px; height: 8px;
    background: #22c55e;
    border-radius: 50%;
    margin-right: 6px;
    animation: blink 1.4s infinite;
}
@keyframes blink {
    0%,100%{opacity:1} 50%{opacity:0.3}
}
</style>
""", unsafe_allow_html=True)


# ── Data ──────────────────────────────────────────────────────────────────────
@st.cache_data
def load():
    with open("data/results.json") as f:
        raw = json.load(f)
    df = pd.DataFrame(raw)
    sizes = df[df.cluster_id >= 0].groupby("cluster_id").size()
    df["reports"] = df.cluster_id.map(sizes).fillna(1).astype(int)
    df["priority"] = df.severity * 10 + df.reports * 3
    return df

df = load()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏙️ CivicSort")
    st.markdown("---")
    st.markdown("### Filters")

    all_cats = sorted(df.category.unique())
    cats = st.multiselect("Category", all_cats, default=all_cats)

    all_depts = sorted(df.department.unique())
    depts = st.multiselect("Department", all_depts, default=all_depts)

    min_sev = st.slider("Min severity", 1, 5, 1)
    show_review = st.checkbox("Only needs review", value=False)

    st.markdown("---")
    st.markdown("### Legend — Severity")
    for label, colour in [
        ("1 – Cosmetic",     "#22c55e"),
        ("2 – Minor",        "#eab308"),
        ("3 – Inconvenient", "#ca8a04"),
        ("4 – Serious",      "#ef4444"),
        ("5 – Danger",       "#991b1b"),
    ]:
        st.markdown(
            f'<span style="color:{colour};font-weight:700">●</span> {label}',
            unsafe_allow_html=True,
        )

# ── Filter ────────────────────────────────────────────────────────────────────
mask = (
    df.category.isin(cats)
    & df.department.isin(depts)
    & (df.severity >= min_sev)
)
if show_review:
    mask = mask & df.needs_human_review
view = df[mask].sort_values("priority", ascending=False)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    '<p class="page-title">Civic Complaint Triage Dashboard</p>'
    '<p class="page-sub"><span class="live-dot"></span>Live · Pune Municipal Corporation · Ward A</p>',
    unsafe_allow_html=True,
)

# ── KPI row ───────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("📋 Complaints", len(view))
k2.metric("🔗 Issue Groups", int(view[view.cluster_id >= 0].cluster_id.nunique()))
k3.metric("🔴 Needs Review", int(view.needs_human_review.sum()))
k4.metric("⚡ High Severity (4-5)", int((view.severity >= 4).sum()))
k5.metric("📍 Avg Severity", f"{view.severity.mean():.1f}" if len(view) else "—")

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts row ────────────────────────────────────────────────────────────────
ch1, ch2, ch3 = st.columns(3)

CHART_CFG = dict(
    background="#1e293b",
    axisX=dict(
        labelColor="#94a3b8", labelFontSize=11, labelAngle=0,
        tickColor="#334155", gridColor="#334155", domainColor="#334155",
        titleColor="#64748b",
    ),
    axisY=dict(
        labelColor="#94a3b8", labelFontSize=11,
        gridColor="#1e293b", domainColor="#334155",
        tickColor="#334155", titleColor="#64748b",
    ),
    view=dict(stroke="transparent"),
)

with ch1:
    st.markdown('<p class="section-header">Complaints by Category</p>', unsafe_allow_html=True)
    cat_df = (
        view.category
        .value_counts()
        .rename_axis("category")
        .reset_index(name="count")
    )
    # shorten labels
    cat_df["label"] = cat_df["category"].str.replace("_", " ").str.title()
    chart = (
        alt.Chart(cat_df)
        .mark_bar(color="#6366f1", cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("label:N", sort="-y", title=None,
                    axis=alt.Axis(labelAngle=0, labelLimit=90, labelFontSize=11)),
            y=alt.Y("count:Q", title="count",
                    axis=alt.Axis(tickMinStep=1)),
            tooltip=["label:N", "count:Q"],
        )
        .properties(height=190)
        .configure(**CHART_CFG)
    )
    st.altair_chart(chart, use_container_width=True)

with ch2:
    st.markdown('<p class="section-header">Severity Distribution</p>', unsafe_allow_html=True)
    SEV_COLORS = {1:"#6ee7b7", 2:"#93c5fd", 3:"#fcd34d", 4:"#fca5a5", 5:"#fda4af"}
    sev_df = (
        view.severity
        .value_counts()
        .sort_index()
        .rename_axis("severity")
        .reset_index(name="count")
    )
    sev_df["label"] = sev_df["severity"].map(
        {1:"1 – Cosmetic", 2:"2 – Minor", 3:"3 – Inconvenient",
         4:"4 – Serious", 5:"5 – Danger"}
    )
    sev_df["color"] = sev_df["severity"].map(SEV_COLORS)
    chart = (
        alt.Chart(sev_df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("label:N", sort=None, title=None,
                    axis=alt.Axis(labelAngle=0, labelLimit=110, labelFontSize=11)),
            y=alt.Y("count:Q", title="count",
                    axis=alt.Axis(tickMinStep=1)),
            color=alt.Color("color:N", scale=None, legend=None),
            tooltip=["label:N", "count:Q"],
        )
        .properties(height=190)
        .configure(**CHART_CFG)
    )
    st.altair_chart(chart, use_container_width=True)

with ch3:
    st.markdown('<p class="section-header">Department Load</p>', unsafe_allow_html=True)
    dept_df = (
        view.department
        .value_counts()
        .rename_axis("department")
        .reset_index(name="count")
    )
    dept_df["label"] = dept_df["department"].str.replace("_", " ").str.title()
    chart = (
        alt.Chart(dept_df)
        .mark_bar(color="#10b981", cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("label:N", sort="-y", title=None,
                    axis=alt.Axis(labelAngle=0, labelLimit=90, labelFontSize=11)),
            y=alt.Y("count:Q", title="count",
                    axis=alt.Axis(tickMinStep=1)),
            tooltip=["label:N", "count:Q"],
        )
        .properties(height=190)
        .configure(**CHART_CFG)
    )
    st.altair_chart(chart, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Main panel: cards + map ───────────────────────────────────────────────────
SEV_COLOUR = {1: "#86efac", 2: "#fde68a", 3: "#fcd34d", 4: "#fca5a5", 5: "#fda4af"}
SEV_BG     = {1: "#14532d", 2: "#713f12", 3: "#78350f", 4: "#7f1d1d", 5: "#4c0519"}

left, right = st.columns([3, 2], gap="large")

with left:
    st.markdown(
        f'<p class="section-header">Ranked Queue &nbsp;·&nbsp; {len(view)} complaints</p>',
        unsafe_allow_html=True,
    )

    for _, row in view.iterrows():
        sc = SEV_COLOUR.get(row.severity, "#94a3b8")
        sb = SEV_BG.get(row.severity, "#1e293b")
        review_tag = (
            '<span class="badge review-yes">⚠ Review</span>'
            if row.needs_human_review
            else '<span class="badge review-no">✓ Auto</span>'
        )
        cluster_tag = (
            f'<span class="cluster-pill">Group #{int(row.cluster_id)} · {int(row.reports)} reports</span>'
            if row.cluster_id >= 0
            else '<span class="cluster-pill">Unique</span>'
        )
        st.markdown(f"""
<div class="complaint-card">
  <div class="complaint-meta">
    <span class="priority-pill">P {int(row.priority)}</span>
    <span class="badge" style="background:{sb};color:{sc}">Sev {int(row.severity)}</span>
    <span class="badge cat-badge">{row.category.replace('_',' ').title()}</span>
    <span class="badge dept-badge">{row.department.replace('_',' ').title()}</span>
    {review_tag}
    {cluster_tag}
  </div>
  <p class="complaint-text">{row.text}</p>
  <div style="font-size:0.72rem;color:#475569">
    ID {row.id} &nbsp;·&nbsp; {row.language.upper()}
    {'&nbsp;·&nbsp; 📍 ' + str(row.location_hint) if 'location_hint' in row and row.location_hint and str(row.location_hint) != 'nan' else ''}
  </div>
</div>
""", unsafe_allow_html=True)

with right:
    st.markdown('<p class="section-header">Complaint Map · Pune</p>', unsafe_allow_html=True)

    # severity colours: 1=green 2=yellow 3=dark-yellow 4=red 5=dark-red
    SEV_RGB = {
        1: [34,  197, 94],    # green
        2: [234, 179, 8],     # yellow
        3: [202, 138, 4],     # dark yellow
        4: [239, 68,  68],    # red
        5: [153, 27,  27],    # dark red
    }
    map_df = view.rename(columns={"lng": "lon"})[
        ["lat", "lon", "severity", "category", "text"]
    ].dropna().copy()
    map_df["color"]  = map_df["severity"].map(SEV_RGB)
    map_df["radius"] = map_df["severity"] * 90

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position="[lon, lat]",
        get_fill_color="color",
        get_line_color=[255, 255, 255, 60],
        get_radius="radius",
        radius_min_pixels=7,
        radius_max_pixels=24,
        stroked=True,
        line_width_min_pixels=1,
        pickable=True,
        opacity=0.9,
    )
    view_state = pdk.ViewState(
        latitude=map_df["lat"].mean(),
        longitude=map_df["lon"].mean(),
        zoom=11,
        pitch=0,
    )
    tooltip = {
        "html": (
            "<div style='font-family:Inter,sans-serif;font-size:12px;"
            "background:#1e293b;color:#e2e8f0;padding:8px 12px;"
            "border-radius:8px;border:1px solid #334155'>"
            "<b style='color:#a5b4fc'>{category}</b><br/>"
            "{text}<br/>"
            "<span style='color:#94a3b8'>Severity {severity}</span>"
            "</div>"
        ),
        "style": {"backgroundColor": "transparent", "border": "none"},
    }
    st.pydeck_chart(
        pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip=tooltip,
            # CARTO dark-matter — free, no Mapbox token needed
            map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
        ),
        use_container_width=True,
        height=400,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<p class="section-header">Top Duplicate Groups</p>', unsafe_allow_html=True)

    groups = (
        view[view.cluster_id >= 0]
        .groupby("cluster_id")
        .agg(reports=("id", "count"), category=("category", "first"),
             severity=("severity", "max"), department=("department", "first"))
        .sort_values(["reports", "severity"], ascending=False)
        .head(8)
        .reset_index()
    )
    for _, g in groups.iterrows():
        sc = SEV_COLOUR.get(g.severity, "#94a3b8")
        sb = SEV_BG.get(g.severity, "#1e293b")
        st.markdown(f"""
<div class="complaint-card" style="padding:0.75rem 1rem;">
  <div class="complaint-meta">
    <span style="font-weight:700;color:#a5b4fc">Group #{int(g.cluster_id)}</span>
    <span class="badge cat-badge">{g.category.replace('_',' ').title()}</span>
    <span class="badge" style="background:{sb};color:{sc}">Sev {int(g.severity)}</span>
  </div>
  <div style="color:#94a3b8;font-size:0.8rem;margin-top:4px">
    {int(g.reports)} reports &nbsp;·&nbsp; {g.department.replace('_',' ').title()}
  </div>
</div>
""", unsafe_allow_html=True)
