import pandas as pd
import streamlit as st
import altair as alt
from lib import data

# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="SolarShield-AI",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# 2. DESIGN SYSTEM
# ============================================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap');

:root {
    --bg: #050B14;
    --sidebar: #0A1120;
    --card-bg-1: #1E293B;
    --card-bg-2: #334155;
    --border: #475569;
    --heading: #FFFFFF;
    --body: #F1F5F9;
    --subheading: #CBD5E1;
    --muted: #94A3B8;
    --cyan: #00E5FF;
    --amber: #FFB703;
    --success: #10B981;
    --font-main: 'Inter', sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
}

/* GLOBAL */
html, body, .stApp { font-family: var(--font-main) !important; }
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background: radial-gradient(circle at 50% 0%, #0A1526 0%, var(--bg) 100%) !important;
    color: var(--body) !important;
}
[data-testid="stHeader"] { background: transparent !important; }
.main .block-container { max-width: 1500px; padding-top: 2rem; padding-bottom: 120px; }

h1, h2, h3, h4, h5, h6 { color: var(--heading) !important; font-weight: 700 !important; }
.stMarkdown p, .stMarkdown li { color: var(--body) !important; font-size: 1.05rem; }
.stMarkdown strong { color: var(--cyan) !important; }

/* SIDEBAR */
[data-testid="stSidebar"] { background: var(--sidebar) !important; border-right: 1px solid var(--border) !important; }
[data-testid="stSidebar"] *, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] a, [data-testid="stSidebar"] label { color: #F1F5F9 !important; }

/* HEADER CARD */
.solar-header {
    background: linear-gradient(135deg, var(--card-bg-2) 0%, var(--card-bg-1) 100%);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 24px 32px;
    margin-bottom: 24px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.1);
    box-sizing: border-box;
    width: 100%;
}
.header-top { display: flex; justify-content: space-between; align-items: center; }
.brand-area { display: flex; align-items: center; gap: 16px; }
.brand-icon {
    width: 52px; height: 52px; border-radius: 16px;
    background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.1);
    display: flex; align-items: center; justify-content: center; font-size: 28px;
}
.brand-name { color: var(--heading); font-size: 1.5rem; font-weight: 800; }
.brand-subtitle { color: var(--cyan); font-family: var(--font-mono); font-size: 0.7rem; letter-spacing: 1.5px; }
.system-status {
    display: flex; align-items: center; gap: 8px;
    background: rgba(0, 0, 0, 0.3); border: 1px solid rgba(0, 229, 255, 0.3);
    color: var(--cyan); border-radius: 30px; padding: 8px 16px;
    font-size: 0.75rem; font-weight: 700; font-family: var(--font-mono);
}
.status-dot { width: 8px; height: 8px; background: var(--success); border-radius: 50%; }
.header-divider { height: 1px; background: rgba(255,255,255,0.1); margin: 20px 0; }
.header-bottom { display: flex; justify-content: space-between; align-items: center; }
.header-label { color: var(--subheading); font-size: 0.7rem; font-family: var(--font-mono); }
.header-cycle { color: var(--heading); font-size: 1.6rem; font-weight: 800; }
.header-cycle-status { color: var(--amber); font-size: 0.8rem; font-weight: 600; }
.header-platform { text-align: right; color: var(--body); font-size: 0.95rem; font-weight: 600; }
.header-platform-sub { color: var(--cyan); font-size: 0.7rem; font-family: var(--font-mono); }

/* METRICS GRID */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 24px;
    margin-bottom: 24px;
    width: 100%;
}
.metric-card {
    background: linear-gradient(135deg, var(--card-bg-2) 0%, var(--card-bg-1) 100%);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 8px 24px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1);
    min-height: 130px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    box-sizing: border-box;
}
.metric-label {
    color: var(--cyan) !important;
    font-family: var(--font-mono);
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 8px;
}
.metric-value {
    color: #FFFFFF !important;
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: -1px;
    line-height: 1.1;
    white-space: nowrap;
}
.metric-delta {
    color: var(--amber) !important;
    font-size: 0.85rem;
    font-weight: 600;
    margin-top: 6px;
}

