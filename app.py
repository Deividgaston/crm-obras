import streamlit as st
from datetime import date, timedelta

# Estilos globales Apple-Blue
from style_injector import inject_global_styles

# Utilidades de datos (Firestore)
from crm_utils import (
    get_clientes,
    get_proyectos,
    actualizar_proyecto,
)

# Páginas específicas
from clientes_page import render_clientes
from proyectos_page import render_proyectos
from buscar_page import render_buscar


# =========================================================
# PANEL DE CONTROL
# =========================================================
def render_panel_control():
    # --- Cabecera compacta estilo Apple ---
    st.markdown(
        """
        <div class="apple-card">
            <div class="section-badge">Panel general</div>
            <h3 style="margin-top: 6px; font-size:1.25rem;">CRM Prescripción · Vista global</h3>
            <p style="color:#9FB3D1; margin-bottom: 0; font-size:0.85rem;">
                Resumen de clientes, proyectos activos y seguimientos pendientes
                para mantener el pipeline siempre controlado.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- Carga de datos ---
    try:
        df_clientes = get_clientes()
    except Exception as e:
        st.error(f"No se pudieron cargar los clientes: {e}")
        df_clientes = None

    try:
        df_proyectos = get_proyectos()
    except Exception as e:
        st.error(f"No se pudieron cargar los proyectos: {e}")
        df_proyectos = None

    total_clientes = 0 if df_clientes is None or df_clientes.empty else len(df_clientes)
    total_proyectos = 0 if df_proyectos is None or df_proyectos.empty else len(df_proyectos)

    proyectos_activos = 0
    if df_proyectos is not None and not df_proyectos.empty and "estado" in df_proyectos.columns:
        proyectos_activos = len(
            df_proyectos[~df_proyectos["estado"].isin(["Ganado", "Perdido"])]
        )

    # --- Métricas principales ---
    with st.container():
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Clientes en CRM", total_clientes, help="Arquitecturas, ingenierías, promotoras, integrators…")

        with col2:
            st.metric("Proyectos totales", total_proyectos, help="Histórico completo de oportunidades.")

        with col3:
            st.metric("Proyectos activos", proyectos_activos,
                      help="En detección, seguimiento, prescripción, oferta o negociación.")

    # --- Bloque de seguimientos pendientes ---
    st.markdown(
        """
        <div class="apple-card-light">
            <div class="section-badge">Seguimiento</div>
            <h4 style="margin-top:10px; margin-bottom:4px; font-size:1.0rem;">🚨 Seguimientos pendientes</h4>
            <p style="color:#9CA3AF; margin-top:0; font-size:0.8rem;">
                Proyectos con fecha de seguimiento hoy o atrasada. 
                Aquí ves el radar de llamadas, emails y visitas que no se pueden escapar.
            </p>
        """,
        unsafe_allow_html=True,
    )

    if df_proyectos is None or df_proyectos.empty or "fecha_seguimiento" not in df_proyectos.columns:
        st.info("Todavía no hay proyectos en el sistema o no hay fecha de seguimiento registrada.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    hoy = date.today()

    # Filtros rápidos del panel
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        estados_disp = sorted(df_proyectos["estado"].dropna().unique().tolist()) if "estado" in df_proyectos.columns else []
        estado_filtro = st.selectbox(
            "Filtrar por estado",
            ["Todos"] + estados_disp,
            index=0,
        )
    with col_f2:
        ciudades_disp = sorted(df_proyectos["ciudad"].dropna().unique().tolist()) if "ciudad" in df_proyectos.columns else []
        ciudad_filtro = st.selectbox(
            "Filtrar por ciudad",
            ["Todas"] + ciudades_disp,
            index=0,
        )

    pendientes = df_proyectos[
        df_proyectos["fecha_seguimiento"].notna()
        & (df_proyectos["fecha_seguimiento"] <= hoy)
        & (~df_proyectos["estado"].isin(["Ganado", "Perdido"]))
    ].copy()

    if estado_filtro != "Todos":
        pendientes = pendientes[pendientes["estado"] == estado_filtro]

    if ciudad_filtro != "Todas":
        pendientes = pendientes[pendientes["ciudad"] == ciudad_filtro]

    if pendientes.empty:
        st.success("No tienes seguimientos atrasados con los filtros actuales. ✅")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    st.error(f"Tienes {len(pendientes)} proyectos con seguimiento pendiente.")

    pendientes = pendientes.sort_values("fecha_seguimiento")

    for _, row in pendientes.iterrows():
        nombre = row.get("nombre_obra", "Sin nombre")
        fecha_seg = row.get("fecha_seguimiento", "")
        cliente = row.get("cliente_principal", "—")
        estado = row.get("estado", "—")
        ciudad = row.get("ciudad", "—")
        notas = row.get("notas_seguimiento", "")

        titulo_expander = f"⏰ {nombre} – {fecha_seg} · {cliente} ({ciudad})"

        with st.expander(titulo_expander):
            st.write(f"**Estado actual:** {estado}")
            st.write(f"**Notas:** {notas or '—'}")

            cols_btn = st.columns(3)
            with cols_btn[0]:
                if st.button("📅 Posponer 1 semana", key=f"pos1_{row['id']}"):
                    nueva_fecha = hoy + timedelta(days=7)
                    try:
                        actualizar_proyecto(row["id"], {"fecha_seguimiento": nueva_fecha.isoformat()})
                        st.success(f"Seguimiento pospuesto a {nueva_fecha}.")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"No se pudo actualizar la fecha de seguimiento: {e}")
            with cols_btn[1]:
                if st.button("📅 Posponer 1 mes", key=f"pos30_{row['id']}"):
                    nueva_fecha = hoy + timedelta(days=30)
                    try:
                        actualizar_proyecto(row["id"], {"fecha_seguimiento": nueva_fecha.isoformat()})
                        st.success(f"Seguimiento pospuesto a {nueva_fecha}.")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"No se pudo actualizar la fecha de seguimiento: {e}")
            with cols_btn[2]:
                st.caption("Consejo: usa la pestaña **Proyectos → Detalle** para registrar la llamada o reunión.")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# MAIN
# =========================================================
def main():
    st.set_page_config(
        page_title="CRM Prescripción",
        layout="wide",
        page_icon="🏗️",
    )

    # Inyectar estilos Apple-Blue
    inject_global_styles()

    # Sidebar
    with st.sidebar:
        st.markdown("### 🏗️ CRM Prescripción")
        st.caption("Tu cockpit de proyectos, clientes y scouting.")
        st.markdown("---")

    menu = st.sidebar.radio(
        "Ir a:",
        ["Panel de Control", "Clientes", "Proyectos", "Buscar"],
    )

    if menu == "Panel de Control":
        render_panel_control()
    elif menu == "Clientes":
        render_clientes()
    elif menu == "Proyectos":
        render_proyectos()
    elif menu == "Buscar":
        render_buscar()


if __name__ == "__main__":
    main()
