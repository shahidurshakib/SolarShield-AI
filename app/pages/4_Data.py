import streamlit as st
from lib import data

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(page_title="Data · SolarShield-AI", layout="centered", page_icon="☀")

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

/* CODE BLOCKS (Citation) */
.stCode, code {
    background-color: var(--card-bg-1) !important;
    color: var(--cyan) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}

/* DOWNLOAD BUTTONS */
.stDownloadButton > button {
    background: var(--card-bg-2) !important;
    color: var(--cyan) !important;
    border: 1px solid var(--cyan) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease;
    width: 100%;
}
.stDownloadButton > button:hover {
    background: var(--cyan) !important;
    color: var(--bg) !important;
    box-shadow: 0 4px 15px rgba(0, 229, 255, 0.4);
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

st.title("Data downloads")
st.caption("Cite the source when you use these files.")

# Displaying the citation using the styled code block
st.code(data.CITATION, language=None)

st.write("") # Spacer

for label, key in [
    ("Monthly sunspot number, 1749 to present", "monthly"),
    ("Solar cycle summary", "cycles"),
    ("Baseline backtest predictions", "backtest"),
]:
    p = data.P[key]
    if not p.exists():
        st.warning(f"Missing file for {label}: {p.name}")
        continue
    
    # Spacer between buttons
    st.download_button(
        f"Download {label} (CSV)",
        p.read_bytes(),
        file_name=p.name,
        mime="text/csv",
        key=key,
    )
    st.markdown("<br>", unsafe_allow_html=True)

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