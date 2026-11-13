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

/* NATIVE COLUMN STYLING (To perfectly mimic custom HTML cards) */
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
[data-testid="stVegaLiteChart"] {
    background-color: transparent !important;
}
[data-testid="stVegaLiteChart"] canvas {
    background-color: transparent !important;
}

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
# 6. DASHBOARD CONTENT (Chart & Navigation)
# ============================================================

# Using Native Columns to guarantee charts and text stay inside their boxes
col_chart, col_nav = st.columns([2, 1], gap="large")

with col_chart:
    st.markdown('<div class="card-title">📈 Solar Activity Trend</div>', unsafe_allow_html=True)
    st.markdown('<div class="technical-label" style="margin-bottom: 15px;">LAST 5 YEARS OF SILSO SUNSPOT DATA</div>', unsafe_allow_html=True)

    cutoff = m["month_start"].max() - pd.DateOffset(years=5)
    recent = m[m["month_start"] >= cutoff].dropna(subset=["ssn"])

    if not recent.empty:
        # Create the Altair chart
        chart = alt.Chart(recent).mark_line(strokeWidth=3, color="#00E5FF").encode(
            x=alt.X("month_start:T", title=None, axis=alt.Axis(labelColor="#CBD5E1", titleColor="#CBD5E1", gridColor="#334155")),
            y=alt.Y("ssn:Q", title="Sunspot Number", axis=alt.Axis(labelColor="#CBD5E1", titleColor="#CBD5E1", gridColor="#334155")),
        ).properties(height=280, background="transparent").interactive()
        
        st.altair_chart(chart, use_container_width=True)
    else:
        st.warning("No recent solar activity data available.")

    provisional_count = int(m["is_provisional"].sum())
    st.markdown(f'<div class="technical-label" style="margin-top: 15px;">Provisional months in dataset: <span style="color: white;">{provisional_count}</span></div>', unsafe_allow_html=True)

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