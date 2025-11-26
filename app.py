import streamlit as st

from panel_page import render_panel
from proyectos_page import render_proyectos
from buscar_page import render_buscar
from dashboard_page import render_dashboard

try:
    from style_injector import inject_apple_style
except Exception:
    def inject_apple_style():
        pass


def app():
    # ==========================
    # CONFIG BÁSICA
    # ==========================
    st.set_page_config(
        page_title="CRM Prescripción 2N",
        layout="wide",
        page_icon="🏗️",
    )

    inject_apple_style()

    # ==========================
    # ESTILO GLOBAL CLARO
    # ==========================
    st.markdown(
        """
        <style>
        /* Fondo general claro tipo Salesforce */
        .stApp {
            background-color: #f4f6f9 !important;
        }
        .block-container {
            padding-top: 0.5rem;
        }

        /* TOPBAR */
        .topbar{
            width:100%;
            background:#ffffff;
            border-bottom:1px solid #d8dde6;
            padding:6px 18px 6px 18px;
            display:flex;
            justify-content:space-between;
            align-items:center;
        }
        .topbar-title{
            font-size:17px;
            font-weight:600;
            color:#032D60;
            margin:0;
        }
        .topbar-sub{
            font-size:12px;
            color:#5A6872;
            margin-top:-4px;
        }

        /* TOOLBAR HORIZONTAL (radio disfrazado de botones) */
        div[data-baseweb="radio"] > div {
            display:flex !important;
            gap:8px;
            flex-wrap:wrap;
        }
        div[data-baseweb="radio"] label {
            background:#ffffff;
            border:1px solid #d8dde6;
            border-radius:4px;
            padding:4px 10px;
            font-size:13px;
            font-weight:500;
            color:#032D60;
            cursor:pointer;
        }
        /* Oculta el circulito del radio */
        div[data-baseweb="radio"] input {
            display:none;
        }
        /* Estado activo */
        div[data-baseweb="radio"] input:checked + div {
            background:#e5f1fb !important;
            border-color:#1b96ff !important;
            color:#032D60 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ==========================
    # TOPBAR
    # ==========================
    st.markdown(
        """
        <div class="topbar">
            <div>
                <div class="topbar-title">CRM Prescripción 2N</div>
                <div class="topbar-sub">Panel · Proyectos · Scouting · Dashboard</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ==========================
    # TOOLBAR SECCIONES
    # ==========================
    col_toolbar = st.container()
    with col_toolbar:
        menu = st.radio(
            "Secciones",
            ["Panel", "Proyectos", "Buscar", "Dashboard"],
            horizontal=True,
            label_visibility="collapsed",
            key="nav_toolbar",
        )

    st.write("")  # pequeño espacio

    # ==========================
    # ROUTING
    # ==========================
    if menu == "Panel":
        render_panel()
    elif menu == "Proyectos":
        render_proyectos()
    elif menu == "Buscar":
        render_buscar()
    elif menu == "Dashboard":
        render_dashboard()


if __name__ == "__main__":
    app()
