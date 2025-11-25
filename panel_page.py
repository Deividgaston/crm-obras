import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta

from crm_utils import get_clientes, get_proyectos

try:
    from style_injector import inject_apple_style
except Exception:
    def inject_apple_style():
        pass


# ===============================================================
# HELPERS
# ===============================================================

def _to_dataframe(data):
    """Convierte listas/dicts/DataFrame en DataFrame sin ambigüedad lógica."""
    if data is None:
        return pd.DataFrame()
    if isinstance(data, pd.DataFrame):
        return data.copy()
    if isinstance(data, (list, tuple)) and not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


# =============================================================
# FORMATEO DE FECHAS
# =============================================================

def _parse_fecha(valor):
    """Convierte una fecha en date o None."""
    if not valor:
        return None
    if isinstance(valor, date) and not isinstance(valor, datetime):
        return valor
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, str):
        formatos = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%Y/%m/%d",
        ]
        for fmt in formatos:
            try:
                return datetime.strptime(valor, fmt).date()
            except Exception:
                continue
    return None


def _formatear_fecha(fecha: date | None) -> str:
    if not fecha:
        return "Sin fecha"
    hoy = date.today()
    if fecha == hoy:
        return "Hoy"
    if fecha == hoy + timedelta(days=1):
        return "Mañana"
    if fecha == hoy - timedelta(days=1):
        return "Ayer"
    return fecha.strftime("%d/%m/%Y")


# =============================================================
# PANEL PRINCIPAL
# =============================================================

