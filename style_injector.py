import streamlit as st


def inject_apple_style():
    """
    Inyecta estilos modernos tipo Apple en toda la app.
    Si ya se inyectó antes, evita duplicaciones.
    """
    if "apple_style_injected" in st.session_state:
        return

    style = """
    <style>

    /* Tipografía tipo SF / Apple */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
        Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans",
        "Helvetica Neue", sans-serif !important;
        font-size: 15px;
    }

    /* Títulos principales */
    h1 {
        font-weight: 700 !important;
        letter-spacing: -1px;
        margin-bottom: 0.5rem;
    }

    /* Subtítulos */
    h2, h3, h4 {
        font-weight: 600 !important;
        margin-top: 1.5rem;
    }

    /* Botones */
    .stButton>button {
        border-radius: 10px !important;
        padding: 0.6rem 1.2rem !important;
        font-weight: 600 !important;
        border: 1px solid #d0d0d0 !important;
        background: #f9f9fb !important;
        transition: all 0.2s ease-in-out;
    }

    .stButton>button:hover {
        background: #e9e9ee !important;
        border-color: #c2c2c2 !important;
    }

    .stButton>button:active {
        background: #dcdce2 !important;
        border-color: #b2b2b2 !important;
    }

    /* Inputs */
    .stTextInput>div>div>input,
    .stTextArea textarea,
    .stSelectbox>div>div>button {
        border-radius: 10px !important;
    }

    /* Tablas */
    .stDataFrame {
        border-radius: 12px !important;
        overflow: hidden !important;
        border: 1px solid #e0e0e0 !important;
    }

    /* Data editor */
    .stDataEditor {
        border-radius: 12px !important;
        border: 1px solid #e0e0e0 !important;
        overflow: hidden !important;
    }

    /* Panel Sidebar estilo Apple */
    section[data-testid="stSidebar"] {
        background-color: #f7f7f9 !important;
        border-right: 1px solid #e3e3e8 !important;
    }

    /* Metric Cards */
    [data-testid="metric-container"] {
        border-radius: 12px !important;
        padding: 1rem !important;
        background-color: #fafafa !important;
        border: 1px solid #e9e9e9 !important;
        box-shadow: 0px 1px 2px rgba(0,0,0,0.04) !important;
    }

    </style>
    """

    st.markdown(style, unsafe_allow_html=True)

    st.session_state["apple_style_injected"] = True
