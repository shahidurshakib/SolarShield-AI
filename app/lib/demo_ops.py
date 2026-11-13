"""Demo-only operations content for NASA Space Apps presentation.

This module is deliberately synthetic. It does not use validated space-weather
impact models. Every surface that consumes it must remain labeled as DEMO.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Literal

RiskLevel = Literal["Normal", "Elevated", "High", "Severe"]

# Visual system from the Web App Plan (UI/UX)
RISK_META = {
    "Normal": {"color": "#2A9D8F", "icon": "✓", "order": 0},
    "Elevated": {"color": "#E9C46A", "icon": "▲", "order": 1},
    "High": {"color": "#E76F51", "icon": "!", "order": 2},
    "Severe": {"color": "#B5223B", "icon": "◉", "order": 3},
}

SECTORS = ("LEO drag", "GNSS", "Power grid", "Aviation")


@dataclass
class SectorStatus:
    name: str
    level: RiskLevel
    probability: float  # 0–100 illustrative
    window_hours: int
    summary: str
    freshness_minutes: int


@dataclass
class Driver:
    name: str
    contribution: float  # relative share 0–1
    direction: str


@dataclass
class Alert:
    id: str
    title: str
    sector: str
    level: RiskLevel
    probability: float
    window_start: datetime
    window_end: datetime
    drivers: list[Driver]
    playbook: str
    model_version: str
    data_snapshot: str
    created_at: datetime
    acknowledged: bool = False
    ack_note: str = ""
    ack_at: datetime | None = None


@dataclass
class DemoState:
    scenario_name: str
    overall: RiskLevel
    generated_at: datetime
    sectors: list[SectorStatus]
    alerts: list[Alert]
    disclaimer: str = (
        "DEMO ONLY — illustrative risk states for NASA Space Apps presentation. "
        "Not a validated forecast, not operational guidance, and not derived from "
        "an accepted SolarShield-AI impact model."
    )


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def scenario_quiet() -> DemoState:
    now = _utcnow()
    return DemoState(
        scenario_name="Quiet conditions",
        overall="Normal",
        generated_at=now,
        sectors=[
            SectorStatus("LEO drag", "Normal", 12, 72, "Atmospheric density near seasonal baseline.", 18),
            SectorStatus("GNSS", "Normal", 8, 48, "No elevated TEC anomaly expected in demo window.", 22),
            SectorStatus("Power grid", "Normal", 5, 72, "GIC-proxy activity low in illustrative series.", 25),
            SectorStatus("Aviation", "Normal", 10, 48, "HF/GNSS conditions nominal for planning demo.", 20),
        ],
        alerts=[],
    )


def scenario_elevated_leo() -> DemoState:
    now = _utcnow()
    return DemoState(
        scenario_name="Elevated LEO drag",
        overall="Elevated",
        generated_at=now,
        sectors=[
            SectorStatus(
                "LEO drag",
                "Elevated",
                38,
                72,
                "Illustrative density increase; operators may review orbit maintenance margins.",
                15,
            ),
            SectorStatus("GNSS", "Normal", 14, 48, "Minor scintillation risk only in demo narrative.", 18),
            SectorStatus("Power grid", "Normal", 9, 72, "No elevated GIC-proxy signal in this scenario.", 21),
            SectorStatus("Aviation", "Normal", 11, 48, "Route planning remains unconstrained in demo.", 19),
        ],
        alerts=[
            Alert(
                id="DEMO-ALRT-2026-001",
                title="Elevated thermospheric density outlook (LEO)",
                sector="LEO drag",
                level="Elevated",
                probability=38,
                window_start=now,
                window_end=now + timedelta(hours=72),
                drivers=[
                    Driver("Elevated solar UV / F10.7 proxy", 0.42, "increases density"),
                    Driver("Recent geomagnetic activity (Kp proxy)", 0.31, "contracts recovery time"),
                    Driver("Seasonal baseline offset", 0.27, "modulates amplitude"),
                ],
                playbook=(
                    "**Guidance (demo, not domain-certified)**\n\n"
                    "1. Confirm latest ephemeris and drag model settings for LEO assets.\n"
                    "2. Review conjunction screening cadence for the next 72 hours.\n"
                    "3. Prefer conservative propellant margins for station-keeping burns.\n"
                    "4. Re-check this board after the next data refresh; do not treat this card as a command.\n\n"
                    "Playbook text is illustrative for NASA Space Apps and is labeled as guidance only."
                ),
                model_version="demo-proxy-v0 (not accepted)",
                data_snapshot="SILSO monthly + synthetic drivers @ demo clock",
                created_at=now - timedelta(minutes=12),
            )
        ],
    )


def scenario_high_multi() -> DemoState:
    now = _utcnow()
    return DemoState(
        scenario_name="High multi-sector stress",
        overall="High",
        generated_at=now,
        sectors=[
            SectorStatus("LEO drag", "High", 62, 72, "Strong illustrative density enhancement.", 12),
            SectorStatus("GNSS", "Elevated", 41, 48, "Demo TEC anomaly band over mid-latitudes.", 14),
            SectorStatus("Power grid", "Elevated", 35, 72, "Elevated GIC-proxy narrative for regional grids.", 16),
            SectorStatus("Aviation", "Elevated", 33, 48, "Possible HF degradation on polar routes (demo).", 15),
        ],
        alerts=[
            Alert(
                id="DEMO-ALRT-2026-002",
                title="High LEO drag and elevated GNSS conditions",
                sector="LEO drag",
                level="High",
                probability=62,
                window_start=now,
                window_end=now + timedelta(hours=72),
                drivers=[
                    Driver("Southward IMF Bz proxy", 0.36, "drives coupling"),
                    Driver("High solar wind speed proxy", 0.34, "sustains activity"),
                    Driver("Prior storm recovery incomplete", 0.30, "raises baseline"),
                ],
                playbook=(
                    "**Guidance (demo, not domain-certified)**\n\n"
                    "1. Elevate on-call awareness for LEO constellation operators.\n"
                    "2. Increase GNSS integrity monitoring for precision users.\n"
                    "3. Share status page with grid and aviation liaisons if integrated.\n"
                    "4. Acknowledge this alert in the board to record shift awareness.\n\n"
                    "This is a presentation scenario only."
                ),
                model_version="demo-proxy-v0 (not accepted)",
                data_snapshot="synthetic multi-driver bundle @ demo clock",
                created_at=now - timedelta(minutes=6),
            ),
            Alert(
                id="DEMO-ALRT-2026-003",
                title="Elevated GNSS TEC anomaly (demo)",
                sector="GNSS",
                level="Elevated",
                probability=41,
                window_start=now,
                window_end=now + timedelta(hours=48),
                drivers=[
                    Driver("Ionospheric storm proxy", 0.55, "raises TEC variance"),
                    Driver("Local time / latitude band", 0.45, "concentrates impact"),
                ],
                playbook=(
                    "**Guidance (demo)**\n\n"
                    "1. Prefer dual-frequency / multi-constellation solutions where available.\n"
                    "2. Widen protection levels for safety-of-life demos only as a narrative step.\n"
                    "3. Re-evaluate after the 48-hour window closes.\n"
                ),
                model_version="demo-proxy-v0 (not accepted)",
                data_snapshot="synthetic TEC bundle @ demo clock",
                created_at=now - timedelta(minutes=4),
            ),
        ],
    )


SCENARIOS = {
    "Quiet conditions": scenario_quiet,
    "Elevated LEO drag": scenario_elevated_leo,
    "High multi-sector stress": scenario_high_multi,
}


def build_state(name: str) -> DemoState:
    fn = SCENARIOS.get(name, scenario_elevated_leo)
    return fn()
