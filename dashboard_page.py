import streamlit as st
import altair as alt
import pandas as pd

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
    """Dashboard principal de analítica de prescripción."""
    inject_apple_style()

    # ===========================
    # CABECERA
    # ===========================
    st.markdown(
        """
        <div class="apple-card">
            <div class="badge">Dashboard</div>
            <h1 style="margin-top:4px; margin-bottom:4px;">📊 Analítica del CRM</h1>
            <p style="font-size:0.9rem; color:#9ca3af; margin-bottom:0;">
                Vista global de tu pipeline de prescripción: estados, prioridades,
                potencial económico y distribución geográfica.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
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
    # KPIs SUPERIORES
    # ===========================
    kpis = compute_kpis(df)

    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Proyectos totales", int(kpis.get("total_proyectos", 0)))

    with col2:
        st.metric("Proyectos activos", int(kpis.get("proyectos_activos", 0)))

    with col3:
        total_pot = float(kpis.get("total_potencial", 0.0))
        st.metric("Potencial total (€)", f"{total_pot:,.0f}")

    with col4:
        ticket_medio = float(kpis.get("ticket_medio", 0.0))
        st.metric("Ticket medio (€)", f"{ticket_medio:,.0f}")

    st.markdown("</div>", unsafe_allow_html=True)

    # ===========================
    # DISTRIBUCIÓN POR ESTADO Y PRIORIDAD (PIE CHARTS)
    # ===========================
    st.markdown(
        '<div class="apple-card-light" style="margin-top:1.25rem;">',
        unsafe_allow_html=True,
    )
    st.markdown("### Pipeline por estado y prioridad", unsafe_allow_html=True)

    col_e, col_p = st.columns(2)

    # --- Estado ---
    with col_e:
        funnel_df = compute_funnel_estado(df)
        if funnel_df is not None and not funnel_df.empty:
            chart_estado = (
                alt.Chart(funnel_df)
                .mark_arc(outerRadius=110, innerRadius=40)
                .encode(
                    theta=alt.Theta("proyectos:Q", stack=True),
                    color=alt.Color(
                        "estado:N",
                        legend=alt.Legend(title="Estado"),
                    ),
                    tooltip=["estado:N", "proyectos:Q"],
                )
            )
            st.altair_chart(chart_estado, use_container_width=True)
        else:
            st.caption("Sin datos de estado.")

    # --- Prioridad ---
    with col_p:
        prio_df = compute_prioridades(df)
        if prio_df is not None and not prio_df.empty:
            chart_prio = (
                alt.Chart(prio_df)
                .mark_arc(outerRadius=110, innerRadius=40)
                .encode(
                    theta=alt.Theta("proyectos:Q", stack=True),
                    color=alt.Color(
                        "prioridad:N",
                        legend=alt.Legend(title="Prioridad"),
                    ),
                    tooltip=["prioridad:N", "proyectos:Q"],
                )
            )
            st.altair_chart(chart_prio, use_container_width=True)
        else:
            st.caption("Sin datos de prioridad.")

    st.markdown("</div>", unsafe_allow_html=True)

    # ===========================
    # GEOGRAFÍA Y RANKING PROMOTORAS
    # ===========================
    st.markdown(
        '<div class="apple-card-light" style="margin-top:1.25rem;">',
        unsafe_allow_html=True,
    )
    st.markdown("### Geografía y ranking de promotoras", unsafe_allow_html=True)

    col_g, col_r = st.columns(2)

    # --- Potencial por provincia (pie) ---
    with col_g:
        prov_df = compute_potencial_por_provincia(df)
        if prov_df is not None and not prov_df.empty:
            top_prov = prov_df.head(8)
            chart_prov = (
                alt.Chart(top_prov)
                .mark_arc(outerRadius=110, innerRadius=40)
                .encode(
                    theta=alt.Theta("proyectos:Q", stack=True),
                    color=alt.Color(
                        "provincia:N",
                        legend=alt.Legend(title="Provincia"),
                    ),
                    tooltip=[
                        "provincia:N",
                        "proyectos:Q",
                        alt.Tooltip(
                            "potencial:Q",
                            title="Potencial (€)",
                            format=",.0f",
                        ),
                    ],
                )
            )
            st.altair_chart(chart_prov, use_container_width=True)
        else:
            st.caption("Sin datos de provincia.")

    # --- Ranking promotoras (tabla) ---
    with col_r:
        rank_df = compute_ranking_promotoras(df, top_n=10)
        if rank_df is not None and not rank_df.empty:
            tabla_rank = rank_df.rename(
                columns={
                    "promotora_display": "Promotora / Cliente principal",
                    "proyectos": "Proyectos",
                    "potencial": "Potencial (€)",
                }
            )
            st.dataframe(
                tabla_rank,
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.caption("Sin datos de promotoras.")

    st.markdown("</div>", unsafe_allow_html=True)

    # ===========================
    # LISTA DE PROYECTOS GANADOS
    # ===========================
    st.markdown(
        '<div class="apple-card-light" style="margin-top:1.25rem;">',
        unsafe_allow_html=True,
    )
    st.markdown("### 🏆 Proyectos ganados", unsafe_allow_html=True)

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

    st.markdown("</div>", unsafe_allow_html=True)
