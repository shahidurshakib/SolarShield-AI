
import pandas as pd
import streamlit as st
from lib import data

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Model status · SolarShield-AI",
    layout="wide",
    page_icon="☀️",
    initial_sidebar_state="expanded",
)

# ============================================================
# DESIGN SYSTEM — DEEP SPACE / STEEL BLUE
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
    --muted: #94A3B8;
    --cyan: #00E5FF;
    --amber: #FFB703;
    --success: #10B981;
    --danger: #EF4444;
    --font-main: 'Inter', sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
}

/* GLOBAL */
html, body, .stApp {
    font-family: var(--font-main) !important;
}

.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background: radial-gradient(
        circle at 50% 0%,
        #0A1526 0%,
        var(--bg) 100%
    ) !important;
    color: var(--body) !important;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

.main .block-container {
    max-width: 1200px;
    padding-top: 2rem;
    padding-bottom: 120px;
}

h1, h2, h3, h4, h5, h6 {
    color: var(--heading) !important;
    font-weight: 700 !important;
}

.stMarkdown p, .stMarkdown li {
    color: var(--body) !important;
    font-size: 1rem;
    line-height: 1.7;
}

.stMarkdown strong {
    color: var(--cyan) !important;
}

/* SIDEBAR */
[data-testid="stSidebar"] {
    background: var(--sidebar) !important;
    border-right: 1px solid var(--border) !important;
}

[data-testid="stSidebar"] * {
    color: #F1F5F9 !important;
}

/* EXPLANATION CARDS */
.explain-card {
    background: linear-gradient(
        145deg,
        rgba(30, 41, 59, 0.96),
        rgba(17, 29, 46, 0.96)
    );
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 20px;
    height: 100%;
}

.explain-title {
    color: var(--cyan);
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    margin-bottom: 10px;
}

.explain-card p {
    color: var(--body);
    font-size: 0.91rem;
    line-height: 1.65;
    margin-bottom: 0;
}

/* SECTION LABEL */
.section-label {
    color: var(--cyan);
    font-family: var(--font-mono);
    font-size: 0.75rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 6px;
}

/* DATAFRAME */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    background: var(--card-bg-1) !important;
}

/* FOOTER */
.custom-footer {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background: rgba(10, 17, 32, 0.95);
    border-top: 1px solid var(--border);
    padding: 12px 2rem;
    text-align: center;
    z-index: 9999;
}

.footer-link {
    color: var(--cyan) !important;
    text-decoration: none !important;
}

.footer-copyright {
    color: var(--muted) !important;
    font-size: 0.75rem;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# PAGE CONTENT
# ============================================================

st.title("Model status")

st.markdown(
    """
    The Model Status page provides an overview of the models and
    experiments documented in the SolarShield-AI project.

    It uses the project's **Master Model Freeze Registry** to show
    recorded model information, development stages, and evaluation
    records.
    """
)

# ============================================================
# LOAD REGISTRY
# ============================================================

try:
    registry = data.registry()

except FileNotFoundError as e:
    st.error(f"Registry file not found: {e}")
    st.stop()

except Exception as e:
    st.error(f"Could not load the model registry: {e}")
    st.stop()


# ============================================================
# WHAT IS THE MODEL REGISTRY?
# ============================================================

st.markdown(
    '<div class="section-label">01 · Understanding the registry</div>',
    unsafe_allow_html=True
)

st.header("What does this page track?")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="explain-card">
        <div class="explain-title">Model documentation</div>
        <p>
            The registry acts as a central record of the project's
            documented models and experiments. It helps identify
            which model versions, tasks, and evaluation records
            are included in the project.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="explain-card">
        <div class="explain-title">Research traceability</div>
        <p>
            Maintaining a model registry makes it easier to trace
            development decisions, compare documented experiments,
            and distinguish experimental work from formally
            accepted model versions.
        </p>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# HOW TO INTERPRET MODEL STATUS
# ============================================================

st.markdown(
    '<div class="section-label">02 · Status interpretation</div>',
    unsafe_allow_html=True
)

st.header("Understanding model acceptance")

st.markdown("""
A model being developed or evaluated does not automatically mean
that it has been scientifically accepted.

In this project, model development, evaluation, and acceptance
should be treated as separate stages:

1. **Development:** A model or forecasting approach is implemented
   and its outputs are generated.

2. **Evaluation:** Its predictions or results are assessed using
   the project's selected evaluation methods and historical data.

3. **Scientific acceptance:** The evidence is reviewed against the
   project's acceptance criteria before a model can be treated as
   an accepted version.

4. **Model freeze:** An accepted version is formally identified
   as the reference model for the project.

The registry records information relevant to this process.
Its presence alone should not be interpreted as proof of
scientific validation or operational readiness.
""")


# ============================================================
# MODEL REGISTRY TABLE
# ============================================================

st.divider()

st.markdown(
    '<div class="section-label">03 · Registry records</div>',
    unsafe_allow_html=True
)

st.header("Documented models and experiments")

entries = registry.get("entries", [])

if entries:
    entries_df = pd.DataFrame(entries)

    st.caption(
        f"Displaying {len(entries_df)} registry record(s) "
        "from the project's master model registry."
    )

    st.dataframe(
        entries_df,
        use_container_width=True,
        hide_index=True
    )

    with st.expander("How should I read this table?"):
        st.markdown("""
        Each row represents a record maintained in the project's
        model registry.

        The columns describe the information recorded for that
        model or experiment, such as its identifier, development
        task, version, evaluation details, or recorded status,
        depending on the fields available in the registry.

        These records should be interpreted using their documented
        fields and the project's evaluation methodology.
        """)

else:
    st.info("No model records are currently available in the registry.")


# ============================================================
# PROJECT SCOPE AND LIMITATIONS
# ============================================================

st.divider()

st.markdown(
    '<div class="section-label">04 · Project scope</div>',
    unsafe_allow_html=True
)

st.header("Current scope and limitations")

st.markdown("""
SolarShield-AI focuses on solar activity analysis and forecasting
using sunspot-number data and related statistical or forecasting
methods.

The model registry documents the project's model-development
and evaluation records. It should not be confused with a
real-time operational monitoring system.

The following capabilities are outside the scope of the current
documented model registry unless separately implemented and validated:

- Operational space-weather warning services.
- Real-time Earth-impact prediction.
- Validated spacecraft or infrastructure risk assessment.
- Automated operational alert delivery.

**Research distinction:** A forecasting result, a model evaluation,
and an operationally validated warning system are different levels
of capability. Claims about the latter require separate evidence.
""")

st.caption(
    "Registry source: reports/MASTER_MODEL_FREEZE_REGISTRY.json"
)


# ============================================================
# FOOTER
# ============================================================

st.html("""
<div class="custom-footer">
    <div>
        <a href="https://github.com/shahidurshakib/SolarShield-AI"
           target="_blank"
           rel="noopener noreferrer"
           class="footer-link">
            GitHub · SolarShield-AI
        </a>
    </div>
    <div class="footer-copyright">
        Copyright © 2026 Team MU Solar Pulse. All Rights Reserved.
    </div>
</div>
""")
