import streamlit as st
import pandas as pd

from crm_utils import get_proyectos, get_clientes

try:
    from style_injector import inject_apple_style
except:
    def inject_apple_style():
        pass


def render_dashboard():
    inject_apple_style()

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
        clientes = get_clientes()
    except Exception as e:
        st.error("No se pudieron cargar los datos del CRM.")
        st.code(str(e))
        return

    df_p = pd.DataFrame(proyectos) if proyectos else pd.DataFrame()
    df_c = pd.DataFrame(clientes) if clientes else pd.DataFrame()

    # ===========================
    # KPIs SUPERIORES
    # ===========================
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Proyectos", len(df_p))

    with col2:
        ganados = df_p[df_p["estado"] == "Ganado"].shape[0] if "estado" in df_p else 0
        st.metric("Proyectos Ganados", ganados)

    with col3:
        perdidos = df_p[df_p["estado"] == "Perdido"].shape[0] if "estado" in df_p else 0
        st.metric("Proyectos Perdidos", perdidos)

    with col4:
        total_pot = float(df_p["potencial_eur"].sum()) if "potencial_eur" in df_p else 0
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

    if not df_p.empty and "estado" in df_p.columns:
        st.dataframe(
            df_p["estado"].value_counts().reset_index().rename(columns={"index": "Estado", "estado": "Total"}),
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

    if not df_p.empty and "ciudad" in df_p.columns:
        tabla_ciudades = df_p["ciudad"].value_counts().reset_index()
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

    if not df_p.empty and "estado" in df_p.columns:
        df_ganados = df_p[df_p["estado"] == "Ganado"]

        if df_ganados.empty:
            st.info("No hay proyectos ganados todavía.")
        else:
            columnas = [c for c in ["nombre_obra", "cliente", "ciudad", "potencial_eur", "fecha_creacion"] if c in df_ganados]

            st.dataframe(
                df_ganados[columnas],
                hide_index=True,
                use_container_width=True,
            )
