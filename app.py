import streamlit as st

# Páginas
from panel_page import render_panel
from proyectos_page import render_proyectos
from buscar_page import render_buscar
from dashboard_page import render_dashboard

# Estilos
try:
    from style_injector import inject_apple_style
except Exception:
    def inject_apple_style():
        pass


def app():
    # ======================================================
    # CONFIG STREAMLIT
    # ======================================================
    st.set_page_config(
        page_title="CRM Prescripción 2N",
        layout="wide",
        page_icon="🏗️",
        initial_sidebar_state="collapsed",
    )

    # Inyectamos estilo Salesforce global
    inject_apple_style()

    # ======================================================
    # TOPBAR SALESFORCE
    # ======================================================
    st.markdown(
        """
        <style>
        .topbar-container {
            width: 100%;
            background: #ffffff;
            border-bottom: 1px solid #d8dde6;
            padding: 4px 18px 2px 18px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .topbar-title {
            font-size: 17px;
            font-weight: 600;
            color: #032D60;
            margin: 0;
            padding: 0;
        }
        .topbar-sub {
            font-size: 12px;
            color: #5A6872;
            margin-top: -4px;
        }
        .topbar-nav {
            display: flex;
            gap: 14px;
            padding-right: 10px;
        }
        .topbar-nav-item {
            font-size: 13.5px;
            font-weight: 500;
            padding: 6px 10px;
            border-radius: 4px;
            cursor: pointer;
            color: #032D60;
        }
        .topbar-nav-item-active {
            background: #e5f1fb;
            border: 1px solid #c8e1fb;
        }
        </style>

        <div class="topbar-container">
            <div>
                <div class="topbar-title">CRM Prescripción 2N</div>
                <div class="topbar-sub">Proyectos · Pipeline · Scouting · Dashboard</div>
            </div>
            <div class="topbar-nav">
        """,
        unsafe_allow_html=True,
    )

    # ======================================================
    # NAVEGACIÓN SIN SIDEBAR
    # ======================================================
    # Mapa de páginas
    pages = {
        "Panel": render_panel,
        "Proyectos": render_proyectos,
        "Buscar": render_buscar,
        "Dashboard": render_dashboard,
    }

    # Estado seleccionado
    if "page" not in st.session_state:
        st.session_state["page"] = "Panel"

    # Render botones tipo Salesforce
    nav_html = ""
    for name in pages:
        is_active = "topbar-nav-item-active" if st.session_state["page"] == name else ""
        nav_html += f"""
            <div class="topbar-nav-item {is_active}"
                 onClick="document.dispatchEvent(new CustomEvent('selectPage', {{detail: '{name}'}}))">
                {name}
            </div>
        """

    st.markdown(nav_html, unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

    # JS para navegación (sin recargar barra)
    st.markdown(
        """
        <script>
        document.addEventListener('selectPage', function(e) {
            const pageName = e.detail;
            window.parent.postMessage(
                { type: "streamlit:setSessionState", key: "page", value: pageName }, "*"
            );
        });
        </script>
        """,
        unsafe_allow_html=True,
    )

    # Recarga estado de página
    if "page" in st.session_state:
        selected_page = st.session_state["page"]
    else:
        selected_page = "Panel"

    # ======================================================
    # RENDER DE LA PÁGINA SELECCIONADA
    # ======================================================
    pages[selected_page]()


if __name__ == "__main__":
    app()
