import streamlit as st
from datetime import date, timedelta

# Funciones de acceso a datos (Firestore) y utilidades
from crm_utils import (
    get_clientes,
    get_proyectos,
    add_cliente,
    actualizar_proyecto,
)

# Páginas específicas
from proyectos_page import render_proyectos
from buscar_page import render_buscar

# ==========================
# CONFIGURACIÓN GENERAL
# ==========================
st.set_page_config(
    page_title="CRM Prescripción",
    layout="wide",
    page_icon="🏗️",
)

# ==========================
# ESTILO APPLE-LIKE
# ==========================
st.markdown("""
<style>
/* Fuente tipo SF / Inter */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
    background: #F3F4F6 !important;
}

/* Contenedor principal */
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
    max-width: 1200px;
}

/* Sidebar Apple style */
[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.92) !important;
    backdrop-filter: blur(16px);
    border-right: 1px solid rgba(0,0,0,0.06);
}

[data-testid="stSidebar"] h1, 
[data-testid="stSidebar"] h2, 
[data-testid="stSidebar"] h3 {
    font-weight: 600 !important;
}

/* Títulos */
h1 {
    font-weight: 650 !important;
    letter-spacing: -0.03em;
    font-size: 2.1rem !important;
}

h2 {
    font-weight: 600 !important;
    letter-spacing: -0.02em;
}

/* Tarjetas genéricas */
.apple-card {
    padding: 18px 22px;
    background: radial-gradient(circle at top left, #FFFFFF 0%, #F9FAFB 70%);
    border-radius: 18px;
    border: 1px solid rgba(15,23,42,0.05);
    box-shadow: 0 18px 45px rgba(15,23,42,0.08);
    margin-bottom: 18px;
}

/* Tarjeta ligera (para listas, tablas, etc.) */
.apple-card-light {
    padding: 16px 20px;
    background: #FFFFFF;
    border-radius: 16px;
    border: 1px solid rgba(148,163,184,0.22);
    box-shadow: 0 10px 25px rgba(15,23,42,0.05);
    margin-bottom: 18px;
}

/* Métricas de cabecera tipo Apple dashboard */
.metric-row {
    display: flex;
    gap: 16px;
    margin-top: 6px;
    margin-bottom: 6px;
}

.metric-box {
    flex: 1;
    padding: 16px 18px;
    background: linear-gradient(145deg, #FFFFFF 0%, #F3F4F6 100%);
    border-radius: 16px;
    border: 1px solid rgba(148,163,184,0.35);
    box-shadow: 0 14px 30px rgba(15,23,42,0.12);
}

.metric-title {
    font-size: 0.86rem;
    color: #6B7280;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.metric-value {
    font-size: 1.8rem;
    font-weight: 650;
    margin-top: 4px;
    color: #0F172A;
}

.metric-sub {
    font-size: 0.78rem;
    color: #9CA3AF;
    margin-top: 2px;
}

/* Botones más suaves y redondeados */
button[kind="primary"] {
    border-radius: 999px !important;
}

/* Campos de formulario redondeados */
textarea, input, select {
    border-radius: 10px !important;
}

/* Pequeño badge para secciones */
.section-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 999px;
    background: rgba(37,99,235,0.08);
    color: #1D4ED8;
    font-size: 0.75rem;
    font-weight: 500;
}

/* Etiqueta de estado (podrías usarlo en proyectos más adelante) */
.status-pill {
    display: inline-flex;
    align-items: center;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 500;
}

/* Colores de estados de ejemplo */
.status-ganado {
    background: rgba(34,197,94,0.12);
    color: #15803D;
}
.status-perdido {
    background: rgba(248,113,113,0.12);
    color: #B91C1C;
}
.status-seguimiento {
    background: rgba(59,130,246,0.12);
    color: #1D4ED8;
}

</style>
""", unsafe_allow_html=True)


