import streamlit as st
import pandas as pd

from data_cache import load_proyectos

try:
    from style_injector import inject_apple_style
except Exception:
    def inject_apple_style():
        pass


def render_proyectos():
    inject_apple_style()

    # ====================
    # CABECERA (diseño original restaurado)
    # ====================
    st.markdown(
        """
        <div style="margin-bottom:10px;">
            <h2 style="margin-bottom:0;color:#032D60;">Proyectos</h2>
            <div style="font-size:12px;color:#5A6872;margin-top:-6px;">
                Vista general del pipeline de obras y filtros de búsqueda
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Cargar datos
    df = load_proyectos()

    if df is None or df.empty:
        st.info("Todavía no hay proyectos en la base de datos.")
        return

    # ====================
    # FILTROS
    # ====================
    col1, col2, col3, col4 = st.columns(4)

    ciudades = ["Todas"] + sorted(df["ciudad"].dropna().unique())
    estados = ["Todos"] + sorted(df["estado"].dropna().unique())
    tipos = ["Todos"] + sorted(df["tipo_proyecto"].dropna().unique())
    prioridades = ["Todas"] + sorted(df["prioridad"].dropna().unique())

    with col1:
        sel_ciudad = st.selectbox("Ciudad", ciudades)

    with col2:
        sel_estado = st.selectbox("Estado", estados)

    with col3:
        sel_tipo = st.selectbox("Tipo de proyecto", tipos)

    with col4:
        sel_prio = st.selectbox("Prioridad", prioridades)

    df_filtrado = df.copy()

    if sel_ciudad != "Todas":
        df_filtrado = df_filtrado[df_filtrado["ciudad"] == sel_ciudad]

    if sel_estado != "Todos":
        df_filtrado = df_filtrado[df_filtrado["estado"] == sel_estado]

    if sel_tipo != "Todos":
        df_filtrado = df_filtrado[df_filtrado["tipo_proyecto"] == sel_tipo]

    if sel_prio != "Todas":
        df_filtrado = df_filtrado[df_filtrado["prioridad"] == sel_prio]

    # ====================
    # MÉTRICAS PIPELINE
    # ====================
    colA, colB, colC, colD = st.columns(4)

    estados_contados = df_filtrado["estado"].value_counts()

    colA.metric("Detectado", int(estados_contados.get("Detectado", 0)))
    colB.metric("Seguimiento", int(estados_contados.get("Seguimiento", 0)))
    colC.metric("En Prescripción", int(estados_contados.get("En Prescripción", 0)))
    colD.metric("Oferta Enviada", int(estados_contados.get("Oferta Enviada", 0)))

    colE, colF, colG, colH = st.columns(4)

    colE.metric("Negociación", int(estados_contados.get("Negociación", 0)))
    colF.metric("Ganado", int(estados_contados.get("Ganado", 0)))
    colG.metric("Perdido", int(estados_contados.get("Perdido", 0)))
    colH.metric("Paralizado", int(estados_contados.get("Paralizado", 0)))

    # ====================
    # TABLA
    # ====================
    st.markdown("<br>", unsafe_allow_html=True)

    st.dataframe(
        df_filtrado,
        use_container_width=True,
        hide_index=True,
    )
