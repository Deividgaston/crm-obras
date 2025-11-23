import streamlit as st
from datetime import date, datetime, timedelta

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
from clientes_page import render_clientes_page  # tu página de clientes


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
st.markdown(
    """
<style>
/* Fuente tipo SF / Inter */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
    background: #020617 !important;  /* fondo dark azul marino */
}

/* Contenedor principal */
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2.4rem;
    max-width: 1200px;
}

/* Sidebar Apple style */
[data-testid="stSidebar"] {
    background: rgba(15,23,42,0.96) !important; /* slate-900 */
    backdrop-filter: blur(16px);
    border-right: 1px solid rgba(15,23,42,0.85);
}

[data-testid="stSidebar"] h1, 
[data-testid="stSidebar"] h2, 
[data-testid="stSidebar"] h3 {
    font-weight: 600 !important;
    color: #E5E7EB !important;
}

/* Títulos globales */
h1 {
    font-weight: 640 !important;
    letter-spacing: -0.03em;
    font-size: 1.7rem !important;
    color: #E5E7EB !important;
}

h2 {
    font-weight: 600 !important;
    letter-spacing: -0.02em;
    font-size: 1.25rem !important;
    color: #E5E7EB !important;
}

/* Tarjetas principales */
.apple-card {
    padding: 16px 20px;
    background: radial-gradient(circle at top left, #0F172A 0%, #020617 70%);
    border-radius: 18px;
    border: 1px solid rgba(148,163,184,0.28);
    box-shadow: 0 24px 60px rgba(15,23,42,0.85);
    margin-bottom: 18px;
}

/* Tarjeta ligera (listas, tablas) */
.apple-card-light {
    padding: 14px 18px;
    background: #020617;
    border-radius: 16px;
    border: 1px solid rgba(51,65,85,0.9);
    box-shadow: 0 18px 40px rgba(15,23,42,0.9);
    margin-bottom: 16px;
}

/* Métricas de cabecera tipo Apple dashboard */
.metric-row {
    display: flex;
    gap: 14px;
    margin-top: 6px;
    margin-bottom: 8px;
}

.metric-box {
    flex: 1;
    padding: 12px 14px;
    background: radial-gradient(circle at top left, #0B1120 0%, #020617 70%);
    border-radius: 14px;
    border: 1px solid rgba(51,65,85,0.9);
    box-shadow: 0 18px 40px rgba(15,23,42,0.9);
}

.metric-title {
    font-size: 0.78rem;
    color: #9CA3AF;
    letter-spacing: 0.09em;
    text-transform: uppercase;
}

.metric-value {
    font-size: 1.5rem;
    font-weight: 640;
    margin-top: 2px;
    color: #E5E7EB;
}

.metric-sub {
    font-size: 0.76rem;
    color: #6B7280;
    margin-top: 2px;
}

/* Botones más suaves y redondeados */
button[kind="primary"] {
    border-radius: 999px !important;
}

/* Campos de formulario redondeados y oscuros */
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
    background: rgba(59,130,246,0.16);
    color: #60A5FA;
    font-size: 0.75rem;
    font-weight: 500;
}

/* Etiqueta de estado */
.status-pill {
    display: inline-flex;
    align-items: center;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 500;
}

.status-ganado {
    background: rgba(34,197,94,0.18);
    color: #6EE7B7;
}
.status-perdido {
    background: rgba(248,113,113,0.18);
    color: #FCA5A5;
}
.status-seguimiento {
    background: rgba(59,130,246,0.20);
    color: #93C5FD;
}

/* Listas compactas en panel */
.next-item {
    padding: 6px 10px;
    border-radius: 10px;
    border: 1px solid rgba(51,65,85,0.85);
    margin-bottom: 6px;
    background: #020617;
    font-size: 0.82rem;
    color: #E5E7EB;
}

.next-item small {
    display: block;
    color: #9CA3AF;
    font-size: 0.72rem;
}

/* Etiqueta pequeña dentro del texto */
.badge-inline {
    display: inline-flex;
    align-items: center;
    padding: 2px 7px;
    border-radius: 999px;
    border: 1px solid rgba(55,65,81,0.9);
    font-size: 0.7rem;
    margin-left: 4px;
    color: #9CA3AF;
}

/* Tabs más compactas */
[data-baseweb="tab-list"] {
    gap: 0.5rem;
}
</style>
""",
    unsafe_allow_html=True,
)


# ==========================
# PÁGINA: PANEL DE CONTROL
# ==========================

def _parse_fecha_iso(valor):
    """Convierte string ISO o datetime en date (o None)."""
    if not valor:
        return None
    if isinstance(valor, date) and not isinstance(valor, datetime):
        return valor
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, str):
        try:
            return datetime.fromisoformat(valor).date()
        except Exception:
            return None
    return None