/* CUSTOM ALERT BOX */
.custom-alert {
    background: rgba(255, 183, 3, 0.1);
    border: 1px solid rgba(255, 183, 3, 0.4);
    border-radius: 12px;
    padding: 1.2rem;
    margin-bottom: 24px;
    width: 100%;
    box-sizing: border-box;
}
.custom-alert p { color: #FFFFFF !important; font-size: 0.95rem; margin: 0; }
.custom-alert strong { color: var(--amber) !important; font-weight: 800 !important; }

/* MISSION OVERVIEW CARD */
.mission-overview {
    background: var(--card-bg-1);
    border: 1px solid var(--border);
    border-left: 4px solid var(--cyan);
    border-radius: 12px;
    padding: 1.5rem 2rem;
    margin-bottom: 24px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}
.mission-overview p {
    color: var(--subheading) !important;
    font-size: 1.05rem;
    line-height: 1.7;
    margin-bottom: 12px;
}
.mission-overview p:last-child { margin-bottom: 0; }
.mission-pipeline {
    color: var(--cyan);
    font-family: var(--font-mono);
    font-weight: 700;
    font-size: 1.1rem;
    text-align: center;
    margin: 20px 0;
    padding: 12px;
    background: rgba(0, 229, 255, 0.05);
    border-radius: 8px;
    border: 1px solid rgba(0, 229, 255, 0.2);
}

/* CHART EXPLAINER & LEGEND */
.legend-row {
    display: flex;
    gap: 20px;
    margin-top: -10px;
    margin-bottom: 20px;
    font-size: 0.85rem;
    color: var(--subheading);
    flex-wrap: wrap;
}
.legend-item {
    display: flex;
    align-items: center;
    gap: 8px;
}
.sw {
    width: 16px;
    height: 3px;
    display: inline-block;
    border-radius: 2px;
    border-style: solid;
    border-width: 2px;
}
.sw-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    border: 2px solid #FFFFFF;
    display: inline-block;
}
.sw-dot.fill {
    background-color: #FFFFFF;
}
.chart-explainer {
    background: rgba(30, 41, 59, 0.5);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.2rem;
    margin-top: 15px;
}
.chart-explainer p {
    color: var(--body) !important;
    font-size: 0.95rem;
    margin-bottom: 10px;
}
.chart-explainer b {
    color: var(--cyan) !important;
}
.chart-explainer ul {
    margin-top: 5px;
    margin-bottom: 0;
    padding-left: 20px;
}
.chart-explainer li {
    color: var(--subheading) !important;
    font-size: 0.9rem;
    margin-bottom: 6px;
}

/* NATIVE COLUMN STYLING */
[data-testid="column"] > div {
    background: var(--card-bg-1) !important;
    border: 1px solid var(--border) !important;
    border-radius: 16px !important;
    padding: 1.5rem !important;
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    height: 100%;
}
.card-title {
    color: var(--heading);
    font-size: 1.25rem;
    font-weight: 700;
    margin-bottom: 4px;
}

/* Streamlit Chart Overrides */
[data-testid="stVegaLiteChart"] { background-color: transparent !important; }
[data-testid="stVegaLiteChart"] canvas { background-color: transparent !important; }

/* FOOTER */
.custom-footer {
    position: fixed; bottom: 0; left: 0; width: 100%;
    background: rgba(10, 17, 32, 0.95); border-top: 1px solid var(--border);
    padding: 12px 2rem; text-align: center; z-index: 9999;
}
.footer-link { color: var(--cyan) !important; text-decoration: none !important; }
.footer-copyright { color: var(--muted) !important; font-size: 0.75rem; }

