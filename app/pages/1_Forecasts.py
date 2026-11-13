import altair as alt
import streamlit as st
from lib import data

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(page_title="Forecasts · SolarShield-AI", layout="centered", page_icon="☀")

# ============================================================
# DESIGN SYSTEM (Deep Space / Steel Blue)
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
    --danger: #EF4444;
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
.main .block-container { max-width: 1200px; padding-top: 2rem; padding-bottom: 120px; }

h1, h2, h3, h4, h5, h6 { color: var(--heading) !important; font-weight: 700 !important; }
.stMarkdown p, .stMarkdown li { color: var(--body) !important; font-size: 1.05rem; }
.stMarkdown strong { color: var(--cyan) !important; }

/* SIDEBAR */
[data-testid="stSidebar"] { background: var(--sidebar) !important; border-right: 1px solid var(--border) !important; }
[data-testid="stSidebar"] * { color: #F1F5F9 !important; }

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

/* CUSTOM METRIC GRID (Replaces native st.metric) */
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
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
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
}

/* SELECTBOX FIX */
[data-testid="stWidgetLabel"] p {
    color: var(--cyan) !important;
    font-family: var(--font-mono) !important;
    font-weight: 600 !important;
}
div[data-baseweb="select"] > div {
    background-color: var(--card-bg-1) !important;
    border: 1px solid var(--border) !important;
}
div[data-baseweb="select"] div[aria-live="polite"] {
    color: #FFFFFF !important;
    font-weight: 600 !important;
}

/* EXPANDER & DATAFRAME FIX */
[data-testid="stExpander"] {
    background-color: var(--card-bg-1) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    overflow: hidden;
}
[data-testid="stExpander"] summary {
    background-color: var(--card-bg-2) !important;
    color: var(--heading) !important;
    border-bottom: 1px solid var(--border) !important;
}
[data-testid="stExpander"] summary * {
    color: var(--heading) !important;
    font-weight: 600 !important;
}
/* Force the dataframe background to be dark */
[data-testid="stDataFrame"] > div {
    background-color: var(--card-bg-1) !important;
}
[data-testid="stDataFrame"] iframe {
    background-color: var(--card-bg-1) !important;
}

/* FOOTER */
.custom-footer {
    position: fixed; bottom: 0; left: 0; width: 100%;
    background: rgba(10, 17, 32, 0.95); border-top: 1px solid var(--border);
    padding: 12px 2rem; text-align: center; z-index: 9999;
}
.footer-link { color: var(--cyan) !important; text-decoration: none !important; }
.footer-copyright { color: var(--muted) !important; font-size: 0.75rem; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# PAGE CONTENT
# ============================================================

st.title("Forecasts")

st.html("""
<div class="custom-alert">
    <p>
        <strong>⚠️ NOTE:</strong> Historical backtests of reference models. 
        None is an accepted or frozen forecast model.
    </p>
</div>
""")

a, b = st.columns(2)
model = a.selectbox("Model", ["persistence", "seasonal_naive", "ETS (exploratory)"])
h = b.selectbox("Horizon (months)", [1, 3, 6, 12], index=2)

try:
    df = data.forecast_frame(model, h).dropna().sort_values("target_month")
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()

if df.empty:
    st.info("No scored forecasts for this model and horizon.")
    st.stop()

s = data.scores(df)

# REPLACED NATIVE st.metric WITH CUSTOM HTML
metrics_html = f"""
<div class="metric-grid">
    <div class="metric-card">
        <div class="metric-label">Forecasts scored</div>
        <div class="metric-value">{s['n']}</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">MAE</div>
        <div class="metric-value">{s['MAE']:.1f}</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">RMSE</div>
        <div class="metric-value">{s['RMSE']:.1f}</div>
    </div>
</div>
"""
st.html(metrics_html)

st.caption(
    f"Evaluation window: {df['target_month'].min():%Y-%m} to {df['target_month'].max():%Y-%m}. "
    "ETS was scored on a longer window (from 1976) than the baseline backtest (from 2016), "
    "so compare scores only between runs that share a window."
)

long = df.melt("target_month", var_name="series", value_name="ssn")

chart = (
    alt.Chart(long)
    .mark_line(strokeWidth=3)
    .encode(
        x=alt.X("target_month:T", title=None, axis=alt.Axis(labelColor="#CBD5E1", titleColor="#CBD5E1", gridColor="#334155")),
        y=alt.Y("ssn:Q", title="Sunspot number", axis=alt.Axis(labelColor="#CBD5E1", titleColor="#CBD5E1", gridColor="#334155")),
        color=alt.Color(
            "series:N", 
            scale=alt.Scale(range=["#00E5FF", "#FFB703", "#10B981"]), 
            legend=alt.Legend(orient="bottom", title=None, labelColor="#CBD5E1")
        ),
    )
    .properties(height=300, background="transparent")
)
st.altair_chart(chart, use_container_width=True)

with st.expander("Data table"):
    st.dataframe(df, use_container_width=True, hide_index=True)

st.subheader("Cycle characteristics (analog method, held-out cycles)")
try:
    st.dataframe(data.cycle_metrics(), use_container_width=True, hide_index=True)
except FileNotFoundError as e:
    st.warning(str(e))
st.caption("Interval coverage here is descriptive, not a validated accuracy claim.")

# ============================================================
# FOOTER
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