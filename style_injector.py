import streamlit as st


def inject_apple_style():
    """
    Inyecta estilos modernos tipo Apple en toda la app.
    Evita duplicar la inyección usando una marca en session_state.
    """
    if "apple_style_injected" in st.session_state:
        return

    style = """
    <style>
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
        Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans",
        "Helvetica Neue", sans-serif !important;
        font-size: 15px;
        background-color: #020617;
    }

    h1 {
        font-weight: 700 !important;
        letter-spacing: -1px;
        margin-bottom: 0.5rem;
    }

    h2, h3, h4 {
        font-weight: 600 !important;
        margin-top: 1.5rem;
    }

    .stButton>button {
        border-radius: 10px !important;
        padding: 0.6rem 1.2rem !important;
        font-weight: 600 !important;
        border: 1px solid #1f2937 !important;
        background: #0b1120 !important;
        color: #e5e7eb !important;
        transition: all 0.2s ease-in-out;
    }

    .stButton>button:hover {
        background: #111827 !important;
        border-color: #4b5563 !important;
    }

    .stButton>button:active {
        background: #020617 !important;
        border-color: #6b7280 !important;
    }

    .stTextInput>div>div>input,
    .stTextArea textarea,
    .stSelectbox>div>div>button {
        border-radius: 10px !important;
        background-color: #020617 !important;
        border-color: #1f2937 !important;
        color: #e5e7eb !important;
    }

    .stDataFrame, .stDataEditor {
        border-radius: 12px !important;
        border: 1px solid #1f2937 !important;
        overflow: hidden !important;
    }

    section[data-testid="stSidebar"] {
        background: radial-gradient(circle at top left, #0f172a, #020617) !important;
        border-right: 1px solid #1f2937 !important;
    }

    [data-testid="metric-container"] {
        border-radius: 12px !important;
        padding: 1rem !important;
        background: radial-gradient(circle at top left, #020617, #020617) !important;
        border: 1px solid #1f2937 !important;
        box-shadow: 0px 10px 25px rgba(15,23,42,0.5) !important;
    }

    .apple-card {
        background: radial-gradient(circle at top left, #0f172a, #020617);
        border-radius: 18px;
        border: 1px solid #1f2937;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 18px 40px rgba(15,23,42,0.9);
        margin-bottom: 1.2rem;
    }

    .card-light, .apple-card-light {
        background: #020617;
        border-radius: 18px;
        border: 1px solid #1f2937;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 12px 25px rgba(15,23,42,0.6);
        margin-bottom: 1.2rem;
    }

    .badge {
        display: inline-flex;
        align-items: center;
        padding: 0.15rem 0.6rem;
        border-radius: 999px;
        font-size: 0.7rem;
        letter-spacing: .08em;
        text-transform: uppercase;
        background: rgba(148,163,184,0.12);
        color: #9ca3af;
    }

    .section-title {
        font-size: 1.1rem;
        margin: 6px 0 10px 0;
    }

    .small-caption {
        font-size: 0.78rem;
        color: #9ca3af;
    }

    .next-item {
        padding: 0.6rem 0.8rem;
        border-radius: 0.75rem;
        border: 1px solid #1f2937;
        background: rgba(15,23,42,0.85);
        margin-bottom: 0.55rem;
    }

    .badge-inline {
        display: inline-block;
        padding: 0.05rem 0.45rem;
        border-radius: 999px;
        font-size: 0.7rem;
        background: #0f766e;
        color: #ecfdf5;
        margin-left: 0.35rem;
    }
    </style>
    """

    st.markdown(style, unsafe_allow_html=True)
    st.session_state["apple_style_injected"] = True
