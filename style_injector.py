import streamlit as st


def inject_apple_style():
    """
    Inyecta estilos globales tipo Salesforce Lightning
    para todo el CRM (panel, proyectos, buscar, dashboard).
    """
    st.markdown(
        """
        <style>
        /* =============================
           BASE GENERAL
        ============================= */
        .stApp {
            background-color: #f4f6f9 !important;
            color: #16325c !important;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
                         sans-serif;
        }

        .block-container {
            padding-top: 0.5rem;
            padding-bottom: 2rem;
            max-width: 1300px;
        }

        /* Quita bordes/zoom raros de imágenes y markdown */
        img {
            max-width: 100%;
        }

        /* =============================
           CARDS PRINCIPALES
        ============================= */

        /* Card grande de cabecera (Panel, Proyectos, Buscar...) */
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
            color: #032D60;
            margin: 0 0 2px 0;
        }
        .apple-card p {
            font-size: 13px;
            color: #5A6872;
            margin: 0;
        }
        .apple-card .badge {
            display: inline-block;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: #0170D2;
            background: #e5f1fb;
            padding: 2px 8px;
            border-radius: 999px;
            margin-bottom: 4px;
        }

        /* Card ligera reutilizada en panel/proyectos/buscar */
        .apple-card-light {
            background: #ffffff;
            border-radius: 0.75rem;
            padding: 12px 16px 14px 16px;
            border: 1px solid #d8dde6;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
            margin-bottom: 12px;
        }

        /* =============================
           METRICS / KPI CARDS
        ============================= */
        .metric-card {
            background: #ffffff;
            border-radius: 0.6rem;
            padding: 10px 14px;
            border: 1px solid #d8dde6;
            box-shadow: 0 1px 2px rgba(0,0,0,0.03);
            margin-top: 8px;
            margin-bottom: 8px;
        }
        .metric-title {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #5A6872;
            margin-bottom: 4px;
        }
        .metric-value {
            font-size: 20px;
            font-weight: 600;
            color: #032D60;
        }

        /* =============================
           TITULOS / TEXTOS GENERALES
        ============================= */
        h1, h2, h3, h4, h5, h6 {
            color: #032D60;
        }
        .stMarkdown p {
            color: #16325c;
        }

        /* =============================
           BOTONES GENERALES STREAMLIT
        ============================= */
        .stButton>button {
            background: #0170D2;
            color: #ffffff;
            border-radius: 4px;
            border: 1px solid #0170D2;
            padding: 6px 16px;
            font-size: 13px;
            font-weight: 500;
        }
        .stButton>button:hover {
            background: #0b84f5;
            border-color: #0b84f5;
            color: #ffffff;
        }

        /* Los botones de la barra superior se sobreescriben
           en app.py con selectores más específicos. */

        /* =============================
           SELECTS / INPUTS
        ============================= */

        /* Fondo blanco para selects sobre fondo gris */
        div[data-baseweb="select"] > div {
            background-color: #ffffff !important;
            border-radius: 4px;
        }

        /* Inputs de texto también en blanco */
        .stTextInput>div>div>input,
        .stNumberInput input,
        .stTextArea textarea {
            background-color: #ffffff !important;
            border-radius: 4px !important;
        }

        /* Radio horizontal (usado en Proyectos) */
        div[data-baseweb="radio"]>div {
            gap: 12px;
        }

        /* =============================
           TABLAS / DATAFRAMES
        ============================= */
        .stDataFrame {
            border-radius: 0.6rem;
            border: 1px solid #d8dde6;
            background: #ffffff;
        }

        /* =============================
           TABS (Vista general / Dashboard / ...)
        ============================= */
        button[role="tab"] {
            font-size: 13px;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )
