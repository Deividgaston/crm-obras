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
    # =========================================
    # CONFIGURACIÓN GENERAL
    # =========================================
    st.set_page_config(
        page_title="CRM Prescripción 2N",
        layout="wide",
        page_icon="🏗️",
    )

    inject_apple_style()

    # =========================================
    # TOP BAR TIPO SALESFORCE (SIN SIDEBAR)
    # =========================================
    col_left, col_right = st.columns([3, 7])

    with col_left:
        st.markdown(
            """
            <div class="crm-topbar">
                <div>
                    <div class="crm-topbar-title">CRM Prescripción 2N</div>
                    <div class="crm-topbar-subtitle">
                        Proyectos, agenda y analítica en una sola vista.
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_right:
        st.markdown(
            """
            <style>
            .top-nav-container {
                display: flex;
                justify-content: flex-end;
                align-items: center;
                gap: 0.25rem;
                margin-top: 0.15rem;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # Radio horizontal como barra de navegación compacta
        menu = st.radio(
            "Navegación",
            ["Panel", "Proyectos", "Buscar", "Dashboard"],
            horizontal=True,
            label_visibility="collapsed",
        )

    # =========================================
    # ROUTING PRINCIPAL
    # =========================================
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
