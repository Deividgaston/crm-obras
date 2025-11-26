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

    # Ocultar cabecera, menú y footer Streamlit
    st.markdown("""
        <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}

            html, body, [class*="css"], * {
                -webkit-user-select: text !important;
                user-select: text !important;
            }

            /* Botones compactos */
            .stButton > button {
                border-radius: 8px;
                padding: 4px 10px !important;
                min-height: 0px !important;
                height: 34px !important;
                font-size: 14px !important;
                margin-bottom: 0px !important;
            }

            /* Eliminar espacio automático entre secciones */
            .block-container {
                padding-top: 6px !important;
            }

            /* Quitar espacio debajo de los botones */
            .nav-spacer {
                margin: 0;
                padding: 0;
                height: 4px;
            }
        </style>
    """, unsafe_allow_html=True)

    inject_apple_style()

    if "page" not in st.session_state:
        st.session_state["page"] = "panel"

    # ========================== CABECERA GLOBAL ==========================
    st.markdown(
        """
        <div style="display:flex;justify-content:space-between;
                    padding:0px 0px 4px 0px;margin-bottom:4px;
                    border-bottom:1px solid #d8dde6;">
            <div style="font-size:12px;color:#5A6872;">
                Herramienta interna para seguimiento de prescripción y pipeline de obras.
            </div>

            <div style="font-size:12px;color:#5A6872;">
                Panel · Proyectos · Scouting · Dashboard
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ========================== BOTONES NAV ==========================
    cols = st.columns(len(PAGES))

    for (key, (label, _)), col in zip(PAGES.items(), cols):
        with col:
            active = st.session_state["page"] == key
            text = f"● {label}" if active else label
            if st.button(text, use_container_width=True, key=f"nav_{key}"):
                st.session_state["page"] = key
                st.rerun()

    # Spacer super compacto
    st.markdown("<div class='nav-spacer'></div>", unsafe_allow_html=True)

    # ========================== CONTENIDO ==========================
    current = st.session_state["page"]
    _, renderer = PAGES.get(current, PAGES["panel"])
    renderer()


if __name__ == "__main__":
    app()
