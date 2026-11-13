import streamlit as st

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(page_title="Data Governance · SolarShield-AI", layout="wide", page_icon="🗄️")

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
.stMarkdown a { color: var(--cyan) !important; text-decoration: none; }
.stMarkdown a:hover { color: var(--amber) !important; }

/* SIDEBAR */
[data-testid="stSidebar"] { background: var(--sidebar) !important; border-right: 1px solid var(--border) !important; }
[data-testid="stSidebar"] * { color: #F1F5F9 !important; }

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
.data-card {
    background: linear-gradient(135deg, var(--card-bg-2) 0%, var(--card-bg-1) 100%);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.8rem;
    margin-bottom: 24px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.data-card:hover {
    transform: translateY(-3px);
    border-color: var(--cyan);
}
.card-title {
    color: var(--heading);
    font-size: 1.3rem;
    font-weight: 700;
    margin-bottom: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;
}
.card-text {
    color: var(--body);
    font-size: 1rem;
    line-height: 1.6;
}
.data-list {
    list-style-type: none;
    padding-left: 0;
    margin: 0;
}
.data-list li {
    color: var(--subheading);
    font-size: 0.95rem;
    line-height: 1.5;
    margin-bottom: 10px;
    padding-left: 20px;
    position: relative;
}
.data-list li::before {
    content: "▹";
    color: var(--amber);
    position: absolute;
    left: 0;
    top: 0;
    font-weight: bold;
}

/* STATUS BADGES */
.status-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-family: var(--font-mono);
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
.status-primary { background: rgba(16, 185, 129, 0.15); color: #10B981; border: 1px solid #10B981; }
.status-exploratory { background: rgba(0, 229, 255, 0.15); color: #00E5FF; border: 1px solid #00E5FF; }
.status-candidate { background: rgba(255, 183, 3, 0.15); color: #FFB703; border: 1px solid #FFB703; }
.status-unverified { background: rgba(239, 68, 68, 0.15); color: #EF4444; border: 1px solid #EF4444; }

/* GOVERNANCE GRID */
.gov-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
}
.gov-card {
    background: var(--card-bg-1);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
}
.gov-title {
    color: var(--cyan);
    font-family: var(--font-mono);
    font-weight: 700;
    font-size: 1.1rem;
    margin-bottom: 12px;
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

st.title("Data Sources & Governance")
st.caption("Principal datasets, intended roles, known processing activities, and integration status.")
st.markdown("<br>", unsafe_allow_html=True)

# 1. Primary Dataset
st.html("""
<div class="section-header">Primary Dataset</div>
<div class="data-card">
    <div class="card-title">
        WDC-SILSO International Sunspot Number
        <span class="status-badge status-primary">Primary / Used</span>
    </div>
    <div class="card-text">
        <p><strong>Provider:</strong> World Data Center SILSO, Royal Observatory of Belgium</p>
        <p><strong>Role:</strong> The SILSO monthly sunspot-number series is the primary historical dataset used for SolarShield-AI's solar-cycle characterization and forecasting research.</p>
        <p><strong>Coverage:</strong> Jan 1749 – Sep 2026 (3,333 records, Version 2.0). Completed cycles 1–24, ongoing cycle 25.</p>
        <p><strong>Links:</strong> <a href="https://www.sidc.be/SILSO/datafiles" target="_blank">Download Data</a> | <a href="https://www.sidc.be/SILSO/infosnmtot" target="_blank">Dataset Info</a></p>
    </div>
</div>
""")

# 2. SDO / HMI
st.html("""
<div class="data-card">
    <div class="card-title">
        Solar Dynamics Observatory — HMI
        <span class="status-badge status-exploratory">Exploratory</span>
    </div>
    <div class="card-text">
        <p><strong>Mission:</strong> NASA SDO | <strong>Instrument:</strong> Helioseismic and Magnetic Imager (HMI)</p>
        <p><strong>Candidate Products:</strong></p>
        <ul class="data-list">
            <li><strong>hmi.M_720s:</strong> Line-of-sight magnetogram data (720s cadence).</li>
            <li><strong>hmi.sharp_cea_720s:</strong> Space-weather HMI Active Region Patch (SHARP) measurements.</li>
        </ul>
        <p style="margin-top: 10px;"><strong>Status:</strong> 9 FITS files exported for testing; 219,686 rows in HARP CSV. Not yet integrated into the main pipeline.</p>
    </div>
</div>
""")

# 3. NASA OMNI
st.html("""
<div class="data-card">
    <div class="card-title">
        NASA OMNI Solar-Wind and Geomagnetic Data
        <span class="status-badge status-candidate">Candidate</span>
    </div>
    <div class="card-text">
        <p><strong>Provider:</strong> NASA Space Physics Data Facility</p>
        <p><strong>Role:</strong> To support the future connection between solar activity and near-Earth space-weather conditions.</p>
        <p><strong>Candidate Variables:</strong> Solar-wind speed, density, IMF Bz, Kp, Dst, AE/AU/AL indices, F10.7.</p>
        <p><strong>Status:</strong> Identified for future development, not yet integrated into completed V2/V3 model experiments.</p>
    </div>
</div>
""")

# 4. Historical Sunspot-Group Records
st.html("""
<div class="data-card">
    <div class="card-title">
        Historical Sunspot-Group Records
        <span class="status-badge status-exploratory">Exploratory</span>
    </div>
    <div class="card-text">
        <p><strong>Audit Record:</strong> Coverage 1874–2025, 152 files, 257,852 records. Schema changes identified in 1977 and 1982.</p>
        <p><strong>Status:</strong> Audited and investigated, but not established as an integrated model input. Complete download provenance must be recovered before it can be treated as a reproducible dependency.</p>
    </div>
</div>
""")

# 5. Candidate Event Data
st.html("""
<div class="section-header">Candidate Event Data</div>
<div class="data-card">
    <div class="card-title">Future Space-Weather Modeling</div>
    <div class="card-text">
        <p>The following data categories are relevant to the long-term architecture and are currently classified as <strong>Candidates</strong>:</p>
        <ul class="data-list">
            <li><strong>Solar Flares:</strong> Class, peak time, duration.</li>
            <li><strong>Coronal Mass Ejections (CMEs):</strong> Speed, direction, angular width.</li>
            <li><strong>Solar Energetic Particles (SEPs):</strong> Particle flux and energy channels.</li>
            <li><strong>Solar Wind:</strong> Speed, density, temperature.</li>
            <li><strong>Interplanetary Magnetic Field (IMF):</strong> Bz and total field.</li>
            <li><strong>Geomagnetic Indices:</strong> Kp, Dst, AE.</li>
            <li><strong>Radio Flux:</strong> F10.7.</li>
        </ul>
    </div>
</div>
""")

# 6. Data Governance Principles (Grid)
st.html("""
<div class="section-header">Data Governance Principles</div>
<div class="gov-grid">
    <div class="gov-card">
        <div class="gov-title">1. Source Traceability</div>
        <ul class="data-list">
            <li>Provider name and official URL</li>
            <li>Dataset/product identifier</li>
            <li>Retrieval timestamp</li>
            <li>Coverage period and version</li>
            <li>File-level integrity hashes</li>
            <li>Processing/transformation records</li>
        </ul>
    </div>
    <div class="gov-card">
        <div class="gov-title">2. Temporal Integrity</div>
        <ul class="data-list">
            <li>Training data must precede evaluation</li>
            <li>No future leakage into features</li>
            <li>Explicit temporal alignment</li>
            <li>Documented resampling/aggregation</li>
            <li>Preserved forecast origins/horizons</li>
        </ul>
    </div>
    <div class="gov-card">
        <div class="gov-title">3. Quality Control</div>
        <ul class="data-list">
            <li>Handling missing observations</li>
            <li>Flagging provisional values</li>
            <li>Removing duplicate timestamps</li>
            <li>Filtering invalid records</li>
            <li>Tracking source schema changes</li>
        </ul>
    </div>
    <div class="gov-card">
        <div class="gov-title">4. Data Versioning</div>
        <ul class="data-list">
            <li>No silent replacement of frozen inputs</li>
            <li>Separate manifests for new snapshots</li>
            <li>Integrity checks on all updates</li>
            <li>Historical data preserved unchanged</li>
        </ul>
    </div>
</div>
""")

# 8. Scientific Limitations
st.html("""
<div class="section-header">Scientific Limitations</div>
<div class="data-card" style="border-color: rgba(255, 183, 3, 0.4);">
    <div class="card-title" style="color: var(--amber);">🛡️ Critical Distinction</div>
    <div class="card-text">
        <p><strong>A solar-activity forecast is not automatically an Earth-impact forecast.</strong></p>
        <p>A scientifically defensible system must <em>separately</em> validate:</p>
        <ol style="color: var(--subheading); line-height: 1.8; margin-left: 20px;">
            <li>Solar activity forecasting.</li>
            <li>Space-weather condition estimation.</li>
            <li>Near-Earth response modeling.</li>
            <li>Sector-specific risk estimation.</li>
            <li>Alert thresholds and uncertainty.</li>
            <li>Operational warning performance.</li>
        </ol>
        <p style="margin-top: 15px; font-style: italic; color: var(--cyan);">
            Documentation principle: Every data source must be traceable, every transformation reproducible, and every integration claim supported by evidence.
        </p>
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
