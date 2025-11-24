import streamlit as st
import plotly.express as px
import plotly.io as pio

from dashboard_utils import (
    load_dashboard_data,
    compute_kpis,
    compute_funnel_estado,
    compute_proyectos_por_mes,
    compute_potencial_por_provincia,
    compute_ranking_promotoras,
    compute_prioridades,
    compute_histograma_potencial,
)

try:
    from style_injector import inject_apple_style
except:
    def inject_apple_style():
        pass


# ===============================================================
# CONFIG PLOTLY TEMA OSCURO TIPO APPLE
# ===============================================================
def _configure_plotly_theme():
    """
    Configura un tema oscuro coherente con el Apple Dark de la app.
    """
    pio.templates["apple_dark"] = pio.templates["plotly_dark"]

    # Ajustamos algunos parámetros base por defecto
    pio.templates["apple_dark"].layout.update(
        {
            "paper_bgcolor": "#020617",
            "plot_bgcolor": "#020617",
            "font": {"family": "-apple-system, BlinkMacSystemFont,system-ui,sans-serif"},
            "title": {"x": 0.02, "xanchor": "left"},
            "xaxis": {
                "gridcolor": "#111827",
                "zerolinecolor": "#111827",
            },
            "yaxis": {
                "gridcolor": "#111827",
                "zerolinecolor": "#111827",
            },
            "legend": {
                "bgcolor": "rgba(15,23,42,0.0)",
                "bordercolor": "rgba(0,0,0,0)",
            },
        }
    )
    pio.templates.default = "apple_dark"


