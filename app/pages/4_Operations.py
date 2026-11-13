"""Operations board — demo risk status, alerts, playbooks, acknowledgement."""
from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

from lib import data
from lib.demo_ops import SCENARIOS, RISK_META, build_state
from lib.ui import demo_banner, risk_badge

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(page_title="Operations · SolarShield-AI", layout="wide", page_icon="☀")

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
.main .block-container { max-width: 1500px; padding-top: 2rem; padding-bottom: 120px; }

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

/* SECTOR GRID */
.sector-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
    margin-bottom: 30px;
    width: 100%;
}
.sector-card {
    background: linear-gradient(135deg, var(--card-bg-2) 0%, var(--card-bg-1) 100%);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.25rem;
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
}
.sector-name { color: var(--heading); font-size: 1rem; font-weight: 700; margin-bottom: 8px; }
.sector-prob { color: var(--cyan); font-size: 2rem; font-weight: 800; margin-top: 10px; line-height: 1; }
.sector-summary { color: var(--subheading); font-size: 0.85rem; margin-top: 8px; line-height: 1.4; flex-grow: 1; }
.sector-footer { color: var(--muted); font-size: 0.75rem; font-family: var(--font-mono); margin-top: 12px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.1); }

/* TOP STATUS BAND */
.status-band {
    background: linear-gradient(135deg, #1E3A8A 0%, #0F172A 100%);
    border: 1px solid #3B82F6;
    border-radius: 16px;
    padding: 1.25rem 1.5rem;
    margin: 1rem 0 2rem 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
    box-shadow: 0 8px 30px rgba(59, 130, 246, 0.2);
}
.status-band-title { color: var(--muted); font-size: 0.8rem; font-family: var(--font-mono); letter-spacing: 1px; }
.status-band-level { color: #FFFFFF; font-size: 1.6rem; font-weight: 800; margin-top: 4px; }
.status-band-sub { color: #93C5FD; font-size: 0.9rem; margin-top: 4px; }
.status-band-meta { text-align: right; color: #BFDBFE; font-size: 0.85rem; font-family: var(--font-mono); line-height: 1.6; }

/* EXPANDER FIX */
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
[data-testid="stExpander"] details[open] {
    background-color: var(--card-bg-1) !important;
    color: var(--body) !important;
}
[data-testid="stExpander"] details[open] * {
    color: var(--body) !important;
}

/* CUSTOM TRACEABILITY BLOCK */
.trace-block {
    background-color: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem;
    font-family: var(--font-mono);
    font-size: 0.85rem;
    color: var(--cyan);
    white-space: pre-wrap;
    line-height: 1.5;
}

/* FOOTER (Synced with Home) */
.custom-footer {
    position: fixed; bottom: 0; left: 0; width: 100%;
    background: rgba(10, 17, 32, 0.95); border-top: 1px solid var(--border);
    padding: 12px 2rem; text-align: center; z-index: 9999;
}
.footer-link { color: var(--cyan) !important; text-decoration: none !important; }
.footer-copyright { color: var(--muted) !important; font-size: 0.75rem; }

/* RESPONSIVE */
@media (max-width: 1100px) {
    .sector-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 600px) {
    .sector-grid { grid-template-columns: 1fr; }
    .status-band { flex-direction: column; align-items: flex-start; }
    .status-band-meta { text-align: left; }
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# PAGE CONTENT
# ============================================================

st.title("Operations board")
st.caption("Live-style status for LEO drag, GNSS, power grid, and aviation — presentation demo.")
demo_banner()

# --- scenario controls ---
if "ops_scenario" not in st.session_state:
    st.session_state.ops_scenario = "Elevated LEO drag"
if "ops_ack" not in st.session_state:
    st.session_state.ops_ack = {}  # alert_id -> {note, at}

col_sc, col_info = st.columns([2, 3])
with col_sc:
    scenario = st.selectbox(
        "Demo scenario",
        list(SCENARIOS.keys()),
        index=list(SCENARIOS.keys()).index(st.session_state.ops_scenario)
        if st.session_state.ops_scenario in SCENARIOS
        else 1,
    )
    st.session_state.ops_scenario = scenario

state = build_state(scenario)

# merge acknowledgements from session
for alert in state.alerts:
    if alert.id in st.session_state.ops_ack:
        alert.acknowledged = True
        alert.ack_note = st.session_state.ops_ack[alert.id].get("note", "")
        alert.ack_at = st.session_state.ops_ack[alert.id].get("at")

with col_info:
    try:
        accept, freeze = data.model_status()
        st.markdown(
            f"**Research model status:** scientific acceptance **{accept}** · "
            f"accepted freeze **{freeze}** · demo board is independent of model freeze."
        )
    except Exception:
        st.markdown("**Research model status:** unavailable in this checkout.")

# --- top status band ---
meta = RISK_META[state.overall]
open_alerts = sum(1 for a in state.alerts if not a.acknowledged)
total_alerts = len(state.alerts)

st.html(f"""
<div class="status-band">
    <div>
        <div class="status-band-title">OVERALL DEMO STATUS</div>
        <div class="status-band-level">{meta['icon']} {state.overall}</div>
        <div class="status-band-sub">Scenario: {state.scenario_name}</div>
    </div>
    <div class="status-band-meta">
        <div>Board clock (UTC): {state.generated_at.strftime('%Y-%m-%d %H:%M')}</div>
        <div>Active demo alerts: {open_alerts} open / {total_alerts} total</div>
    </div>
</div>
""")

# --- sector cards ---
st.subheader("Sector risk (demo)")

sector_html = '<div class="sector-grid">'
for sector in state.sectors:
    m = RISK_META[sector.level]
    badge_html = risk_badge(sector.level)
    
    sector_html += f"""
    <div class="sector-card">
        <div class="sector-name">{sector.name}</div>
        <div>{badge_html}</div>
        <div class="sector-prob">{sector.probability:.0f}%</div>
        <div class="sector-summary">{sector.summary}</div>
        <div class="sector-footer">
            illustrative · {sector.window_hours}h window<br>
            Data age (demo): {sector.freshness_minutes} min
        </div>
    </div>
    """
sector_html += '</div>'
st.html(sector_html)


# --- alerts ---
st.subheader("Active alerts")
if not state.alerts:
    st.success("No active demo alerts in this scenario.")
else:
    for alert in state.alerts:
        open_label = "Acknowledged" if alert.acknowledged else "Open"
        with st.expander(
            f"{alert.level} · {alert.title} · {open_label}",
            expanded=not alert.acknowledged,
        ):
            left, right = st.columns([2, 1])
            with left:
                st.html(risk_badge(alert.level))
                st.write(
                    f"**Sector:** {alert.sector} · **Probability (demo):** {alert.probability:.0f}%  \n"
                    f"**Window:** {alert.window_start.strftime('%Y-%m-%d %H:%M')} → "
                    f"{alert.window_end.strftime('%Y-%m-%d %H:%M')} UTC"
                )
                st.markdown("**Top drivers (illustrative)**")
                for d in alert.drivers:
                    st.progress(min(max(d.contribution, 0.0), 1.0), text=f"{d.name} — {d.direction} ({d.contribution:.0%})")
                st.markdown("**Playbook**")
                st.markdown(alert.playbook)
            with right:
                st.markdown("**Traceability**")
                
                # Replaced st.code with pure HTML
                trace_text = (
                    f"Alert ID: {alert.id}\n"
                    f"Model: {alert.model_version}\n"
                    f"Snapshot: {alert.data_snapshot}\n"
                    f"Created: {alert.created_at.isoformat()}"
                )
                st.html(f'<div class="trace-block">{trace_text}</div>')
                
                if alert.acknowledged:
                    st.success(
                        f"Acknowledged at {alert.ack_at.strftime('%Y-%m-%d %H:%M UTC') if alert.ack_at else '—'}"
                    )
                    if alert.ack_note:
                        st.caption(f"Note: {alert.ack_note}")
                else:
                    note = st.text_input(
                        "Optional shift note",
                        key=f"note_{alert.id}",
                        placeholder="e.g. reviewed by on-call",
                    )
                    if st.button("Acknowledge alert", key=f"ack_{alert.id}", type="primary"):
                        st.session_state.ops_ack[alert.id] = {
                            "note": note.strip(),
                            "at": datetime.now(timezone.utc).replace(microsecond=0),
                        }
                        st.rerun()

# --- audit trail ---
st.subheader("Acknowledgement log (this session)")
if not st.session_state.ops_ack:
    st.caption("No acknowledgements yet. Open an alert and confirm to record shift awareness.")
else:
    rows = []
    for aid, payload in st.session_state.ops_ack.items():
        at = payload.get("at")
        rows.append(
            {
                "alert_id": aid,
                "acknowledged_at_utc": at.isoformat() if at else "",
                "note": payload.get("note", ""),
            }
        )
    st.dataframe(rows, use_container_width=True, hide_index=True)

# --- BOTTOM DISCLAIMER (Matches custom styling) ---
st.html(f'<div class="custom-alert"><p>{state.disclaimer}</p></div>')

# --- FOOTER (Synced with Home) ---
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
