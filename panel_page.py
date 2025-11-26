import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta

from crm_utils import get_clientes, get_proyectos

try:
    from style_injector import inject_apple_style
except Exception:
    def inject_apple_style():
        pass


# ============================
# HELPERS
# ============================

def _to_df(data):
    if data is None:
        return pd.DataFrame()
    if isinstance(data, pd.DataFrame):
        return data.copy()
    if isinstance(data, (list, tuple)) and not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


def _parse_fecha(v):
    if not v:
        return None
    if isinstance(v, date) and not isinstance(v, datetime):
        return v
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, str):
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(v, fmt).date()
            except Exception:
                continue
    return None


def _fecha_txt(f: date | None):
    if not f:
        return "—"
    h = date.today()
    if f == h:
        return "Hoy"
    if f == h + timedelta(days=1):
        return "Mañana"
    if f == h - timedelta(days=1):
        return "Ayer"
    return f.strftime("%d/%m/%Y")


# ============================
# PANEL / AGENDA (SLDS)
# ============================

def render_panel():
    inject_apple_style()

    # ---------------------------------
    # CABECERA TIPO SALESFORCE
    # ---------------------------------
    st.markdown(
        """
        <div class="apple-card">
            <div class="badge">Agenda</div>
            <h3 style="margin-top:2px; margin-bottom:2px;">Agenda de acciones</h3>
            <p>
                Seguimientos y tareas pendientes ordenadas por urgencia. 
                Vista rápida para saber qué hacer hoy, qué está retrasado y qué viene en la semana.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------------------------------
    # CARGA DE DATOS
    # ---------------------------------
    try:
        clientes_raw = get_clientes()
        proyectos_raw = get_proyectos()
    except Exception as e:
        st.error("Error cargando datos desde Firestore.")
        st.code(str(e))
        return

    df_clientes = _to_df(clientes_raw)
    df_proyectos = _to_df(proyectos_raw)

    acciones = []
    hoy = date.today()
    en_7 = hoy + timedelta(days=7)

    # ---------------------------------
    # SEGUIMIENTOS POR PROYECTO
    # ---------------------------------
    if not df_proyectos.empty:
        for _, r in df_proyectos.iterrows():
            fecha_seg = _parse_fecha(r.get("fecha_seguimiento"))
            if fecha_seg:
                acciones.append({
                    "tipo": "Seguimiento",
                    "proyecto": r.get("nombre_obra", "Sin nombre"),
                    "cliente": r.get("cliente_principal", "—"),
                    "ciudad": r.get("ciudad", "—"),
                    "provincia": r.get("provincia", "—"),
                    "fecha": fecha_seg,
                    "prioridad": r.get("prioridad", "Media"),
                })

    # ---------------------------------
    # TAREAS DE CADA PROYECTO
    # ---------------------------------
    if "tareas" in df_proyectos.columns:
        for _, r in df_proyectos.iterrows():
            tareas = r.get("tareas") or []
            for t in tareas:
                if t.get("completado"):
                    continue
                fecha_lim = _parse_fecha(t.get("fecha_limite"))
                if not fecha_lim:
                    continue

                acciones.append({
                    "tipo": t.get("tipo", "Tarea"),
                    "proyecto": r.get("nombre_obra", "Sin nombre"),
                    "cliente": r.get("cliente_principal", "—"),
                    "ciudad": r.get("ciudad", "—"),
                    "provincia": r.get("provincia", "—"),
                    "fecha": fecha_lim,
                    "prioridad": r.get("prioridad", "Media"),
                })

    if not acciones:
        st.info("No hay acciones pendientes en la agenda.")
        return

    df_acc = pd.DataFrame(acciones).sort_values("fecha")

    # ---------------------------------
    # KPIs TIPO SUMMARY PANEL SF
    # ---------------------------------
    retrasadas = df_acc[df_acc["fecha"] < hoy]
    hoy_df = df_acc[df_acc["fecha"] == hoy]
    semana = df_acc[(df_acc["fecha"] > hoy) & (df_acc["fecha"] <= en_7)]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Total acciones</div>
                <div class="metric-value">{len(df_acc)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Retrasadas</div>
                <div class="metric-value">{len(retrasadas)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Hoy</div>
                <div class="metric-value">{len(hoy_df)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Próx. 7 días</div>
                <div class="metric-value">{len(semana)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("")

    # ---------------------------------
    # LISTADO TIPO "LIGHTNING LAYOUT"
    # ---------------------------------
    col_late, col_today, col_week = st.columns(3)

    def _render_list(col, titulo, icono, df):
        with col:
            st.markdown(
                f"""
                <div style="margin-bottom:4px;">
                    <span style="font-size:13px; font-weight:600; color:#032D60;">
                        {icono} {titulo}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if df.empty:
                st.caption("Sin acciones.")
                return

            for _, row in df.iterrows():
                st.markdown(
                    f"""
                    <div class="next-item">
                        <div style="font-size:13px; margin-bottom:2px;">
                            <strong>{_fecha_txt(row['fecha'])}</strong>
                            &nbsp;·&nbsp; {row['tipo']}
                        </div>
                        <div style="font-size:12px;">
                            {row['proyecto']} – {row['cliente']}
                            <span style="color:#5A6872;">({row['ciudad']})</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    _render_list(col_late, "Retrasadas", "⏰", retrasadas)
    _render_list(col_today, "Hoy", "📍", hoy_df)
    _render_list(col_week, "Próximos 7 días", "📅", semana)
