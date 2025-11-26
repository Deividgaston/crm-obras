import streamlit as st


def inject_apple_style():
    """
    Estilo Salesforce Lightning forzado (modo claro, tonos azulados,
    texto visible, interfaz densa y profesional) + pantalla limpia
    sin menús propios de Streamlit.
    """
    if st.session_state.get("crm_style_injected"):
        return

    st.session_state["crm_style_injected"] = True

    style = """
    <style>

    /* ======================================
       🔵 BASE GLOBAL — Salesforce Lightning
    ====================================== */
    html, body, .stApp, [class*="css"] {
        background-color: #F3F6FB !important;   /* Fondo SF Lightning */
        color: #032D60 !important;              /* Azul oscuro texto */
        font-family: 'Segoe UI', sans-serif !important;
        font-size: 14px !important;
    }

    .block-container {
        max-width: 1280px;
        padding-top: 0.5rem;
        padding-bottom: 1.5rem;
        margin: 0 auto;
    }

    /* ======================================
       🔵 TOP BAR — Estilo Salesforce Header
    ====================================== */
    .crm-topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #ffffff !important;
        border-bottom: 1px solid #D8E6FF;
        padding: 8px 4px;
        margin-bottom: 0.7rem;
    }

    .crm-topbar-title {
        font-size: 17px;
        font-weight: 600;
        color: #0170FE;      /* Azul Salesforce */
    }

    .crm-topbar-subtitle {
        font-size: 12.5px;
        color: #4A5F7D;
    }

    /* ======================================
       🔵 BOTONES SALESFORCE RECTANGULARES
    ====================================== */
    button, .stButton>button {
        background: #0170FE !important;
        border-radius: 4px !important;
        padding: 6px 16px !important;
        color: white !important;
        font-size: 13px !important;
        border: none !important;
    }

    button:hover, .stButton>button:hover {
        background: #005FDF !important;
    }

    /* Botones secundarios manuales (si los usas con class="sf-btn-secondary") */
    .sf-btn-secondary {
        background: #E5ECF6 !important;
        color: #032D60 !important;
        border: 1px solid #A8C1EA !important;
        border-radius: 4px !important;
        padding: 5px 14px !important;
        font-size: 13px !important;
    }

    /* ======================================
       🔵 CARDS — estilo Salesforce Lightning
    ====================================== */
    .apple-card,
    .apple-card-light {
        background: #ffffff !important;
        border: 1px solid #D8E6FF !important;
        padding: 12px 14px !important;
        border-radius: 6px !important;
        margin-bottom: 10px !important;
        color: #032D60 !important;
    }

    .badge {
        background: #E0EDFF !important;
        color: #0170FE !important;
        padding: 2px 8px;
        border-radius: 999px;
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 0.6px;
        text-transform: uppercase;
        margin-bottom: 4px;
    }

    .apple-card h1, .apple-card h2, .apple-card h3,
    .apple-card-light h1, .apple-card-light h2, .apple-card-light h3 {
        font-size: 16px !important;
        font-weight: 600 !important;
        margin-bottom: 4px !important;
        color: #032D60 !important;
    }

    .apple-card p,
    .apple-card-light p {
        font-size: 13px !important;
        color: #4A5F7D !important;
        margin: 0;
    }

    /* ======================================
       🔵 MÉTRICAS DENSAS
    ====================================== */
    .metric-card {
        background: #ffffff;
        border: 1px solid #CFE0FF;
        padding: 10px 12px;
        border-radius: 6px;
        min-width: 120px;
    }

    .metric-title {
        color: #516B8E;
        font-size: 11px;
        text-transform: uppercase;
        margin-bottom: 3px;
    }

    .metric-value {
        color: #032D60;
        font-size: 18px;
        font-weight: 600;
        line-height: 1.1;
    }

    /* ======================================
       🔵 LIST ITEMS (Agenda)
    ====================================== */
    .next-item {
        background: #ffffff !important;
        border: 1px solid #D6E2FF !important;
        padding: 8px 10px;
        border-radius: 6px;
        margin-bottom: 6px;
    }

    .next-item strong {
        font-size: 13px;
        color: #032D60 !important;
    }

    .next-item small {
        font-size: 12px;
        color: #576C89 !important;
    }

    /* ======================================
       🔵 TABLAS
    ====================================== */
    .stDataFrame table,
    .stDataFrame th,
    .stDataFrame td {
        background: #ffffff !important;
        color: #032D60 !important;
        font-size: 13px !important;
    }

    .stDataFrame tbody tr:nth-child(even) {
        background: #F3F6FF !important;
    }

    /* ======================================
       🔥 LIMPIAR UI DE STREAMLIT
       Ocultar menú, footer, header, barra deploy, etc.
    ====================================== */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}
    .stDeployButton {display: none !important;}
    .stStatusWidget {display: none !important;}

    </style>
    """

    st.markdown(style, unsafe_allow_html=True)
