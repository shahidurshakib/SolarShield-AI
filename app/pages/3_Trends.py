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

st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

peaks = done["raw_monthly_peak_ssn"].dropna()
if len(peaks) >= 8:
    pk = mann_kendall(peaks)
    st.subheader("Across completed cycles")
    st.write(
        f"Peak strength: **{pk['direction']}** "
        f"(p = {pk['p']:.3f}, n = {pk['n']}, Sen slope {pk['sen_slope']:.2f} per cycle)."
    )

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