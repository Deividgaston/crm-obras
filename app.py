import streamlit as st
from datetime import date, timedelta

# Funciones backend mínimas que usa el panel
from crm_utils import get_clientes, get_proyectos, actualizar_proyecto

# Páginas específicas
from proyectos_page import render_proyectos
from clientes_page import render_clientes_page
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
    background: #0F172A !important; /* fondo oscuro azul marino */
}

/* Contenedor principal */
.block-container {
    padding-top: 1.0rem;
    padding-bottom: 3rem;
    max-width: 1200px;
}

/* Sidebar Apple style */
[data-testid="stSidebar"] {
    background: rgba(15,23,42,0.98) !important;
    backdrop-filter: blur(16px);
    border-right: 1px solid rgba(148,163,184,0.35);
}

[data-testid="stSidebar"] h1, 
[data-testid="stSidebar"] h2, 
[data-testid="stSidebar"] h3 {
    font-weight: 600 !important;
    color: #E5E7EB !important;
}

[data-testid="stSidebar"] p, 
[data-testid="stSidebar"] span {
    color: #9CA3AF !important;
}

/* Títulos */
h1 {
    font-weight: 650 !important;
    letter-spacing: -0.03em;
    font-size: 1.6rem !important;
    color: #E5E7EB !important;
}

h2 {
    font-weight: 600 !important;
    letter-spacing: -0.02em;
    color: #E5E7EB !important;
}

