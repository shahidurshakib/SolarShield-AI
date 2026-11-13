import streamlit as st

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(page_title="Documentation · SolarShield-AI", layout="wide", page_icon="📖")

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
    --body: #FFFFFF;
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
.main .block-container { max-width: 1200px; padding-top: 2rem; padding-bottom: 120px; }

h1, h2, h3, h4, h5, h6 { color: var(--heading) !important; font-weight: 700 !important; }
.stMarkdown p, .stMarkdown li { color: var(--body) !important; font-size: 1.1rem; line-height: 1.6; }
.stMarkdown strong { color: var(--cyan) !important; font-weight: 700 !important; }

/* SIDEBAR */
[data-testid="stSidebar"] { background: var(--sidebar) !important; border-right: 1px solid var(--border) !important; }
[data-testid="stSidebar"] * { color: #F1F5F9 !important; }

/* TABS CUSTOMIZATION (BULLETPROOF) */
.stTabs [data-baseweb="tab-list"] {
    gap: 24px;
    background-color: transparent;
    border-bottom: 2px solid var(--border);
    padding-bottom: 10px;
}

.stTabs button[data-baseweb="tab"] {
    background-color: transparent !important;
    border: none !important;
    padding: 10px 0 !important;
    box-shadow: none !important;
}

.stTabs button[data-baseweb="tab"] div {
    color: #F1F5F9 !important;
    font-weight: 600 !important;
    font-family: var(--font-mono) !important;
    font-size: 0.95rem !important;
    opacity: 1 !important;
    transition: color 0.2s ease;
}

.stTabs button[data-baseweb="tab"][aria-selected="true"] {
    border-bottom: 3px solid var(--cyan) !important;
}

.stTabs button[data-baseweb="tab"][aria-selected="true"] div {
    color: var(--cyan) !important; 
}

.stTabs button[data-baseweb="tab"]:hover div {
    color: var(--heading) !important;
}

/* HEADINGS WITHIN TABS */
h3 {
    color: var(--cyan) !important;
    font-family: var(--font-mono) !important;
    font-size: 1.4rem !important;
    margin-top: 2rem !important;
    margin-bottom: 1rem !important;
    border-bottom: 1px solid var(--border);
    padding-bottom: 8px;
}

/* TABLES */
table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 20px;
}
th, td {
    border: 1px solid var(--border) !important;
    padding: 12px !important;
    text-align: left;
    color: var(--body) !important;
    font-size: 1rem;
}
th {
    background-color: var(--card-bg-2) !important;
    color: var(--cyan) !important;
    font-weight: 700;
}
tr:nth-child(even) { background-color: var(--card-bg-1) !important; }
tr:nth-child(odd) { background-color: var(--bg) !important; }

