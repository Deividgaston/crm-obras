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
def _parse_fecha_iso(valor):
    """
    Convierte distintos formatos de fecha (iso, date, datetime, str, serial Excel)
    en un date. Si no se puede, devuelve None.
    """
    if not valor:
        return None

    if isinstance(valor, date) and not isinstance(valor, datetime):
        return valor

    if isinstance(valor, datetime):
        return valor.date()

    if isinstance(valor, (int, float)):
        # Por si algún día se cuela un serial de Excel
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


# ===============================================================
# PANEL PRINCIPAL
# ===============================================================
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
            <p style="margin-bottom: 0; font-size:0.9rem; color:#9ca3af;">
                Vista unificada de seguimientos y tareas sobre tus proyectos clave.
                Perfecto para empezar el día sabiendo a quién llamar, qué ofertas mover
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

    df_clientes = pd.DataFrame(lista_clientes) if lista_clientes else pd.DataFrame()
    df_proyectos = pd.DataFrame(lista_proyectos) if lista_proyectos else pd.DataFrame()

    # ================= CONSTRUCCIÓN DE ACCIONES =================
    acciones = []  # cada acción es un dict: {tipo, subtipo, fecha, texto, detalle, estado, prioridad}

    hoy = date.today()
    en_7 = hoy + timedelta(days=7)

    # --- Seguimientos en proyectos (fecha_seguimiento) ---
    if not df_proyectos.empty:
        for _, row in df_proyectos.iterrows():
            nombre_obra = row.get("nombre_obra", "Sin nombre")
            estado = row.get("estado", "Detectado") or "Detectado"
            prioridad = row.get("prioridad", "Media") or "Media"
            cliente = (
                row.get("cliente_principal")
                or row.get("promotora")
                or row.get("cliente")
                or ""
            )

            fecha_seg = _parse_fecha_iso(row.get("fecha_seguimiento"))
            if fecha_seg:
                acciones.append(
                    {
                        "tipo": "Seguimiento",
                        "subtipo": "Proyecto",
                        "fecha": fecha_seg,
                        "texto": nombre_obra,
                        "detalle": cliente,
                        "estado": estado,
                        "prioridad": prioridad,
                    }
                )

            # --- TAREAS asociadas al proyecto (si existen) ---
            tareas = row.get("tareas") or []
            if isinstance(tareas, list):
                for t in tareas:
                    # Estructura esperada: {"titulo":..., "fecha_limite":..., "completado": bool}
                    fecha_lim = _parse_fecha_iso(t.get("fecha_limite"))
                    if not fecha_lim:
                        continue

                    titulo = t.get("titulo") or "(Tarea sin título)"
                    completado = bool(t.get("completado"))
                    acciones.append(
                        {
                            "tipo": "Tarea",
                            "subtipo": "Proyecto",
                            "fecha": fecha_lim,
                            "texto": titulo,
                            "detalle": nombre_obra,
                            "estado": "Completada" if completado else "Pendiente",
                            "prioridad": prioridad,
                        }
                    )

    # (Opcional futuro) acciones ligadas directamente a clientes (por ahora no se añaden)

    # Si no hay acciones, mostramos tarjeta vacía
    if not acciones:
        st.markdown(
            """
            <div class="apple-card-light">
                <div class="badge">Sin acciones pendientes</div>
                <h3 style="margin-top:8px; margin-bottom:4px;">Todo al día ✅</h3>
                <p style="font-size:0.9rem; margin-bottom:0; color:#9ca3af;">
                    Todavía no hay seguimientos ni tareas con fecha asignada. 
                    Usa la página de <strong>Proyectos</strong> para añadir tareas 
                    y fechas de seguimiento que aparecerán aquí.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # ================= KPIs DE AGENDA =================
    acciones_atrasadas = [a for a in acciones if a["fecha"] < hoy]
    acciones_hoy = [a for a in acciones if a["fecha"] == hoy]
    acciones_semana = [a for a in acciones if hoy < a["fecha"] <= en_7]

    st.markdown(
        """
        <div class="apple-card-light">
            <h2 class="section-title">📊 Resumen de acciones</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("⏰ Retrasadas", len(acciones_atrasadas))
    with col2:
        st.metric("📍 Para hoy", len(acciones_hoy))
    with col3:
        st.metric("📅 Próximos 7 días", len(acciones_semana))

    st.markdown("<br>", unsafe_allow_html=True)

    # ================= LISTAS DETALLADAS =================
    st.markdown(
        """
        <div class="apple-card-light">
            <div style="display:flex; align-items:center; justify-content:space-between;">
                <div>
                    <div class="badge">Próximos pasos</div>
                    <h3 style="margin-top:8px; margin-bottom:4px;">Agenda por prioridad temporal</h3>
                </div>
            </div>
            <p class="small-caption">
                Acciones ordenadas en retrasadas, para hoy y próximos 7 días. 
                Cada línea combina seguimiento o tarea con el proyecto y su prioridad.
            </p>
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

            # Ordenamos por fecha ascendente
            acciones_ordenadas = sorted(acciones_lista, key=lambda x: x["fecha"])

            for a in acciones_ordenadas[:30]:  # límite de 30 por columna
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
