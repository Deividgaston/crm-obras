import streamlit as st


def inject_apple_style():
    """
    Estilo tipo Salesforce forzando modo CLARO aunque el usuario tenga dark mode.
    """
    if st.session_state.get("crm_style_injected"):
        return

    st.session_state["crm_style_injected"] = True

    style = """
    <style>

    /* ======================================================
       🔥 FORCE LIGHT MODE — Ignora el modo oscuro de Streamlit
       ====================================================== */
    html, body, [class*="css"], .stApp, .stAppViewContainer {
        background-color: #f5f7ff !important;
        color: #1e293b !important;
        filter: invert(0%) !important;
    }

    /* Bloques interiores */
    .block-container, .main, .stDataFrame, .stMarkdown, .stColumn {
        background-color: #f5f7ff !important;
        color: #1e293b !important;
    }

    /* ======================================================
       TIPOGRAFÍA Y BASE DE ESTILO
       ====================================================== */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
        font-size: 13px !important;
    }

    .block-container {
        padding-top: 0.6rem;
        padding-bottom: 1.5rem;
        max-width: 1200px;
        margin: 0 auto;
    }

    /* ======================================================
       TOPBAR COMPACTA TIPO SALESFORCE
       ====================================================== */
    .crm-topbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 6px 2px;
        border-bottom: 1px solid #c7d2fe;
        background: #ffffff !important;
    }

    .crm-topbar-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: #1d4ed8 !important;
    }

    .crm-topbar-subtitle {
        font-size: 0.75rem;
        color: #64748b !important;
    }

    /* NAV PILL */
    .crm-nav-pill {
        padding: 3px 12px;
        border-radius: 999px;
        font-size: 0.78rem;
        background: #e0ecff;
        border: 1px solid #c7d2fe;
        color: #1e3a8a !important;
        cursor: pointer;
    }

    .crm-nav-pill-active {
        background: #2563eb !important;
        border-color: #1d4ed8 !important;
        color: #ffffff !important;
    }

    /* ======================================================
       CARDS
       ====================================================== */
    .apple-card,
    .apple-card-light {
        background: #ffffff !important;
        border-radius: 6px;
        padding: 8px 10px;
        border: 1px solid #dbe3ff;
        color: #1e293b !important;
        margin-bottom: 8px;
    }

    .badge {
        background: #e0ecff !important;
        color: #1d4ed8 !important;
        padding: 2px 8px;
        font-size: 0.68rem;
        border-radius: 999px;
    }

    /* ======================================================
       MÉTRICAS COMPACTAS
       ====================================================== */
    .metric-card {
        background: #ffffff !important;
        border: 1px solid #c7d2fe !important;
        padding: 6px 10px;
        border-radius: 6px;
    }

    .metric-title {
        font-size: 0.7rem;
        color: #64748b !important;
    }

    .metric-value {
        font-size: 1.15rem;
        font-weight: 600;
        color: #1e293b !important;
    }

    /* ======================================================
       LISTAS / ITEMS
       ====================================================== */
    .next-item {
        background: #ffffff !important;
        padding: 6px 8px;
        border-radius: 4px;
        border: 1px solid #e5edff !important;
        margin-bottom: 6px;
        color: #1e293b !important;
    }

    .next-item small {
        color: #64748b !important;
        font-size: 0.75rem;
    }

    /* ======================================================
       TABLAS
       ====================================================== */
    .stDataFrame table,
    .stDataFrame tbody,
    .stDataFrame th,
    .stDataFrame td {
        background: #ffffff !important;
        color: #1e293b !important;
        font-size: 0.78rem !important;
    }

    </style>
    """

    st.markdown(style, unsafe_allow_html=True)