/* BLOCKQUOTE */
blockquote {
    border-left: 4px solid var(--cyan);
    background: rgba(0, 229, 255, 0.05);
    padding: 15px 20px;
    margin: 20px 0;
    border-radius: 0 8px 8px 0;
    color: var(--heading) !important;
    font-size: 1.1rem;
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

st.title("Project Documentation")
st.caption("Complete Project Overview & Technical Documentation")
st.markdown("""
<p style="font-family: var(--font-mono); color: var(--cyan); font-size: 1.1rem; margin-bottom: 2rem;">
Predict the Sun. Understand the Risk. Prepare Earth.
</p>
""", unsafe_allow_html=True)

# Create Tabs for the massive amount of content
tab1, tab2, tab3, tab4 = st.tabs([
    "📌 Overview & Vision", 
    "🔬 Data & Methodology", 
    "🤖 Model Experiments", 
    "🏗️ Architecture & Future"
])

# --- TAB 1: OVERVIEW & VISION ---
with tab1:
    st.markdown("""
    ### 1. Project Overview
    **SolarShield-AI** is a research-oriented artificial intelligence and space weather risk assessment project developed by Team MU Solar Pulse for the NASA Space Apps Challenge 2026.

    The project investigates how historical and ongoing solar activity can be analyzed, modeled, and translated into meaningful information about potential space weather conditions and their possible consequences for Earth-based technological infrastructure.

    Changes in solar magnetic activity, sunspots, solar flares, coronal mass ejections (CMEs), and solar wind conditions can contribute to disturbances in Earth's magnetosphere and ionosphere. These may affect satellites, GNSS, communications, aviation, power grids, and scientific instruments.

    > **Core Concept Pipeline:** Solar Activity → Space Weather → Earth Response → Risk Assessment → Early Warning → Mitigation

    ### 2. Problem Statement
    The central problem is the difficulty of translating complex solar observations and space weather information into understandable, sector-specific risk information.

    Several challenges motivate this research:
    1. Solar activity changes over multiple timescales.
    2. Long-term solar cycles are not perfectly periodic.
    3. Solar observations contain noise, uncertainty, and provisional measurements.
    4. Solar activity alone cannot establish the severity of an Earth-directed event.
    5. Forecasting models require rigorous historical evaluation.
    6. Warning systems must communicate uncertainty instead of presenting false certainty.

    ### 3. NASA Space Apps Challenge Alignment
    SolarShield-AI is aligned with the 2026 theme: **Be An Earth System Trend Detective!**

    | Challenge Concept | SolarShield-AI Implementation |
    |---|---|
    | Historical scientific observations | SILSO monthly sunspot records |
    | Long-term trend analysis | Historical solar activity analysis |
    | Temporal pattern identification | Solar-cycle decomposition and phase normalization |
    | Statistical investigation | Autocorrelation and forecasting diagnostics |
    | Predictive analysis | Baseline, spline and cycle-conditioned models |

    ### 4. Project Objectives
    **Primary Objectives:**
    1. Build a reproducible historical solar activity dataset.
    2. Investigate the characteristics of solar cycles.
    3. Develop and evaluate solar-cycle forecasting models.
    4. Compare statistical and machine learning approaches.
    5. Investigate amplitude and shape differences between solar cycles.
    
    **Long-Term Objectives:**
    1. Integrate multiple solar and space weather datasets.
    2. Introduce calibrated probabilistic risk assessments.
    3. Validate outputs with relevant scientific and operational partners.
    """)

# --- TAB 2: DATA & METHODOLOGY ---
with tab2:
    st.markdown("""
    ### 5. Data Sources & Datasets
    The project distinguishes between datasets directly used, inspected experimentally, and identified for future integration.

    **Primary Dataset: SILSO**
    - **Source:** World Data Center SILSO, Royal Observatory of Belgium.
    - **Usage:** Historical solar activity reconstruction, cycle segmentation, phase normalization, and forecasting experiments.
    - **Policy:** CC BY-NC license.

    **Secondary Datasets (Exploratory/Future):**
    1. **NASA OMNI:** Near-Earth solar wind, magnetic field, and geomagnetic information.
    2. **NASA SDO/HMI:** Solar magnetic field information and active-region properties.
    3. **Historical Sunspot Group Archive:** Audited for schema changes and historical coverage.

    ### 6. Data Processing Workflow
    1. **Acquisition:** Retrieve raw SILSO data.
    2. **Validation:** Check for duplicates, dates, and provisional markers.
    3. **Cycle Segmentation:** Isolate completed cycles (1–24) from the ongoing Cycle 25.
    4. **Phase Normalization:** Transform completed cycles into normalized phase representations (121 points per cycle).
    5. **Integrity:** Generate SHA-256 hashes for frozen input records.

    ### 7. Statistical Analysis
    - **Autocorrelation:** Reported lag-1 autocorrelation of ~0.887 indicates strong temporal dependence.
    - **Metrics:** MAE, RMSE, MAPE, and R².
    - **Trend Analysis:** Mann-Kendall trend testing and Sen's slope.
    """)

# --- TAB 3: MODEL EXPERIMENTS ---
with tab3:
    st.markdown("""
    ### 8. Machine Learning Models
    **Implemented & Evaluated:**
    1. Persistence (Baseline)
    2. Seasonal-naive (Baseline)
    3. ARIMA/SARIMA (Statistical time series)
    4. Phase-median (Solar-cycle baseline)
    5. Constrained cubic B-spline (Curve modeling)
    6. Amplitude-aware models
    7. T0/T1/T2 (V3 cycle-conditioned methods)

    **Candidate Models (Future):** Random Forest, XGBoost, LightGBM, SVR, LSTM, GRU, Temporal CNN, Transformers.

    ### 9. SolarShield-AI V2 Research (Controlled historical forecasting)
    The V2 research used outer evaluation folds covering solar cycles 6–24.

    **V2-004: Phase-Median Baseline**
    - MAE: 32.286
    - RMSE: 43.007
    - Result: Became the C2/reference model for subsequent comparisons.

    **V2-006: Constrained Cubic B-Spline**
    - MAE: 32.897
    - RMSE: 43.207
    - Final Decision: **Not accepted** (MAE threshold not met).

    **V2-007: Amplitude-Aware Forecasting**
    Evaluated seven candidates. The best challenger (A4-S1) achieved an MAE of 37.885 and RMSE of 48.740. However, it exceeded the acceptance limits.
    - Final Decision: **NOT MET — Frozen and preserved unchanged.**

    ### 10. SolarShield-AI V3 Research (Adaptive Forecasting)
    V3 introduces a more adaptive and cycle-conditioned forecasting strategy.
    
    **Key Principles:**
    1. Adaptive correction using early observed portions of a solar cycle.
    2. Physical solar dynamo/Babcock–Leighton modeling.
    3. Machine learning residual modeling.
    4. Dynamic Time Warping (DTW)-based shape-aware investigation.

    **V3 Exploratory Run Results (T2 anchored-template at k=48):**
    - MAE: 22.994
    - RMSE: 29.321
    - Skill vs T0: 0.216
    
    *(Note: These are exploratory V3 results and should not be treated as V2 acceptance results or production forecasting accuracy.)*
    """)

# --- TAB 4: ARCHITECTURE & FUTURE ---
with tab4:
    st.markdown("""
    ### 11. System Architecture
    SolarShield-AI is designed as a layered research and application system:

    1. **Layer 1: Data Sources** (SILSO, NASA OMNI, SDO/HMI)
    2. **Layer 2: Data Engineering** (Acquisition, Validation, Feature Engineering)
    3. **Layer 3: Research & Modeling** (Statistical Analysis, V2/V3 Forecasting)
    4. **Layer 4: Impact Assessment** (Space Weather Analysis, Sector Risk)
    5. **Layer 5: Application** (Monitoring Dashboard, Alert Interface)

    *Note: Automated operational impact assessment and end-to-end real-time alert delivery must be treated as future implementation.*

    ### 12. Future Development & Automation Roadmap
    1. **Phase 1: Research Completion** (Complete V3 verification and execution).
    2. **Phase 2: Multi-Source Data Integration** (Integrate OMNI, HMI, flare catalogues).
    3. **Phase 3: Automated Data Collection** (Scheduled pipelines).
    4. **Phase 4: Automated Model Execution** (Controlled pipeline checks).
    5. **Phase 5: Real-Time Monitoring** (Data freshness, activity visualization).
    6. **Phase 6: Earth-Level Risk Assessment** (Validated impact models).
    7. **Phase 7: Early Warning and Mitigation** (Risk levels, forecast windows).
    8. **Phase 8: Shadow-Mode Pilot** (Operational validation with partners).

    ### 13. Disclaimer
    SolarShield-AI is a research and prototype development project. Its current forecasting experiments primarily investigate historical solar activity and solar-cycle behavior. A forecast of solar activity does not independently establish the occurrence, Earth-directed trajectory, or severity of a solar eruption or geomagnetic storm. The project does not claim to replace established operational space weather forecasting services.

    ### 14. Project Vision
    > SolarShield-AI aims to bridge the gap between understanding the Sun and preparing Earth for space weather risks.
    
    By combining historical scientific observations, statistical research, adaptive machine learning, explainability, and future operational validation, Team MU Solar Pulse seeks to develop an accessible framework for understanding solar activity and its potential effects on the technological systems modern society depends on.
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
