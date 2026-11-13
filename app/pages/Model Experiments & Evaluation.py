import pandas as pd
import streamlit as st

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(page_title="Experiments · SolarShield-AI", layout="wide", page_icon="🧪")

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
.main .block-container { max-width: 1400px; padding-top: 2rem; padding-bottom: 120px; }

h1, h2, h3, h4, h5, h6 { color: var(--heading) !important; font-weight: 700 !important; }
.stMarkdown p, .stMarkdown li { color: var(--body) !important; font-size: 1.05rem; line-height: 1.6; }
.stMarkdown strong { color: var(--cyan) !important; }

/* SIDEBAR */
[data-testid="stSidebar"] { background: var(--sidebar) !important; border-right: 1px solid var(--border) !important; }
[data-testid="stSidebar"] * { color: #F1F5F9 !important; }

/* TABS CUSTOMIZATION (BULLETPROOF FIX) */
.stTabs [data-baseweb="tab-list"] {
    gap: 24px;
    background-color: transparent;
    border-bottom: 1px solid var(--border);
    padding-bottom: 10px;
}
.stTabs button[data-baseweb="tab"] {
    background-color: transparent !important;
    border: none !important;
    padding: 10px 0 !important;
}
.stTabs button[data-baseweb="tab"] p {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    font-weight: 600 !important;
    font-family: var(--font-mono) !important;
    font-size: 0.95rem !important;
    opacity: 1 !important;
}
.stTabs button[data-baseweb="tab"][aria-selected="true"] {
    border-bottom: 3px solid var(--cyan) !important;
}
.stTabs button[data-baseweb="tab"][aria-selected="true"] p {
    color: var(--cyan) !important;
    -webkit-text-fill-color: var(--cyan) !important;
}
.stTabs [data-baseweb="tab-highlight"] {
    background-color: var(--cyan) !important;
}
.stTabs button[data-baseweb="tab"]:hover p {
    color: var(--cyan) !important;
    -webkit-text-fill-color: var(--cyan) !important;
}

/* CARDS & EXPLANATIONS */
.explainer-card {
    background: rgba(30, 41, 59, 0.5);
    border: 1px solid var(--border);
    border-left: 4px solid var(--cyan);
    border-radius: 8px;
    padding: 1.5rem;
    margin-top: 20px;
    margin-bottom: 20px;
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

/* METRIC CARDS */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin-bottom: 20px;
    width: 100%;
}
.metric-card {
    background: linear-gradient(135deg, var(--card-bg-2) 0%, var(--card-bg-1) 100%);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.2rem;
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    display: flex;
    flex-direction: column;
    justify-content: center;
    box-sizing: border-box;
}
.metric-label {
    color: var(--cyan) !important;
    font-family: var(--font-mono);
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 8px;
}
.metric-value {
    color: #FFFFFF !important;
    font-size: 1.8rem;
    font-weight: 800;
    letter-spacing: -1px;
    line-height: 1.1;
}
.metric-delta {
    font-size: 0.8rem;
    font-weight: 600;
    margin-top: 6px;
}

/* BADGES */
.badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-family: var(--font-mono);
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    margin-bottom: 10px;
}
.badge-success { background: rgba(16, 185, 129, 0.15); color: var(--success); border: 1px solid var(--success); }
.badge-danger { background: rgba(239, 68, 68, 0.15); color: var(--danger); border: 1px solid var(--danger); }
.badge-amber { background: rgba(255, 183, 3, 0.15); color: var(--amber); border: 1px solid var(--amber); }
.badge-cyan { background: rgba(0, 229, 255, 0.15); color: var(--cyan); border: 1px solid var(--cyan); }
.badge-muted { background: rgba(148, 163, 184, 0.15); color: var(--muted); border: 1px solid var(--muted); }

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

st.title("Model Experiments & Evaluation")
st.caption("Consolidated record of forecasting methods, configurations, results, and acceptance decisions.")
st.markdown("<br>", unsafe_allow_html=True)

