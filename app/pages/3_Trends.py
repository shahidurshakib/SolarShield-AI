import pandas as pd
import streamlit as st
from lib import data
from lib.stats import mann_kendall

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(page_title="Trends · SolarShield-AI", layout="centered", page_icon="☀")

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

/* CUSTOM METRIC GRID */
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
.metric-delta {
    color: var(--amber) !important;
    font-size: 0.85rem;
    font-weight: 600;
    margin-top: 6px;
}

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

/* DATAFRAME */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    background: var(--card-bg-1) !important;
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

st.title("Trend tests")
st.caption(
    "Mann-Kendall test with Sen's slope, computed by this app on the SILSO series. "
    "Within a cycle, a trend mostly reflects the natural rise and decay."
)

try:
    cy = data.cycles()
    m = data.monthly()
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()

done = cy[cy["status"] == "completed"]
rows = []
for n in done["cycle_number"]:
    series = m.loc[m["cycle_number"] == n, "ssn"]
    try:
        r = mann_kendall(series)
    except ValueError:
        continue
    rows.append(
        {
            "cycle": int(n),
            "months": r["n"],
            "direction": r["direction"],
            "p": round(r["p"], 4),
            "tau": round(r["tau"], 3),
            "Sen slope /month": round(r["sen_slope"], 3),
            "95% CI": f"{r['sen_ci95'][0]:.3f} to {r['sen_ci95'][1]:.3f}",
        }
    )

df_trends = pd.DataFrame(rows)

# --- CYCLE-BY-CYCLE TABLE & EXPLANATION ---
st.subheader("Cycle-by-Cycle Trend Results")
st.dataframe(df_trends, use_container_width=True, hide_index=True)

st.html("""
<div class="explainer-card">
    <h3>Understanding Within-Cycle Trends</h3>
    <p>
        This table applies the Mann-Kendall trend test to the monthly sunspot numbers of each individual completed solar cycle. 
    </p>
    <p>
        <b>Important Interpretation:</b> Within a single solar cycle, a trend primarily reflects the natural rise toward solar maximum and the subsequent decay toward solar minimum. It does <b>not</b> indicate a long-term change in the Sun's overall output.
    </p>
</div>
""")

# --- ACROSS-CYCLES SECTION ---
peaks = done["raw_monthly_peak_ssn"].dropna()

if len(peaks) >= 8:
    pk = mann_kendall(peaks)
    
    st.subheader("Across Completed Cycles")
    
    # Custom Metrics Display
    direction_str = f"{pk['direction'].capitalize()}"
    metrics_html = f"""
    <div class="metric-grid">
        <div class="metric-card">
            <div class="metric-label">Trend Direction</div>
            <div class="metric-value" style="color: var(--cyan) !important;">{direction_str}</div>
            <div class="metric-delta">Across {pk['n']} cycles</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Sen's Slope (per cycle)</div>
            <div class="metric-value">{pk['sen_slope']:.2f}</div>
            <div class="metric-delta">Change in peak SSN</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Statistical Significance (p-value)</div>
            <div class="metric-value">{pk['p']:.3f}</div>
            <div class="metric-delta">{'Significant' if pk['p'] < 0.05 else 'Not significant'} at α=0.05</div>
        </div>
    </div>
    """
    st.html(metrics_html)

    st.html("""
    <div class="explainer-card">
        <h3>Understanding the Statistical Methods</h3>
        <p>This section tests whether the maximum peak strength of solar cycles has significantly changed over history.</p>
        
        <p><b>Mann-Kendall Test:</b> A non-parametric statistical test used to identify monotonic trends in time-series data. It does not assume any particular distribution (like a normal distribution).</p>
        
        <p><b>Kendall's Tau (τ):</b> A measure of correlation that indicates the strength and direction of the relationship between the cycles over time. Values closer to +1 or -1 indicate a strong trend.</p>
        
        <p><b>Sen's Slope:</b> A robust estimate of the true slope of the trend. It represents the median rate of change per unit of time (in this case, per cycle).</p>
        
        <p><b>P-value:</b> The probability that the observed trend occurred by random chance. A p-value below 0.05 (5%) typically indicates strong evidence of a real trend.</p>
        
        <p><b>95% Confidence Interval (CI):</b> The range within which the true Sen's slope is likely to fall with 95% confidence.</p>
        
        <p style="color: var(--amber); margin-top: 15px; font-weight: 600;">
            Limitations: Solar cycles exhibit high natural variability. Statistical tests across a relatively small number of cycles (n ~ 24) must be interpreted carefully. Multiple-testing bias should also be considered when analyzing cycle-by-cycle p-values.
        </p>
    </div>
    """)

else:
    st.info("Not enough completed cycles to run the across-cycle trend test.")

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
