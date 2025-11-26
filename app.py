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

LOGO_PATH = "Logo Dgo insight.png"  # archivo junto a app.py


def app():
    st.set_page_config(
        page_title="CRM Prescripción 2N",
        layout="wide",
        page_icon="🏗️",
    )

    # Estilos globales
    st.markdown(
        """
        <style>
            #MainMenu, header, footer {visibility: hidden;}
            html, body, * { user-select:text !important; }

            .block-container {
                padding-top: 1rem !important;
            }

            .stButton > button {
                border-radius: 8px;
                height: 34px !important;
                font-size: 14px !important;
                padding: 3px 10px !important;
                margin: 0 !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    inject_apple_style()

    if "page" not in st.session_state:
        st.session_state["page"] = "panel"

    # ===============================
    #   CABECERA CON LOGO
    # ===============================
    st.markdown(
        "<div style='display:flex;align-items:center;margin-bottom:10px;'>",
        unsafe_allow_html=True,
    )

    # Intentar mostrar el logo; si falla, mostrar texto
    try:
        st.image(LOGO_PATH, width=240)
    except Exception:
        st.markdown(
            "<div style='font-size:22px;font-weight:700;color:#032D60;'>DGO Insight</div>",
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # ===============================
    #   BOTONES DE NAVEGACIÓN
    # ===============================
    cols = st.columns(len(PAGES))
    for (key, (label, _)), col in zip(PAGES.items(), cols):
        with col:
            active = st.session_state["page"] == key
            text = f"● {label}" if active else label
            if st.button(text, use_container_width=True):
                st.session_state["page"] = key
                st.rerun()

    # ===============================
    #   CONTENIDO DE LA PÁGINA
    # ===============================
    _, renderer = PAGES[st.session_state["page"]]
    renderer()


if __name__ == "__main__":
    app()
