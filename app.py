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
    # ======================================================
    # CONFIG
    # ======================================================
    st.set_page_config(
        page_title="CRM Prescripción 2N",
        layout="wide",
        page_icon="🏗️"
    )

    inject_apple_style()

    # ======================================================
    # TOPBAR SALESFORCE (sin JS, navegación 100% estable)
    # ======================================================
    st.markdown(
        """
        <style>
        .topbar{
            width:100%;
            background:white;
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
        </style>

        <div class="topbar">
            <div>
                <div class="topbar-title">CRM Prescripción 2N</div>
                <div class="topbar-sub">Pipeline · Scouting · Seguimiento · Dashboard</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ======================================================
    # NAVEGACIÓN NUEVA (100% fiable)
    # ======================================================
    menu = st.radio(
        "",
        ["Panel", "Proyectos", "Buscar", "Dashboard"],
        horizontal=True,
        label_visibility="collapsed",
        key="nav_radio"
    )

    # ======================================================
    # ROUTING
    # ======================================================
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
