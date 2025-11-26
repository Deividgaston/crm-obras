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


def render_dashboard() -> None:
    """Dashboard principal de analítica de prescripción (estilo Salesforce / denso)."""
    inject_apple_style()

    # ===========================
    # HEADER COMPACTO
    # ===========================
    st.markdown("### Dashboard de prescripción")
    st.caption(
        "Resumen de pipeline, concentración por empresa y distribución geográfica."
    )

    # ===========================
    # CARGA DE DATOS
    # ===========================
    try:
        df = load_dashboard_data()
    except Exception as e:
        st.error("No se pudieron cargar los datos del CRM.")
        st.code(str(e))
        return

    if df is None or df.empty:
        st.info("Todavía no hay proyectos en el CRM para mostrar en el dashboard.")
        return

    # ===========================
    # KPIs SUPERIORES (COMPACTOS)
    # ===========================
    kpis = compute_kpis(df)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Proyectos totales", int(kpis.get("total_proyectos", 0)))

    with col2:
        st.metric("Activos", int(kpis.get("proyectos_activos", 0)))

    with col3:
        total_pot = float(kpis.get("total_potencial", 0.0))
        st.metric("Potencial total (€)", f"{total_pot:,.0f}")

    with col4:
        ticket_medio = float(kpis.get("ticket_medio", 0.0))
        st.metric("Ticket medio (€)", f"{ticket_medio:,.0f}")

    with col5:
        ratio = float(kpis.get("ratio_ganados", 0.0))
        st.metric("Ratio ganados (%)", f"{ratio:.1f}%")

    st.markdown("---")

    # ===========================
    # BLOQUE 1: PIPELINE + PRIORIDAD
    # ===========================
    st.markdown("#### Pipeline y prioridad")

    col_pipe, col_prio = st.columns([3, 2])

    # --- Pipeline por estado (barra horizontal) ---
    with col_pipe:
        funnel_df = compute_funnel_estado(df)
        if funnel_df is not None and not funnel_df.empty:
            chart_estado = (
                alt.Chart(funnel_df)
                .mark_bar()
                .encode(
                    x=alt.X("proyectos:Q", title="Número de proyectos"),
                    y=alt.Y("estado:N", sort="-x", title="Estado"),
                    color=alt.Color("estado:N", legend=None),
                    tooltip=[
                        alt.Tooltip("estado:N", title="Estado"),
                        alt.Tooltip("proyectos:Q", title="Proyectos"),
                    ],
                )
                .properties(height=260)
            )
            st.altair_chart(chart_estado, use_container_width=True)
        else:
            st.caption("Sin datos de estado.")

    # --- Proyectos por prioridad (donut compacto) ---
    with col_prio:
        prio_df = compute_prioridades(df)
        if prio_df is not None and not prio_df.empty:
            chart_prio = (
                alt.Chart(prio_df)
                .mark_arc(outerRadius=90, innerRadius=40)
                .encode(
                    theta=alt.Theta("proyectos:Q", stack=True),
                    color=alt.Color(
                        "prioridad:N", legend=alt.Legend(title="Prioridad")
                    ),
                    tooltip=[
                        alt.Tooltip("prioridad:N", title="Prioridad"),
                        alt.Tooltip("proyectos:Q", title="Proyectos"),
                    ],
                )
                .properties(height=260)
            )
            st.altair_chart(chart_prio, use_container_width=True)
            st.caption("Reparto de proyectos por prioridad.")
        else:
            st.caption("Sin datos de prioridad.")

    st.markdown("---")

    # ===========================
    # BLOQUE 2: EMPRESAS (OBRAS POR EMPRESA)
    # ===========================
    st.markdown("#### Concentración por empresa (promotora / cliente principal)")

    col_emp_chart, col_emp_table = st.columns([3, 2])

    rank_df = compute_ranking_promotoras(df, top_n=15)

    # --- Gráfico: nº de obras por empresa ---
    with col_emp_chart:
        if rank_df is not None and not rank_df.empty:
            chart_rank = (
                alt.Chart(rank_df)
                .mark_bar()
                .encode(
                    x=alt.X("proyectos:Q", title="Número de obras"),
                    y=alt.Y(
                        "promotora_display:N",
                        sort="-x",
                        title="Empresa / Promotora",
                    ),
                    color=alt.Color("promotora_display:N", legend=None),
                    tooltip=[
                        alt.Tooltip("promotora_display:N", title="Empresa"),
                        alt.Tooltip("proyectos:Q", title="Obras"),
                        alt.Tooltip(
                            "potencial:Q",
                            title="Potencial (€)",
                            format=",.0f",
                        ),
                    ],
                )
                .properties(height=320)
            )
            st.altair_chart(chart_rank, use_container_width=True)
        else:
            st.caption("Sin datos de empresas / promotoras.")

    # --- Tabla: obras y potencial por empresa ---
    with col_emp_table:
        if rank_df is not None and not rank_df.empty:
            tabla_rank = rank_df.rename(
                columns={
                    "promotora_display": "Empresa",
                    "proyectos": "Obras",
                    "potencial": "Potencial (€)",
                }
            )
            st.dataframe(
                tabla_rank,
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.caption("Sin datos para tabla de empresas.")

    st.markdown("---")

    # ===========================
    # BLOQUE 3: GEOGRAFÍA (PROVINCIA)
    # ===========================
    st.markdown("#### Distribución geográfica (provincia)")

    col_geo_chart, col_geo_table = st.columns([3, 2])

    prov_df = compute_potencial_por_provincia(df)

    # --- Gráfico por provincia ---
    with col_geo_chart:
        if prov_df is not None and not prov_df.empty:
            top_prov = prov_df.head(12)
            chart_prov = (
                alt.Chart(top_prov)
                .mark_bar()
                .encode(
                    x=alt.X("potencial:Q", title="Potencial total (€)"),
                    y=alt.Y(
                        "provincia:N",
                        sort="-x",
                        title="Provincia",
                    ),
                    color=alt.Color("provincia:N", legend=None),
                    tooltip=[
                        alt.Tooltip("provincia:N", title="Provincia"),
                        alt.Tooltip("proyectos:Q", title="Obras"),
                        alt.Tooltip(
                            "potencial:Q",
                            title="Potencial (€)",
                            format=",.0f",
                        ),
                    ],
                )
                .properties(height=300)
            )
            st.altair_chart(chart_prov, use_container_width=True)
        else:
            st.caption("Sin datos de provincias.")

    # --- Tabla por provincia ---
    with col_geo_table:
        if prov_df is not None and not prov_df.empty:
            tabla_prov = prov_df.rename(
                columns={
                    "provincia": "Provincia",
                    "proyectos": "Obras",
                    "potencial": "Potencial (€)",
                }
            )
            st.dataframe(
                tabla_prov,
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.caption("Sin datos para tabla de provincias.")

    st.markdown("---")

    # ===========================
    # BLOQUE 4: PROYECTOS GANADOS (TABLA ANCHA)
    # ===========================
    st.markdown("#### 🏆 Proyectos ganados")

    if "estado" in df.columns:
        df_ganados = df[df["estado"] == "Ganado"]
        if df_ganados.empty:
            st.info("No hay proyectos ganados todavía.")
        else:
            columnas_preferidas = [
                "nombre_obra",
                "cliente_principal",
                "promotora_display",
                "ciudad",
                "provincia",
                "estado",
                "potencial_eur",
                "fecha_creacion",
            ]
            columnas = [c for c in columnas_preferidas if c in df_ganados.columns]

            if columnas:
                tabla_ganados = df_ganados[columnas].copy()
                if "potencial_eur" in tabla_ganados.columns:
                    tabla_ganados["potencial_eur"] = tabla_ganados[
                        "potencial_eur"
                    ].round(0)
                st.dataframe(
                    tabla_ganados,
                    hide_index=True,
                    use_container_width=True,
                )
            else:
                st.caption("No hay columnas adecuadas para mostrar en el listado.")
    else:
        st.info("Los proyectos no tienen campo 'estado', no se puede listar ganados.")
