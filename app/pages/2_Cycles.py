import altair as alt
import pandas as pd
import streamlit as st
from lib import data

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Cycles · SolarShield-AI",
    layout="wide",
    page_icon="☀",
)

# ============================================================
# DESIGN SYSTEM (DEEP SPACE / STEEL BLUE)
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
.main .block-container {
    max-width: 1250px;
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
.stMarkdown strong { color: var(--cyan) !important; }

/* SIDEBAR */
[data-testid="stSidebar"] {
    background: var(--sidebar) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: #F1F5F9 !important; }

/* ALERT */
.custom-alert {
    background: rgba(255, 183, 3, 0.10);
    border: 1px solid rgba(255, 183, 3, 0.40);
    border-radius: 12px;
    padding: 1.1rem 1.3rem;
    margin: 0.5rem 0 1.5rem 0;
    box-sizing: border-box;
}
.custom-alert p {
    color: #FFFFFF !important;
    font-size: 0.95rem;
    margin: 0;
}
.custom-alert strong {
    color: var(--amber) !important;
    font-weight: 800 !important;
}

/* EXPLANATION CARDS */
.explainer-card {
    background: rgba(30, 41, 59, 0.58);
    border: 1px solid var(--border);
    border-left: 4px solid var(--cyan);
    border-radius: 10px;
    padding: 1.35rem 1.5rem;
    margin: 1rem 0 1.5rem 0;
}
.explainer-card h3 {
    color: var(--cyan) !important;
    font-size: 1.05rem;
    margin: 0 0 0.8rem 0;
    font-family: var(--font-mono);
}
.explainer-card p, .explainer-card li {
    color: var(--subheading) !important;
    font-size: 0.93rem;
    line-height: 1.7;
}
.explainer-card b { color: var(--heading) !important; }

/* WIDGETS / EXPANDERS / TABLES */
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
[data-testid="stDataFrame"] > div,
[data-testid="stDataFrame"] iframe {
    background-color: var(--card-bg-1) !important;
}

/* FOOTER */
.custom-footer {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background: rgba(10, 17, 32, 0.96);
    border-top: 1px solid var(--border);
    padding: 11px 2rem;
    text-align: center;
    z-index: 9999;
}
.footer-link {
    color: var(--cyan) !important;
    text-decoration: none !important;
    font-weight: 600;
}
.footer-copyright {
    color: var(--muted) !important;
    font-size: 0.72rem;
    margin-top: 3px;
}
@media (max-width: 700px) {
    .explainer-card { padding: 1rem; }
    .custom-footer { padding: 10px 0.75rem; }
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# PAGE HEADER AND DATA LOADING
# ============================================================

st.title("Solar Cycles")

st.markdown("""
Explore observed monthly sunspot activity across numbered solar cycles.
Select a cycle to inspect its historical development, peak values,
and the underlying monthly observations.
""")

try:
    cy = data.cycles()
    m = data.monthly()
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()

if cy.empty:
    st.info("No solar-cycle summary records are available.")
    st.stop()

if m.empty:
    st.info("No processed monthly sunspot observations are available.")
    st.stop()

# Keep the cycle selector in the order provided by the summary dataset.
cycle_numbers = cy["cycle_number"].dropna().tolist()
if not cycle_numbers:
    st.info("The cycle summary does not contain valid cycle numbers.")
    st.stop()

n = st.selectbox(
    "Select Solar Cycle",
    cycle_numbers,
    index=len(cycle_numbers) - 1,
    format_func=lambda x: f"Cycle {x}",
)

d = (
    m[m["cycle_number"] == n]
    .sort_values("month_start")
    .copy()
)

if d.empty:
    st.warning(f"No monthly observations were found for Solar Cycle {n}.")
    st.stop()

d["month_start"] = pd.to_datetime(d["month_start"], errors="coerce")
d = d.dropna(subset=["month_start", "ssn"])

if d.empty:
    st.warning(f"No valid monthly sunspot observations were found for Solar Cycle {n}.")
    st.stop()

row = cy[cy["cycle_number"] == n].iloc[0]

# ============================================================
# SELECTED CYCLE SUMMARY
# ============================================================

st.subheader(f"Solar Cycle {n} · Historical Activity")

status = str(row["status"])
raw_peak = row["raw_monthly_peak_ssn"]
raw_peak_month = row["raw_monthly_peak_month"]
smoothed_peak = row["official_smoothed_max_sn"]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Cycle Status", status.title())

with col2:
    st.metric(
        "Raw Monthly Peak",
        f"{raw_peak:.1f}" if pd.notna(raw_peak) else "—"
    )

with col3:
    st.metric(
        "Official Smoothed Maximum",
        f"{smoothed_peak:.1f}" if pd.notna(smoothed_peak) else "—"
    )

st.caption(
    f"Raw monthly peak recorded in: {raw_peak_month}"
    if pd.notna(raw_peak_month)
    else "Raw monthly peak month is not available in the cycle summary."
)

if status.lower() != "completed":
    st.html("""
    <div class="custom-alert">
        <p>
            <strong>PROVISIONAL DATA NOTE:</strong>
            This cycle is ongoing. Recent monthly observations may be
            provisional and can be revised as source data are updated.
        </p>
    </div>
    """)

# ============================================================
# HISTORICAL MONTHLY SUNSPOT ACTIVITY CHART
# ============================================================

st.subheader("Monthly Sunspot Activity")

chart_main = (
    alt.Chart(d)
    .mark_line(
        strokeWidth=2.5,
        color="#00E5FF"
    )
    .encode(
        x=alt.X(
            "month_start:T",
            title="Month",
            axis=alt.Axis(
                format="%Y",
                labelColor="#CBD5E1",
                titleColor="#CBD5E1",
                gridColor="#334155"
            )
        ),
        y=alt.Y(
            "ssn:Q",
            title="Monthly Sunspot Number (SSN)",
            axis=alt.Axis(
                labelColor="#CBD5E1",
                titleColor="#CBD5E1",
                gridColor="#334155"
            )
        ),
        tooltip=[
            alt.Tooltip(
                "month_start:T",
                title="Month",
                format="%Y-%m"
            ),
            alt.Tooltip(
                "ssn:Q",
                title="Monthly Sunspot Number",
                format=".2f"
            ),
            *(
                [
                    alt.Tooltip(
                        "is_provisional:N",
                        title="Provisional Observation"
                    )
                ]
                if "is_provisional" in d.columns
                else []
            )
        ]
    )
    .properties(
        height=350,
        background="transparent"
    )
    .interactive()
)

st.altair_chart(chart_main, use_container_width=True)

st.html("""
<div class="explainer-card">
    <h3>Understanding the Solar Cycle Chart</h3>
    <p>
        The line chart displays the processed monthly sunspot-number
        observations assigned to the selected solar cycle.
        It shows how solar activity changed over the cycle's recorded
        period.
    </p>
    <ul>
        <li><b>Horizontal axis (Month):</b> The date of each monthly
        observation.</li>
        <li><b>Vertical axis (Monthly Sunspot Number):</b> The recorded
        sunspot-number value for that month.</li>
        <li><b>Cyan line:</b> The sequence of monthly observations
        across the selected cycle.</li>
    </ul>
    <p>
        <b>How to interpret it:</b> A rising line indicates increasing
        monthly sunspot activity, while a falling line indicates
        decreasing activity. The broad rise and fall in activity
        illustrate the development of the solar cycle. Individual
        months can fluctuate, so the highest single-month value does
        not necessarily coincide with the official smoothed maximum.
    </p>
    <p>
        <b>Raw monthly peak vs. official smoothed maximum:</b>
        The raw monthly peak is the largest individual monthly value
        in the cycle summary. The official smoothed maximum is a
        smoothed solar-cycle measure reported separately in that
        summary. They are different quantities and may occur at
        different values or dates.
    </p>
</div>
""")

# ============================================================
# MONTHLY OBSERVATION TABLE
# ============================================================

with st.expander("View Monthly Observation Data", expanded=False):
    table_columns = [
        col for col in [
            "month_start",
            "cycle_number",
            "ssn",
            "is_provisional"
        ]
        if col in d.columns
    ]

    monthly_table = d[table_columns].copy()

    if "month_start" in monthly_table.columns:
        monthly_table["month_start"] = (
            pd.to_datetime(monthly_table["month_start"])
            .dt.strftime("%Y-%m")
        )

    monthly_table = monthly_table.rename(columns={
        "month_start": "Month",
        "cycle_number": "Solar Cycle",
        "ssn": "Monthly Sunspot Number",
        "is_provisional": "Provisional Observation"
    })

    st.dataframe(
        monthly_table,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("""
    **Understanding the monthly observation table**

    Each row represents one monthly observation included in the
    selected solar cycle.

    - **Month:** Calendar month associated with the observation.
    - **Solar Cycle:** Cycle number assigned to that observation.
    - **Monthly Sunspot Number:** Processed monthly sunspot-number
      value for that month.
    - **Provisional Observation:** Indicates whether the monthly
      record is marked provisional in the processed dataset.

    Provisional observations may be revised when updated source
    data become available. The table provides the monthly values
    underlying the historical activity chart.
    """)

# ============================================================
# EXPLORATORY ANALOG CURVES — CYCLES 26 AND 27
# ============================================================

st.divider()
st.subheader("Exploratory Analog Curves")
st.caption("Cycles 26 and 27 · Research Exploration")

st.html("""
<div class="custom-alert">
    <p>
        <strong>RESEARCH LIMITATION:</strong>
        These are exploratory analog curves with an empirical
        10th–90th percentile band. They are not validated forecasts
        and should not be interpreted as operational predictions.
    </p>
</div>
""")

try:
    c = data.curves()
except FileNotFoundError as e:
    st.warning(str(e))
else:
    if c.empty:
        st.info("No exploratory analog-curve records are available.")
    else:
        available_cycles = sorted(
            c["future_cycle"].dropna().unique().tolist()
        )

        if not available_cycles:
            st.info("No valid future-cycle identifiers are available.")
        else:
            k = st.radio(
                "Exploratory cycle",
                available_cycles,
                horizontal=True,
                format_func=lambda x: f"Cycle {x}"
            )

            cc = (
                c[c["future_cycle"] == k]
                .sort_values("normalized_phase")
                .copy()
            )

            if cc.empty:
                st.info("No curve data are available for this selection.")
            else:
                base = alt.Chart(cc).encode(
                    x=alt.X(
                        "normalized_phase:Q",
                        title="Normalized Cycle Phase (0 to 1)",
                        scale=alt.Scale(domain=[0, 1]),
                        axis=alt.Axis(
                            labelColor="#CBD5E1",
                            titleColor="#CBD5E1",
                            gridColor="#334155",
                            format=".1f"
                        )
                    )
                )

                band = base.mark_area(
                    opacity=0.28,
                    color="#FFB703"
                ).encode(
                    y=alt.Y(
                        "interval_lower_q10:Q",
                        title="Sunspot Number",
                        axis=alt.Axis(
                            labelColor="#CBD5E1",
                            titleColor="#CBD5E1",
                            gridColor="#334155"
                        )
                    ),
                    y2="interval_upper_q90:Q",
                    tooltip=[
                        alt.Tooltip(
                            "normalized_phase:Q",
                            title="Normalized Phase",
                            format=".2f"
                        ),
                        alt.Tooltip(
                            "interval_lower_q10:Q",
                            title="10th Percentile",
                            format=".2f"
                        ),
                        alt.Tooltip(
                            "interval_upper_q90:Q",
                            title="90th Percentile",
                            format=".2f"
                        )
                    ]
                )

                predicted = base.mark_line(
                    strokeWidth=3,
                    color="#00E5FF"
                ).encode(
                    y=alt.Y(
                        "predicted_curve_ssn:Q",
                        title="Sunspot Number"
                    ),
                    tooltip=[
                        alt.Tooltip(
                            "normalized_phase:Q",
                            title="Normalized Phase",
                            format=".2f"
                        ),
                        alt.Tooltip(
                            "predicted_curve_ssn:Q",
                            title="Analog Curve Value",
                            format=".2f"
                        )
                    ]
                )

                chart_exploratory = (
                    (band + predicted)
                    .properties(
                        height=350,
                        background="transparent"
                    )
                    .interactive()
                )

                st.altair_chart(
                    chart_exploratory,
                    use_container_width=True
                )

                st.html("""
                <div class="explainer-card">
                    <h3>Understanding the Exploratory Analog Curve</h3>
                    <p>
                        This visualization presents an exploratory
                        cycle-shaped curve generated by the repository's
                        analog-method output for the selected cycle.
                        The horizontal axis uses normalized cycle phase
                        rather than calendar dates.
                    </p>
                    <ul>
                        <li><b>Normalized Cycle Phase (0 to 1):</b>
                        Represents relative progress through the
                        cycle, from its beginning (0) to its end (1).</li>
                        <li><b>Cyan line — Analog Curve:</b>
                        The value stored in
                        <code>predicted_curve_ssn</code>, representing
                        the experiment's estimated curve across
                        normalized phase.</li>
                        <li><b>Amber shaded band:</b>
                        The range between the empirical 10th percentile
                        (<code>interval_lower_q10</code>) and 90th
                        percentile (<code>interval_upper_q90</code>)
                        values in the experiment output.</li>
                    </ul>
                    <p>
                        <b>How to interpret the band:</b> It visualizes
                        the spread represented by the empirical
                        10th–90th percentile values. A wider band
                        indicates greater spread among the values
                        represented by the analog experiment at that
                        phase.
                    </p>
                    <p>
                        <b>Important distinction:</b> The shaded region
                        is an empirical range from an exploratory
                        analysis. It should not automatically be called
                        a confidence interval or prediction interval,
                        and it does not establish calibrated
                        uncertainty or guaranteed future coverage.
                    </p>
                </div>
                """)

                # Detailed data supporting the exploratory curve.
                with st.expander("View Exploratory Curve Data", expanded=False):
                    curve_columns = [
                        col for col in [
                            "future_cycle",
                            "normalized_phase",
                            "predicted_curve_ssn",
                            "interval_lower_q10",
                            "interval_upper_q90"
                        ]
                        if col in cc.columns
                    ]

                    curve_table = cc[curve_columns].copy().rename(
                        columns={
                            "future_cycle": "Selected Cycle",
                            "normalized_phase": "Normalized Phase",
                            "predicted_curve_ssn": "Analog Curve Value",
                            "interval_lower_q10": "10th Percentile",
                            "interval_upper_q90": "90th Percentile"
                        }
                    )

                    st.dataframe(
                        curve_table,
                        use_container_width=True,
                        hide_index=True
                    )

                    st.markdown("""
                    **Understanding the exploratory curve table**

                    Each row represents a point along the normalized
                    cycle phase.

                    - **Selected Cycle:** The future cycle identifier
                      associated with this exploratory curve.
                    - **Normalized Phase:** Relative position within
                      the cycle, from 0 to 1.
                    - **Analog Curve Value:** The experiment's
                      estimated sunspot-number value at that phase.
                    - **10th Percentile:** Lower empirical bound
                      recorded for that phase.
                    - **90th Percentile:** Upper empirical bound
                      recorded for that phase.

                    These values describe the exploratory analog
                    output. They are not a validated future forecast.
                    """)

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
