import streamlit as st

from panel_page import render_panel
from proyectos_page import render_proyectos
from clientes_page import render_clientes
from buscar_page import render_buscar

from crm_utils import delete_all_proyectos

# Intento cargar estilos si existen
try:
    from style_injector import inject_apple_style
except:
    def inject_apple_style():
        pass


# ============================================================
# CONFIG GENERAL
# ============================================================
st.set_page_config(
    page_title="CRM Prescripción",
    layout="wide",
    page_icon="🏗️",
)

inject_apple_style()


# ============================================================
# MENÚ LATERAL
# ============================================================
st.sidebar.title("📌 Navegación")

pagina = st.sidebar.radio(
    "Ir a:",
    ["Panel", "Proyectos", "Clientes", "Buscar"],
    index=0
)


# ============================================================
# RENDER PÁGINAS
# ============================================================
if pagina == "Panel":
    render_panel()

elif pagina == "Proyectos":
    render_proyectos()

elif pagina == "Clientes":
    render_clientes()

elif pagina == "Buscar":
    render_buscar()


# ============================================================
# OPCIONES AVANZADAS
# ============================================================
st.sidebar.markdown("---")
st.sidebar.subheader("⚠️ Opciones avanzadas")

with st.sidebar.expander("🧨 Borrar TODOS los proyectos"):
    st.warning(
        "Esta acción eliminará *todos los proyectos* de la base de datos.\n\n"
        "No se puede deshacer."
    )
    confirmar = st.checkbox("Entiendo las consecuencias")

    if confirmar:
        if st.button("❌ Borrar todos los proyectos"):
            total = delete_all_proyectos()
            st.success(f"Se han eliminado {total} proyectos.")
            st.toast("Base de datos limpiada.", icon="🧹")
            st.experimental_rerun()
