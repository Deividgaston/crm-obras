import streamlit as st

from panel_page import render_panel
from proyectos_page import render_proyectos
from clientes_page import render_clientes
from buscar_page import render_buscar

try:
    from style_injector import inject_apple_style
except:
    def inject_apple_style():
        pass


# ==========================
# CONFIGURACIÓN GENERAL
# ==========================
st.set_page_config(
    page_title="CRM Prescripción",
    layout="wide",
    page_icon="🏗️",
)

inject_apple_style()


# ==========================
# SIDEBAR / MENÚ
# ==========================
with st.sidebar:
    st.markdown("### 🏗️ CRM Prescripción")
    st.caption("Tu cockpit de proyectos, clientes y scouting.")
    st.markdown("---")

menu = st.sidebar.radio(
    "Ir a:",
    ["Panel de Control", "Proyectos", "Clientes", "Buscar"],
    index=0,
)


# ==========================
# ROUTING
# ==========================
if menu == "Panel de Control":
    render_panel()
elif menu == "Proyectos":
    render_proyectos()
elif menu == "Clientes":
    render_clientes()
elif menu == "Buscar":
    render_buscar()
