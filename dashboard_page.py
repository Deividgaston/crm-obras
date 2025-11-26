import streamlit as st
import pandas as pd
import altair as alt
from datetime import date

from crm_utils import (
    get_proyectos,
    filtrar_obras_importantes,
)

try:
    from style_injector import inject_apple_style
except Exception:
    def inject_apple_style():
        pass


# ============================================================================
# CARGA CACHÉ
# ============================================================================

@st.cache_data(show_spinner=False)
def load_proyectos_dashboard() -> pd.DataFrame | None:
    return get_proyectos()


# ============================================================================
# TABLA CRM (HTML)
# ============================================================================

def _tabla_crm(df: pd.DataFrame):
    if df.empty:
        st.info("No hay datos para esta tabla.")
        return

    html = df.to_html(
        index=False,
        classes="crm-table",
        border=0,
        justify="left",
    )
    st.markdown(html, unsafe_allow_html=True)


# ============================================================================
# GRÁFICOS ALTAR (FONDO BLANCO)
# ============================================================================

COLOR_AZUL = "#0170D2"
COLOR_AZUL_CLARO = "#5AB0F5"


def _pie_chart(df: pd.DataFrame, col: str, titulo: str):
    if df.empty or col not in df.columns:
        st.warning(f"No hay datos para {titulo}.")
        return

    resumen = df[col].value_counts().reset_index()
    resumen.columns = [col, "count"]

    chart = (
        alt.Chart(resumen, title=None)
        .mark_arc()
        .encode(
            theta="count:Q",
            color=alt.Color(f"{col}:N", legend=alt.Legend(title=col)),
            tooltip=[col, "count"],
        )
        .properties(height=300, width="container", background="white")
        .configure_view(stroke=None)
    )
    st.altair_chart(chart, use_container_width=True)


def _bar_chart(df: pd.DataFrame, group_col: str, value_col: str, titulo: str):
    if df.empty or group_col not in df.columns:
        st.warning(f"No hay datos para {titulo}.")
        return

    resumen = (
        df.groupby(group_col)[value_col]
        .count()
        .reset_index()
        .rename(columns={value_col: "num"})
        .sort_values("num", ascending=False)
        .head(10)
    )

    chart = (
        alt.Chart(resumen, title=None)
        .mark_bar(color=COLOR_AZUL)
        .encode(
            x="num:Q",
            y=alt.Y(f"{group_col}:N", sort="-x"),
            tooltip=[group_col, "num"],
        )
        .properties(height=300, background="white")
        .configure_view(stroke=None)
    )
    st.altair_chart(chart, use_container_width=True)


def _bar_chart_sum(df: pd.DataFrame, group_col: str, sum_col: str, titulo: str):
    if df.empty or group_col not in df.columns or sum_col not in df.columns:
        st.warning(f"No hay datos para {titulo}.")
        return

    resumen = (
        df.groupby(group_col)[sum_col]
        .sum()
        .reset_index()
        .sort_values(sum_col, ascending=False)
        .head(10)
    )

    chart = (
        alt.Chart(resumen, title=None)
        .mark_bar(color=COLOR_AZUL_CLARO)
        .encode(
            x=f"{sum_col}:Q",
            y=alt.Y(f"{group_col}:N", sort="-x"),
            tooltip=[group_col, sum_col],
        )
        .properties(height=300, background="white")
        .configure_view(stroke=None)
    )
    st.altair_chart(chart, use_container_width=True)


# ============================================================================
# DASHBOARD
# ============================================================================

def render_dashboard():
    inject_apple_style()

    st.markdown(
        """
        <div class="apple-card">
            <div class="badge">Dashboard</div>
            <h3 style="margin-top:2px; margin-bottom:2px;">Análisis general de la actividad</h3>
            <p>
                Visualiza la distribución completa de tus proyectos, el potencial económico,
                los clientes con más obras y las zonas prioritarias. Todo en un vistazo.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df = load_proyectos_dashboard()

    if df is None or df.empty:
        st.info("No hay proyectos para analizar todavía.")
        return

    # ============================================================================
    # MÉTRICAS GENERALES
    # ============================================================================

    total = len(df)
    total_potencial = df["potencial_eur"].fillna(0).sum()
    ciudades = df["ciudad"].dropna().nunique()
    clientes = df["cliente_principal"].dropna().nunique()

    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.markdown(
        '<h4 style="color:#032D60;margin:0 0 8px 0;">📊 Resumen general</h4>',
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Proyectos totales", total)
    col2.metric("Potencial total (€)", f"{total_potencial:,.0f}")
    col3.metric("Ciudades", ciudades)
    col4.metric("Clientes", clientes)

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================================
    # DISTRIBUCIÓN POR ESTADO / TIPO
    # ============================================================================

    colA, colB = st.columns(2)
    with colA:
        st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
        st.markdown("<h4>Distribución por estado</h4>", unsafe_allow_html=True)
        _pie_chart(df, "estado", "Estados")
        st.markdown("</div>", unsafe_allow_html=True)

    with colB:
        st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
        st.markdown("<h4>Distribución por tipo de proyecto</h4>", unsafe_allow_html=True)
        _pie_chart(df, "tipo_proyecto", "Tipos")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================================
    # OBRAS POR CLIENTE / OBRAS POR CIUDAD
    # ============================================================================

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
        st.markdown("<h4>Clientes con más obras</h4>", unsafe_allow_html=True)
        _bar_chart(df, "cliente_principal", "id", "Clientes top")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
        st.markdown("<h4>Ciudades con más obras</h4>", unsafe_allow_html=True)
        _bar_chart(df, "ciudad", "id", "Ciudades top")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================================
    # POTENCIAL POR CLIENTE
    # ============================================================================

    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.markdown("<h4>Potencial económico por cliente (€)</h4>", unsafe_allow_html=True)
    _bar_chart_sum(df, "cliente_principal", "potencial_eur", "Potencial por cliente")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================================
    # TABLA OBRAS IMPORTANTES
    # ============================================================================

    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.markdown("<h4>🏆 Obras importantes</h4>", unsafe_allow_html=True)

    df_imp = filtrar_obras_importantes(df)
    if df_imp.empty:
        st.caption("No se han identificado obras importantes según el criterio actual.")
    else:
        _tabla_crm(df_imp)

    st.markdown("</div>", unsafe_allow_html=True)
