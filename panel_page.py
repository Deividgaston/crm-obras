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
# PANEL ULTRA COMPACTO SALESFORCE
# ============================

def render_panel():
    inject_apple_style()

    # TÍTULO SUPER PEQUEÑO
    st.markdown(
        """
        <div style="margin-bottom:4px;">
            <span style="font-size:0.95rem; font-weight:600;">Agenda de acciones</span><br>
            <span style="font-size:0.75rem; color:#6b7b93;">
                Seguimientos y tareas urgentes en formato compacto.
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------------- Cargar datos ----------------
    try:
        clientes_raw = get_clientes()
        proyectos_raw = get_proyectos()
    except Exception as e:
        st.error("Error cargando datos.")
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
            if fecha_seg:
                acciones.append({
                    "tipo": "Seguimiento",
                    "proyecto": r.get("nombre_obra", ""),
                    "cliente": r.get("cliente_principal", "—"),
                    "ciudad": r.get("ciudad", "—"),
                    "fecha": fecha_seg,
                })

    # ---------------- Tareas ----------------
    if "tareas" in df_proyectos.columns:
        for _, r in df_proyectos.iterrows():
            for t in r.get("tareas") or []:
                if t.get("completado"):
                    continue
                fecha_lim = _parse_fecha(t.get("fecha_limite"))
                if not fecha_lim:
                    continue
                acciones.append({
                    "tipo": t.get("tipo", "Tarea"),
                    "proyecto": r.get("nombre_obra", ""),
                    "cliente": r.get("cliente_principal", "—"),
                    "ciudad": r.get("ciudad", "—"),
                    "fecha": fecha_lim,
                })

    if not acciones:
        st.info("No hay acciones pendientes.")
        return

    df_acc = pd.DataFrame(acciones).sort_values("fecha")

    # ---------------- KPIs Estrechos ----------------
    retrasadas = df_acc[df_acc["fecha"] < hoy]
    hoy_df = df_acc[df_acc["fecha"] == hoy]
    semana = df_acc[(df_acc["fecha"] > hoy) & (df_acc["fecha"] <= en_7)]

    # Métricas estilo Salesforce ultra compactas
    st.markdown(
        """
        <div style="display:flex; gap:6px; margin-bottom:6px;">
            <div class="metric-card" style="min-width:100px;">
                <div class="metric-title">Totales</div>
                <div class="metric-value">{}</div>
            </div>
            <div class="metric-card" style="min-width:100px;">
                <div class="metric-title">Retrasadas</div>
                <div class="metric-value">{}</div>
            </div>
            <div class="metric-card" style="min-width:100px;">
                <div class="metric-title">Hoy</div>
                <div class="metric-value">{}</div>
            </div>
            <div class="metric-card" style="min-width:120px;">
                <div class="metric-title">Próx 7 días</div>
                <div class="metric-value">{}</div>
            </div>
        </div>
        """.format(len(df_acc), len(retrasadas), len(hoy_df), len(semana)),
        unsafe_allow_html=True,
    )

    # ---------------- Listas estilo Salesforce compactas ----------------

    col_late, col_today, col_week = st.columns([1, 1, 1])

    def _render_list(col, title, data):
        with col:
            st.markdown(
                f"<div style='font-size:0.78rem; font-weight:600; margin-bottom:4px;'>{title}</div>",
                unsafe_allow_html=True,
            )

            if data.empty:
                st.caption("—")
                return

            # Items compactos
            for _, row in data.iterrows():
                st.markdown(
                    f"""
                    <div class="next-item" style="padding:4px 6px;">
                        <div style="font-size:0.78rem;"><b>{_fecha_txt(row['fecha'])}</b> — {row['tipo']}</div>
                        <div style="font-size:0.72rem; color:#6b7b93;">
                            {row['proyecto']} · {row['cliente']} ({row['ciudad']})
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    _render_list(col_late, "⏰ Retrasadas", retrasadas)
    _render_list(col_today, "📍 Hoy", hoy_df)
    _render_list(col_week, "📅 Próximos 7 días", semana)
