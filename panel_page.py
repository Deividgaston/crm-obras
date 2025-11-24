import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta

from crm_utils import get_clientes, get_proyectos

try:
    from style_injector import inject_apple_style
except:
    def inject_apple_style():
        pass


def _parse_fecha_iso(valor):
    """
    Convierte distintos formatos de fecha (iso, date, datetime, str) en date.
    """
    if not valor:
        return None

    if isinstance(valor, date) and not isinstance(valor, datetime):
        return valor

    if isinstance(valor, datetime):
        return valor.date()

    if isinstance(valor, (int, float)):
        # por si algún día se cuela serial de Excel
        base = datetime(1899, 12, 30)
        try:
            return (base + timedelta(days=float(valor))).date()
        except Exception:
            return None

    if isinstance(valor, str):
        valor = valor.strip()
        if not valor:
            return None
        formatos = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%d/%m/%Y",
            "%d-%m-%Y",
        ]
        for fmt in formatos:
            try:
                return datetime.strptime(valor, fmt).date()
            except ValueError:
                continue
    return None


def render_panel():
    inject_apple_style()

    # Cabecera tipo Apple
    st.markdown(
        """
        <div class="apple-card">
            <div class="section-badge">Agenda de acciones</div>
            <h1 style="margin-top: 4px; margin-bottom:4px;">Qué tengo que hacer ahora</h1>
            <p style="margin-bottom: 0; font-size:0.9rem;">
                Vista unificada de seguimientos y tareas sobre proyectos y clientes.
                Ideal para empezar el día sabiendo a quién llamar, qué ofertas mover
                y qué proyectos no se pueden enfriar.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ================= CARGA DE DATOS =================
    with st.spinner("Cargando agenda desde la base de datos…"):
        try:
            lista_clientes = get_clientes()
            lista_proyectos = get_proyectos()
        except Exception as e:
            st.error("No se han podido cargar los datos desde Firestore.")
            st.code(str(e))
            return

    df_clientes = pd.DataFrame(lista_clientes) if lista_clientes else pd.DataFrame()
    df_proyectos = pd.DataFrame(lista_proyectos) if lista_proyectos else pd.DataFrame()

    acciones = []  # tipo, subtipo, fecha, texto, detalle, estado, prioridad

    hoy = date.today()
    en_7 = hoy + timedelta(days=7)

    # ---- Seguimientos en proyectos (fecha_seguimiento) ----
    if not df_proyectos.empty:
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
                        "detalle": row.get("cliente_principal") or row.get("cliente") or "",
                        "estado": estado,
                        "prioridad": row.get("prioridad", "Media"),
                    }
                )

            # TAREAS asociadas al proyecto (si existen)
            tareas = row.get("tareas") or []
            if isinstance(tareas, list):
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

    # (Futuro) se podrían añadir tareas/seguimientos sobre clientes aquí.

    if not acciones:
        st.markdown(
            """
            <div class="apple-card-light">
                <div class="section-badge">Sin acciones pendientes</div>
                <h3 style="margin-top:8px; margin-bottom:4px;">Todo al día ✅</h3>
                <p style="font-size:0.9rem; margin-bottom:0;">
                    Todavía no hay seguimientos ni tareas con fecha asignada. 
                    Usa la página de <strong>Proyectos</strong> para añadir tareas 
                    y fechas de seguimiento.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # ================= MÉTRICAS RESUMEN =================
    acciones_atrasadas = [a for a in acciones if a["fecha"] < hoy]
    acciones_hoy = [a for a in acciones if a["fecha"] == hoy]
    acciones_semana = [a for a in acciones if hoy < a["fecha"] <= en_7]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("⏰ Retrasadas", len(acciones_atrasadas))
    with col2:
        st.metric("📍 Para hoy", len(acciones_hoy))
    with col3:
        st.metric("📅 Próximos 7 días", len(acciones_semana))

    # ================= LISTAS DETALLADAS =================
    st.markdown(
        """
        <div class="apple-card-light">
            <div style="display:flex; align-items:center; justify-content:space-between;">
                <div>
                    <div class="section-badge">Próximos pasos</div>
                    <h3 style="margin-top:8px; margin-bottom:4px;">Agenda por prioridad temporal</h3>
                </div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    col_late, col_today, col_week = st.columns(3)

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
            for a in acciones_ordenadas[:20]:
                fecha_txt = a["fecha"].strftime("%d/%m/%y")
                texto = a["texto"]
                detalle = a.get("detalle", "")
                tipo = a["tipo"]
                subtipo = a["subtipo"]
                prioridad = a.get("prioridad", "Media")
                estado = a.get("estado", "")

                pill_estado = (
                    "<span class='badge-inline'>Seguimiento</span>"
                    if tipo == "Seguimiento"
                    else "<span class='badge-inline'>Tarea</span>"
                )

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

    st.markdown("</div>", unsafe_allow_html=True)
