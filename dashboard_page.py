import streamlit as st
import pandas as pd
import altair as alt

try:
    from style_injector import inject_apple_style
except Exception:
    def inject_apple_style():
        pass

from dashboard_utils import (
    load_dashboard_data,
    compute_kpis,
    compute_funnel_estado,
    compute_potencial_por_provincia,
    compute_ranking_promotoras,
    compute_prioridades,
)


# ====================================================================
# DASHBOARD — Estilo Salesforce Lightning REAL (SLDS)
# ====================================================================

def render_dashboard() -> None:
    inject_apple_style()

    # =====================================================
    # CABECERA
    # =====================================================
    st.markdown(
        """
        <div class="apple-card">
            <div class="badge">Dashboard</div>
            <h3 style="margin-top:2px; margin-bottom:2px;">Resumen de prescripción</h3>
            <p>
                Análisis del pipeline, actividad comercial por promotora y mapa de valor.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # =====================================================
    # CARGA DATOS
    # =====================================================
    try:
        df = load_dashboard_data()
    except Exception as e:
        st.error("No se pudieron cargar los datos del dashboard.")
        st.code(str(e))
        return

    if df is None or df.empty:
        st.info("Todavía no hay proyectos en el CRM.")
        return

    # =====================================================
    # KPIs TOP (Lightning Cards)
    # =====================================================
    kpis = compute_kpis(df)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Proyectos totales</div>
            <div class="metric-value">{int(kpis['total_proyectos'])}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Activos</div>
            <div class="metric-value">{int(kpis['proyectos_activos'])}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Potencial total (€)</div>
            <div class="metric-value">{kpis['total_potencial']:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Ticket medio (€)</div>
            <div class="metric-value">{kpis['ticket_medio']:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Ganados (%)</div>
            <div class="metric-value">{kpis['ratio_ganados']:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # =====================================================
    # PIPELINE + PRIORIDADES
    # =====================================================
    st.markdown("### 📂 Pipeline y prioridades")

    col_pipe, col_prio = st.columns([3, 2])

    # --- Pipeline por estado ---
    with col_pipe:
        funnel_df = compute_funnel_estado(df)
        if funnel_df is not None and not funnel_df.empty:
            chart_funnel = (
                alt.Chart(funnel_df)
                .mark_bar(size=22)
                .encode(
                    x=alt.X("proyectos:Q", title="Proyectos"),
                    y=alt.Y("estado:N", sort="-x", title="Estado"),
                    color=alt.Color("estado:N", legend=None),
                    tooltip=["estado", "proyectos"],
                )
                .properties(height=300)
            )
            st.altair_chart(chart_funnel, use_container_width=True)
        else:
            st.info("Sin datos suficientes para pipeline.")

    # --- Donut prioridades ---
    with col_prio:
        prio_df = compute_prioridades(df)

        if prio_df is not None and not prio_df.empty:
            chart_prio = (
                alt.Chart(prio_df)
                .mark_arc(innerRadius=45, outerRadius=90)
                .encode(
                    theta="proyectos:Q",
                    color=alt.Color("prioridad:N", legend=alt.Legend(title="Prioridad")),
                    tooltip=["prioridad", "proyectos"],
                )
                .properties(height=320)
            )
            st.altair_chart(chart_prio, use_container_width=True)
        else:
            st.caption("Sin datos de prioridades.")

    st.markdown("---")

    # =====================================================
    # RANKING DE EMPRESAS
    # =====================================================
    st.markdown("### 🏢 Concentración por promotora")

    col_rank_chart, col_rank_table = st.columns([3, 2])

    rank_df = compute_ranking_promotoras(df, top_n=15)

    # --- Gráfico ---
    with col_rank_chart:
        if rank_df is not None and not rank_df.empty:
            chart_rank = (
                alt.Chart(rank_df)
                .mark_bar(size=18)
                .encode(
                    x=alt.X("proyectos:Q", title="Obras"),
                    y=alt.Y("promotora_display:N", sort="-x"),
                    tooltip=["promotora_display", "proyectos", "potencial"],
                    color=alt.Color("promotora_display:N", legend=None),
                )
                .properties(height=360)
            )
            st.altair_chart(chart_rank, use_container_width=True)
        else:
            st.info("No hay suficientes empresas para mostrar ranking.")

    # --- Tabla ---
    with col_rank_table:
        if rank_df is not None and not rank_df.empty:
            tabla_rank = rank_df.rename(
                columns={
                    "promotora_display": "Promotora",
                    "proyectos": "Obras",
                    "potencial": "Potencial (€)",
                }
            )
            st.dataframe(tabla_rank, hide_index=True, use_container_width=True)
        else:
            st.caption("Tabla vacía.")

    st.markdown("---")

    # =====================================================
    # MAPA DE VALOR POR PROVINCIA
    # =====================================================
    st.markdown("### 🗺 Distribución geográfica por provincia")

    col_geo_chart, col_geo_table = st.columns([3, 2])

    prov_df = compute_potencial_por_provincia(df)

    with col_geo_chart:
        if prov_df is not None and not prov_df.empty:
            chart_prov = (
                alt.Chart(prov_df)
                .mark_bar(size=18)
                .encode(
                    x=alt.X("potencial:Q", title="Potencial (€)"),
                    y=alt.Y("provincia:N", sort="-x"),
                    tooltip=["provincia", "proyectos", "potencial"],
                    color=alt.Color("provincia:N", legend=None),
                )
                .properties(height=350)
            )
            st.altair_chart(chart_prov, use_container_width=True)
        else:
            st.caption("Sin datos de provincias.")

    with col_geo_table:
        if prov_df is not None and not prov_df.empty:
            tabla_prov = prov_df.rename(
                columns={
                    "provincia": "Provincia",
                    "proyectos": "Obras",
                    "potencial": "Potencial (€)",
                }
            )
            st.dataframe(tabla_prov, hide_index=True, use_container_width=True)
        else:
            st.caption("Sin datos.")

    st.markdown("---")

    # =====================================================
    # PROYECTOS GANADOS
    # =====================================================
    st.markdown("### 🏆 Proyectos ganados")

    if "estado" in df.columns:
        df_ganados = df[df["estado"] == "Ganado"]
        if df_ganados.empty:
            st.info("Todavía no hay proyectos ganados.")
        else:
            columnas_preferidas = [
                "nombre_obra",
                "cliente_principal",
                "ciudad",
                "provincia",
                "potencial_eur",
                "fecha_creacion",
            ]
            cols_ok = [c for c in columnas_preferidas if c in df_ganados.columns]

            st.dataframe(
                df_ganados[cols_ok].rename(
                    columns={"potencial_eur": "Potencial (€)"}
                ),
                hide_index=True,
                use_container_width=True,
            )
    else:
        st.info("Los proyectos no tienen campo 'estado' para detectar ganados.")
