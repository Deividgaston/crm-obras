import streamlit as st


def inject_apple_style():
    """
    Tema único tipo Salesforce Lightning para todo el CRM.
    Fuerza modo claro, texto oscuro y tablas legibles.
    """
    st.markdown(
        """
        <style>
        /* =========================================
           RESET GLOBAL A MODO CLARO
        ========================================= */
        :root {
            color-scheme: light !important;
        }

        body,
        .stApp,
        [data-testid="stAppViewContainer"] {
            background-color: #f4f6f9 !important;
            color: #16325c !important;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
                         sans-serif;
        }

        /* TODO lo que cuelga del contenedor principal usa texto oscuro */
        [data-testid="stAppViewContainer"] * {
            color: #16325c !important;
        }

        .block-container {
            padding-top: 0.5rem;
            padding-bottom: 2rem;
            max-width: 1300px;
        }

        /* =========================================
           CARDS
        ========================================= */
        .apple-card {
            background: #ffffff;
            border-radius: 0.75rem;
            padding: 14px 20px 16px 20px;
            border: 1px solid #d8dde6;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
            margin: 10px 0 18px 0;
        }
        .apple-card h3 {
            font-size: 18px;
            font-weight: 600;
            color: #032D60 !important;
            margin: 0 0 2px 0;
        }
        .apple-card p {
            font-size: 13px;
            color: #5A6872 !important;
            margin: 0;
        }
        .apple-card .badge {
            display: inline-block;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: #0170D2 !important;
            background: #e5f1fb;
            padding: 2px 8px;
            border-radius: 999px;
            margin-bottom: 4px;
        }

        .apple-card-light {
            background: #ffffff;
            border-radius: 0.75rem;
            padding: 12px 16px 14px 16px;
            border: 1px solid #d8dde6;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
            margin-bottom: 12px;
        }

        /* =========================================
           TITULOS / TEXTOS
        ========================================= */
        h1, h2, h3, h4, h5, h6 {
            color: #032D60 !important;
        }
        .stMarkdown p {
            color: #16325c !important;
        }

        /* =========================================
           BOTONES GENERALES
        ========================================= */
        .stButton>button {
            background: #0170D2;
            color: #ffffff !important;
            border-radius: 4px;
            border: 1px solid #0170D2;
            padding: 6px 16px;
            font-size: 13px;
            font-weight: 500;
        }
        .stButton>button:hover {
            background: #0b84f5;
            border-color: #0b84f5;
            color: #ffffff !important;
        }

        /* La barra superior se estiliza aparte en app.py.
           Esto solo afecta al resto de botones. */

        /* =========================================
           INPUTS / SELECTS
        ========================================= */
        div[data-baseweb="select"] > div {
            background-color: #ffffff !important;
            border-radius: 4px;
        }

        .stTextInput>div>div>input,
        .stNumberInput input,
        .stTextArea textarea {
            background-color: #ffffff !important;
            border-radius: 4px !important;
        }

        div[data-baseweb="radio"]>div {
            gap: 12px;
        }

        /* =========================================
           TABLAS / DATAFRAME / DATAEDITOR
        ========================================= */
        [data-testid="stDataFrame"],
        [data-testid="stDataEditor"] {
            background:#ffffff !important;
            border-radius: 0.6rem;
            border: 1px solid #d8dde6 !important;
        }

        [data-testid="stDataFrame"] table,
        [data-testid="stDataEditor"] table {
            background:#ffffff !important;
            color:#16325c !important;
        }

        [data-testid="stDataFrame"] th,
        [data-testid="stDataFrame"] td,
        [data-testid="stDataEditor"] th,
        [data-testid="stDataEditor"] td {
            border-color:#d8dde6 !important;
        }

        [data-testid="stDataFrame"] thead,
        [data-testid="stDataEditor"] thead {
            background-color:#f4f6f9 !important;
        }

        /* =========================================
           TABS
        ========================================= */
        button[role="tab"] {
            font-size: 13px !important;
            color:#032D60 !important;
        }
        button[role="tab"][aria-selected="true"] {
            border-bottom:2px solid #0170D2 !important;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )
