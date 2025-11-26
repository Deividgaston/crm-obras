import streamlit as st
import pandas as pd
import altair as alt

from crm_utils import get_proyectos, filtrar_obras_importantes

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
    html = df.to_html(index=False, classes="crm-table", border=0)
    st.markdown(html, unsafe_allow_html=True)


# ============================================================================
# TEMA GRÁFICOS (CLARO + LETRAS GRANDES)
# ============================================================================

def _tema_grafico(chart: alt.Chart) -> alt.Chart:
    """Tema Salesforce: fondo blanco y letras muy visibles."""
    return (
        chart
        .configure_view(stroke=None, fill="white")
        .configure(background="white")
        .configure_axis(
            labelColor="#032D60",
            titleColor="#032D60",
            labelFontSize=14,
            titleFontSize=16,
            gridColor="#d8dde6",
        )
        .configure_legend(
            labelColor="#032D60",
            titleColor="#032D60",
            labelFontSize=13,
            titleFontSize=15,
            symbolSize=150,
        )
        .configure_title(
            color="#032D60",
            fontSize=20,
            anchor="start"
        )
    )


# ============================================================================
# GRÁFICOS
# ============================================================================

COLOR_AZUL = "#0170D2"
COLOR_AZUL_CLARO = "#5AB0F5"


def _pie_chart(df: pd.DataFrame, col: str):
    if df.empty or col not in df.columns:
        st.warning("No hay datos para este gráfico.")
        return

    resumen = df[col].value_counts().reset_index()
    resumen.columns = [col, "count"]

    base = (
        alt.Chart(resumen, title="")
        .mark_arc()
        .encode(
            theta="count:Q",
            color=alt.Color(f"{col}:N", legend=alt.Legend(title=col)),
            tooltip=[col, "count"],
        )
        .properties(height=300, width=300)
    )
    st.altair_chart(_tema_grafico(base), use_container_width=True)


def _bar_chart(df: pd.DataFrame, group_col: str, value_col: str):
    if df.empty:
        return

    resumen = (
        df.groupby(group_col)[value_col]
        .count()
        .reset_index()
        .rename(columns={value_col: "num"})
        .sort_values("num", ascending=False)
        .head(10)
    )

    base = (
        alt.Chart(resumen, title="")
        .mark_bar(color=COLOR_AZUL)
        .encode(
            x="num:Q",
            y=alt.Y(f"{group_col}:N", sort="-x"),
            tooltip=[group_col, "num"],
        )
        .properties(height=300, width=300)
    )
    st.altair_chart(_tema_grafico(base), use_container_width=True)


def _bar_chart_sum(df: pd.DataFrame, group_col: str, sum_col: str):
    if df.empty:
        return

    resumen = (
        df.groupby(group_col)[sum_col]
        .sum()
        .reset_index()
        .sort_values(sum_col, ascending=False)
        .head(10)
    )

    base = (
        alt.Chart(resumen, title="")
        .mark_bar(color=COLOR_AZUL_CLARO)
        .encode(
            x=f"{sum_col}:Q",
            y=alt.Y(f"{group_col}:N", sort="-x"),
            tooltip=[group_col, sum_col],
        )
        .properties(height=300, width=300)
    )
    st.altair_chart(_tema_grafico(base), use_container_width=True)


# ============================================================================
# DASHBOARD
# ============================================================================

def render_dashboard():
    inject_apple_style()

    st.markdown(
        """
        <div class="apple-card">
            <div class="badge">Dashboard</div>
            <h3>Análisis general de la actividad</h3>
            <p>Indicadores clave, distribución de proyectos y potencial económico.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df = load_proyectos_dashboard()
    if df is None or df.empty:
        st.info("No hay proyectos todavía.")
        return

    # ==========================
    # MÉTRICAS
    # ==========================
    total = len(df)
    total_potencial = df["potencial_eur"].fillna(0).sum()
    ciudades = df["ciudad"].dropna().nunique()
    clientes = df["cliente_principal"].dropna().nunique()

    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Proyectos", total)
    col2.metric("Potencial (€)", f"{total_potencial:,.0f}")
    col3.metric("Ciudades", ciudades)
    col4.metric("Clientes", clientes)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================
    # PIE CHARTS
    # ==========================
    colA, colB = st.columns(2)
    with colA:
        st.markdown('<div class="apple-card-light"><h4>Por estado</h4>', unsafe_allow_html=True)
        _pie_chart(df, "estado")
        st.markdown("</div>", unsafe_allow_html=True)

    with colB:
        st.markdown('<div class="apple-card-light"><h4>Por tipo</h4>', unsafe_allow_html=True)
        _pie_chart(df, "tipo_proyecto")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================
    # BAR CHARTS
    # ==========================
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="apple-card-light"><h4>Clientes con más obras</h4>', unsafe_allow_html=True)
        _bar_chart(df, "cliente_principal", "id")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="apple-card-light"><h4>Ciudades con más obras</h4>', unsafe_allow_html=True)
        _bar_chart(df, "ciudad", "id")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown('<div class="apple-card-light"><h4>Potencial por cliente (€)</h4>', unsafe_allow_html=True)
    _bar_chart_sum(df, "cliente_principal", "potencial_eur")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================
    # OBRAS IMPORTANTES
    # ==========================
    st.markdown('<div class="apple-card-light"><h4>🏆 Obras importantes</h4>', unsafe_allow_html=True)
    df_imp = filtrar_obras_importantes(df)
    _tabla_crm(df_imp)
    st.markdown("</div>", unsafe_allow_html=True)
