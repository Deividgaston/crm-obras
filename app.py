import streamlit as st
from datetime import date, timedelta

# 🔥 Firebase se inicializa AQUÍ, antes de cargar crm_utils
# ----------------------------------------------------------
import json
import firebase_admin
from firebase_admin import credentials

if not firebase_admin._apps:
    try:
        key_str = st.secrets["firebase_key"]
        key_dict = json.loads(key_str)
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"No se pudo inicializar Firebase: {e}")
        st.stop()


# ----------------------------------------------------------
# Ahora que Firebase YA está inicializado:
# → YA se puede cargar crm_utils sin errores
# ----------------------------------------------------------
from crm_utils import get_clientes, get_proyectos, add_cliente, actualizar_proyecto

# Páginas
from proyectos_page import render_proyectos
from buscar_page import render_buscar
from clientes_page import render_clientes_page  # si lo usas


# ==========================
# CONFIGURACIÓN
# ==========================
st.set_page_config(
    page_title="CRM Prescripción",
    layout="wide",
    page_icon="🏗️",
)


# ==========================
# ESTILO APPLE
# ==========================
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
}
.block-container {
    padding-top: 1rem;
    max-width: 1400px;
}
h1 { font-size: 1.55rem !important; font-weight: 650; }
h2 { font-size: 1.2rem !important; font-weight: 600; }
h3 { font-size: 1rem !important; font-weight: 600; }
.section-badge {
    padding: 3px 9px;
    background: rgba(37,99,235,0.1);
    border-radius: 999px;
    font-size: 0.70rem;
    color: #2563EB;
}
.apple-card {
    padding: 15px 20px;
    border-radius: 16px;
    background: rgba(255,255,255,0.05);
}
</style>
""", unsafe_allow_html=True)


# ==========================
# PANEL
# ==========================
def render_panel_control():
    st.markdown("""
    <div class="apple-card">
        <div class="section-badge">Panel</div>
        <h1>CRM Prescripción</h1>
        <p style="font-size:0.9rem;color:#999">Resumen del estado general</p>
    </div>
    """, unsafe_allow_html=True)

    df_clientes = get_clientes()
    df_proy = get_proyectos()

    col1, col2, col3 = st.columns(3)
    col1.metric("Clientes", len(df_clientes) if not df_clientes.empty else 0)
    col2.metric("Proyectos", len(df_proy) if not df_proy.empty else 0)
    col3.metric(
        "Activos",
        len(df_proy[~df_proy["estado"].isin(["Ganado", "Perdido"])])
        if not df_proy.empty else 0
    )


# ==========================
# MAIN APP
# ==========================
def main():
    with st.sidebar:
        st.markdown("### 🏗️ CRM Prescripción")
        st.caption("Cockpit de prescripción profesional")
        st.markdown("---")

    menu = st.sidebar.radio(
        "Ir a:",
        ["Panel de Control", "Clientes", "Proyectos", "Buscar"]
    )

    if menu == "Panel de Control":
        render_panel_control()
    elif menu == "Clientes":
        render_clientes_page()
    elif menu == "Proyectos":
        render_proyectos()
    elif menu == "Buscar":
        render_buscar()


if __name__ == "__main__":
    main()
