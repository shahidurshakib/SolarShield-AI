import streamlit as st

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(page_title="Tech Stack · SolarShield-AI", layout="wide", page_icon="☀")

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
.main .block-container { max-width: 1500px; padding-top: 2rem; padding-bottom: 120px; }

h1, h2, h3, h4, h5, h6 { color: var(--heading) !important; font-weight: 700 !important; }
.stMarkdown p, .stMarkdown li { color: var(--body) !important; font-size: 1.05rem; }
.stMarkdown strong { color: var(--cyan) !important; }

/* SIDEBAR */
[data-testid="stSidebar"] { background: var(--sidebar) !important; border-right: 1px solid var(--border) !important; }
[data-testid="stSidebar"] * { color: #F1F5F9 !important; }

/* TECH GRID */
.tech-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 24px;
    margin-top: 24px;
    margin-bottom: 40px;
}
.tech-card {
    background: linear-gradient(135deg, var(--card-bg-2) 0%, var(--card-bg-1) 100%);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.tech-card:hover {
    transform: translateY(-4px);
    border-color: var(--cyan);
}
.tech-title { 
    color: var(--cyan); 
    font-size: 1.2rem; 
    font-weight: 700; 
    font-family: var(--font-mono); 
    margin-bottom: 16px; 
    display: flex; 
    align-items: center; 
    gap: 10px; 
}
.tech-list {
    list-style-type: none;
    padding-left: 0;
    margin: 0;
}
.tech-list li {
    color: var(--subheading);
    font-size: 0.95rem;
    line-height: 1.5;
    margin-bottom: 12px;
    padding-left: 20px;
    position: relative;
}
.tech-list li::before {
    content: "▹";
    color: var(--amber);
    position: absolute;
    left: 0;
    top: 0;
    font-weight: bold;
}
.tech-list li strong {
    color: var(--heading) !important;
}

/* STATUS BADGES */
.status-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-family: var(--font-mono);
    font-weight: 700;
    margin-left: 8px;
}
.status-confirmed { background: rgba(16, 185, 129, 0.2); color: #10B981; border: 1px solid #10B981; }
.status-candidate { background: rgba(255, 183, 3, 0.2); color: #FFB703; border: 1px solid #FFB703; }
.status-exploratory { background: rgba(0, 229, 255, 0.2); color: #00E5FF; border: 1px solid #00E5FF; }

/* ALERT BOX */
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

st.title("Technology Stack")
st.caption("Technologies, development environment, scientific methods, and proposed tools.")
st.markdown("<br>", unsafe_allow_html=True)

# Card 1: Development Environment
st.html("""
<div class="tech-grid">
    <div class="tech-card">
        <div class="tech-title">💻 Development Environment</div>
        <ul class="tech-list">
            <li><strong>Operating System:</strong> Windows 11 <span class="status-badge status-confirmed">Confirmed</span></li>
            <li><strong>Command-line:</strong> Windows PowerShell <span class="status-badge status-confirmed">Confirmed</span></li>
            <li><strong>Main Runtime:</strong> Python 3.15.1 <span class="status-badge status-confirmed">Confirmed</span></li>
            <li><strong>Scientific Env:</strong> Python 3.14.10 <span class="status-badge status-confirmed">Confirmed</span></li>
            <li><strong>Astronomy Lib:</strong> Astropy 8.0.2 <span class="status-badge status-confirmed">Confirmed</span></li>
            <li><strong>Solar Physics Lib:</strong> SunPy 8.0.1 <span class="status-badge status-confirmed">Confirmed</span></li>
        </ul>
    </div>
    
    <div class="tech-card">
        <div class="tech-title">📊 Data Sources & Infrastructure</div>
        <ul class="tech-list">
            <li><strong>WDC-SILSO:</strong> Historical sunspot observations <span class="status-badge status-confirmed">Used</span></li>
            <li><strong>NASA SDO/HMI:</strong> Solar magnetogram data <span class="status-badge status-exploratory">Exploratory</span></li>
            <li><strong>JSOC:</strong> HMI data access infrastructure <span class="status-badge status-exploratory">Explored</span></li>
            <li><strong>NASA OMNIWeb:</strong> Solar-wind and geomagnetic data <span class="status-badge status-candidate">Candidate</span></li>
            <li><strong>Formats:</strong> FITS (Exploratory), CSV (Used in recorded artifacts)</li>
        </ul>
    </div>
</div>
""")

# Card 2: Scientific Methods
st.html("""
<div class="tech-grid">
    <div class="tech-card">
        <div class="tech-title">🔬 Forecasting & Statistical Methods</div>
        <ul class="tech-list">
            <li><strong>Persistence:</strong> Baseline forecasting <span class="status-badge status-confirmed">Executed</span></li>
            <li><strong>Seasonal-naive:</strong> Baseline forecasting <span class="status-badge status-confirmed">Executed</span></li>
            <li><strong>ARIMA/SARIMA:</strong> Statistical time-series modeling <span class="status-badge status-exploratory">Investigated</span></li>
            <li><strong>Phase median:</strong> Historical cycle-shape baseline <span class="status-badge status-confirmed">Executed</span></li>
            <li><strong>Cubic B-spline:</strong> Cycle-shape estimation <span class="status-badge status-exploratory">Executed </span></li>
            <li><strong>Amplitude-aware:</strong> Amplitude and shape forecasting <span class="status-badge status-exploratory">Executed </span></li>
            <li><strong>T0/T1/T2:</strong> Partial-observation cycle forecasting <span class="status-badge status-exploratory">Exploratory V3</span></li>
        </ul>
    </div>
    
    <div class="tech-card">
        <div class="tech-title">🤖 Candidate Machine Learning (Future)</div>
        <ul class="tech-list">
            <li><strong>Random Forest:</strong> Nonlinear feature modeling <span class="status-badge status-candidate">Candidate</span></li>
            <li><strong>XGBoost / LightGBM:</strong> Gradient-boosted forecasting <span class="status-badge status-candidate">Candidate</span></li>
            <li><strong>SVR:</strong> Nonlinear regression <span class="status-badge status-candidate">Candidate</span></li>
            <li><strong>LSTM / GRU:</strong> Sequential time-series modeling <span class="status-badge status-candidate">Candidate</span></li>
            <li><strong>Temporal CNN:</strong> Temporal feature extraction <span class="status-badge status-candidate">Candidate</span></li>
            <li><strong>Transformer:</strong> Long-range sequence modeling <span class="status-badge status-candidate">Candidate</span></li>
        </ul>
    </div>
</div>
""")

# Card 3: Explainability & Metrics
st.html("""
<div class="tech-grid">
    <div class="tech-card">
        <div class="tech-title">📈 Explainability & Evaluation</div>
        <ul class="tech-list">
            <li><strong>Confirmed Metrics:</strong> MAE, RMSE, Skill relative to baseline.</li>
            <li><strong>Planned Metrics:</strong> R², MAPE, F1-score, ROC-AUC, PR-AUC, Brier score, Calibration diagnostics.</li>
            <li><strong>Explainability:</strong> V2-007 analysis includes amplitude-versus-shape error attribution. SHAP is a proposed candidate for future feature-level explainability.</li>
        </ul>
    </div>
    
    <div class="tech-card">
        <div class="tech-title">🛡️ Development Quality & Reproducibility</div>
        <ul class="tech-list">
            <li>Frozen experiment configurations.</li>
            <li>Controlled research protocols.</li>
            <li>Source and artifact hash verification.</li>
            <li>Historical artifact preservation.</li>
            <li>Synthetic testing and full regression.</li>
            <li>Explicit experiment acceptance criteria.</li>
        </ul>
    </div>
</div>
""")

# Web & Dashboard Layer
st.html("""
<div class="custom-alert" style="background: rgba(0,229,255,0.05); border-color: rgba(0,229,255,0.3);">
    <p style="color: #FFFFFF !important;">
        <strong style="color: var(--cyan) !important;">🌐 Web & Dashboard Layer:</strong> 
        The long-term concept includes a dashboard for solar activity visualization, historical cycle exploration, forecast curves, uncertainty communication, and sector-specific risk information. 
        <br><br>
        <em>Note: The frontend framework, backend architecture, database, and hosting configuration are not fully established in the available technical record.</em>
    </p>
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