# ==========================
# PÁGINA: PANEL DE CONTROL
# ==========================
def render_panel_control():
    # Cabecera tipo Apple
    st.markdown(
        """
        <div class="apple-card">
            <div class="section-badge">Panel general</div>
            <h1 style="margin-top: 6px;">CRM Prescripción</h1>
            <p style="color:#6B7280; margin-bottom: 0;">
                Visión global de clientes y proyectos en curso. 
                Revisa seguimientos pendientes y el pulso de la prescripción.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_clientes = get_clientes()
    df_proyectos = get_proyectos()

    total_clientes = 0 if df_clientes is None or df_clientes.empty else len(df_clientes)
    total_proyectos = 0 if df_proyectos is None or df_proyectos.empty else len(df_proyectos)

    proyectos_activos = 0
    if df_proyectos is not None and not df_proyectos.empty and "estado" in df_proyectos.columns:
        proyectos_activos = len(
            df_proyectos[~df_proyectos["estado"].isin(["Ganado", "Perdido"])]
        )

    # Métricas Apple-style
    st.markdown("<div class='metric-row'>", unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="metric-box">
            <div class="metric-title">Clientes en CRM</div>
            <div class="metric-value">{total_clientes}</div>
            <div class="metric-sub">Arquitecturas, ingenierías, promotoras, integrators</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="metric-box">
            <div class="metric-title">Proyectos totales</div>
            <div class="metric-value">{total_proyectos}</div>
            <div class="metric-sub">Histórico de oportunidades trabajadas</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="metric-box">
            <div class="metric-title">Proyectos activos</div>
            <div class="metric-value">{proyectos_activos}</div>
            <div class="metric-sub">En seguimiento, prescripción, oferta o negociación</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)

    # Bloque de seguimientos
    st.markdown(
        """
        <div class="apple-card-light">
            <div class="section-badge">Seguimiento</div>
            <h3 style="margin-top:10px; margin-bottom:4px;">🚨 Seguimientos pendientes</h3>
            <p style="color:#6B7280; margin-top:0; font-size:0.9rem;">
                Proyectos con fecha de seguimiento hoy o atrasada. 
                Mantén el radar siempre al día.
            </p>
        """,
        unsafe_allow_html=True,
    )

    if df_proyectos is None or df_proyectos.empty or "fecha_seguimiento" not in df_proyectos.columns:
        st.info("Todavía no hay proyectos en el sistema o no hay fecha de seguimiento registrada.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    hoy = date.today()

    pendientes = df_proyectos[
        df_proyectos["fecha_seguimiento"].notna()
        & (df_proyectos["fecha_seguimiento"] <= hoy)
        & (~df_proyectos["estado"].isin(["Ganado", "Perdido"]))
    ]

    if pendientes.empty:
        st.success("No tienes seguimientos atrasados. ✅")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    st.error(f"Tienes {len(pendientes)} proyectos con seguimiento pendiente.")

    pendientes = pendientes.sort_values("fecha_seguimiento")

    for _, row in pendientes.iterrows():
        nombre = row.get("nombre_obra", "Sin nombre")
        fecha_seg = row.get("fecha_seguimiento", "")
        cliente = row.get("cliente_principal", "—")
        estado = row.get("estado", "—")
        notas = row.get("notas_seguimiento", "")

        with st.expander(f"⏰ {nombre} – {fecha_seg} ({cliente})"):
            st.write(f"**Estado actual:** {estado}")
            st.write(f"**Notas:** {notas or '—'}")

            if st.button("Posponer 1 semana", key=f"posponer_{row['id']}"):
                nueva_fecha = (hoy + timedelta(days=7)).isoformat()
                try:
                    actualizar_proyecto(row["id"], {"fecha_seguimiento": nueva_fecha})
                    st.success(f"Seguimiento pospuesto a {nueva_fecha}.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"No se pudo actualizar la fecha de seguimiento: {e}")

    st.markdown("</div>", unsafe_allow_html=True)


# ==========================
# PÁGINA: CLIENTES
# ==========================
def render_clientes():
    st.markdown(
        """
        <div class="apple-card">
            <div class="section-badge">Relaciones</div>
            <h1 style="margin-top: 6px;">Clientes</h1>
            <p style="color:#6B7280; margin-bottom: 0;">
                Gestiona ingenierías, arquitecturas, promotoras e integrators clave
                para la prescripción.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Alta de cliente
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.markdown("#### ➕ Añadir nuevo cliente", unsafe_allow_html=True)

    with st.form("form_cliente"):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre / persona de contacto")
            empresa = st.text_input("Empresa")
            tipo_cliente = st.selectbox(
                "Tipo de cliente",
                ["Ingeniería", "Promotora", "Arquitectura", "Integrator Partner", "Otro"],
            )
        with col2:
            email = st.text_input("Email")
            telefono = st.text_input("Teléfono")
            ciudad = st.text_input("Ciudad")
            provincia = st.text_input("Provincia")

        notas = st.text_area("Notas (proyectos, relación, info importante)")

        enviar = st.form_submit_button("Guardar cliente")

    if enviar:
        if not nombre and not empresa:
            st.warning("Pon al menos un nombre o una empresa.")
        else:
            try:
                add_cliente(
                    {
                        "nombre": nombre,
                        "empresa": empresa,
                        "tipo_cliente": tipo_cliente,
                        "email": email,
                        "telefono": telefono,
                        "ciudad": ciudad,
                        "provincia": provincia,
                        "notas": notas,
                    }
                )
                st.success("Cliente guardado correctamente.")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"No se pudo guardar el cliente: {e}")

    st.markdown("</div>", unsafe_allow_html=True)

    # Listado
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.markdown("#### 📋 Listado de clientes", unsafe_allow_html=True)

    df_clientes = get_clientes()
    if df_clientes is None or df_clientes.empty:
        st.info("Aún no hay clientes en el CRM.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    cols_mostrar = ["nombre", "empresa", "tipo_cliente", "email", "telefono", "ciudad", "provincia"]
    cols_mostrar = [c for c in cols_mostrar if c in df_clientes.columns]

    st.dataframe(
        df_clientes[cols_mostrar],
        hide_index=True,
        use_container_width=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)


# ==========================
# MAIN
# ==========================
def main():
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
