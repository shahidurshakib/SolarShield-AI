"""Shared UI helpers for the SolarShield-AI Streamlit demo."""
from __future__ import annotations

import streamlit as st

GITHUB_URL = "https://github.com/shahidurshakib/SolarShield-AI"
COPYRIGHT = "Copyright © 2026 Team MU Solar Pulse. All Rights Reserved."

from lib.demo_ops import RISK_META, RiskLevel


def risk_badge(level: RiskLevel) -> str:
    meta = RISK_META[level]
    return f"<span style='display:inline-block;padding:0.2rem 0.55rem;border-radius:999px;background:{meta['color']};color:#111;font-weight:600;font-size:0.85rem;'>{meta['icon']} {level}</span>"


def footer() -> None:
    st.markdown("---")
    st.markdown(
        f"""
<div style="text-align:center;color:#5a6570;font-size:0.85rem;line-height:1.6;padding:0.5rem 0 1rem 0;">
  <div><strong>SolarShield-AI</strong> · Team MU Solar Pulse · NASA Space Apps Challenge 2026</div>
  <div><a href="{GITHUB_URL}" target="_blank" rel="noopener noreferrer">{GITHUB_URL}</a></div>
  <div>{COPYRIGHT}</div>

</div>
""",
        unsafe_allow_html=True,
    )


def demo_banner(text: str | None = None) -> None:
    st.warning(
        text
        or (
            "**DEMO MODE** — Illustrative risk states for NASA Space Apps. "
            "Not validated impact forecasts. Not operational guidance."
        )
    )
