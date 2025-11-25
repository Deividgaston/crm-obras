import streamlit as st
import pandas as pd
import altair as alt

from crm_utils import get_proyectos

try:
    from style_injector import inject_apple_style
except Exception:
    def inject_apple_style():
        pass


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
    # CARGA DE DATOS
    # ===========================
    try:
        proyectos = get_proyectos()
    except Exception as e:
        st.error("No se pudieron cargar los datos del CRM.")
        st.code(str(e))
        return

    df_p = pd.DataFrame(proyectos) if proyectos is not None else pd.DataFrame()

    # ===========================
    # KPIs SUPERIORES
    # ===========================
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Proyectos", len(df_p))

    with col2:
        if not df_p.empty and "estado" in df_p.columns:
            ganados = df_p[df_p["estado"] == "Ganado"].shape[0]
        else:
            ganados = 0
        st.metric("Proyectos Ganados", ganados)

    with col3:
        if not df_p.empty and "estado" in df_p.columns:
            perdidos = df_p[df_p["estado"] == "Perdido"].shape[0]
        else:
            perdidos = 0
        st.metric("Proyectos Perdidos", perdidos)

    with col4:
        if not df_p.empty and "potencial_eur" in df_p.columns:
            total_pot = float(df_p["potencial_eur"].sum())
        else:
            total_pot = 0.0
        st.metric("Potencial Total (€)", f"{total_pot:,.0f}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ===========================
    # DISTRIBUCIÓN POR ESTADO (GRÁFICO CIRCULAR)
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

    if not df_p.empty and "estado" in df_p.columns:
        df_estado = (
            df_p["estado"]
            .fillna("Sin estado")
            .value_counts()
            .reset_index()
        )
        df_estado.columns = ["estado", "total"]

        chart_estado = (
            alt.Chart(df_estado)
            .mark_arc(outerRadius=110, innerRadius=40)
            .encode(
                theta=alt.Theta("total:Q", stack=True),
                color=alt.Color(
                    "estado:N",
                    legend=alt.Legend(title="Estado"),
                ),
                tooltip=["estado:N", "total:Q"],
            )
        )
        st.altair_chart(chart_estado, use_container_width=True)
    else:
        st.info("No hay información de estados para mostrar.")

    # ===========================
    # DISTRIBUCIÓN POR CIUDAD (GRÁFICO CIRCULAR)
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

    if not df_p.empty and "ciudad" in df_p.columns:
        df_ciudad = (
            df_p["ciudad"]
            .fillna("Sin ciudad")
            .value_counts()
            .head(10)
            .reset_index()
        )
        df_ciudad.columns = ["ciudad", "total"]

        chart_ciudad = (
            alt.Chart(df_ciudad)
            .mark_arc(outerRadius=110, innerRadius=40)
            .encode(
                theta=alt.Theta("total:Q", stack=True),
                color=alt.Color(
                    "ciudad:N",
                    legend=alt.Legend(title="Ciudad"),
                ),
                tooltip=["ciudad:N", "total:Q"],
            )
        )
        st.altair_chart(chart_ciudad, use_container_width=True)
    else:
        st.info("No hay información de ciudades para mostrar.")

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

    if not df_p.empty and "estado" in df_p.columns:
        df_ganados = df_p[df_p["estado"] == "Ganado"]

        if df_ganados.empty:
            st.info("No hay proyectos ganados todavía.")
        else:
            columnas = [
                c
                for c in ["nombre_obra", "cliente", "ciudad", "potencial_eur", "fecha_creacion"]
                if c in df_ganados.columns
            ]
            if columnas:
                st.dataframe(
                    df_ganados[columnas],
                    hide_index=True,
                    use_container_width=True,
                )
            else:
                st.info("No hay columnas para mostrar en el detalle de proyectos ganados.")
    else:
        st.info("Los proyectos no tienen campo 'estado', no se puede listar ganados.")
