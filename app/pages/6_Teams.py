import streamlit as st
import base64
import os

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(page_title="Team · SolarShield-AI", layout="wide", page_icon="☀")

# ============================================================
# HELPER FUNCTION FOR IMAGES
# ============================================================

def get_base64_image(image_path):
    """Reads an image and converts it to base64 so it displays in raw HTML."""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        # Returns a blank 1x1 pixel if the image is missing
        return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

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

/* TEAM GRID */
.team-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 24px;
    margin-top: 24px;
    margin-bottom: 40px;
}
.team-card {
    background: linear-gradient(135deg, var(--card-bg-2) 0%, var(--card-bg-1) 100%);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
    transition: transform 0.2s ease, border-color 0.2s ease;
    align-items: center; /* Center everything in the card */
    text-align: center;  /* Center the text */
}
.team-card:hover {
    transform: translateY(-4px);
    border-color: var(--cyan);
}

/* Profile Image Styling */
.team-img {
    width: 110px;
    height: 110px;
    border-radius: 50%;
    object-fit: cover;
    border: 3px solid var(--border);
    margin-bottom: 16px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.4);
    transition: border-color 0.3s ease;
    background-color: var(--bg); /* Fallback for transparent images */
}
.team-card:hover .team-img {
    border-color: var(--cyan);
}

.team-name { color: var(--heading); font-size: 1.3rem; font-weight: 800; margin-bottom: 4px; }
.team-role { color: var(--cyan); font-size: 0.85rem; font-family: var(--font-mono); font-weight: 600; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 1px; }
.team-bio { color: var(--subheading); font-size: 0.95rem; line-height: 1.6; flex-grow: 1; text-align: left; }
.team-email { 
    color: var(--amber); 
    font-size: 0.85rem; 
    font-family: var(--font-mono);
    margin-top: 16px; 
    padding-top: 12px;
    border-top: 1px solid rgba(255,255,255,0.1);
    display: block;
    text-decoration: none;
    width: 100%;
    text-align: center;
}
.team-email:hover {
    color: #FFFFFF;
}

/* SECTION HEADERS */
.section-header {
    color: var(--heading);
    font-size: 1.5rem;
    font-weight: 800;
    margin-top: 40px;
    margin-bottom: 10px;
    border-bottom: 2px solid var(--border);
    padding-bottom: 10px;
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

st.title("Meet the Team")
st.markdown("""
<p style="color: var(--subheading); font-size: 1.1rem; margin-bottom: 2rem;">
The passionate individuals behind SolarShield-AI, bridging technology and space weather science.
</p>
""", unsafe_allow_html=True)

# IMPORTANT: Notice the paths start with "assets/" and NOT "/assets/". 
# If your python script is in the "app" folder, you might need "../assets/" instead.
team_members = [
    {
        "name": "Shahidur Rahman Shakib",
        "role": "AI Model Architect & Lead Researcher",
        "bio": "Shahidur is a CSE student at Metropolitan University, researcher, designer, web developer, and ML Engineer. As *AI Model Architect & Lead Researcher* of SolarShield-AI, he independently architected and developed the entire AI model pipeline, leading its research and development from data ingestion to predictive modeling for NASA Space Apps Challenge 2026. He is passionate about AI innovation, scientific exploration, and building technology-driven solutions through interdisciplinary research and creative problem-solving.",
        "email": "shahidurrahmanshakib15@gmail.com",
        "image": "assets/shahidur.jpg"  
    },
    {
        "name": "G.M. Sifat Iqbal",
        "role": "Data Scientist & Researcher",
        "bio": "Sifat is a data scientist with expertise in satellite data processing and climate modeling. He focuses on turning raw datasets into actionable insights, ensuring the platform remains scientifically rigorous and accessible. His work helps bridge the gap between global climate drivers and local realities.",
        "email": "gaziiqbal001@gmail.com",
        "image": "assets/sifat.jpg"  
    },
    {
        "name": "Anika Tabassum",
        "role": "Frontend Developer & Researcher",
        "bio": "Anika is a frontend developer and researcher with expertise in the MERN stack, Python, C, and C++. With a degree in CSE and currently pursuing an MBA, she combines technical skills with strategic thinking. Recently, Anika published a research paper on depression detection. At our platform, Anika focuses on building interactive user experiences and ensuring complex data is transformed into accessible insights.",
        "email": "at621504@gmail.com",
        "image": "assets/anika.jpg"  
    },
    {
        "name": "Sabira Begum",
        "role": "Multimedia Editor & Researcher",
        "bio": "Sabira is a multimedia editor and researcher with a strong academic foundation in Software Engineering. Her technical background brings a sharp, analytical lens to her creative and investigative work, ensuring structural precision and thoughtful execution. By blending thorough research with compelling visual storytelling, she crafts clear, high-impact narratives and delivers engaging presentations.",
        "email": "sabirabegum827@gmail.com",
        "image": "assets/Sabira.jpg"  
    }
]

# Build the Team HTML
team_html = '<div class="team-grid">'
for member in team_members:
    # Read the image and convert to base64 string
    b64_img = get_base64_image(member["image"])
    img_src = f"data:image/jpeg;base64,{b64_img}" if b64_img else ""
    
    img_html = f'<img src="{img_src}" class="team-img" alt="{member["name"]}">'
    email_html = f'<a href="mailto:{member["email"]}" class="team-email">📩 {member["email"]}</a>' if member["email"] else ""
    
    team_html += f"""
    <div class="team-card">
        {img_html}
        <div class="team-name">{member['name']}</div>
        <div class="team-role">{member['role']}</div>
        <div class="team-bio">{member['bio']}</div>
        {email_html}
    </div>
    """
team_html += '</div>'

st.html(team_html)

# ============================================================
# GET IN TOUCH SECTION
# ============================================================

st.html("""
<div class="section-header">Get In Touch</div>
<p style="color: var(--body); font-size: 1.05rem; margin-bottom: 24px;">
    For collaborations, partnerships, research inquiries, or to learn more about our work.
</p>

<div class="team-grid">
    <div class="team-card" style="align-items: center; text-align: center;">
        <h4 style="color: var(--cyan); margin-bottom: 12px; font-family: var(--font-mono);">Research Collaborations</h4>
        <p style="color: var(--subheading); font-size: 0.95rem;">Partner with us on space weather data analysis and visualization projects.</p>
    </div>
    
    <div class="team-card" style="align-items: center; text-align: center;">
        <h4 style="color: var(--cyan); margin-bottom: 12px; font-family: var(--font-mono);">Technical Partnerships</h4>
        <p style="color: var(--subheading); font-size: 0.95rem;">Integrate our data and tools into your platforms and applications.</p>
    </div>
    
    <div class="team-card" style="align-items: center; text-align: center;">
        <h4 style="color: var(--cyan); margin-bottom: 12px; font-family: var(--font-mono);">Educational Outreach</h4>
        <p style="color: var(--subheading); font-size: 0.95rem;">Use our platform for educational purposes and space weather awareness.</p>
    </div>
</div>

<div style="text-align: center; margin-top: 30px;">
    <p style="color: var(--muted); font-family: var(--font-mono);">📩 Contact us via the individual team member emails above.</p>
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
