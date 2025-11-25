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
    """Convierte datos en DataFrame sin ambigüedad."""
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
    if isinstance(v, date):
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
# PANEL (AGENDA)
# ============================

def render_panel():
    inject_apple_style()

    st.markdown("### Agenda de acciones")
    st.caption("Seguimientos y tareas ordenadas por urgencia")

    # ---------------- Cargar datos ----------------
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

    # ---------------- Seguimientos ----------------
    if not df_proyectos.empty:
        for _, r in df_proyectos.iterrows():
            fecha_seg = _parse_fecha(r.get("fecha_seguimiento"))
            if not fecha_seg:
                continue

            acciones.append({
                "tipo": "Seguimiento",
                "proyecto": r.get("nombre_obra", "Sin nombre"),
                "cliente": r.get("cliente_principal", "—"),
                "ciudad": r.get("ciudad", "—"),
                "provincia": r.get("provincia", "—"),
                "fecha": fecha_seg,
                "prioridad": r.get("prioridad", "Media"),
            })

    # ---------------- Tareas ----------------
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
        st.info("No hay acciones pendientes.")
        return

    df_acc = pd.DataFrame(acciones).sort_values("fecha")

    # ---------------- KPIs compactos ----------------
    retrasadas = df_acc[df_acc["fecha"] < hoy]
    hoy_df = df_acc[df_acc["fecha"] == hoy]
    semana = df_acc[(df_acc["fecha"] > hoy) & (df_acc["fecha"] <= en_7)]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Totales", len(df_acc))
    c2.metric("Retrasadas", len(retrasadas))
    c3.metric("Hoy", len(hoy_df))
    c4.metric("Próx 7 días", len(semana))

    st.markdown("---")

    # ---------------- Listas estilo Salesforce ----------------

    col_late, col_today, col_week = st.columns(3)

    def _listado(col, titulo, df):
        with col:
            st.markdown(f"**{titulo}**")
            if df.empty:
                st.caption("Sin acciones")
                return

            for _, row in df.iterrows():
                st.markdown(
                    f"""
                    <div class="next-item">
                        <strong>{_fecha_txt(row['fecha'])}</strong> · {row['tipo']}
                        <br><small>{row['proyecto']} – {row['cliente']} ({row['ciudad']})</small>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    _listado(col_late, "⏰ Retrasadas", retrasadas)
    _listado(col_today, "📍 Hoy", hoy_df)
    _listado(col_week, "📅 Próximos 7 días", semana)