st.html("""
<div class="explainer-card" style="border-left-color: var(--danger);">
    <h3 style="color: var(--danger) !important;">⚠️ Master Executive Conclusion</h3>
    <p>
        SolarShield-AI has reproducible data-preparation, descriptive-analysis evidence, and frozen V2/V3 protocols. However, the evidence <b>does not</b> support declaring any model scientifically accepted or freezing a production winner. 
    </p>
    <p>
        <b>Assessment cutoff:</b> 2026-11-12 UTC<br>
        <b>Repository HEAD:</b> 43157e02c90c425a1226fdf4c6332e770cbf81fb<br>
        <b>Overall disposition:</b> Historical evidence consolidated; <b>no scientifically accepted production model</b>.
    </p>
</div>
""")

# Create Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Baselines & V1", 
    "🔬 V2 Cycle-Shape", 
    "🚀 V3 Adaptive", 
    "🧪 Current V3 Draft", 
    "📋 Registry & Blockers"
])

# --- TAB 1: BASELINES & V1 ---
with tab1:
    st.markdown("### Baseline & V1 Forecasting")
    
    st.html("""
    <div class="explainer-card">
        <h3>Baseline Definitions</h3>
        <ul>
            <li><b>Persistence:</b> Assumes the latest observed value remains unchanged over the forecast horizon.</li>
            <li><b>Seasonal-Naive:</b> Uses a previous seasonal observation as the forecast reference.</li>
        </ul>
        <p>The historical baseline evaluation covered 129 paired target/horizon cases from Jan 2016 through Sep 2026. Persistence outperformed seasonal-naive at all horizons except 12 months (where they are identical by definition).</p>
    </div>
    """)

    st.markdown("#### V1.1 Monthly Baseline Hindcasts")
    st.caption("Expanding-window origins from 1976-01 to 2025-06, target cutoff 2026-06. 594 forecasts per model/horizon.")
    
    st.html("""
    <div class="metric-grid">
        <div class="metric-card">
            <div class="metric-label">ETS (1-Month)</div>
            <div class="metric-value" style="color: var(--cyan);">17.0</div>
            <div class="metric-delta" style="color: var(--success);">7.1% Skill vs Persistence</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">ETS (3-Month)</div>
            <div class="metric-value" style="color: var(--cyan);">21.2</div>
            <div class="metric-delta" style="color: var(--success);">8.8% Skill vs Persistence</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">ETS (6-Month)</div>
            <div class="metric-value" style="color: var(--cyan);">25.7</div>
            <div class="metric-delta" style="color: var(--success);">4.4% Skill vs Persistence</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">ETS (12-Month)</div>
            <div class="metric-value" style="color: var(--cyan);">37.5</div>
            <div class="metric-delta" style="color: var(--success);">2.5% Skill vs Persistence</div>
        </div>
    </div>
    """)

    st.html("""
    <div class="explainer-card">
        <h3>ETS (Additive Damped Trend)</h3>
        <p>ETS had zero recorded fit failures and warnings and lower point errors than paired persistence at each horizon. It remains an <b>exploratory candidate</b>, not an accepted or frozen winner. Origins overlap, errors are dependent, and historical data are revised rather than archived real-time vintages.</p>
    </div>
    """)

    st.markdown("#### ARIMA/SARIMA Investigation")
    st.html("""
    <div class="explainer-card" style="border-left-color: var(--danger);">
        <h3 style="color: var(--danger) !important;">ARIMA v1 <span class="badge badge-danger">No Candidate Selected</span></h3>
        <p>Selection period: 1976–1995 | Confirmation period: 1996–2015 | Quarterly forecast origins.</p>
        <p>Best recorded MAE ratio: <b>0.96635</b> (Threshold required: 0.95).</p>
        <p>No ARIMA/SARIMA model qualified. Confirmation on 1996-2015 was not run. No final evaluation runner is authorized.</p>
    </div>
    """)


