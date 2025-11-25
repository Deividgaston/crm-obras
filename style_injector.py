import streamlit as st


def inject_apple_style():
    """
    Inyecta el estilo global del CRM (look más tipo Salesforce, compacto).
    Usa un flag de session_state para inyectarlo solo una vez.
    """
    if st.session_state.get("crm_style_injected"):
        return

    st.session_state["crm_style_injected"] = True

    style = """
    <style>
    /* ============================
       TIPOGRAFÍA + BASE
    ============================ */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
        font-size: 13px !important;              /* Más pequeño, estilo CRM */
        background: #f4f5f7 !important;          /* Gris claro tipo Salesforce */
        color: #1f2933 !important;
    }

    /* CONTENEDOR PRINCIPAL */
    .block-container {
        padding-top: 0.8rem;
        padding-bottom: 1.5rem;
        max-width: 1400px;
    }

    /* ============================
       TOP BAR (la usaremos desde app.py)
    ============================ */
    .crm-topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.35rem 0.6rem 0.35rem 0;
        border-bottom: 1px solid #d0d4dc;
        margin-bottom: 0.6rem;
    }

    .crm-topbar-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: #1f2933;
    }

    .crm-topbar-subtitle {
        font-size: 0.78rem;
        color: #6b7b93;
    }

    .crm-topbar-nav {
        display: inline-flex;
        gap: 0.25rem;
        align-items: center;
    }

    .crm-nav-pill {
        padding: 0.25rem 0.7rem;
        border-radius: 999px;
        font-size: 0.8rem;
        border: 1px solid transparent;
        background: transparent;
        color: #374151;
        cursor: pointer;
        transition: background 0.15s ease, border-color 0.15s ease;
    }

    .crm-nav-pill:hover {
        background: #e5e7eb;
        border-color: #cbd2e1;
    }

    .crm-nav-pill-active {
        background: #2563eb;
        color: #f9fafb;
        border-color: #1d4ed8;
    }

    /* ============================
       CARDS (reutilizamos clases existentes pero compactas)
    ============================ */

    .apple-card {
        background: #ffffff;
        border-radius: 6px;
        padding: 0.6rem 0.75rem;
        border: 1px solid #d0d4dc;
        margin-bottom: 0.5rem;
    }

    .apple-card-light {
        background: #ffffff;
        border-radius: 6px;
        padding: 0.6rem 0.75rem;
        border: 1px solid #e1e4eb;
        margin-bottom: 0.6rem;
    }

    .badge {
        display: inline-flex;
        align-items: center;
        padding: 0.1rem 0.45rem;
        border-radius: 999px;
        background: #eef2ff;
        color: #4b6cb7;
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.15rem;
    }

    /* Títulos y textos compactos */
    .apple-card h1,
    .apple-card h2,
    .apple-card h3,
    .apple-card-light h1,
    .apple-card-light h2,
    .apple-card-light h3 {
        font-size: 1rem;
        margin: 0 0 0.15rem 0;
    }

    .apple-card p,
    .apple-card-light p {
        font-size: 0.8rem;
        margin: 0;
        color: #6b7b93;
    }

    /* ============================
       MÉTRICAS COMPACTAS
    ============================ */
    .metric-row {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
    }

    .metric-card {
        flex: 1 1 0;
        min-width: 140px;
        background: #ffffff;
        border-radius: 6px;
        border: 1px solid #d9dde8;
        padding: 0.4rem 0.55rem;
    }

    .metric-title {
        font-size: 0.72rem;
        color: #6b7b93;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.1rem;
    }

    .metric-value {
        font-size: 1.2rem;
        font-weight: 600;
        color: #111827;
        line-height: 1.2;
    }

    /* ============================
       LISTAS / PILLS / DETALLES
    ============================ */
    .next-item {
        padding: 0.35rem 0.45rem;
        border-radius: 4px;
        border: 1px solid #e5e7eb;
        background: #ffffff;
        margin-bottom: 0.35rem;
    }

    .next-item small {
        font-size: 0.76rem;
        color: #6b7b93;
    }

    .pill {
        display: inline-flex;
        align-items: center;
        padding: 0.05rem 0.45rem;
        border-radius: 999px;
        font-size: 0.7rem;
        margin-left: 0.25rem;
        border: 1px solid transparent;
    }

    .pill-red {
        background: #fee2e2;
        color: #b91c1c;
        border-color: #fecaca;
    }

    .pill-amber {
        background: #fef3c7;
        color: #92400e;
        border-color: #fde68a;
    }

    .pill-slate {
        background: #e5e7eb;
        color: #374151;
        border-color: #d1d5db;
    }

    /* ============================
       TABLAS (más densas)
    ============================ */
    .stDataFrame table,
    .stDataFrame tbody,
    .stDataFrame th,
    .stDataFrame td {
        font-size: 0.78rem !important;
    }

    /* Captions pequeñas */
    .small-caption {
        color: #9ca3af;
        font-size: 0.75rem;
    }
    </style>
    """

    st.markdown(style, unsafe_allow_html=True)