/* Tarjetas genéricas */
.apple-card {
    padding: 14px 18px;
    background: radial-gradient(circle at top left, #1F2937 0%, #020617 70%);
    border-radius: 18px;
    border: 1px solid rgba(148,163,184,0.35);
    box-shadow: 0 20px 60px rgba(15,23,42,0.8);
    margin-bottom: 16px;
}

/* Tarjeta ligera (para listas, tablas, etc.) */
.apple-card-light {
    padding: 14px 18px;
    background: #020617;
    border-radius: 16px;
    border: 1px solid rgba(31,41,55,0.9);
    box-shadow: 0 14px 35px rgba(15,23,42,0.9);
    margin-bottom: 18px;
}

/* Métricas de cabecera tipo Apple dashboard */
.metric-row {
    display: flex;
    gap: 12px;
    margin-top: 4px;
    margin-bottom: 4px;
}

.metric-box {
    flex: 1;
    padding: 12px 14px;
    background: linear-gradient(145deg, #020617 0%, #111827 100%);
    border-radius: 16px;
    border: 1px solid rgba(55,65,81,0.9);
    box-shadow: 0 18px 45px rgba(15,23,42,1);
}

.metric-title {
    font-size: 0.8rem;
    color: #9CA3AF;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

.metric-value {
    font-size: 1.4rem;
    font-weight: 650;
    margin-top: 4px;
    color: #F9FAFB;
}

.metric-sub {
    font-size: 0.78rem;
    color: #6B7280;
    margin-top: 2px;
}

/* Botones más suaves y redondeados */
button[kind="primary"] {
    border-radius: 999px !important;
}

/* Pequeño badge para secciones */
.section-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 9px;
    border-radius: 999px;
    background: rgba(59,130,246,0.15);
    color: #93C5FD;
    font-size: 0.7rem;
    font-weight: 500;
}

/* Texto general en tarjetas */
.apple-card p,
.apple-card-light p,
.apple-card-light h3,
.apple-card-light h4 {
    color: #E5E7EB !important;
}

/* Dataframes: bordes más sutiles en oscuro */
[data-testid="stDataFrame"] div {
    color: #E5E7EB !important;
}

/* Ajuste de radio buttons / selects en oscuro */
label, .stSelectbox label {
    color: #E5E7EB !important;
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
            <h1 style="margin-top: 4px; margin-bottom: 4px;">CRM Prescripción</h1>
            <p style="color:#9CA3AF; margin-bottom: 0; font-size:0.9rem;">
                Visión global de clientes y proyectos. Revisa seguimientos pendientes y
                qué tareas vienen a corto plazo, tanto por cliente como por obra.
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
            <div class="metric-title">CLIENTES EN CRM</div>
            <div class="metric-value">{total_clientes}</div>
            <div class="metric-sub">Arquitecturas, ingenierías, promotoras, integrators</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="metric-box">
            <div class="metric-title">PROYECTOS TOTALES</div>
            <div class="metric-value">{total_proyectos}</div>
            <div class="metric-sub">Histórico de oportunidades trabajadas</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="metric-box">
            <div class="metric-title">PROYECTOS ACTIVOS</div>
            <div class="metric-value">{proyectos_activos}</div>
            <div class="metric-sub">En seguimiento, prescripción, oferta o negociación</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)

    # Bloque de seguimientos próximos / atrasados
    st.markdown(
        """
        <div class="apple-card-light">
            <div class="section-badge">Seguimiento</div>
            <h3 style="margin-top:8px; margin-bottom:4px; font-size:1.0rem;">🚨 Agenda de seguimientos</h3>
            <p style="color:#9CA3AF; margin-top:0; font-size:0.9rem;">
                Proyectos con fecha de seguimiento hoy, atrasada o en los próximos días.
            </p>
        """,
        unsafe_allow_html=True,
    )

    if df_proyectos is None or df_proyectos.empty or "fecha_seguimiento" not in df_proyectos.columns:
        st.info("Todavía no hay proyectos en el sistema o no hay fecha de seguimiento registrada.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    hoy = date.today()

    # Aseguramos que fecha_seguimiento sea comparable como string ISO o date
    df = df_proyectos.copy()
    fechas = []
    for v in df["fecha_seguimiento"]:
        if v is None:
            fechas.append(None)
        elif isinstance(v, date):
            fechas.append(v)
        elif isinstance(v, str):
            try:
                fechas.append(date.fromisoformat(v))
            except Exception:
                fechas.append(None)
        else:
            fechas.append(None)

    df["fecha_seg_parsed"] = fechas
    pendientes = df[
        df["fecha_seg_parsed"].notna()
        & (df["fecha_seg_parsed"] <= hoy)
        & (~df["estado"].isin(["Ganado", "Perdido"]))
    ]

    proximos = df[
        df["fecha_seg_parsed"].notna()
        & (df["fecha_seg_parsed"] > hoy)
        & (df["fecha_seg_parsed"] <= hoy + timedelta(days=7))
        & (~df["estado"].isin(["Ganado", "Perdido"]))
    ]

    if pendientes.empty and proximos.empty:
        st.success("No tienes seguimientos atrasados ni en los próximos 7 días. ✅")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    if not pendientes.empty:
        st.error(f"Tienes {len(pendientes)} proyectos con seguimiento pendiente o atrasado.")
        pendientes = pendientes.sort_values("fecha_seg_parsed")
        for _, row in pendientes.iterrows():
            nombre = row.get("nombre_obra", "Sin nombre")
            fecha_seg = row.get("fecha_seg_parsed", "")
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
                        st.rerun()
                    except Exception as e:
                        st.error(f"No se pudo actualizar la fecha de seguimiento: {e}")

    if not proximos.empty:
        st.markdown("---")
        st.markdown("#### 📆 Próximos 7 días")
        proximos = proximos.sort_values("fecha_seg_parsed")
        for _, row in proximos.iterrows():
            nombre = row.get("nombre_obra", "Sin nombre")
            fecha_seg = row.get("fecha_seg_parsed", "")
            cliente = row.get("cliente_principal", "—")
            estado = row.get("estado", "—")

            st.write(f"• **{nombre}** – {fecha_seg} ({cliente}) · _{estado}_")

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
        render_clientes_page()
    elif menu == "Proyectos":
        render_proyectos()
    elif menu == "Buscar":
        render_buscar()


if __name__ == "__main__":
    main()
