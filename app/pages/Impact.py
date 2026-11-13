import streamlit as st

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(page_title="Impact · SolarShield-AI", layout="wide", page_icon="🌍")

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
.main .block-container { max-width: 1400px; padding-top: 3rem; padding-bottom: 120px; }

h1, h2, h3, h4, h5, h6 { color: var(--heading) !important; font-weight: 700 !important; }
.stMarkdown p, .stMarkdown li { color: var(--body) !important; font-size: 1.05rem; line-height: 1.7; }
.stMarkdown strong { color: var(--cyan) !important; }

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
    font-size: 1.2rem;
    font-family: var(--font-mono);
    letter-spacing: 1px;
    font-weight: 600;
    margin-bottom: 1rem;
}
.hero-quote {
    color: var(--amber);
    font-size: 1.1rem;
    font-style: italic;
    font-weight: 600;
}

/* SECTION HEADERS */
.section-header {
    color: var(--heading);
    font-size: 1.8rem;
    font-weight: 800;
    margin-top: 40px;
    margin-bottom: 20px;
    border-bottom: 2px solid var(--border);
    padding-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.section-header::before {
    content: "";
    display: inline-block;
    width: 6px;
    height: 24px;
    background: var(--cyan);
    border-radius: 3px;
}

/* CARDS */
.impact-card {
    background: linear-gradient(135deg, var(--card-bg-2) 0%, var(--card-bg-1) 100%);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.8rem;
    margin-bottom: 24px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.impact-card:hover {
    transform: translateY(-3px);
    border-color: var(--cyan);
}
.card-title {
    color: var(--cyan);
    font-size: 1.2rem;
    font-weight: 700;
    font-family: var(--font-mono);
    margin-bottom: 12px;
}
.card-text {
    color: var(--body);
    font-size: 1rem;
    line-height: 1.6;
}

/* TIMELINE (Staged Development) */
.timeline {
    border-left: 2px solid var(--border);
    margin-left: 10px;
    padding-left: 24px;
}
.timeline-item {
    position: relative;
    margin-bottom: 24px;
}
.timeline-item::before {
    content: '';
    position: absolute;
    left: -30px;
    top: 4px;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: var(--bg);
    border: 3px solid var(--cyan);
}
.timeline-title {
    color: var(--heading);
    font-weight: 700;
    font-size: 1.05rem;
    margin-bottom: 6px;
}
.timeline-desc {
    color: var(--subheading);
    font-size: 0.95rem;
    line-height: 1.5;
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
    <div class="hero-title">Project Impact</div>
    <div class="hero-subtitle">SolarShield-AI</div>
    <div class="hero-quote">"Predict the Sun. Understand the Risk. Prepare Earth."</div>
</div>
""")

st.markdown("""
<p style="font-size: 1.15rem; text-align: center; max-width: 900px; margin: 0 auto 3rem auto; color: var(--subheading);">
    SolarShield-AI bridges the gap between solar activity analysis and Earth-level preparedness by developing an explainable, AI-driven space weather risk assessment and early-warning framework.
</p>
""", unsafe_allow_html=True)

# Overview
st.html("""
<div class="section-header">Overview</div>
<div class="impact-card">
    <div class="card-text">
        <p>Solar activity continuously changes, producing phenomena such as solar flares and coronal mass ejections (CMEs) that can influence Earth's space environment and technological infrastructure. These disturbances can pose risks to satellites, navigation systems, aviation, communication networks, and electrical power infrastructure.</p>
        <p>However, understanding solar activity alone is not sufficient. Decision-makers also need to understand what these changes could mean for Earth. SolarShield-AI addresses this broader challenge through a research-driven framework that connects:</p>
        <p style="color: var(--cyan); font-family: var(--font-mono); font-weight: 600; text-align: center; margin: 20px 0; font-size: 1.1rem;">
            Solar Activity &rarr; Space Weather &rarr; Earth Response &rarr; Risk Assessment &rarr; Early Warning &rarr; Mitigation
        </p>
    </div>
</div>
""")

# The Core Impact Dimensions
st.html("""
<div class="section-header">The Core Impact Dimensions</div>

<div class="impact-card">
    <div class="card-title">🔬 Scientific Impact</div>
    <div class="card-text">
        <p>Contributing to solar-cycle research and data-driven understanding of long-term solar activity through historical analysis of International Sunspot Number data, investigation of patterns across Solar Cycles 1–25, and exploration of explainable AI methods for understanding model behaviour.</p>
    </div>
</div>

<div class="impact-card">
    <div class="card-title">💻 Technological Impact</div>
    <div class="card-text">
        <p>Proposing an integrated analytical framework that combines historical solar observations, statistical analysis, machine learning, and explainability to make complex space weather information easier to interpret and use.</p>
        <p style="color: var(--amber); font-size: 0.9rem; margin-top: 10px;"><strong>Note:</strong> The current research does not establish an operational, validated Earth-impact forecasting service.</p>
    </div>
</div>

<div class="impact-card">
    <div class="card-title">🌍 Societal Impact</div>
    <div class="card-text">
        <p>Seeking to improve awareness and preparedness by making space weather information more accessible and understandable for the public, educational institutions, and relevant stakeholders.</p>
    </div>
</div>
""")

# Infrastructure & Economic Impact
st.html("""
<div class="section-header">Infrastructure & Economic Impact</div>
<div class="impact-card">
    <div class="card-text">
        <p>Space weather disturbances can create operational challenges for critical technological infrastructure. SolarShield-AI identifies several sectors where improved space weather awareness could have practical value:</p>
        <ul style="color: var(--subheading); line-height: 1.8;">
            <li><strong>Satellites:</strong> Radiation exposure, charging, and orbital drag.</li>
            <li><strong>GPS/GNSS:</strong> Navigation and positioning inaccuracies.</li>
            <li><strong>Aviation:</strong> Communication and navigation disruptions on polar routes.</li>
            <li><strong>Telecommunications:</strong> Disturbances affecting radio communication.</li>
            <li><strong>Power grids:</strong> Geomagnetically induced currents and potential transformer stress.</li>
        </ul>
    </div>
</div>
""")

# Bangladesh-Specific Impact
st.html("""
<div class="section-header">Bangladesh-Specific Impact</div>
<div class="impact-card">
    <div class="card-text">
        <p>Although Bangladesh does not have the same exposure to every space weather hazard as high-latitude regions, it remains part of a globally interconnected technological environment. SolarShield-AI introduces an opportunity to strengthen local awareness, research capacity, and preparedness discussions.</p>
        <ul style="color: var(--subheading); line-height: 1.8; margin-top: 10px;">
            <li><strong>Research Development:</strong> Encouraging university-level research in solar physics and AI.</li>
            <li><strong>Satellite Awareness:</strong> Supporting awareness of conditions affecting satellite services.</li>
            <li><strong>Power Infrastructure:</strong> Providing a framework for understanding geomagnetic disturbances.</li>
            <li><strong>Global Participation:</strong> Demonstrating how a team from Sylhet can contribute to global challenges.</li>
        </ul>
    </div>
</div>
""")

# Staged Development Pathway (Timeline)
st.html("""
<div class="section-header">From Research to Real-World Impact</div>
<p style="color: var(--subheading); margin-bottom: 24px;">SolarShield-AI follows a staged development pathway to ensure responsible innovation.</p>

<div class="impact-card">
    <div class="timeline">
        <div class="timeline-item">
            <div class="timeline-title">Stage 1 — Historical Research & Data Foundation</div>
            <div class="timeline-desc">Establish reliable historical solar datasets, investigate long-term trends, and develop reproducible analytical workflows.</div>
        </div>
        <div class="timeline-item">
            <div class="timeline-title">Stage 2 — Model Development & Evaluation</div>
            <div class="timeline-desc">Develop and compare forecasting approaches through controlled experiments and uncertainty analysis.</div>
        </div>
        <div class="timeline-item">
            <div class="timeline-title">Stage 3 — Space Weather Integration</div>
            <div class="timeline-desc">Integrate relevant space weather observations and investigate solar-geospace relationships.</div>
        </div>
        <div class="timeline-item">
            <div class="timeline-title">Stage 4 — Earth-Level Risk Research</div>
            <div class="timeline-desc">Develop and independently evaluate sector-specific impact indicators.</div>
        </div>
        <div class="timeline-item">
            <div class="timeline-title">Stage 5 — Explainable Decision-Support Prototype</div>
            <div class="timeline-desc">Develop an interface that presents research outputs, uncertainty, and risk information.</div>
        </div>
        <div class="timeline-item">
            <div class="timeline-title">Stage 6 — Shadow-Mode Pilot</div>
            <div class="timeline-desc">Work with research partners to evaluate the system without allowing unvalidated outputs to control decisions.</div>
        </div>
        <div class="timeline-item">
            <div class="timeline-title">Stage 7 — Academic & Professional Deployment</div>
            <div class="timeline-desc">Expand academic access and establish collaborations following successful validation.</div>
        </div>
    </div>
</div>
""")

# Responsible Innovation & Limitations
st.html("""
<div class="section-header">Responsible Innovation & Limitations</div>
<div class="impact-card" style="border-color: rgba(255, 183, 3, 0.4);">
    <div class="card-title" style="color: var(--amber);">🛡️ Our Commitments</div>
    <div class="card-text">
        <ul style="color: var(--subheading); line-height: 1.8;">
            <li>No guarantee of predicting every solar storm.</li>
            <li>No claim of operational readiness without independent validation.</li>
            <li>No replacement of official space weather monitoring authorities.</li>
            <li>No unsupported claims of preventing satellite failures or power outages.</li>
            <li>No confusion between solar activity forecasting and geomagnetic impact prediction.</li>
            <li>No presentation of model uncertainty as absolute certainty.</li>
        </ul>
    </div>
</div>
""")

# Final Statement
st.html("""
<div class="impact-card" style="text-align: center; background: linear-gradient(135deg, rgba(0,229,255,0.05) 0%, rgba(30,41,59,1) 100%); border-color: var(--cyan);">
    <div style="font-size: 1.3rem; font-weight: 800; color: var(--heading); margin-bottom: 12px;">
        "Our mission is not to promise perfect predictions, but to build a scientifically responsible pathway from observation to understanding, and from understanding to preparedness."
    </div>
    <div style="color: var(--cyan); font-family: var(--font-mono); font-weight: 600; letter-spacing: 1px;">
        Evidence Before Claims. Validation Before Deployment. Preparedness Through Understanding.
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
