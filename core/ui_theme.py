"""Custom UI theme system for Statement-to-Insights.

Supports both Dark and Light modes dynamically using CSS variables,
providing a non-conventional, ultra-modern neo-glassmorphism aesthetic.
"""


CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg: #0B100D;
    --surface: #141C17;
    --surface-2: #1B2720;
    --accent: #65D6A0;
    --accent-soft: #A5C7A4;
    --text: #ECF3EE;
    --muted: #89978E;
    --border: rgba(165, 199, 164, 0.12);
}

/* Global */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(ellipse at 15% 0%, rgba(55, 120, 81, .13), transparent 38%),
        radial-gradient(ellipse at 90% 35%, rgba(42, 105, 76, .08), transparent 35%),
        var(--bg);
    color: var(--text);
}

.block-container {
    max-width: 1500px;
    padding-top: 2.2rem;
    padding-bottom: 3rem;
}

/* Hide Streamlit chrome */
#MainMenu, footer {
    visibility: hidden;
}

header[data-testid="stHeader"] {
    background: transparent;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: rgba(15, 23, 18, .96);
    border-right: 1px solid var(--border);
}

section[data-testid="stSidebar"] > div {
    padding-top: 2rem;
}

section[data-testid="stSidebar"] h3 {
    color: var(--text);
    font-weight: 700;
    letter-spacing: -.4px;
}

/* Typography */
h1, h2, h3, h4 {
    color: var(--text) !important;
    letter-spacing: -0.7px;
}

p, label, .stCaption {
    color: var(--muted);
}

[data-testid="stMarkdownContainer"] p {
    line-height: 1.65;
}