# --- TAB 2: V2 EXPERIMENTS ---
with tab2:
    st.markdown("### V2 Cycle-Shape Experiments")
    
    st.html("""
    <div class="explainer-card">
        <h3>Evaluation Structure</h3>
        <p>V2 experiments used 19 outer evaluation folds covering historical solar cycles 6–24.</p>
        <p><b>Acceptance Limits:</b> MAE &le; 30.67 and RMSE &le; 47.31.</p>
    </div>
    """)

    st.html("""
    <div class="explainer-card">
        <h3>V2-004: Phase Median Baseline <span class="badge badge-cyan">Reference Baseline</span></h3>
        <p>Establishes a cycle-shape reference model using historical phase-normalized solar-cycle curves (121 normalized phase points per cycle).</p>
        <p><b>Result:</b> MAE 32.286 | RMSE 43.007 | 19/19 Folds Passed.</p>
        <p>Served as the C2 reference point for all subsequent V2 experiments.</p>
    </div>
    """)

    st.html("""
    <div class="explainer-card" style="border-left-color: var(--danger);">
        <h3 style="color: var(--danger) !important;">V2-005: C3 Constrained Cubic B-Spline <span class="badge badge-danger">Failed</span></h3>
        <p><b>Result:</b> 0/19 successful folds. 19 failure records.</p>
        <p>No valid aggregate MAE/RMSE could be calculated. SLSQP reported success in all folds, but dense-grid monotonicity validation passed in 0/19. 13 folds passed the 481-point constraint grid but failed the 1921-point dense grid; six failed both.</p>
        <p>The experiment cannot pass with failed required folds.</p>
    </div>
    """)

    st.html("""
    <div class="explainer-card" style="border-left-color: var(--danger);">
        <h3 style="color: var(--danger) !important;">V2-006: Derivative-Constrained Cubic B-Spline <span class="badge badge-danger">Not Accepted</span></h3>
        <p>Configuration: lambda = 0.0001. Evaluated over 19/19 folds (2,299 predictions).</p>
        <p><b>Result:</b> MAE 32.897 (Failed) | RMSE 43.207 (Passed).</p>
        <p><b>Diagnostics:</b> Peak attenuation in cycles 17, 19, and 21. Elevated errors in the second-quarter phase interval.</p>
        <p>The experiment was closed without modification or rerun. Its frozen results must remain unchanged. It is also worse than C2 on both aggregate errors.</p>
    </div>
    """)

    st.markdown("#### V2-007: Amplitude-Aware Forecasting")
    st.html("""
    <div class="explainer-card" style="border-left-color: var(--amber);">
        <h3 style="color: var(--amber) !important;">V2-007 Overview <span class="badge badge-amber">NOT MET — Frozen</span></h3>
        <p>Evaluated seven candidate configurations over cycles 6-24. Produced 133 fold-level records and 16,093 curve predictions. A decomposition report on Nov 4, 2026 found reconstruction error of 2.8 x 10^-14.</p>
    </div>
    """)
    
    v2_data = pd.DataFrame({
        "Candidate": ["A1-S1", "A2-S1", "A3-S1", "A4-S1", "A1-S2", "A1-S3", "A1-S4"],
        "Role": ["Frozen Primary", "Challenger", "Challenger", "Challenger", "Challenger", "Challenger", "Challenger"],
        "MAE": [40.061081, 39.605292, 40.928021, 37.885980, 45.256044, 43.292634, 41.256814],
        "RMSE": [51.255516, 50.914046, 52.102782, 48.740444, 55.976587, 54.020653, 52.154874],
    })
    st.dataframe(v2_data, use_container_width=True, hide_index=True)

    st.html("""
    <div class="explainer-card">
        <h3>V2-007 Key Finding</h3>
        <p>A4-S1 achieved the lowest MAE among challengers (37.89), but it remains worse than the C2 reference (32.28) and exceeds the MAE acceptance limit (30.67). It cannot replace the registered primary.</p>
        <p>The results were frozen. The experiment must not be rerun or silently modified.</p>
    </div>
    """)

