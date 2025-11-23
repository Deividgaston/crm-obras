import streamlit as st

def inject_apple_style():
    st.markdown("""
    <style>

    /* =========================================
       APPLE BLUE THEME — DUAL MODE
       ========================================= */

    /* Detect Dark Mode */
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-main: #0E1A2B;                /* Navy profundo */
            --bg-card: rgba(21, 36, 58, 0.65); /* Semi transparente */
            --bg-card-light: rgba(28, 49, 78, 0.85);
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
            --bg-card: rgba(255,255,255,0.75);
            --bg-card-light: rgba(255,255,255,0.92);
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

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: var(--bg-card-light) !important;
        backdrop-filter: blur(18px);
        border-right: 1px solid var(--border-color);
        color: var(--text-color);
    }

    /* HEADERS */
    h1, h2, h3, h4 {
        color: var(--text-color) !important;
        letter-spacing: -0.02em !important;
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
    .metric-row { display: flex; gap: 14px; margin: 12px 0; }
    .metric-box {
        flex: 1;
        padding: 18px;
        background: var(--bg-card-light);
        border-radius: 16px;
        border: 1px solid var(--border-color);
        box-shadow: 0 8px 18px rgba(0,0,0,0.10);
    }
    .metric-title { font-size: 0.8rem; color: var(--text-muted); }
    .metric-value { font-size: 1.8rem; margin-top: 4px; color: var(--accent); }

    /* Section badge */
    .section-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 999px;
        background: var(--accent-soft);
        color: var(--accent);
        font-weight: 600;
        font-size: 0.75rem;
    }

    /* Dataframes */
    .stDataFrame td {
        color: var(--text-color) !important;
        background-color: var(--bg-card) !important;
    }
    .stDataFrame th {
        background-color: var(--bg-card-light) !important;
        color: var(--text-color) !important;
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

    /* Pills (pipeline) */
    .status-pill {
        padding: 6px 14px;
        border-radius: 999px;
        background: var(--accent-soft);
        color: var(--accent);
        font-weight: 600;
        box-shadow: 0 0 0 2px var(--pill-shadow);
    }

    /* Inputs */
    input, textarea, select {
        background: var(--bg-card-light) !important;
        border-radius: 12px !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-color) !important;
    }

    </style>
    """, unsafe_allow_html=True)
