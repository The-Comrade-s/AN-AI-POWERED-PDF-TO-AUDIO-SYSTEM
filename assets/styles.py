"""
Centralized CSS injection for the premium SaaS look:
dark theme, glassmorphism cards, purple gradient accents.
"""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Poppins:wght@600;700&display=swap');

:root {
    --bg-primary: #0d0b1a;
    --bg-secondary: #14112a;
    --bg-card: rgba(255, 255, 255, 0.045);
    --border-glass: rgba(255, 255, 255, 0.08);
    --purple-1: #7c3aed;
    --purple-2: #a855f7;
    --purple-3: #c084fc;
    --text-primary: #f1f0f7;
    --text-secondary: #9d97b8;
    --success: #22c55e;
    --danger: #ef4444;
    --warning: #f59e0b;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    color: var(--text-primary);
}

.stApp {
    background: radial-gradient(circle at 15% 0%, #1c1436 0%, #0d0b1a 45%, #0a0815 100%);
}

#MainMenu, header, footer {visibility: hidden;}

/* ---------- Typography ---------- */
h1, h2, h3 {
    font-family: 'Poppins', sans-serif;
    letter-spacing: -0.02em;
}

.gradient-text {
    background: linear-gradient(135deg, var(--purple-2), var(--purple-3));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* ---------- Glass Card ---------- */
.glass-card {
    background: var(--bg-card);
    border: 1px solid var(--border-glass);
    border-radius: 18px;
    padding: 22px 24px;
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.glass-card:hover {
    transform: translateY(-2px);
    border-color: rgba(168, 85, 247, 0.35);
    box-shadow: 0 12px 40px rgba(124, 58, 237, 0.18);
}

/* ---------- Stat Card ---------- */
.stat-card {
    background: var(--bg-card);
    border: 1px solid var(--border-glass);
    border-radius: 16px;
    padding: 18px 20px;
    backdrop-filter: blur(16px);
}

.stat-icon {
    width: 40px;
    height: 40px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    margin-bottom: 10px;
}

.stat-value {
    font-size: 26px;
    font-weight: 700;
    font-family: 'Poppins', sans-serif;
    margin: 2px 0 0 0;
}

.stat-label {
    font-size: 13px;
    color: var(--text-secondary);
    margin: 0;
}

.stat-delta {
    font-size: 12px;
    color: var(--success);
    margin-top: 4px;
}

/* ---------- Buttons ---------- */
.stButton > button {
    background: linear-gradient(135deg, var(--purple-1), var(--purple-2));
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.55rem 1.3rem;
    font-weight: 600;
    font-size: 14px;
    transition: all 0.2s ease;
    box-shadow: 0 4px 14px rgba(124, 58, 237, 0.35);
}

.stButton > button:hover {
    box-shadow: 0 6px 20px rgba(124, 58, 237, 0.55);
    transform: translateY(-1px);
}

.stButton > button:active {
    transform: translateY(0px);
}

/* Secondary / ghost button variant via data-testid workaround */
button[kind="secondary"] {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid var(--border-glass) !important;
    box-shadow: none !important;
}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #120f24 0%, #0c0a1a 100%);
    border-right: 1px solid var(--border-glass);
}

section[data-testid="stSidebar"] .stButton > button {
    background: transparent;
    box-shadow: none;
    color: var(--text-secondary);
    text-align: left;
    justify-content: flex-start;
    width: 100%;
    font-weight: 500;
    border-radius: 10px;
    padding: 0.5rem 0.8rem;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(168, 85, 247, 0.12);
    color: var(--text-primary);
    transform: none;
}

.sidebar-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 6px 4px 18px 4px;
    font-family: 'Poppins', sans-serif;
    font-weight: 700;
    font-size: 17px;
}

.sidebar-nav-active {
    background: linear-gradient(135deg, rgba(124,58,237,0.35), rgba(168,85,247,0.2));
    border-radius: 10px;
    padding: 0.5rem 0.8rem;
    color: var(--text-primary) !important;
    font-weight: 600;
    border-left: 3px solid var(--purple-2);
    margin-bottom: 2px;
}

/* ---------- Inputs ---------- */
.stTextInput > div > div > input,
.stTextArea textarea,
.stSelectbox > div > div,
.stNumberInput input {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid var(--border-glass) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
}

/* ---------- Progress Bar ---------- */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, var(--purple-1), var(--purple-3));
}

/* ---------- Badge ---------- */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
}
.badge-success { background: rgba(34,197,94,0.15); color: var(--success); }
.badge-warning { background: rgba(245,158,11,0.15); color: var(--warning); }
.badge-purple { background: rgba(168,85,247,0.15); color: var(--purple-3); }

/* ---------- Library / File Row Card ---------- */
.file-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 16px;
    border-radius: 14px;
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--border-glass);
    margin-bottom: 8px;
    transition: background 0.2s ease;
}
.file-row:hover {
    background: rgba(255,255,255,0.06);
}

/* ---------- Now Playing Widget ---------- */
.now-playing-card {
    background: linear-gradient(160deg, rgba(124,58,237,0.18), rgba(20,17,42,0.6));
    border: 1px solid rgba(168,85,247,0.25);
    border-radius: 20px;
    padding: 20px;
    backdrop-filter: blur(20px);
}

.album-art {
    width: 100%;
    aspect-ratio: 1;
    border-radius: 14px;
    background: linear-gradient(135deg, #4c1d95, #7c3aed, #c026d3);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 40px;
    margin-bottom: 14px;
}

/* ---------- Divider ---------- */
.soft-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border-glass), transparent);
    margin: 18px 0;
}

/* ---------- Auth Page ---------- */
.auth-wrapper {
    max-width: 420px;
    margin: 40px auto;
    padding: 36px 32px;
    background: var(--bg-card);
    border: 1px solid var(--border-glass);
    border-radius: 22px;
    backdrop-filter: blur(20px);
    box-shadow: 0 20px 60px rgba(0,0,0,0.4);
}

.auth-logo {
    text-align: center;
    font-family: 'Poppins', sans-serif;
    font-weight: 800;
    font-size: 26px;
    margin-bottom: 6px;
}

.auth-subtitle {
    text-align: center;
    color: var(--text-secondary);
    font-size: 14px;
    margin-bottom: 26px;
}

/* Scrollbar */
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(168,85,247,0.35); border-radius: 10px; }
</style>
"""


def inject_css(st):
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
