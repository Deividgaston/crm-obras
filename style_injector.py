import streamlit as st

def inject_apple_style():
    st.markdown("""
    <style>

    /* =========================================
       APPLE BLUE THEME — DUAL MODE
       ========================================= */

    /* Dark Mode */
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-main: #0E1A2B;                /* Navy profundo */
            --bg-card: rgba(21, 36, 58, 0.65); /* Semi transparente */
            --bg-card-light: rgba(28, 49, 78, 0.90);
            --border-color: rgba(255,255,255,0.08);
            --text-color: #E9EEF6;
            --text-muted: #9FB3D1;
            --accent: #3EA0FF;
            --accent-soft: rgba(62,160,255,0.18);
            --pill-shadow: rgba(62,160,255,0.45);
        }
    }

    /* Light Mode */
    @media (prefers-color-scheme: light) {
        :root {
            --bg-main: #EAF4FF;                /* Azul Apple súper claro */
            --bg-card: rgba(255,255,255,0.82);
            --bg-card-light: rgba(255,255,255,0.96);
            --border-color: rgba(0,0,0,0.08);
            --text-color: #0A1A2F;
            --text-muted: #4B5E74;
            --accent: #0077FF;
            --accent-soft: rgba(0,119,255,0.12);
            --pill-shadow: rgba(0,119,255,0.35);
        }
    }

    /* Global font and background */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, Inter, sans-serif !important;
        background: var(--bg-main) !important;
        color: var(--text-color) !important;
    }

    /* Streamlit block container width */
    .block-container {
        max-width: 1200px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: var(--bg-card-light) !important;
        backdrop-filter: blur(18px);
        border-right: 1px solid var(--border-color);
        color: var(--text-color);
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: var(--text-color) !important;
    }

    /* HEADERS */
    h1, h2, h3, h4 {
        color: var(--text-color) !important;
        letter-spacing: -0.02em !important;
    }

    h1 {
        font-size: 2.1rem !important;
        font-weight: 650 !important;
    }

    h2 {
        font-size: 1.5rem !important;
        font-weight: 600 !important;
    }

    /* Apple Card */
    .apple-card {
        padding: 22px 26px;
        background: var(--bg-card);
        backdrop-filter: blur(18px);
        border-radius: 20px;
        border: 1px solid var(--border-color);
        box-shadow: 0 14px 40px rgba(0,0,0,0.25);
        margin-bottom: 20px;
    }

    .apple-card-light {
        padding: 20px 24px;
        background: var(--bg-card-light);
        border-radius: 18px;
        border: 1px solid var(--border-color);
        box-shadow: 0 10px 30px rgba(0,0,0,0.10);
        margin-bottom: 20px;
    }

    /* Metrics Apple */
    .metric-row { 
        display: flex; 
        gap: 14px; 
        margin: 12px 0; 
    }
    .metric-box {
        flex: 1;
        padding: 18px;
        background: var(--bg-card-light);
        border-radius: 16px;
        border: 1px solid var(--border-color);
        box-shadow: 0 8px 18px rgba(0,0,0,0.12);
    }
    .metric-title { 
        font-size: 0.8rem; 
        color: var(--text-muted); 
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .metric-value { 
        font-size: 1.8rem; 
        margin-top: 4px; 
        color: var(--accent); 
        font-weight: 650;
    }
    .metric-sub { 
        font-size: 0.78rem; 
        color: var(--text-muted); 
        margin-top: 3px;
    }

    /* Section badge */
    .section-badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 12px;
        border-radius: 999px;
        background: var(--accent-soft);
        color: var(--accent);
        font-weight: 600;
        font-size: 0.75rem;
    }

    /* DataFrames */
    .stDataFrame table {
        border-radius: 12px;
        overflow: hidden;
    }
    .stDataFrame tbody tr td {
        background-color: var(--bg-card) !important;
        color: var(--text-color) !important;
        border-color: var(--border-color) !important;
    }
    .stDataFrame thead tr th {
        background-color: var(--bg-card-light) !important;
        color: var(--text-color) !important;
        border-color: var(--border-color) !important;
    }

    /* Buttons */
    button[kind="primary"] {
        background: var(--accent) !important;
        color: white !important;
        border-radius: 999px !important;
        border: none !important;
        padding: 8px 20px !important;
        font-weight: 600 !important;
        box-shadow: 0 3px 10px rgba(0,0,0,0.25);
    }
    button[kind="primary"]:hover {
        background: white !important;
        color: var(--accent) !important;
        border: 1px solid var(--accent) !important;
        box-shadow: 0 4px 14px rgba(0,0,0,0.35);
    }

    /* Inputs */
    input, textarea, select {
        background: var(--bg-card-light) !important;
        border-radius: 12px !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-color) !important;
    }

    /* Code block (para el prompt de Buscar) */
    pre, code {
        background: #020617 !important;
        color: #E5E7EB !important;
        border-radius: 12px !important;
    }

    </style>
    """, unsafe_allow_html=True)