# --- TAB 3: V3 EXPLORATORY ---
with tab3:
    st.markdown("### V3 Exploratory Forecasting (REV1)")
    
    st.html("""
    <div class="explainer-card">
        <h3>V3 Research Principles</h3>
        <p>V3 introduces a more adaptive, cycle-conditioned forecasting strategy.</p>
        <ul>
            <li><b>Adaptive Correction:</b> Use early rising-phase observations (first k months) to adjust forecasts.</li>
            <li><b>Physical Integration:</b> Investigate Babcock–Leighton solar dynamo concepts (not currently authorized).</li>
            <li><b>Shape-Aware Modeling:</b> Dynamic Time Warping (DTW) to compare cycle shapes.</li>
        </ul>
    </div>
    """)

    st.markdown("#### V3 Part A: Cycle-Conditioned Results")
    st.caption("Settings selected on cycles 6-15. Evaluated on cycles 16-24.")
    
    st.html("""
    <div class="metric-grid">
        <div class="metric-card">
            <div class="metric-label">T2 MAE (k=48)</div>
            <div class="metric-value" style="color: var(--cyan);">22.99</div>
            <div class="metric-delta" style="color: var(--success);">Skill vs T0: 0.216</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">T2 RMSE (k=48)</div>
            <div class="metric-value" style="color: var(--cyan);">29.32</div>
            <div class="metric-delta" style="color: var(--muted);">Anchored-template approach</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">T1 MAE (k=60)</div>
            <div class="metric-value" style="color: var(--cyan);">21.89</div>
            <div class="metric-delta" style="color: var(--success);">Lowest MAE at 60 months</div>
        </div>
    </div>
    """)

    st.html("""
    <div class="explainer-card">
        <h3>V3 Part B: Monthly Ridge-Lag Model</h3>
        <p>Tested on the full 594-case window. Ridge MAE skill vs persistence:</p>
        <ul>
            <li><b>1-Month:</b> 9.5% (MAE 16.60)</li>
            <li><b>3-Month:</b> 12.8% (MAE 20.30)</li>
            <li><b>6-Month:</b> 13.4% (MAE 23.34)</li>
            <li><b>12-Month:</b> 23.3% (MAE 29.46)</li>
        </ul>
        <p>All corresponding 95% block-bootstrap intervals included zero. This is retrospective evidence, not proof of real-time performance.</p>
    </div>
    """)

# --- TAB 4: CURRENT V3 DRAFT ---
with tab4:
    st.markdown("### Current V3 Draft 1.7 Workflow")
    
    st.html("""
    <div class="explainer-card" style="border-left-color: var(--amber);">
        <h3 style="color: var(--amber) !important;">Execution Status <span class="badge badge-amber">Partially Complete</span></h3>
        <p>Draft 1.7 is frozen (Protocol SHA-256: 18DD4B...565048). R29/R30 authorization and the execution gate were recorded as cleared.</p>
        <p>The V3 completion release reports and preserves the following A0-only results:</p>
    </div>
    """)

    st.html("""
    <div class="metric-grid">
        <div class="metric-card">
            <div class="metric-label">A0 Calibration (Cycles 13-15)</div>
            <div class="metric-value">31.16</div>
            <div class="metric-delta" style="color: var(--muted);">MAE | RMSE: 39.17 | 720 forecasts</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">A0 Final Backtest (Cycles 16-24)</div>
            <div class="metric-value">25.40</div>
            <div class="metric-delta" style="color: var(--muted);">MAE | RMSE: 33.91 | 3,112 forecasts</div>
        </div>
    </div>
    """)

    st.html("""
    <div class="explainer-card" style="border-left-color: var(--danger);">
        <h3 style="color: var(--danger) !important;">R21 Covariance Fit: Rejected</h3>
        <p>Nine training-only starts over eligible cycles 4-12 and 1,101 post-warm-up residuals. <b>All nine starts reached the q/r upper bound</b>, returning candidate q = r = 100.002981.</p>
        <p>The local Hessian had a negative eigenvalue (-364.706834). The estimate was not accepted or applied. Identifiability remains <b>NOT_ESTABLISHED</b>.</p>
    </div>
    """)

    st.html("""
    <div class="explainer-card" style="border-left-color: var(--danger);">
        <h3 style="color: var(--danger) !important;">What Was NOT Executed</h3>
        <ul>
            <li><b>A1/KF and A2/EnKF:</b> Not executed. R21 covariance acceptance and held-out scale mapping are unresolved.</li>
            <li><b>Cycle 25 under Draft 1.7:</b> Not executed. The protocol does not specify the forecast origin/horizon.</li>
            <li><b>R32 Acceptance Evaluation:</b> Not evaluated. Requires all four conditions (lower MAE, no higher RMSE, no higher peak-amplitude error, no higher peak-timing error). None can be evaluated without protocol-compliant A1/A2 matched forecasts.</li>
            <li><b>Babcock-Leighton:</b> Not authorized and not integrated.</li>
        </ul>
    </div>
    """)