# ===============================================================
# RENDER DASHBOARD
# ===============================================================
def render_dashboard():
    inject_apple_style()
    _configure_plotly_theme()

    # Cabecera principal tipo Apple card
    st.markdown(
        """
        <div class="apple-card">
            <div class="badge">Dashboard · Analítica</div>
            <h1 style="margin-top:4px;margin-bottom:4px;">📊 Gráficos y Estadísticas</h1>
            <p style="font-size:0.9rem; color:#9ca3af; margin-bottom:0;">
                Analiza tu pipeline de prescripción con vistas de funnel, promotoras clave, 
                potencial económico y distribución geográfica. Datos en tiempo real desde tu CRM.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ================= CARGA DE DATOS =================
    with st.spinner("Cargando datos desde Firestore…"):
        try:
            df = load_dashboard_data()
        except Exception as e:
            st.error("No se pudo cargar Firestore (posible cuota agotada).")
            st.code(str(e))
            return

    if df.empty:
        st.warning("No hay proyectos suficientes para generar gráficos.")
        return

    # ================= KPIs SUPERIORES =================
    kpis = compute_kpis(df)

    st.markdown(
        """
        <div class="card-light">
            <h2 class="section-title">📌 Resumen ejecutivo</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Proyectos totales",
            f"{kpis['total_proyectos']}",
        )
    with col2:
        st.metric(
            "Potencial total",
            f"{kpis['total_potencial']:,.0f} €".replace(",", "."),
        )
    with col3:
        st.metric(
            "Ticket medio",
            f"{kpis['ticket_medio']:,.0f} €".replace(",", "."),
        )
    with col4:
        st.metric(
            "Proyectos activos",
            f"{kpis['proyectos_activos']}",
        )
    with col5:
        st.metric(
            "% proyectos ganados",
            f"{kpis['ratio_ganados']:.1f} %",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ================= FILTROS BÁSICOS =================
    st.markdown(
        """
        <div class="card-light">
            <div class="badge">Filtros</div>
            <h3 style="margin-top:8px;margin-bottom:4px;">🎛️ Filtro rápido de estado y prioridad</h3>
            <p class="small-caption">
                Aplica filtros para centrar los gráficos en determinados estados o prioridades.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    colf1, colf2 = st.columns(2)

    estados_unicos = sorted(df["estado"].dropna().unique().tolist())
    prioridades_unicas = sorted(df["prioridad"].dropna().unique().tolist())

    with colf1:
        estados_sel = st.multiselect(
            "Estados",
            options=estados_unicos,
            default=estados_unicos,
        )
    with colf2:
        prioridades_sel = st.multiselect(
            "Prioridades",
            options=prioridades_unicas,
            default=prioridades_unicas,
        )

    df_filtrado = df[
        df["estado"].isin(estados_sel) & df["prioridad"].isin(prioridades_sel)
    ].copy()

    if df_filtrado.empty:
        st.warning("No hay proyectos con la combinación de filtros seleccionada.")
        return

    # ================= FUNNEL Y EVOLUCIÓN =================
    st.markdown(
        """
        <div class="card-light">
            <div class="badge">Pipeline</div>
            <h3 style="margin-top:8px;margin-bottom:4px;">Embudo de prescripción y evolución temporal</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns(2)

    # FUNNEL
    with col_a:
        df_funnel = compute_funnel_estado(df_filtrado)
        if df_funnel["proyectos"].sum() == 0:
            st.info("No hay datos para el funnel con los filtros aplicados.")
        else:
            fig_funnel = px.funnel(
                df_funnel,
                x="proyectos",
                y="estado",
                title="Funnel por estado",
            )
            st.plotly_chart(fig_funnel, use_container_width=True)

    # EVOLUCIÓN TEMPORAL
    with col_b:
        df_mes = compute_proyectos_por_mes(df_filtrado)
        if df_mes.empty:
            st.info("No hay fechas válidas para graficar evolución temporal.")
        else:
            fig_line = px.line(
                df_mes,
                x="anio_mes",
                y="proyectos",
                markers=True,
                title="Proyectos creados por mes",
            )
            st.plotly_chart(fig_line, use_container_width=True)

    # ================= RANKING PROMOTORAS Y POTENCIAL POR PROVINCIA =================
    st.markdown(
        """
        <div class="card-light">
            <div class="badge">Oportunidad de negocio</div>
            <h3 style="margin-top:8px;margin-bottom:4px;">Promotoras clave y distribución geográfica</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_c, col_d = st.columns(2)

    # RANKING PROMOTORAS
    with col_c:
        df_rank = compute_ranking_promotoras(df_filtrado, top_n=10)
        if df_rank.empty:
            st.info("No hay datos de promotora / cliente principal para rankear.")
        else:
            fig_rank = px.bar(
                df_rank,
                x="potencial",
                y="promotora_display",
                orientation="h",
                title="Ranking promotoras por potencial",
                hover_data=["proyectos"],
            )
            fig_rank.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig_rank, use_container_width=True)

    # POTENCIAL POR PROVINCIA
    with col_d:
        df_geo = compute_potencial_por_provincia(df_filtrado)
        if df_geo.empty:
            st.info("No hay provincias definidas.")
        else:
            fig_geo = px.bar(
                df_geo,
                x="provincia",
                y="potencial",
                title="Potencial por provincia",
                hover_data=["proyectos"],
            )
            st.plotly_chart(fig_geo, use_container_width=True)

    # ================= PRIORIDADES Y DISTRIBUCIÓN DE POTENCIAL =================
    st.markdown(
        """
        <div class="card-light">
            <div class="badge">Calidad del pipeline</div>
            <h3 style="margin-top:8px;margin-bottom:4px;">Prioridades y distribución de potencial</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_e, col_f = st.columns(2)

    # PRIORIDADES (barras o pie)
    with col_e:
        df_prio = compute_prioridades(df_filtrado)
        if df_prio.empty:
            st.info("No hay prioridades definidas.")
        else:
            fig_prio = px.bar(
                df_prio,
                x="prioridad",
                y="proyectos",
                title="Proyectos por prioridad",
            )
            st.plotly_chart(fig_prio, use_container_width=True)

    # HISTOGRAMA POTENCIAL
    with col_f:
        serie_pot = compute_histograma_potencial(df_filtrado)
        if serie_pot.empty:
            st.info("No hay datos de potencial para histogramas.")
        else:
            fig_hist = px.histogram(
                serie_pot,
                nbins=20,
                title="Distribución del potencial (€)",
            )
            st.plotly_chart(fig_hist, use_container_width=True)
