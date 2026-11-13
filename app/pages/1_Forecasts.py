import altair as alt
import streamlit as st
from lib import data

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(page_title="Forecasts · SolarShield-AI", layout="centered", page_icon="☀")

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

/* SELECTBOX FIX */
[data-testid="stWidgetLabel"] p {
    color: var(--cyan) !important;
    font-family: var(--font-mono) !important;
    font-weight: 600 !important;
}
div[data-baseweb="select"] > div {
    background-color: var(--card-bg-1) !important;
    border: 1px solid var(--border) !important;
}
div[data-baseweb="select"] div[aria-live="polite"] {
    color: #FFFFFF !important;
    font-weight: 600 !important;
}

/* EXPANDER & DATAFRAME FIX */
[data-testid="stExpander"] {
    background-color: var(--card-bg-1) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    overflow: hidden;
}
[data-testid="stExpander"] summary {
    background-color: var(--card-bg-2) !important;
    color: var(--heading) !important;
    border-bottom: 1px solid var(--border) !important;
}
[data-testid="stExpander"] summary * {
    color: var(--heading) !important;
    font-weight: 600 !important;
}
[data-testid="stDataFrame"] > div {
    background-color: var(--card-bg-1) !important;
}
[data-testid="stDataFrame"] iframe {
    background-color: var(--card-bg-1) !important;
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

st.title("Forecasts")

st.html("""

""")

a, b = st.columns(2)
model = a.selectbox("Model", ["persistence", "seasonal_naive", "ETS (exploratory)"])
h = b.selectbox("Horizon (months)", [1, 3, 6, 12], index=2)

try:
    df = data.forecast_frame(model, h).dropna().sort_values("target_month")
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()

if df.empty:
    st.info("No scored forecasts for this model and horizon.")
    st.stop()

# --- CHART SECTION ---
long = df.melt("target_month", var_name="series", value_name="ssn")

chart = (
    alt.Chart(long)
    .mark_line(strokeWidth=3)
    .encode(
        x=alt.X("target_month:T", title=None, axis=alt.Axis(labelColor="#CBD5E1", titleColor="#CBD5E1", gridColor="#334155")),
        y=alt.Y("ssn:Q", title="Sunspot number", axis=alt.Axis(labelColor="#CBD5E1", titleColor="#CBD5E1", gridColor="#334155")),
        color=alt.Color(
            "series:N", 
            scale=alt.Scale(range=["#00E5FF", "#FFB703", "#10B981"]), 
            legend=alt.Legend(orient="bottom", title=None, labelColor="#CBD5E1")
        ),
    )
    .properties(height=300, background="transparent")
)
st.altair_chart(chart, use_container_width=True)

st.html("""
<div class="explainer-card">
    <h3>Understanding the Forecast Chart</h3>
    <p>This chart illustrates the historical sunspot-number patterns and the corresponding forecast estimates generated by the selected reference model.</p>
    <p><b>How to read the chart:</b></p>
    <ul>
        <li><b>X-axis (Target Month):</b> Represents the month for which the sunspot number is being evaluated or forecast.</li>
        <li><b>Y-axis (Sunspot Number):</b> Represents the recorded or estimated monthly sunspot activity.</li>
        <li><b>Colored lines:</b> Represent the different data series returned by the selected forecasting model.</li>
    </ul>
    <p><b>Interpretation:</b> Sunspot activity follows an approximately 11-year solar cycle. The chart helps visualize how the selected reference model reproduces or estimates these historical patterns. A closer alignment between forecast estimates and observed sunspot activity generally indicates better historical performance.</p>
    <p style="color: var(--amber); margin-top: 10px; font-weight: 600;">Important: These visualizations represent historical backtesting results. They should not be interpreted as operational predictions of future solar activity.</p>
</div>
""")

# --- METRICS SECTION ---
s = data.scores(df)

metrics_html = f"""
<div class="metric-grid">
    <div class="metric-card">
        <div class="metric-label">Forecasts scored</div>
        <div class="metric-value">{s['n']}</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">MAE</div>
        <div class="metric-value">{s['MAE']:.1f}</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">RMSE</div>
        <div class="metric-value">{s['RMSE']:.1f}</div>
    </div>
</div>
"""
st.html(metrics_html)

with st.expander("How to interpret the evaluation metrics"):
    st.markdown("""
    **Forecasts Scored (N)**
    The total number of monthly observations included in the evaluation after removing missing values.

    **Mean Absolute Error (MAE)**
    Measures the average absolute difference between forecast estimates and actual observed sunspot numbers. Lower MAE indicates smaller average forecasting errors.

    **Root Mean Squared Error (RMSE)**
    Measures forecasting error while assigning greater weight to larger errors through squaring before averaging. Lower RMSE generally indicates better forecasting performance.

    Both MAE and RMSE are expressed in sunspot-number units.

    **Note:** Model comparisons are meaningful only when they use the same evaluation period and comparable observations.
    """)

st.caption(
    f"Evaluation window: {df['target_month'].min():%Y-%m} to {df['target_month'].max():%Y-%m}. "
    "ETS was scored on a longer window (from 1976) than the baseline backtest (from 2016), "
    "so compare scores only between runs that share a window."
)

# --- DATA TABLE SECTION ---
with st.expander("View monthly forecast data", expanded=False):
    
    # Prepare a clean dataframe for display
    display_df = df.copy()
    
    # Calculate error metrics for the table
    if "actual" in display_df.columns and "prediction" in display_df.columns:
        display_df["Forecast Error"] = display_df["prediction"] - display_df["actual"]
        display_df["Absolute Error"] = display_df["Forecast Error"].abs()
        
        display_df.rename(columns={
            "target_month": "Target Month",
            "actual": "Observed SSN",
            "prediction": "Forecast SSN"
        }, inplace=True)
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Observed SSN": st.column_config.NumberColumn(format="%.2f"),
            "Forecast SSN": st.column_config.NumberColumn(format="%.2f"),
            "Forecast Error": st.column_config.NumberColumn(format="%.2f"),
            "Absolute Error": st.column_config.NumberColumn(format="%.2f"),
        }
    )

    st.markdown("""
    **Understanding the table**

    Each row represents one monthly forecast evaluation.

    | Column | Meaning |
    |---|---|
    | **Target Month** | Month for which the forecast was evaluated. |
    | **Observed SSN** | Actual observed sunspot number for that month. |
    | **Forecast SSN** | Estimate generated by the selected model. |
    | **Forecast Error** | Forecast SSN minus Observed SSN. |
    | **Absolute Error** | Absolute magnitude of the forecast error. |

    **Reading the forecast error**

    - **Positive:** The forecast was higher than the observed value (overestimation).
    - **Negative:** The forecast was lower than the observed value (underestimation).
    - **Zero:** The forecast exactly matched the observed value.

    Absolute error removes the sign and shows only the size of the difference. The MAE and RMSE above summarize errors across all scored rows.
    """)

