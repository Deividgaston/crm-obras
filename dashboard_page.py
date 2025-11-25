import streamlit as st
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
)


def render_dashboard():
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
                Vista global de tus KPIs de prescripción: pipeline, ganancias,
                evolución de obras y distribución geográfica.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ===========================
    # CARGA DE DATOS (NORMALIZADOS)
    # ===========================
    try:
        df_p = load_dashboard_data()
    except Exception as e:
        st.error("No se pudieron cargar los datos del CRM.")
        st.code(str(e))
        return

    if df_p is None or df_p.empty:
        st.info("Todavía no hay proyectos en el CRM.")
        return

    # ===========================
    # KPIs SUPERIORES
    # ===========================
    kpis = compute_kpis(df_p)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Proyectos", int(kpis["total_proyectos"]))

    with col2:
        ganados = int((df_p["estado"] == "Ganado").sum()) if "estado" in df_p.columns else 0
        st.metric("Proyectos Ganados", ganados)

    with col3:
        perdidos = int((df_p["estado"] == "Perdido").sum()) if "estado" in df_p.columns else 0
        st.metric("Proyectos Perdidos", perdidos)

    with col4:
        total_pot = float(kpis["total_potencial"])
        st.metric("Potencial Total (€)", f"{total_pot:,.0f}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ===========================
    # DISTRIBUCIÓN POR ESTADO (TABLA)
    # ===========================
    st.markdown(
        """
        <div class="apple-card-light">
            <div class="badge">Pipeline</div>
            <h3 style="margin-top:8px; margin-bottom:4px;">📁 Distribución por estado</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    funnel_df = compute_funnel_estado(df_p)

    if not funnel_df.empty:
        tabla_estado = funnel_df.rename(columns={"estado": "Estado", "proyectos": "Total"})
        st.dataframe(
            tabla_estado,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No hay información de estados para mostrar.")

    # ===========================
    # DISTRIBUCIÓN POR CIUDAD
    # ===========================
    st.markdown(
        """
        <div class="apple-card-light" style="margin-top:1.5rem;">
            <div class="badge">Geografía</div>
            <h3 style="margin-top:8px; margin-bottom:4px;">📌 Obras por ciudad</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "ciudad" in df_p.columns and not df_p.empty:
        tabla_ciudades = (
            df_p["ciudad"]
            .fillna("Sin ciudad")
            .value_counts()
            .reset_index()
        )
        tabla_ciudades.columns = ["Ciudad", "Total"]

        st.dataframe(
            tabla_ciudades,
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("No hay campo 'ciudad' en tus proyectos.")

    # ===========================
    # LISTA DE PROYECTOS GANADOS
    # ===========================
    st.markdown(
        """
        <div class="apple-card-light" style="margin-top:1.5rem;">
            <div class="badge">Resultados</div>
            <h3 style="margin-top:8px; margin-bottom:4px;">🏆 Proyectos Ganados</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "estado" in df_p.columns:
        df_ganados = df_p[df_p["estado"] == "Ganado"]

        if df_ganados.empty:
            st.info("No hay proyectos ganados todavía.")
        else:
            columnas_preferidas = [
                "nombre_obra",
                "cliente_principal",
                "promotora_display",
                "cliente",
                "ciudad",
                "provincia",
                "potencial_eur",
                "fecha_creacion",
            ]
            columnas = [c for c in columnas_preferidas if c in df_ganados.columns]

            st.dataframe(
                df_ganados[columnas],
                hide_index=True,
                use_container_width=True,
            )
    else:
        st.info("Los proyectos no tienen campo de 'estado', no se puede listar ganados.")
