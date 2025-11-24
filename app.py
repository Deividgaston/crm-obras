import streamlit as st
from panel_page import render_panel
from proyectos_page import render_proyectos
from clientes_page import render_clientes
from buscar_page import render_buscar
from crm_utils import delete_all_proyectos

st.set_page_config(
    page_title="CRM Prescripción",
    layout="wide",
    page_icon="🏗️",
)

# -------------------------
# LATERAL NAV
# -------------------------
st.sidebar.title("📌 Navegación")
pagina = st.sidebar.radio(
    "Ir a:",
    ["Panel", "Proyectos", "Clientes", "Buscar"]
)

# -------------------------
# RENDERIZADO
# -------------------------
if pagina == "Panel":
    render_panel()

elif pagina == "Proyectos":
    render_proyectos()

elif pagina == "Clientes":
    render_clientes()

elif pagina == "Buscar":
    render_buscar()

# -------------------------
# BOTÓN PARA BORRAR TODO
# -------------------------
st.sidebar.markdown("---")
st.sidebar.markdown("### ⚠️ Opciones avanzadas")

# Expansor con seguridad
with st.sidebar.expander("🧨 Borrar TODOS los proyectos"):
    st.warning("Esta acción eliminará **todos los datos** de la tabla 'proyectos'.")
    confirmado = st.checkbox("Entiendo las consecuencias")

    if confirmado:
        if st.button("❌ Borrar todos los proyectos", type="primary"):
            total = delete_all_proyectos()
            st.success(f"Proyectos eliminados: {total}")
            st.balloons()
            st.experimental_rerun()