# --- CYCLE CHARACTERISTICS SECTION ---
st.subheader("Cycle Characteristics")
st.caption("Analog Method · Held-Out Cycles")

try:
    cycle_df = data.cycle_metrics()

    st.dataframe(
        cycle_df,
        use_container_width=True,
        hide_index=True
    )

    st.html("""
    <div class="explainer-card">
        <h3>Understanding Solar Cycle Characteristics</h3>
        <p>
            Solar activity changes over time and is commonly
            characterized by recurring increases and decreases in
            sunspot activity. A solar cycle is often described as
            having an approximate duration of 11 years, although
            individual cycles vary.
        </p>
        <p>
            This section displays the results loaded from the
            repository's cycle-hindcast metrics output for the
            analog-method experiment.
        </p>
        <p><b>What the analysis is intended to examine:</b></p>
        <ul>
            <li>How the analog method performs on the held-out
            historical cycles included in the experiment.</li>
            <li>How estimated cycle characteristics compare with
            the corresponding held-out reference values.</li>
            <li>Descriptive interval and error information reported
            by the experiment.</li>
        </ul>
        <p>
            <b>Held-out cycles:</b> The term indicates cycles set
            aside for evaluation in the experiment. The exact
            interpretation of each metric depends on the experiment's
            methodology and the columns in its output file.
        </p>
        <p style="color: var(--amber); margin-top: 10px; font-weight: 600;">
            Research limitation: Interval coverage shown in this
            experiment is descriptive. It should not be presented
            as statistically validated predictive accuracy or as
            a guarantee of future coverage.
        </p>
    </div>
    """)

except FileNotFoundError as e:
    st.warning(str(e))

st.caption(
    "Cycle-hindcast results are a separate experiment from the "
    "monthly forecast backtests. Interval coverage is descriptive, "
    "not a validated accuracy claim."
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
