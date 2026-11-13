import altair as alt
import streamlit as st
from lib import data

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(page_title="Cycles · SolarShield-AI", layout="centered", page_icon="☀")

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

/* EXPLANATION CARDS */
.explainer-card {
    background: rgba(30, 41, 59, 0.5);
    border: 1px solid var(--border);
    border-left: 4px solid var(--cyan);
    border-radius: 8px;
    padding: 1.5rem;
    margin-top: 20px;
    margin-bottom: 30px;
}
.explainer-card h3 {
    color: var(--cyan) !important;
    font-size: 1.1rem;
    margin-bottom: 12px;
    font-family: var(--font-mono);
}
.explainer-card p, .explainer-card li {
    color: var(--subheading) !important;
    font-size: 0.95rem;
    line-height: 1.6;
}
.explainer-card b { color: var(--heading) !important; }

/* FORMS & INPUTS */
.stSelectbox div[data-baseweb="select"] {
    background: var(--card-bg-1) !important;
    border: 1px solid var(--border) !important;
    color: var(--heading) !important;
    border-radius: 10px !important;
}

/* EXPANDER */
[data-testid="stExpander"] {
    background-color: var(--card-bg-1) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
}
[data-testid="stExpander"] summary {
    background-color: var(--card-bg-2) !important;
    color: var(--heading) !important;
}
[data-testid="stExpander"] summary * {
    color: var(--heading) !important;
    font-weight: 600 !important;
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

st.title("Solar cycles")

try:
    cy = data.cycles()
    m = data.monthly()
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()

n = st.selectbox(
    "Select Solar Cycle",
    cy["cycle_number"].tolist(),
    index=len(cy) - 1,
    format_func=lambda x: f"Cycle {x}",
)

d = m[m["cycle_number"] == n]

# Styled Altair chart
chart_main = (
    alt.Chart(d)
    .mark_line(strokeWidth=3, color="#00E5FF")
    .encode(
        x=alt.X("month_start:T", title=None, axis=alt.Axis(labelColor="#CBD5E1", titleColor="#CBD5E1", gridColor="#334155")),
        y=alt.Y("ssn:Q", title="Monthly sunspot number", axis=alt.Axis(labelColor="#CBD5E1", titleColor="#CBD5E1", gridColor="#334155")),
    )
    .properties(height=280, background="transparent")
)
st.altair_chart(chart_main, use_container_width=True)

# Cycle Summary Text
row = cy[cy["cycle_number"] == n].iloc[0]
st.write(
    f"Status: **{row['status']}** · peak monthly value **{row['raw_monthly_peak_ssn']}** "
    f"in {row['raw_monthly_peak_month']} · official smoothed maximum **{row['official_smoothed_max_sn']}**"
)

if row["status"] != "completed":
    st.caption("This cycle is ongoing; recent months are provisional and may be revised.")

# Explanation Card
st.html("""
<div class="explainer-card">
    <h3>Understanding the Solar Cycle Chart</h3>
    <p>Solar activity is not constant. It naturally rises and falls over an approximately 11-year period. This chart displays the monthly sunspot numbers recorded during the selected solar cycle.</p>
    <p><b>How to read this chart:</b></p>
    <ul>
        <li><b>X-axis:</b> The timeline of the cycle in months and years.</li>
        <li><b>Y-axis:</b> The monthly sunspot number, which acts as a proxy for solar activity.</li>
        <li><b>The Curve:</b> The shape of the curve shows the "rise" to a maximum peak (solar maximum) and the subsequent "decay" toward a minimum (solar minimum).</li>
    </ul>
    <p>If the cycle is marked as <b>"ongoing"</b>, the most recent data points (often drawn as hollow circles or marked as provisional) are subject to revision as new observations come in. Older, completed cycles represent finalized historical data.</p>
</div>
""")

# Exploratory Curves Section
with st.expander("Exploratory curves for Cycles 26 and 27"):
    try:
        c = data.curves()
    except FileNotFoundError as e:
        st.warning(str(e))
        st.stop()
    
    st.html("""
    <div class="custom-alert">
        <p><strong>⚠️ NOTE:</strong> Exploratory analog curves with an empirical 10–90% band. Not validated, and not a forecast.</p>
    </div>
    """)
    
    k = st.radio("Select Future Cycle", sorted(c["future_cycle"].unique().tolist()), horizontal=True)
    cc = c[c["future_cycle"] == k]
    
    base = alt.Chart(cc).encode(
        x=alt.X("normalized_phase:Q", title="Phase of cycle (0 to 1)", axis=alt.Axis(labelColor="#CBD5E1", titleColor="#CBD5E1", gridColor="#334155"))
    )
    
    # Styled Altair area and line
    chart_exploratory = base.mark_area(opacity=0.3, color="#FFB703").encode(
        y=alt.Y("interval_lower_q10:Q", axis=alt.Axis(labelColor="#CBD5E1", titleColor="#CBD5E1", gridColor="#334155")), 
        y2="interval_upper_q90:Q"
    ) + base.mark_line(strokeWidth=3, color="#00E5FF").encode(
        y=alt.Y("predicted_curve_ssn:Q", title="Sunspot number", axis=alt.Axis(labelColor="#CBD5E1", titleColor="#CBD5E1", gridColor="#334155"))
    )
    
    chart_exploratory = chart_exploratory.properties(background="transparent")
    st.altair_chart(chart_exploratory, use_container_width=True)
    
    st.html("""
    <div class="explainer-card">
        <h3>Understanding the Exploratory Curves</h3>
        <p>These curves represent <b>research explorations</b>, not official forecasts. Because historical solar cycles differ in shape and amplitude, researchers use analog methods to project what future cycles might look like.</p>
        <p><b>How to read this chart:</b></p>
        <ul>
            <li><b>Normalized Phase:</b> The X-axis compresses the expected ~11-year cycle into a scale from 0 to 1, making it easier to compare cycles of different lengths.</li>
            <li><b>Cyan Line:</b> The predicted median curve for the future cycle based on historical analogs.</li>
            <li><b>Amber Band:</b> The 10–90% confidence interval. This represents the wide range of uncertainty. It shows where the actual cycle might fall based on past variability.</li>
        </ul>
        <p style="color: var(--amber); margin-top: 10px; font-weight: 600;">Important: This is an empirical exploration. It is not a validated scientific forecast, and it does not predict specific space weather events.</p>
    </div>
    """)

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
