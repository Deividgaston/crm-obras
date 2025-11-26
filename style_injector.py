import streamlit as st


def inject_apple_style():
    """
    Inyecta el estilo global del CRM (look tipo Salesforce, compacto, azul/blanco).
    Usa un flag de session_state para inyectarlo solo una vez.
    """
    if st.session_state.get("crm_style_injected"):
        return

    st.session_state["crm_style_injected"] = True

    style = """
    <style>
    /* ============================
       BASE GLOBAL
    ============================ */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
        font-size: 13px !important;
        background: #f5f7ff !important;          /* Blanco azulado */
        color: #1e293b !important;               /* Azul grisáceo, no negro */
    }

    /* CONTENEDOR PRINCIPAL CENTRADO Y ESTRECHO */
    .block-container {
        padding-top: 0.6rem;
        padding-bottom: 1.5rem;
        max-width: 1200px;                       /* Más estrecho */
        margin: 0 auto;                          /* Centrado */
    }

    /* ============================
       TOP BAR (app.py)
    ============================ */
    .crm-topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.30rem 0.2rem 0.30rem 0;
        border-bottom: 1px solid #c7d2fe;
        margin-bottom: 0.4rem;
    }

    .crm-topbar-title {
        font-size: 0.9rem;
        font-weight: 600;
        color: #1d4ed8; /* Azul principal */
    }

    .crm-topbar-subtitle {
        font-size: 0.78rem;
        color: #64748b;
    }

    .crm-topbar-nav {
        display: inline-flex;
        gap: 0.25rem;
        align-items: center;
    }

    .crm-nav-pill {
        padding: 0.20rem 0.7rem;
        border-radius: 999px;
        font-size: 0.8rem;
        border: 1px solid transparent;
        background: transparent;
        color: #334155;
        cursor: pointer;
        transition: background 0.15s ease, border-color 0.15s ease;
    }

    .crm-nav-pill:hover {
        background: #e0ecff;
        border-color: #bfdbfe;
    }

    .crm-nav-pill-active {
        background: #2563eb;
        color: #f9fafb;
        border-color: #1d4ed8;
    }

    /* ============================
       CARDS COMPACTAS
    ============================ */

    .apple-card,
    .apple-card-light {
        background: #ffffff;
        border-radius: 6px;
        padding: 0.55rem 0.7rem;
        border: 1px solid #dbe3ff;
        margin-bottom: 0.5rem;
    }

    .apple-card {
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
    }

    .badge {
        display: inline-flex;
        align-items: center;
        padding: 0.06rem 0.45rem;
        border-radius: 999px;
        background: #e0ecff;
        color: #1d4ed8;
        font-size: 0.68rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.15rem;
    }

    .apple-card h1,
    .apple-card h2,
    .apple-card h3,
    .apple-card-light h1,
    .apple-card-light h2,
    .apple-card-light h3 {
        font-size: 0.98rem;
        margin: 0 0 0.12rem 0;
        color: #0f172a;
    }

    .apple-card p,
    .apple-card-light p {
        font-size: 0.8rem;
        margin: 0;
        color: #6b7280;
    }

    /* ============================
       MÉTRICAS COMPACTAS
    ============================ */
    .metric-row {
        display: flex;
        gap: 0.45rem;
        flex-wrap: wrap;
        justify-content: center;
    }

    .metric-card {
        flex: 0 0 auto;
        min-width: 120px;
        background: #ffffff;
        border-radius: 6px;
        border: 1px solid #c7d2fe;
        padding: 0.35rem 0.55rem;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
    }

    .metric-title {
        font-size: 0.7rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.05rem;
    }

    .metric-value {
        font-size: 1.15rem;
        font-weight: 600;
        color: #1e293b;
        line-height: 1.2;
        text-align: left;
    }

    /* ============================
       LISTAS / PILLS / ITEMS
    ============================ */
    .next-item {
        padding: 0.32rem 0.5rem;
        border-radius: 4px;
        border: 1px solid #e5edff;
        background: #ffffff;
        margin-bottom: 0.3rem;
    }

    .next-item small {
        font-size: 0.75rem;
        color: #6b7280;
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
        background: #e5edff;
        color: #1d4ed8;
        border-color: #c7d2fe;
    }

    /* ============================
       TABLAS MÁS DENSAS
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