/* Hero */
.hero-container {
    position: relative;
    overflow: hidden;
    padding: 32px 36px;
    margin-bottom: 26px;
    border-radius: 22px;
    border: 1px solid rgba(101, 214, 160, .17);
    background:
        radial-gradient(circle at 90% 20%, rgba(101, 214, 160, .17), transparent 36%),
        linear-gradient(120deg, #17251C, #101813 75%);
}

.hero-container:after {
    content: "";
    position: absolute;
    width: 220px;
    height: 220px;
    right: -75px;
    bottom: -135px;
    border-radius: 50%;
    border: 1px solid rgba(101, 214, 160, .15);
    box-shadow: 0 0 0 25px rgba(101, 214, 160, .025),
                0 0 0 50px rgba(101, 214, 160, .02);
}

.hero-badge {
    display: inline-block;
    padding: 6px 11px;
    border-radius: 30px;
    border: 1px solid rgba(101, 214, 160, .25);
    background: rgba(101, 214, 160, .08);
    color: var(--accent);
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.4px;
    margin-bottom: 16px;
}

.hero-title {
    font-size: clamp(27px, 3.5vw, 40px);
    font-weight: 800;
    letter-spacing: -1.7px;
    color: #F0F7F1;
    line-height: 1.2;
}

.hero-subtitle {
    color: #9EADA2;
    max-width: 650px;
    font-size: 14px;
    margin-top: 12px;
    line-height: 1.8;
}

/* KPI cards */
div[data-testid="stMetric"] {
    background: linear-gradient(145deg, #19241D, #121A15);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 20px 20px 16px;
    min-height: 120px;
    box-shadow: 0 8px 24px rgba(0,0,0,.12);
    transition: border-color .2s, transform .2s;
}

div[data-testid="stMetric"]:hover {
    border-color: rgba(101, 214, 160, .35);
    transform: translateY(-2px);
}

div[data-testid="stMetricLabel"] p {
    color: #9AA99E !important;
    font-size: 12px !important;
    font-weight: 600;
}

div[data-testid="stMetricValue"] {
    color: #ECF3EE !important;
    font-size: clamp(20px, 2vw, 29px) !important;
    font-weight: 750;
}

div[data-testid="stMetricDelta"] {
    font-size: 11px;
}

/* Tabs */
div[data-testid="stTabs"] > div:first-child {
    gap: 8px;
    border-bottom: 1px solid var(--border);
}

button[data-baseweb="tab"] {
    background: transparent;
    border-radius: 10px 10px 0 0;
    color: #89978E;
    font-size: 12px;
    font-weight: 600;
    padding: 13px 16px;
    border-bottom: 2px solid transparent;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent);
    background: rgba(101, 214, 160, .055);
}

/* Buttons */
.stButton > button,
.stDownloadButton > button {
    border: 1px solid var(--border);
    background: #1A251E;
    color: var(--text);
    border-radius: 11px;
    padding: 9px 15px;
    font-size: 12px;
    font-weight: 600;
    transition: all .2s ease;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    color: var(--accent);
    border-color: rgba(101, 214, 160, .45);
    background: #213127;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(110deg, #247A52, #38A875);
    color: #FFFFFF;
    border: none;
    box-shadow: 0 5px 18px rgba(48, 169, 111, .18);
}

.stButton > button[kind="primary"]:hover {
    background: linear-gradient(110deg, #2C9363, #49BD89);
    color: white;
}

/* Inputs */
.stTextInput input,
.stTextArea textarea,
.stSelectbox [data-baseweb="select"],
.stMultiSelect [data-baseweb="select"] {
    background: #111A14 !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
    border-radius: 10px !important;
}

.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 1px rgba(101, 214, 160, .15);
}

.stSlider [data-baseweb="slider"] {
    color: var(--accent);
}

/* Expanders */
div[data-testid="stExpander"] {
    border: 1px solid var(--border);
    background: rgba(20, 28, 23, .72);
    border-radius: 13px;
    overflow: hidden;
}

div[data-testid="stExpander"] summary {
    color: var(--text);
    font-weight: 600;
}

/* Dataframes */
div[data-testid="stDataFrame"] {
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
}

/* Charts */
div[data-testid="stVegaLiteChart"],
div[data-testid="stArrowVegaLiteChart"] {
    background: rgba(20, 28, 23, .5);
    border: 1px solid var(--border);
    border-radius: 15px;
    padding: 12px;
}

/* Alerts */
div[data-testid="stAlert"] {
    border-radius: 12px;
    border: 1px solid var(--border);
}

/* Chat input */
div[data-testid="stChatInput"] {
    border: 1px solid rgba(101, 214, 160, .2);
    border-radius: 14px;
    background: #141C17;
}

div[data-testid="stChatInput"] textarea {
    color: var(--text);
}

/* Dividers */
hr {
    border-color: var(--border);
    margin: 1.5rem 0;
}

/* File uploader */
div[data-testid="stFileUploader"] {
    background: rgba(20, 28, 23, .65);
    border: 1px dashed rgba(101, 214, 160, .3);
    border-radius: 14px;
    padding: 10px;
}

/* Status pill */
.score-pill {
    display: inline-block;
    padding: 7px 12px;
    border-radius: 30px;
    font-size: 11px;
    font-weight: 650;
    border: 1px solid var(--border);
}

.score-excellent {
    color: var(--accent);
    background: rgba(101, 214, 160, .09);
    border-color: rgba(101, 214, 160, .25);
}

.score-moderate {
    color: #E7C77D;
    background: rgba(231, 199, 125, .08);
}

.score-poor {
    color: #F18C8C;
    background: rgba(241, 140, 140, .08);
}

/* Responsive */
@media (max-width: 768px) {
    .block-container {
        padding: 1rem 1rem 2rem;
    }

    .hero-container {
        padding: 23px 20px;
    }

    .hero-title {
        font-size: 28px;
    }

    div[data-testid="stMetric"] {
        padding: 13px;
    }
}
</style>
"""


def get_health_score_badge(score, label):
    if score >= 75:
        css_class = "score-excellent"
    elif score >= 45:
        css_class = "score-moderate"
    else:
        css_class = "score-poor"

    return f'''
    <div class="score-pill {css_class}">
        ● FINANCIAL HEALTH &nbsp; {score}/100 &nbsp;·&nbsp; {label}
    </div>
    '''



def get_health_score_badge(score: int, label: str) -> str:
    """Return an HTML score badge with color-coded styling."""
    if score >= 80:
        cls = "score-excellent"
        icon = "✦"
    elif score >= 65:
        cls = "score-good"
        icon = "●"
    elif score >= 50:
        cls = "score-caution"
        icon = "▲"
    else:
        cls = "score-warning"
        icon = "✕"

    return f'<span class="score-pill {cls}">{icon} Financial Health: {score}/100 · {label}</span>'
