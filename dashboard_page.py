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


# ==========================================================
# DASHBOARD SLDS + PESTAÑA KANBAN
# ==========================================================

def render_dashboard():
    inject_apple_style()

    # HEADER
    st.markdown("""
        <div class="apple-card">
            <div class="badge">Dashboard</div>
            <h3 style="margin-top:2px; margin-bottom:2px;">Análisis y pipeline</h3>
            <p>Datos agregados, actividad por promotora, mapa geográfico y vista Kanban.</p>
        </div>
    """, unsafe_allow_html=True)

    # CARGA DATOS
    try:
        df = load_dashboard_data()
    except Exception as e:
        st.error("Error cargando datos del dashboard.")
        st.code(str(e))
        return

    if df is None or df.empty:
        st.info("No hay proyectos suficientes para generar dashboard.")
        return

    # TABS PRINCIPALES
    tab_general, tab_kanban = st.tabs([
        "📊 Resumen",
        "🗂 Kanban"
    ])

    # ======================================================
    # TAB 1: DASHBOARD / RESUMEN
    # ======================================================
    with tab_general:

        # KPIs
        k = compute_kpis(df)

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.markdown(f"""<div class="metric-card"><div class="metric-title">Proyectos</div><div class="metric-value">{k['total_proyectos']}</div></div>""", unsafe_allow_html=True)
        c2.markdown(f"""<div class="metric-card"><div class="metric-title">Activos</div><div class="metric-value">{k['proyectos_activos']}</div></div>""", unsafe_allow_html=True)
        c3.markdown(f"""<div class="metric-card"><div class="metric-title">Potencial (€)</div><div class="metric-value">{k['total_potencial']:,.0f}</div></div>""", unsafe_allow_html=True)
        c4.markdown(f"""<div class="metric-card"><div class="metric-title">Ticket Medio (€)</div><div class="metric-value">{k['ticket_medio']:,.0f}</div></div>""", unsafe_allow_html=True)
        c5.markdown(f"""<div class="metric-card"><div class="metric-title">Ganados (%)</div><div class="metric-value">{k['ratio_ganados']:.1f}%</div></div>""", unsafe_allow_html=True)

        st.markdown("---")

        # PIPELINE + PRIORIDAD
        st.markdown("### 📂 Pipeline y prioridades")

        col1, col2 = st.columns([3, 2])

        with col1:
            fdf = compute_funnel_estado(df)
            if fdf is not None and not fdf.empty:
                chart = (
                    alt.Chart(fdf)
                    .mark_bar(size=22)
                    .encode(
                        x=alt.X("proyectos:Q", title="Proyectos"),
                        y=alt.Y("estado:N", sort="-x", title="Estado"),
                        color=alt.Color("estado:N", legend=None),
                        tooltip=["estado", "proyectos"],
                    )
                    .properties(height=280)
                )
                st.altair_chart(chart, use_container_width=True)

        with col2:
            pdf = compute_prioridades(df)
            if pdf is not None and not pdf.empty:
                donut = (
                    alt.Chart(pdf)
                    .mark_arc(innerRadius=40, outerRadius=90)
                    .encode(
                        theta="proyectos:Q",
                        color="prioridad:N",
                        tooltip=["prioridad", "proyectos"],
                    )
                    .properties(height=260)
                )
                st.altair_chart(donut, use_container_width=True)

        st.markdown("---")

        # RANKING PROMOTORAS
        st.markdown("### 🏢 Ranking por promotora")

        col1, col2 = st.columns([3, 2])
        r = compute_ranking_promotoras(df, top_n=15)

        with col1:
            if r is not None and not r.empty:
                chart = (
                    alt.Chart(r)
                    .mark_bar(size=18)
                    .encode(
                        x="proyectos:Q",
                        y=alt.Y("promotora_display:N", sort="-x"),
                        tooltip=["promotora_display", "proyectos", "potencial"],
                        color=alt.Color("promotora_display:N", legend=None),
                    )
                    .properties(height=340)
                )
                st.altair_chart(chart, use_container_width=True)

        with col2:
            if r is not None and not r.empty:
                st.dataframe(
                    r.rename(columns={
                        "promotora_display": "Promotora",
                        "proyectos": "Obras",
                        "potencial": "Potencial (€)"
                    }),
                    hide_index=True,
                    use_container_width=True
                )

        st.markdown("---")

        # GEO
        st.markdown("### 🗺 Distribución por provincia")

        col1, col2 = st.columns([3, 2])
        g = compute_potencial_por_provincia(df)

        with col1:
            if g is not None and not g.empty:
                chart = (
                    alt.Chart(g)
                    .mark_bar(size=18)
                    .encode(
                        x="potencial:Q",
                        y=alt.Y("provincia:N", sort="-x"),
                        tooltip=["provincia", "proyectos", "potencial"],
                        color=alt.Color("provincia:N", legend=None),
                    )
                    .properties(height=330)
                )
                st.altair_chart(chart, use_container_width=True)

        with col2:
            if g is not None and not g.empty:
                st.dataframe(
                    g.rename(columns={
                        "provincia": "Provincia",
                        "proyectos": "Obras",
                        "potencial": "Potencial (€)"
                    }),
                    hide_index=True,
                    use_container_width=True
                )

    # ======================================================
    # TAB 2: KANBAN
    # ======================================================
    with tab_kanban:
        from dashboard_kanban import render_kanban
        render_kanban(df)
