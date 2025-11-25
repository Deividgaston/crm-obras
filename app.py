import streamlit as st

from panel_page import render_panel
from proyectos_page import render_proyectos
from clientes_page import render_clientes
from buscar_page import render_buscar
from dashboard_page import render_dashboard

try:
    from style_injector import inject_apple_style
except Exception:
    def inject_apple_style():
        """Fallback si no existe style_injector."""
        pass


def main():
    # ============================================================
    # CONFIGURACIÓN GENERAL
    # ============================================================
    st.set_page_config(
        page_title="CRM Prescripción 2N",
        layout="wide",
        page_icon="🏗️",
    )

    inject_apple_style()

    # ============================================================
    # SIDEBAR / MENÚ
    # ============================================================
    with st.sidebar:
        st.markdown("### 🏗️ CRM Prescripción")
        st.caption("Tu cockpit de proyectos, clientes y analítica.")
        st.markdown("---")

        menu = st.radio(
            "Ir a:",
            ["Panel de Control", "Proyectos", "Clientes", "Buscar", "Dashboard"],
            index=0,
        )

    # ============================================================
    # ROUTING PRINCIPAL
    # ============================================================
    if menu == "Panel de Control":
        render_panel()

    elif menu == "Proyectos":
        render_proyectos()

    elif menu == "Clientes":
        render_clientes()

    elif menu == "Buscar":
        render_buscar()

    elif menu == "Dashboard":
        render_dashboard()


if __name__ == "__main__":
    main()