def render_panel():
    """
    Panel principal tipo 'agenda' con estilo Apple Dark:
    - Cabecera Apple card
    - KPIs de acciones
    - Listas de acciones: Retrasadas / Hoy / Próximos 7 días
    - Acciones = Seguimientos por fecha + Tareas por fecha
    """
    inject_apple_style()

    # Cabecera tipo Apple card
    st.markdown(
        """
        <div class="apple-card">
            <div class="badge">Agenda de acciones</div>
            <h1 style="margin-top: 4px; margin-bottom:4px;">Qué tengo que hacer ahora</h1>
            <p style="margin-bottom: 0; color: #9CA3AF;">
                Una vista única para combinar seguimientos y tareas críticas, 
                para que empieces el día sabiendo a quién llamar, qué ofertas mover
                y qué obras no se pueden enfriar.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ================= CARGA DE DATOS (UNA SOLA VEZ) =================
    with st.spinner("Cargando agenda desde la base de datos…"):
        try:
            lista_clientes = get_clientes()     # cacheado en crm_utils
            lista_proyectos = get_proyectos()   # cacheado en crm_utils
        except Exception as e:
            st.error("❌ No se han podido cargar los datos desde Firestore.")
            st.code(str(e))
            return

    df_clientes = _to_dataframe(lista_clientes)
    df_proyectos = _to_dataframe(lista_proyectos)

    # ================= CONSTRUCCIÓN DE ACCIONES =================
    acciones = []  # cada acción es un dict: {tipo, subtipo, fecha, texto, detalle, estado, prioridad}

    hoy = date.today()
    en_7 = hoy + timedelta(days=7)

    # --- Seguimientos en proyectos (fecha_seguimiento) ---
    if not df_proyectos.empty:
        for _, row in df_proyectos.iterrows():
            nombre_obra = row.get("nombre_obra", "Sin nombre")
            cliente = row.get("cliente_principal", "—")
            ciudad = row.get("ciudad", "—")
            provincia = row.get("provincia", "—")
            prioridad = row.get("prioridad", "Media")
            estado = row.get("estado", "Detectado")

            fecha_seg = _parse_fecha(row.get("fecha_seguimiento"))
            if not fecha_seg:
                continue

            texto = f"Seguimiento obra: {nombre_obra}"
            detalle = f"{cliente} · {ciudad}, {provincia}"

            acciones.append(
                {
                    "tipo": "seguimiento",
                    "subtipo": "Seguimiento",
                    "fecha": fecha_seg,
                    "texto": texto,
                    "detalle": detalle,
                    "estado": estado,
                    "prioridad": prioridad,
                }
            )

    # --- Tareas por proyecto (tareas.fecha_limite) ---
    if not df_proyectos.empty and "tareas" in df_proyectos.columns:
        for _, row in df_proyectos.iterrows():
            nombre_obra = row.get("nombre_obra", "Sin nombre")
            cliente = row.get("cliente_principal", "—")
            ciudad = row.get("ciudad", "—")
            provincia = row.get("provincia", "—")
            prioridad_proy = row.get("prioridad", "Media")

            tareas = row.get("tareas") or []
            for t in tareas:
                fecha_lim = _parse_fecha(t.get("fecha_limite"))
                if not fecha_lim:
                    continue

                titulo = t.get("titulo", "(sin título)")
                tipo_tarea = t.get("tipo", "Tarea")
                completado = bool(t.get("completado", False))

                if completado:
                    continue

                texto = f"{tipo_tarea}: {titulo}"
                detalle = f"{nombre_obra} · {cliente} · {ciudad}, {provincia}"
                estado = row.get("estado", "Detectado")

                acciones.append(
                    {
                        "tipo": "tarea",
                        "subtipo": tipo_tarea,
                        "fecha": fecha_lim,
                        "texto": texto,
                        "detalle": detalle,
                        "estado": estado,
                        "prioridad": prioridad_proy,
                    }
                )

    if not acciones:
        st.info("No hay acciones pendientes (seguimientos o tareas) en este momento.")
        return

    df_acc = pd.DataFrame(acciones)

    # ================= KPIs SUPERIORES =================
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)

    col_k1, col_k2, col_k3, col_k4 = st.columns(4)

    total_acciones = len(df_acc)
    atrasadas = len(df_acc[df_acc["fecha"] < hoy])
    hoy_count = len(df_acc[df_acc["fecha"] == hoy])
    semana_count = len(df_acc[(df_acc["fecha"] > hoy) & (df_acc["fecha"] <= en_7)])

    with col_k1:
        st.metric("Acciones totales", total_acciones)

    with col_k2:
        st.metric("Retrasadas", atrasadas)

    with col_k3:
        st.metric("Para hoy", hoy_count)

    with col_k4:
        st.metric("Próximos 7 días", semana_count)

    st.markdown("</div>", unsafe_allow_html=True)

    # ================= TRES COLUMNAS: RETRASADAS / HOY / 7 DÍAS =================
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.markdown("### Próximas acciones", unsafe_allow_html=True)

    col_late, col_today, col_week = st.columns(3)

    acciones_atrasadas = df_acc[df_acc["fecha"] < hoy].sort_values("fecha")
    acciones_hoy = df_acc[df_acc["fecha"] == hoy].sort_values("fecha")
    acciones_semana = df_acc[(df_acc["fecha"] > hoy) & (df_acc["fecha"] <= en_7)].sort_values("fecha")

    def _render_lista(col, titulo, df_list: pd.DataFrame, icono: str):
        with col:
            st.markdown(f"#### {icono} {titulo}")
            if df_list.empty:
                st.caption("Sin acciones.")
                return

            for _, row in df_list.iterrows():
                fecha_txt = _formatear_fecha(row.get("fecha"))
                texto = row.get("texto", "")
                detalle = row.get("detalle", "")
                subtipo = row.get("subtipo", "")
                prioridad = row.get("prioridad", "Media")
                estado = row.get("estado", "—")

                if prioridad == "Alta":
                    pill_estado = "<span class='pill pill-red'>Alta</span>"
                elif prioridad == "Media":
                    pill_estado = "<span class='pill pill-amber'>Media</span>"
                else:
                    pill_estado = "<span class='pill pill-slate'>Baja</span>"

                html = f"""
                <div class="next-item">
                    <div><strong>{fecha_txt}</strong> · {texto} {pill_estado}</div>
                    <small>{subtipo} · {detalle}</small><br/>
                    <small>Prioridad: {prioridad} · Estado: {estado}</small>
                </div>
                """
                st.markdown(html, unsafe_allow_html=True)

    _render_lista(col_late, "Retrasadas", acciones_atrasadas, "⏰")
    _render_lista(col_today, "Para hoy", acciones_hoy, "📍")
    _render_lista(col_week, "Próximos 7 días", acciones_semana, "📅")
