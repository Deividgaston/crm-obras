import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta

from crm_utils import get_proyectos

try:
    from style_injector import inject_apple_style
except Exception:
    def inject_apple_style():
        pass


# ==========================
# CARGA DATOS (cache)
# ==========================

@st.cache_data(show_spinner=False)
def load_proyectos() -> pd.DataFrame | None:
    return get_proyectos()


# ==========================
# HELPERS
# ==========================

def _parse_fecha_iso(valor):
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


def _relativo(fecha: date, hoy: date) -> str:
    delta = (fecha - hoy).days
    if delta == 0:
        return "Hoy"
    if delta == -1:
        return "Ayer"
    if delta == 1:
        return "Mañana"
    if delta < -1:
        return f"Hace {abs(delta)} días"
    return f"En {delta} días"


# ==========================
# PANEL PRINCIPAL
# ==========================

def render_panel():
    inject_apple_style()

    # CABECERA
    st.markdown(
        """
        <div class="apple-card">
            <div class="badge">Agenda</div>
            <h3 style="margin-top:4px; margin-bottom:4px;">Agenda de acciones</h3>
            <p style="margin-bottom:0;">
                Seguimientos y tareas pendientes ordenadas por urgencia. Vista rápida para saber
                qué hacer hoy, qué está retrasado y qué viene en la semana.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df = load_proyectos()

    if df is None or df.empty:
        st.info("Todavía no hay proyectos en el CRM para generar la agenda.")
        return

    hoy = date.today()

    acciones = []
    for _, row in df.iterrows():
        fecha_seg = _parse_fecha_iso(row.get("fecha_seguimiento"))
        if not fecha_seg:
            continue

        acciones.append(
            {
                "fecha": fecha_seg,
                "proyecto": row.get("nombre_obra", "Sin nombre"),
                "cliente": row.get("cliente_principal", "—"),
                "ciudad": row.get("ciudad", "—"),
                "provincia": row.get("provincia", "—"),
                "tipo": "Seguimiento",
            }
        )

    if not acciones:
        st.info("No hay acciones de seguimiento planificadas.")
        return

    df_acc = pd.DataFrame(acciones)

    atrasadas = df_acc[df_acc["fecha"] < hoy].sort_values("fecha")
    hoy_df = df_acc[df_acc["fecha"] == hoy].sort_values("fecha")
    prox7 = df_acc[(df_acc["fecha"] > hoy) & (df_acc["fecha"] <= hoy + timedelta(days=7))].sort_values("fecha")

    total_acciones = len(df_acc)
    num_retrasadas = len(atrasadas)
    num_hoy = len(hoy_df)
    num_prox7 = len(prox7)

    # =====================================
    # KPIs
    # =====================================
    c1, c2, c3, c4 = st.columns(4)

    c1.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">Total acciones</div>
            <div class="metric-value">{total_acciones}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c2.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">Retrasadas</div>
            <div class="metric-value">{num_retrasadas}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c3.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">Hoy</div>
            <div class="metric-value">{num_hoy}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c4.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">Próx. 7 días</div>
            <div class="metric-value">{num_prox7}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # =====================================
    # LISTAS POR COLUMNA
    # =====================================
    col_r, col_h, col_p = st.columns(3)

    # --- Retrasadas ---
    with col_r:
        st.markdown(
            """
            <div style="font-size:13px; font-weight:600; color:#C23934; margin-bottom:4px;">
                🔁 Retrasadas
            </div>
            """,
            unsafe_allow_html=True,
        )
        if atrasadas.empty:
            st.caption("Sin acciones.")
        else:
            for _, a in atrasadas.iterrows():
                _render_action_card(a, hoy)

    # --- Hoy ---
    with col_h:
        st.markdown(
            """
            <div style="font-size:13px; font-weight:600; color:#032D60; margin-bottom:4px;">
                📍 Hoy
            </div>
            """,
            unsafe_allow_html=True,
        )
        if hoy_df.empty:
            st.caption("Sin acciones.")
        else:
            for _, a in hoy_df.iterrows():
                _render_action_card(a, hoy)

    # --- Próximos 7 días ---
    with col_p:
        st.markdown(
            """
            <div style="font-size:13px; font-weight:600; color:#032D60; margin-bottom:4px;">
                📅 Próximos 7 días
            </div>
            """,
            unsafe_allow_html=True,
        )
        if prox7.empty:
            st.caption("Sin acciones.")
        else:
            for _, a in prox7.iterrows():
                _render_action_card(a, hoy)


def _render_action_card(a: pd.Series, hoy: date):
    fecha = a["fecha"]
    proyecto = a["proyecto"]
    cliente = a["cliente"]
    ciudad = a["ciudad"]
    provincia = a["provincia"]
    relativo = _relativo(fecha, hoy)

    st.markdown(
        f"""
        <div class="apple-card-light" style="margin-bottom:8px;">
            <div style="font-size:12px; font-weight:600; color:#032D60;">
                {relativo} · Seguimiento
            </div>
            <div style="font-size:12px; margin-top:2px;">
                {proyecto}
            </div>
            <div style="font-size:11.5px; color:#5A6872; margin-top:2px;">
                {cliente} — {ciudad} ({provincia})
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
