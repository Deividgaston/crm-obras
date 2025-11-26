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


PAGES = {
    "panel": ("Panel", render_panel),
    "proyectos": ("Proyectos", render_proyectos),
    "buscar": ("Buscar", render_buscar),
    "dashboard": ("Dashboard", render_dashboard),
}


def app():
    # ==========================
    # CONFIGURACIÓN GENERAL
    # ==========================
    st.set_page_config(
        page_title="CRM Prescripción 2N",
        layout="wide",
        page_icon="🏗️",
    )

    # Ocultar cabecera, menú y footer de Streamlit
    st.markdown(
        """
        <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ======= CSS extra: diseño compacto + habilitar copiar/pegar =======
    st.markdown(
        """
        <style>
        /* Habilitar seleccionar texto / copiar-pegar en toda la app */
        html, body, [class*="css"], * {
            -webkit-user-select: text !important;
            -moz-user-select: text !important;
            -ms-user-select: text !important;
            user-select: text !important;
        }

        /* Cabecera compacta del app */
        .crm-app-header {
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            padding: 4px 4px 6px 4px;
            margin-bottom: 6px;
            border-bottom: 1px solid #d8dde6;
        }
        .crm-app-header-left {
            display: flex;
            flex-direction: column;
            gap: 0;
        }
        .crm-app-title {
            font-size: 18px;
            font-weight: 600;
            color: #032D60;
            margin: 0;
        }
        .crm-app-subtitle {
            font-size: 11px;
            color: #5A6872;
            margin: 0;
        }
        .crm-app-breadcrumbs {
            font-size: 11px;
            color: #5A6872;
            margin-top: 2px;
        }

        /* Botones de navegación más compactos */
        .stButton > button {
            border-radius: 8px;
            padding: 6px 12px;
            min-height: 0px;
            height: 36px;
            font-size: 14px;
            font-weight: 500;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    inject_apple_style()

    if "page" not in st.session_state:
        st.session_state["page"] = "panel"

    # ==========================
    # CABECERA COMPACTA GLOBAL
    # ==========================
    st.markdown(
        """
        <div class="crm-app-header">
            <div class="crm-app-header-left">
                <div class="crm-app-title">CRM Prescripción 2N</div>
                <div class="crm-app-subtitle">
                    Herramienta interna para seguimiento de prescripción y pipeline de obras.
                </div>
            </div>
            <div class="crm-app-breadcrumbs">
                Panel · Proyectos · Scouting · Dashboard
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ==========================
    # NAVEGACIÓN HORIZONTAL COMPACTA
    # ==========================
    cols = st.columns(len(PAGES))

    for (page_key, (label, _)), col in zip(PAGES.items(), cols):
        with col:
            is_active = st.session_state["page"] == page_key
            # Activo: punto + mismo color de fondo que ya tenías, pero más compacto
            button_label = f"● {label}" if is_active else label
            if st.button(
                button_label,
                use_container_width=True,
                key=f"nav_{page_key}",
            ):
                st.session_state["page"] = page_key
                st.rerun()

    st.markdown("<div style='margin-bottom:6px;'></div>", unsafe_allow_html=True)

    # ==========================
    # RENDER PÁGINA ACTUAL
    # ==========================
    current_page_key = st.session_state.get("page", "panel")
    _, renderer = PAGES.get(current_page_key, PAGES["panel"])
    renderer()


if __name__ == "__main__":
    app()