# --- TAB 5: REGISTRY & BLOCKERS ---
with tab5:
    st.markdown("### Master Registry & Remaining Blockers")
    
    st.html("""
    <div class="explainer-card">
        <h3>Status Definitions</h3>
        <ul>
            <li><b>Frozen Protocol/Result:</b> Artifact is fixed; does not imply model acceptance.</li>
            <li><b>Reference Baseline:</b> Comparison method, not an accepted production candidate.</li>
            <li><b>Historical/Exploratory:</b> Executed evidence retained, but not promoted.</li>
            <li><b>Pending/Blocked:</b> Required evidence, selection, authorization, or evaluation is missing.</li>
        </ul>
    </div>
    """)
    
    st.markdown("#### Consolidated Experiment Status")
    
    status_data = pd.DataFrame({
        "Experiment": ["Historical Baseline", "Historical Baseline", "ARIMA v1", "V2-004", "V2-005", "V2-006", "V2-007", "V3 Exploratory", "V3 Future Execution", "V3 Future Comparison", "Physical Integration"],
        "Method": ["Persistence", "Seasonal-naive", "ARIMA/SARIMA", "Phase median", "C3 B-spline", "Derivative-constrained B-spline", "Amplitude-aware", "Cycle-conditioned T0/T1/T2", "Selection, calibration, backtesting", "KF versus EnKF", "Babcock–Leighton/dynamo"],
        "Status": ["Completed", "Completed", "No accepted candidate", "Completed reference", "Failed", "Not accepted; closed", "NOT MET; frozen", "Exploratory", "Awaiting gate", "Awaiting gate", "Not authorized"]
    })
    st.dataframe(status_data, use_container_width=True, hide_index=True)

    st.markdown("#### Evidence Integrity & Remaining Blockers")
    
    st.html("""
    <div class="explainer-card">
        <h3>Verified Hashes & Evidence</h3>
        <p>The project maintains SHA-256 hashes for all frozen releases. Key verified packages include:</p>
        <ul>
            <li><b>V3 Production Completion:</b> 132/132 files match (Manifest: 6AFBF...46E5F)</li>
            <li><b>V3 Engine Release:</b> 52/52 files match (Manifest: 119DB...8EB4D)</li>
            <li><b>V2-006 Execution Ledger:</b> 10 artifacts match</li>
            <li><b>V2-007 Results Freeze:</b> 10 artifacts match (Manifest: 6FC6E...7E6CA)</li>
        </ul>
    </div>
    """)

    st.html("""
    <div class="explainer-card" style="border-left-color: var(--amber);">
        <h3 style="color: var(--amber) !important;">Remaining Blockers</h3>
        <ul>
            <li><b>Production KF/EnKF Covariance:</b> Blocked. Owner disposition of boundary-seeking R21 fit is required.</li>
            <li><b>R22-R25 Production Configuration:</b> Blocked. Frozen deterministic selection objectives are needed.</li>
            <li><b>V3 Matched Comparison/R32:</b> Not evaluable. Protocol-compliant A1/A2 forecasts are required.</li>
            <li><b>Draft 1.7 Cycle 25 Forecast:</b> Not executed. Explicit origin and horizon policy needed.</li>
            <li><b>Data Provenance:</b> Incomplete. Exact SILSO source URL and retrieval date are not recorded.</li>
        </ul>
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
