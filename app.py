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

    inject_apple_style()

    if "page" not in st.session_state:
        st.session_state["page"] = "panel"

    # ==========================
    # ENCABEZADO TIPO SALESFORCE
    # ==========================
    st.markdown(
        """
        <div class="apple-card" style="margin-bottom:12px;">
            <div style="font-size:13px;color:#5A6872;margin-bottom:2px;">
                Panel · Proyectos · Scouting · Dashboard
            </div>
            <h2 style="margin:0;color:#032D60;">CRM Prescripción 2N</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ==========================
    # NAVEGACIÓN HORIZONTAL
    # ==========================
    cols = st.columns(len(PAGES))

    for (page_key, (label, _)), col in zip(PAGES.items(), cols):
        with col:
            is_active = st.session_state["page"] == page_key
            button_label = label
            if is_active:
                button_label = f"● {label}"
            if st.button(
                button_label,
                use_container_width=True,
                key=f"nav_{page_key}",
            ):
                st.session_state["page"] = page_key
                st.rerun()

    st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)

    # ==========================
    # RENDER PÁGINA ACTUAL
    # ==========================
    current_page_key = st.session_state.get("page", "panel")
    label, renderer = PAGES.get(current_page_key, PAGES["panel"])

    renderer()


if __name__ == "__main__":
    app()
