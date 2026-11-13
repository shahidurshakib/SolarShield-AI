import streamlit as st

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(page_title="About · SolarShield-AI", layout="centered", page_icon="☀")

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
.main .block-container { max-width: 1100px; padding-top: 3rem; padding-bottom: 120px; }

h1, h2, h3, h4, h5, h6 { color: var(--heading) !important; font-weight: 700 !important; }
.stMarkdown p, .stMarkdown li { color: var(--body) !important; font-size: 1.05rem; line-height: 1.7; }
.stMarkdown strong { color: var(--cyan) !important; }
.stMarkdown a { color: var(--cyan) !important; text-decoration: none; }
.stMarkdown a:hover { color: var(--amber) !important; }

/* SIDEBAR */
[data-testid="stSidebar"] { background: var(--sidebar) !important; border-right: 1px solid var(--border) !important; }
[data-testid="stSidebar"] * { color: #F1F5F9 !important; }

/* HERO SECTION */
.hero-section {
    text-align: center;
    margin-bottom: 3rem;
    padding: 2rem 1rem;
}
.hero-title {
    color: var(--heading);
    font-size: 3rem;
    font-weight: 800;
    letter-spacing: -1px;
    margin-bottom: 0.5rem;
}
.hero-subtitle {
    color: var(--cyan);
    font-size: 1.1rem;
    font-family: var(--font-mono);
    letter-spacing: 1px;
}
.hero-description {
    color: var(--subheading);
    font-size: 1.15rem;
    max-width: 800px;
    margin: 1.5rem auto 0 auto;
}

/* CARDS */
.about-card {
    background: linear-gradient(135deg, var(--card-bg-2) 0%, var(--card-bg-1) 100%);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 2rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.about-card:hover {
    transform: translateY(-2px);
    border-color: var(--cyan);
}
.card-header {
    color: var(--cyan);
    font-size: 1.25rem;
    font-weight: 700;
    font-family: var(--font-mono);
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 10px;
}
.card-text {
    color: var(--body);
    font-size: 1rem;
    line-height: 1.6;
}
.scope-list {
    list-style: none;
    padding: 0;
    margin: 0;
}
.scope-list li {
    margin-bottom: 1rem;
    color: var(--subheading);
    display: flex;
    align-items: flex-start;
    gap: 10px;
}
.scope-list li::before {
    content: "▹";
    color: var(--cyan);
    font-weight: bold;
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

# Hero Section
st.html("""
<div class="hero-section">
    <div class="hero-title">About SolarShield-AI</div>
    <div class="hero-subtitle">NASA SPACE APPS CHALLENGE 2026</div>
    <div class="hero-description">
        An AI-driven research project mapping the journey from solar activity to space weather risk, 
        developed by Team MU Solar Pulse at Metropolitan University, Sylhet, Bangladesh.
    </div>
</div>
""")

# The Vision
st.html("""
<div class="about-card">
    <div class="card-header">🌌 The Project Vision</div>
    <div class="card-text">
        <p>
            <strong>SolarShield-AI</strong> was developed for the NASA challenge <em>Be An Earth System Trend Detective!</em>
            We map the risk pathway from solar activity to Earth's response.
        </p>
        <p style="color: var(--cyan); font-family: var(--font-mono); font-size: 0.95rem; margin-top: 15px; background: rgba(0,229,255,0.05); padding: 10px; border-radius: 8px; border-left: 3px solid var(--cyan);">
            Solar activity &rarr; space weather &rarr; Earth response &rarr; risk assessment &rarr; early warning &rarr; mitigation
        </p>
        <p style="margin-top: 15px;">
            While long-term aims include support for satellite operations, GNSS, and power infrastructure, 
            the <strong>current scope</strong> is focused on historical analysis, forecasting experiments, and a 
            <strong>presentation-only</strong> operations demo.
        </p>
    </div>
</div>
""")

# Application Scope
st.html("""
<div class="about-card">
    <div class="card-header">💻 Application Scope</div>
    <ul class="scope-list">
        <li>
            <div>
                <strong style="color: var(--heading);">Operations Board:</strong> 
                A demo risk board covering LEO, GNSS, grid, and aviation, complete with interactive alerts, playbooks, and an acknowledge flow.
            </div>
        </li>
        <li>
            <div>
                <strong style="color: var(--heading);">Research Explorer:</strong> 
                Forecasts, Cycle comparisons, and Trend analysis built on historical SILSO data and experiment artifacts.
            </div>
        </li>
        <li>
            <div>
                <strong style="color: var(--heading);">Data & Registry:</strong> 
                Direct downloads of datasets alongside a transparent model-freeze status registry.
            </div>
        </li>
    </ul>
    <div style="margin-top: 20px; padding: 15px; background: rgba(255,183,3,0.1); border-radius: 8px; border: 1px solid rgba(255,183,3,0.3);">
        <p style="margin: 0; font-size: 0.9rem; color: #FFFFFF;">
            <strong>Note:</strong> Operations views are illustrative for the challenge presentation. They are not validated impact forecasts and not an operational early-warning system.
        </p>
    </div>
</div>
""")

# Data & Integrity
st.html("""
<div class="about-card">
    <div class="card-header">🛡️ Data Integrity & Sources</div>
    <div class="card-text">
        <p>
            We prioritize scientific honesty. Model acceptance and freeze status are reported directly from our project registry.
            Demo risk levels are synthetic scenarios built strictly for UX demonstration.
        </p>
        <p style="margin-bottom: 5px;"><strong>Primary historical data:</strong> WDC-SILSO International Sunspot Number (monthly total), Royal Observatory of Belgium.</p>
        <p><strong>Source Code:</strong> <a href="https://github.com/shahidurshakib/SolarShield-AI" target="_blank">GitHub Repository</a></p>
        <p style="font-size: 0.9rem; color: var(--muted); margin-top: 15px;">
            When reusing charts or data, please cite SILSO and credit Team MU Solar Pulse, SolarShield-AI (2026).
        </p>
    </div>
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