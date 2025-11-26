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
    # CONFIG BÁSICA + TEMA LIGHT
    # ==========================
    st.set_page_config(
        page_title="CRM Prescripción 2N",
        layout="wide",
        page_icon="🏗️",
        initial_sidebar_state="collapsed",
        theme={
            "base": "light",
            "primaryColor": "#0170D2",
            "backgroundColor": "#f4f6f9",
            "secondaryBackgroundColor": "#ffffff",
            "textColor": "#16325c",
        },
    )

    inject_apple_style()

    # ==========================
    # ESTILO GLOBAL CLARO + BOTONES
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

        /* BOTONES DE LA BARRA DE HERRAMIENTAS */
        .toolbar-row {
            margin: 8px 18px 2px 18px;
        }
        .toolbar-row .stButton>button {
            background:#ffffff;
            border:1px solid #d8dde6;
            border-radius:4px;
            padding:6px 18px;
            font-size:13px;
            font-weight:500;
            color:#032D60;
            cursor:pointer;
        }
        .toolbar-row .stButton>button:hover {
            background:#e5f1fb;
            border-color:#1b96ff;
        }

        /* Botón activo */
        .toolbar-active>button {
            background:#0170D2 !important;
            border-color:#0170D2 !important;
            color:#ffffff !important;
        }

        /* Selects sobre fondo blanco */
        div[data-baseweb="select"] > div {
            background-color:#ffffff !important;
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
    # ESTADO DE NAVEGACIÓN
    # ==========================
    pages = ["Panel", "Proyectos", "Buscar", "Dashboard"]
    if "page" not in st.session_state:
        st.session_state["page"] = "Panel"

    current = st.session_state["page"]

    # ==========================
    # BARRA DE HERRAMIENTAS (BOTONES)
    # ==========================
    toolbar = st.container()
    with toolbar:
        st.markdown('<div class="toolbar-row">', unsafe_allow_html=True)
        cols = st.columns(len(pages))
        for i, name in enumerate(pages):
            with cols[i]:
                btn_class = "toolbar-active" if current == name else ""
                st.markdown(f'<div class="{btn_class}">', unsafe_allow_html=True)
                if st.button(name, key=f"nav_{name}"):
                    st.session_state["page"] = name
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("")  # pequeño espacio

    # ==========================
    # ROUTING
    # ==========================
    page = st.session_state["page"]

    if page == "Panel":
        render_panel()
    elif page == "Proyectos":
        render_proyectos()
    elif page == "Buscar":
        render_buscar()
    elif page == "Dashboard":
        render_dashboard()


if __name__ == "__main__":
    app()