def render_panel_control():
    # Cabecera tipo Apple
    st.markdown(
        """
        <div class="apple-card">
            <div class="section-badge">Agenda de acciones</div>
            <h1 style="margin-top: 4px; margin-bottom:4px;">Qué tengo que hacer ahora</h1>
            <p style="color:#9CA3AF; margin-bottom: 0; font-size:0.9rem;">
                Vista unificada de seguimientos y tareas sobre proyectos y clientes.
                Ideal para empezar el día sabiendo a quién llamar, qué ofertas mover
                y qué proyectos no se pueden enfriar.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_clientes = get_clientes()
    df_proyectos = get_proyectos()

    acciones = []  # cada elemento: dict con tipo, subtipo, fecha, texto, origen, prioridad, estado

    hoy = date.today()
    en_7 = hoy + timedelta(days=7)

    # ---- Seguimientos en proyectos (fecha_seguimiento) ----
    if df_proyectos is not None and not df_proyectos.empty:
        for _, row in df_proyectos.iterrows():
            fecha_seg = _parse_fecha_iso(row.get("fecha_seguimiento"))
            estado = row.get("estado", "Detectado")
            if fecha_seg:
                acciones.append(
                    {
                        "tipo": "Seguimiento",
                        "subtipo": "Proyecto",
                        "fecha": fecha_seg,
                        "texto": row.get("nombre_obra", "Sin nombre"),
                        "detalle": row.get("cliente_principal", "") or "",
                        "estado": estado,
                        "prioridad": row.get("prioridad", "Media"),
                    }
                )

            # Tareas asociadas al proyecto
            tareas = row.get("tareas") or []
            for t in tareas:
                fecha_lim = _parse_fecha_iso(t.get("fecha_limite"))
                if not fecha_lim:
                    continue
                acciones.append(
                    {
                        "tipo": "Tarea",
                        "subtipo": "Proyecto",
                        "fecha": fecha_lim,
                        "texto": t.get("titulo", "(sin título)"),
                        "detalle": row.get("nombre_obra", "Sin obra"),
                        "estado": "Completada" if t.get("completado") else "Pendiente",
                        "prioridad": row.get("prioridad", "Media"),
                    }
                )

    # (Opcional) futuro: tareas/seguimientos en clientes si los añades allí.

    if not acciones:
        st.markdown(
            """
            <div class="apple-card-light">
                <div class="section-badge">Sin acciones pendientes</div>
                <h3 style="margin-top:8px; margin-bottom:4px;">Todo al día ✅</h3>
                <p style="color:#9CA3AF; font-size:0.9rem; margin-bottom:0;">
                    Todavía no hay seguimientos ni tareas con fecha asignada. 
                    Usa la página de <strong>Proyectos</strong> para añadir tareas 
                    y fechas de seguimiento.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Clasificación por rango temporal
    acciones_hoy = [a for a in acciones if a["fecha"] == hoy and a.get("estado") != "Completada"]
    acciones_semana = [
        a
        for a in acciones
        if hoy < a["fecha"] <= en_7 and a.get("estado") != "Completada"
    ]
    acciones_atrasadas = [
        a for a in acciones if a["fecha"] < hoy and a.get("estado") != "Completada"
    ]

    total_pend = len(acciones_hoy) + len(acciones_semana) + len(acciones_atrasadas)

    # ---- Métricas cabecera ----
    st.markdown("<div class='metric-row'>", unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="metric-box">
            <div class="metric-title">Acciones pendientes totales</div>
            <div class="metric-value">{total_pend}</div>
            <div class="metric-sub">Entre tareas y seguimientos programados</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="metric-box">
            <div class="metric-title">Para hoy</div>
            <div class="metric-value">{len(acciones_hoy)}</div>
            <div class="metric-sub">Llamadas, emails o visitas que no pueden esperar</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="metric-box">
            <div class="metric-title">Retrasadas</div>
            <div class="metric-value">{len(acciones_atrasadas)}</div>
            <div class="metric-sub">Acciones que ya deberían haberse hecho</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)

    # ---- Listas detalladas ----
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.markdown(
        """
        <div style="display:flex; align-items:center; justify-content:space-between;">
            <div>
                <div class="section-badge">Próximos pasos</div>
                <h3 style="margin-top:8px; margin-bottom:4px;">Agenda por prioridad temporal</h3>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    # Helper para dibujar lista
    def _render_lista(col, titulo, acciones_lista, emoji):
        with col:
            st.markdown(
                f"<p style='font-size:0.9rem; color:#E5E7EB; margin-bottom:6px;'><strong>{emoji} {titulo}</strong></p>",
                unsafe_allow_html=True,
            )
            if not acciones_lista:
                st.markdown(
                    "<p style='color:#6B7280; font-size:0.78rem;'>Nada pendiente en este bloque.</p>",
                    unsafe_allow_html=True,
                )
                return
            acciones_ordenadas = sorted(acciones_lista, key=lambda x: x["fecha"])
            for a in acciones_ordenadas[:20]:  # límite visual
                fecha_txt = a["fecha"].strftime("%d/%m/%y")
                tipo = a["tipo"]
                subtipo = a["subtipo"]
                texto = a["texto"]
                detalle = a.get("detalle", "")
                prioridad = a.get("prioridad", "Media")
                estado = a.get("estado", "")

                pill_estado = ""
                if tipo == "Seguimiento":
                    pill_estado = "<span class='badge-inline'>Seguimiento</span>"
                else:
                    pill_estado = "<span class='badge-inline'>Tarea</span>"

                html = f"""
                <div class="next-item">
                    <div><strong>{fecha_txt}</strong> · {texto} {pill_estado}</div>
                    <small>{subtipo} · {detalle if detalle else ""}</small><br/>
                    <small>Prioridad: {prioridad} · Estado: {estado}</small>
                </div>
                """
                st.markdown(html, unsafe_allow_html=True)

    _render_lista(col1, "Retrasadas", acciones_atrasadas, "⏰")
    _render_lista(col2, "Para hoy", acciones_hoy, "📍")
    _render_lista(col3, "Próximos 7 días", acciones_semana, "📅")

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