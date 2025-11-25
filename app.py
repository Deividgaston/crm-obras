import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta

from crm_utils import (
    get_clientes,
    get_proyectos,
    actualizar_proyecto,
)

from proyectos_page import render_proyectos
from buscar_page import render_buscar
from clientes_page import render_clientes_page


# ==========================
# CARGA OPTIMIZADA (Firebase)
# ==========================

@st.cache_data(show_spinner=False)
def load_clientes():
    """Carga los clientes desde Firebase con caché."""
    return get_clientes()


@st.cache_data(show_spinner=False)
def load_proyectos():
    """Carga los proyectos desde Firebase con caché."""
    return get_proyectos()


def invalidate_clientes_cache():
    load_clientes.clear()


def invalidate_proyectos_cache():
    load_proyectos.clear()


# ==========================
# ESTILO GENERAL
# ==========================

def set_page_style():
    st.set_page_config(
        page_title="CRM Prescripción 2N",
        layout="wide",
        page_icon="🏗️",
    )

    st.markdown(
        """
        <style>
        /* Fuente base */
        html, body, [class*="css"] {
            font-family: -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
            background: #020617;
            color: #E5E7EB;
        }

        .apple-card {
            background: radial-gradient(circle at top left, #1E293B, #020617);
            border-radius: 24px;
            padding: 20px 24px;
            border: 1px solid rgba(148,163,184,0.35);
            box-shadow: 0 18px 45px rgba(15,23,42,0.80);
            margin-bottom: 18px;
        }

        .apple-card-light {
            background: rgba(15,23,42,0.92);
            border-radius: 20px;
            padding: 16px 20px;
            border: 1px solid rgba(51,65,85,0.9);
            box-shadow: 0 16px 38px rgba(15,23,42,0.75);
            margin-bottom: 14px;
        }

        .section-badge {
            display: inline-flex;
            align-items: center;
            padding: 3px 10px;
            border-radius: 999px;
            background: rgba(148,163,184,0.16);
            color: #9CA3AF;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.12em;
        }

        .metric-pill {
            display: inline-flex;
            flex-direction: column;
            justify-content: center;
            padding: 12px 14px;
            border-radius: 18px;
            background: rgba(15,23,42,0.95);
            border: 1px solid rgba(55,65,81,0.9);
            min-width: 140px;
        }

        .metric-label {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: #9CA3AF;
        }

        .metric-value {
            font-size: 22px;
            font-weight: 600;
            color: #F9FAFB;
        }

        .status-pill {
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 10px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            border: 1px solid transparent;
        }
        .status-ganado {
            background: rgba(34,197,94,0.18);
            color: #6EE7B7;
            border-color: rgba(34,197,94,0.40);
        }
        .status-perdido {
            background: rgba(248,113,113,0.18);
            color: #FCA5A5;
            border-color: rgba(248,113,113,0.40);
        }
        .status-seguimiento,
        .status-en-curso {
            background: rgba(59,130,246,0.20);
            color: #93C5FD;
            border-color: rgba(59,130,246,0.45);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ==========================
# PANEL DE CONTROL
# ==========================

def _safe_len(df):
    return 0 if df is None else len(df)


def render_panel_control():
    """Panel con KPIs básicos usando las funciones cacheadas."""

    df_clientes = load_clientes()
    df_proyectos = load_proyectos()

    num_clientes = _safe_len(df_clientes)
    num_proyectos = _safe_len(df_proyectos)

    # Proyectos por estado (defensivo)
    estados_resumen = {}
    if df_proyectos is not None and not df_proyectos.empty and "estado" in df_proyectos.columns:
        estados_resumen = df_proyectos["estado"].value_counts().to_dict()

    st.markdown(
        """
        <div class="apple-card">
            <div class="section-badge">Visión general</div>
            <h1 style="margin-top:6px; margin-bottom:6px;">Panel de control</h1>
            <p style="color:#9CA3AF; margin-bottom:0; font-size:0.9rem;">
                Resumen rápido de relaciones y proyectos de prescripción.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Métricas principales
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <div class="metric-pill">
                <div class="metric-label">Clientes activos</div>
                <div class="metric-value">{num_clientes}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="metric-pill">
                <div class="metric-label">Proyectos totales</div>
                <div class="metric-value">{num_proyectos}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        ganados = estados_resumen.get("Ganado", 0) + estados_resumen.get("ganado", 0)
        st.markdown(
            f"""
            <div class="metric-pill">
                <div class="metric-label">Proyectos ganados</div>
                <div class="metric-value">{ganados}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # Últimos proyectos (defensivo con columnas)
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.markdown("#### Últimos proyectos", unsafe_allow_html=True)

    if df_proyectos is None or df_proyectos.empty:
        st.info("Todavía no hay proyectos en el CRM.")
    else:
        df_to_show = df_proyectos.copy()

        # Orden por fecha si existe
        for col_fecha in ["fecha_apertura", "fecha", "created_at"]:
            if col_fecha in df_to_show.columns:
                try:
                    df_to_show[col_fecha] = pd.to_datetime(df_to_show[col_fecha])
                    df_to_show = df_to_show.sort_values(col_fecha, ascending=False)
                except Exception:
                    pass
                break

        # Selección básica de columnas
        columnas_preferidas = ["nombre_proyecto", "cliente", "estado", "ciudad", "provincia"]
        columnas_presentes = [c for c in columnas_preferidas if c in df_to_show.columns]
        if columnas_presentes:
            df_to_show = df_to_show[columnas_presentes]

        st.dataframe(
            df_to_show.head(10),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


# ==========================
# MAIN APP
# ==========================

def main():
    set_page_style()

    with st.sidebar:
        st.markdown("## CRM Prescripción 2N")
        menu = st.radio(
            "Navegación",
            ("Panel de Control", "Clientes", "Proyectos", "Buscar"),
            index=0,
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