/* RESPONSIVE */
@media (max-width: 1000px) {
    .metric-grid { grid-template-columns: 1fr; }
    .header-bottom { flex-direction: column; align-items: flex-start; gap: 10px; }
    .header-platform { text-align: left; }
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# 3. DATA FETCHING
# ============================================================

try:
    m = data.monthly()
    if m is None or m.empty:
        st.error("Monthly dataset empty.")
        st.stop()

    if "month_start" in m.columns and not pd.api.types.is_datetime64_any_dtype(m["month_start"]):
        m["month_start"] = pd.to_datetime(m["month_start"], errors="coerce")

    if "is_provisional" not in m.columns:
        m["is_provisional"] = False

    valid_months = m.dropna(subset=["ssn"])
    if valid_months.empty:
        st.error("No valid sunspot observations.")
        st.stop()

    last = valid_months.iloc[-1]
    cycles = data.cycles()
    if cycles is None or cycles.empty:
        st.error("Solar cycle dataset empty.")
        st.stop()

    cyc = cycles.iloc[-1]
    status = data.model_status()
    accept, freeze = status if isinstance(status, (tuple, list)) and len(status) == 2 else ("unknown", "unknown")

except Exception as e:
    st.error(f"Data Error: {e}")
    st.stop()


# ============================================================
# 4. HEADER
# ============================================================

cycle_number = int(cyc.get("cycle_number", 0))
cycle_status = str(cyc.get("status", "unknown")).upper()

header_html = f"""
<div class="solar-header">
    <div class="header-top">
        <div class="brand-area">
            <div class="brand-icon">☀️</div>
            <div>
                <div class="brand-name">SolarShield-AI</div>
                <div class="brand-subtitle">SPACE WEATHER INTELLIGENCE</div>
            </div>
        </div>
        <div class="system-status">
            <span class="status-dot"></span> RESEARCH DASHBOARD
        </div>
    </div>
    <div class="header-divider"></div>
    <div class="header-bottom">
        <div>
            <div class="header-label">CURRENT SOLAR CYCLE</div>
            <div class="header-cycle">Cycle {cycle_number}</div>
            <div class="header-cycle-status">● {cycle_status}</div>
        </div>
        <div class="header-platform">
            Research Dashboard
            <div class="header-platform-sub">SOLAR ACTIVITY MONITORING</div>
        </div>
    </div>
</div>
"""
st.html(header_html)


# ============================================================
# 5. KEY SOLAR METRICS & ALERT
# ============================================================

month_str = pd.to_datetime(last["month_start"]).strftime("%b %Y")
if bool(last["is_provisional"]):
    month_str += " (Prov)"

metrics_html = f"""
<div class="metric-grid">
    <div class="metric-card">
        <div class="metric-label">Latest Sunspot Number</div>
        <div class="metric-value">{last['ssn']:.1f}</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">Observation Month</div>
        <div class="metric-value">{month_str}</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">Active Solar Cycle</div>
        <div class="metric-value">Cycle {cycle_number}</div>
        <div class="metric-delta">{cycle_status.capitalize()}</div>
    </div>
</div>

<div class="custom-alert">
    <p>
        <strong>⚠️ MODEL STATUS:</strong> Scientific acceptance is <strong>{accept}</strong> | Model Freeze: <strong>{freeze}</strong><br><br>
        This app shows historical research evidence and a <strong>presentation-only</strong> operations demo. It does not issue real storm probabilities or operational risk alerts.
    </p>
</div>
"""
st.html(metrics_html)


# ============================================================
# 5.5 MISSION OVERVIEW
# ============================================================

st.html("""
<div class="mission-overview">
    <p>
        <strong>SolarShield-AI</strong> is a research-driven initiative focused on understanding solar activity, investigating its potential space-weather implications, and developing a pathway toward Earth-impact risk assessment and early warning.
    </p>
    <p>
        The project aims to connect long-term solar observations with data-driven forecasting, uncertainty-aware analysis, and interpretable risk communication.
    </p>
    
    <div class="mission-pipeline">
        Solar Activity &rarr; Space Weather &rarr; Earth Response &rarr; Risk Assessment &rarr; Early Warning &rarr; Mitigation
    </div>
    
    <p style="font-size: 0.95rem; color: var(--muted);">
        The project is being developed incrementally. Its current research primarily focuses on solar-cycle characterization and forecasting. A fully validated, operational solar-to-Earth impact prediction and alerting system has not yet been established.
    </p>
</div>
""")


# ============================================================
# 6. DASHBOARD CONTENT (Chart & Navigation)
# ============================================================

CYAN, AMBER = "#00E5FF", "#FFB703"

def pct_phrase(now, then):
    d = (now - then) / then * 100
    return f"{abs(d):.0f}% {'above' if d >= 0 else 'below'}"

col_chart, col_nav = st.columns([2, 1], gap="large")

with col_chart:
    st.markdown('<div class="card-title">📈 Solar Activity Trend</div>', unsafe_allow_html=True)
    st.markdown('<div class="technical-label" style="margin-bottom: 15px;">Monthly sunspot number · last 5 years (SILSO)</div>', unsafe_allow_html=True)

    series = m.dropna(subset=["ssn"]).sort_values("month_start").copy()
    series["avg12"] = series["ssn"].rolling(12, min_periods=12).mean()
    recent = series[series["month_start"] >= series["month_start"].max() - pd.DateOffset(years=5)].copy()

    if recent.empty:
        st.warning("No recent solar activity data available.")
    else:
        recent["month_label"] = recent["month_start"].dt.strftime("%b %Y")
        recent["kind"] = recent["is_provisional"].map({True: "Provisional", False: "Final"})
        y_scale = alt.Scale(domain=[0, float(recent["ssn"].max()) * 1.15])
        base = alt.Chart(recent).encode(x=alt.X("month_start:T", title=None))
        latest, peak = recent.iloc[-1], recent.loc[recent["ssn"].idxmax()]
        prov = recent[recent["is_provisional"]]

        layers = [
            base.mark_area(opacity=0.12, color=CYAN).encode(y=alt.Y("ssn:Q", scale=y_scale)),
            base.mark_line(strokeWidth=1.8, color=CYAN).encode(y=alt.Y("ssn:Q", title="Sunspot number", scale=y_scale)),
            base.mark_line(strokeWidth=3.5, color=AMBER).encode(y=alt.Y("avg12:Q", scale=y_scale)),
            base.mark_circle(opacity=0, size=250).encode(
                y=alt.Y("ssn:Q", scale=y_scale),
                tooltip=[alt.Tooltip("month_label:N", title="Month"),
                         alt.Tooltip("ssn:Q", title="Sunspot number", format=".1f"),
                         alt.Tooltip("avg12:Q", title="12-month average", format=".1f"),
                         alt.Tooltip("kind:N", title="Status")]),
            alt.Chart(recent.tail(1)).mark_point(shape="circle", filled=True, size=160, color="#FFFFFF")
                .encode(x="month_start:T", y=alt.Y("ssn:Q", scale=y_scale)),
            alt.Chart(pd.DataFrame([{"month_start": peak["month_start"], "ssn": peak["ssn"], "label": f"Peak {peak['ssn']:.0f}"}]))
                .mark_text(dy=-14, color=AMBER, fontWeight="bold", fontSize=12)
                .encode(x="month_start:T", y=alt.Y("ssn:Q", scale=y_scale), text="label:N"),
        ]
        if not prov.empty:
            layers.append(alt.Chart(prov).mark_point(shape="circle", filled=False, size=90, strokeWidth=2, color="#FFFFFF")
                          .encode(x="month_start:T", y=alt.Y("ssn:Q", scale=y_scale)))

        chart = (alt.layer(*layers).properties(height=300, background="transparent")
                 .configure_axis(labelColor="#CBD5E1", titleColor="#CBD5E1", gridColor="#334155",
                                 domainColor="#475569", tickColor="#475569")
                 .configure_view(strokeWidth=0))
        st.altair_chart(chart, use_container_width=True)

        # Custom Legend
        st.html(f"""
        <div class="legend-row">
          <span class="legend-item"><span class="sw" style="border-color:{CYAN}"></span>Monthly value</span>
          <span class="legend-item"><span class="sw" style="border-color:{AMBER}"></span>12-month average</span>
          <span class="legend-item"><span class="sw-dot"></span>Provisional month</span>
          <span class="legend-item"><span class="sw-dot fill"></span>Latest month</span>
        </div>""")

        # Dynamic Explanation Text
        yr = recent.iloc[-13] if len(recent) >= 13 else recent.iloc[0]
        prov_note = ", provisional" if bool(latest["is_provisional"]) else ""
        st.html(f"""
        <div class="chart-explainer">
          <p><b>Right now:</b> the latest value is <b>{latest['ssn']:.1f}</b> ({latest['month_label']}{prov_note}).
          That is {pct_phrase(latest['ssn'], yr['ssn'])} the value a year earlier ({yr['ssn']:.1f}, {yr['month_label']})
          and {pct_phrase(latest['ssn'], peak['ssn'])} the highest month in this window ({peak['ssn']:.1f}, {peak['month_label']}).
          The 12-month average is {latest['avg12']:.1f}.</p>
          <p><b>How to read this chart</b></p>
          <ul>
            <li>Each point is one month's average sunspot number. More sunspots means a more active Sun.</li>
            <li>The cyan line is noisy month to month. The thick amber line averages 12 months to show the underlying direction.</li>
            <li>Hollow circles are provisional months that may be revised.</li>
            <li>Activity rises and falls in cycles of about 11 years. This chart describes past data and is not a forecast.</li>
          </ul>
        </div>""")

with col_nav:
    st.markdown('<div class="card-title">🧭 Mission Navigation</div>', unsafe_allow_html=True)
    st.markdown('<div class="technical-label" style="margin-bottom: 15px;">EXPLORE THE SOLARSHIELD SYSTEM</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <ul style="list-style-type: none; padding-left: 0; line-height: 2.2; font-family: var(--font-main);">
        <li><strong style="color: #00E5FF;">⚙️ Operations</strong> <span style="color: #CBD5E1;">— Demo risk board</span></li>
        <li><strong style="color: #00E5FF;">📈 Forecasts</strong> <span style="color: #CBD5E1;">— Predictive models</span></li>
        <li><strong style="color: #00E5FF;">🔄 Cycles</strong> <span style="color: #CBD5E1;">— Historical data</span></li>
        <li><strong style="color: #00E5FF;">📊 Trends</strong> <span style="color: #CBD5E1;">— Long-term analysis</span></li>
        <li><strong style="color: #00E5FF;">🗄️ Data</strong> <span style="color: #CBD5E1;">— Raw datasets</span></li>
        <li><strong style="color: #00E5FF;">🤖 Model Status</strong> <span style="color: #CBD5E1;">— Acceptance details</span></li>
    </ul>
    """, unsafe_allow_html=True)


# ============================================================
# 7. FOOTER
# ============================================================

st.html("""
<div class="custom-footer">
    <div>
        <a href="https://github.com/shahidurshakib/SolarShield-AI" target="_blank" rel="noopener noreferrer" class="footer-link">
            GitHub · SolarShield-AI
        </a>
    </div>
    <div class="footer-copyright">
        Copyright © 2026 Team MU Solar Pulse. All Rights Reserved.
    </div>
</div>
""")
