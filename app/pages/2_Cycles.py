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

/* CUSTOM ALERT BOX (Replaces st.warning) */
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

/* FORMS & INPUTS */
.stSelectbox div[data-baseweb="select"] {
    background: var(--card-bg-1) !important;
    border: 1px solid var(--border) !important;
    color: var(--heading) !important;
    border-radius: 10px !important;
}

/* EXPANDER */
[data-testid="stExpander"] {
    background: var(--card-bg-1) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
}
[data-testid="stExpander"] * { color: var(--heading) !important; }

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
    "Cycle",
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

row = cy[cy["cycle_number"] == n].iloc[0]
st.write(
    f"Status: **{row['status']}** · peak monthly value **{row['raw_monthly_peak_ssn']}** "
    f"in {row['raw_monthly_peak_month']} · official smoothed maximum **{row['official_smoothed_max_sn']}**"
)

if row["status"] != "completed":
    st.caption("This cycle is ongoing; recent months are provisional and may be revised.")

with st.expander("Exploratory curves for Cycles 26 and 27"):
    try:
        c = data.curves()
    except FileNotFoundError as e:
        st.warning(str(e))
        st.stop()
    
    # Custom warning box
    st.html("""
    <div class="custom-alert">
        <p><strong>⚠️ NOTE:</strong> Exploratory analog curves with an empirical 10–90% band. Not validated, and not a forecast.</p>
    </div>
    """)
    
    k = st.radio("Cycle", sorted(c["future_cycle"].unique().tolist()), horizontal=True)
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