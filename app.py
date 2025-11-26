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

    st.set_page_config(
        page_title="CRM Prescripción 2N",
        layout="wide",
        page_icon="🏗️",
    )

    # === Estilo global compactado ===
    st.markdown("""
        <style>
            #MainMenu, header, footer {visibility: hidden;}

            html, body, * { user-select:text !important; }

            /* Ultra compact spacing */
            .block-container {
                padding-top: 1px !important;
            }

            /* Botones navegación */
            .stButton > button {
                border-radius: 8px;
                height: 34px !important;
                font-size: 14px !important;
                padding: 3px 10px !important;
            }

            .nav-gap { height: 2px; margin:0; padding:0; }
        </style>
    """, unsafe_allow_html=True)

    inject_apple_style()

    if "page" not in st.session_state:
        st.session_state["page"] = "panel"

    # === Título DGO Insight ===
    st.markdown("""
        <div style="font-size:22px;font-weight:700;color:#032D60;margin-bottom:2px;">
            DGO Insight
        </div>
        <div style="font-size:12px;color:#5A6872;margin-bottom:6px;">
            Herramienta interna para seguimiento de prescripción y pipeline de obras.
        </div>
    """, unsafe_allow_html=True)

    # === Botones de navegación ===
    cols = st.columns(len(PAGES))
    for (key, (label, _)), col in zip(PAGES.items(), cols):
        with col:
            active = st.session_state["page"] == key
            text = f"● {label}" if active else label
            if st.button(text, use_container_width=True):
                st.session_state["page"] = key
                st.rerun()

    # Pequeñísimo hueco (2px)
    st.markdown("<div class='nav-gap'></div>", unsafe_allow_html=True)

    # === Cargar página seleccionada ===
    _, renderer = PAGES[st.session_state["page"]]
    renderer()


if __name__ == "__main__":
    app()
