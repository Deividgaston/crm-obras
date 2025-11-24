import streamlit as st
import pandas as pd
from crm_utils import get_proyectos, get_clientes


# ============================================================
#  PANEL PRINCIPAL – RESUMEN CRM
# ============================================================
def render_panel():
    st.title("🏗️ Panel General del CRM de Prescripción")
    st.markdown("<br>", unsafe_allow_html=True)

    # -------------------------------
    # LECTURA SEGURA DE FIRESTORE
    # -------------------------------
    with st.spinner("Cargando datos desde la base de datos…"):
        try:
            proyectos = get_proyectos()   # cacheado 60s
            clientes = get_clientes()     # cacheado 60s
        except Exception as e:
            st.error(
                """
                ❌ No se pudieron cargar los datos desde Firestore.

                **Es posible que la cuota gratuita de Firebase se haya agotado hoy**  
                (error típico: 429 QUOTA EXCEEDED).

                Inténtalo más tarde (Firebase resetea las cuotas cada 24h).
                """
            )
            st.code(str(e))
            return

    df_proy = pd.DataFrame(proyectos) if proyectos else pd.DataFrame()
    df_cli = pd.DataFrame(clientes) if clientes else pd.DataFrame()

    # -----------------------------------------
    # MÉTRICAS PRINCIPALES
    # -----------------------------------------
    st.markdown("## 📊 Resumen general")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total de proyectos", len(df_proy))

    with col2:
        st.metric("Total de clientes", len(df_cli))

    with col3:
        if not df_proy.empty and "estado" in df_proy.columns:
            ganados = (df_proy["estado"] == "Ganado").sum()
        else:
            ganados = 0
        st.metric("Proyectos ganados", ganados)

    st.markdown("---")

    # -----------------------------------------
    # PIPELINE POR ESTADO
    # -----------------------------------------
    st.markdown("### 🔁 Pipeline por estado")

    if df_proy.empty or "estado" not in df_proy.columns:
        st.info("No hay proyectos aún o falta el campo 'estado'.")
        return

    estados_orden = [
        "Detectado",
        "Seguimiento",
        "En Prescripción",
        "Oferta Enviada",
        "Negociación",
        "Ganado",
        "Perdido",
        "Paralizado",
    ]

    counts = df_proy["estado"].value_counts()

    cols = st.columns(len(estados_orden))

    for col, est in zip(cols, estados_orden):
        col.metric(est, int(counts.get(est, 0)))

    st.markdown("---")

    # -----------------------------------------
    # ÚLTIMOS PROYECTOS
    # -----------------------------------------
    st.markdown("### 📂 Últimos proyectos creados")

    if "fecha_creacion" in df_proy.columns:
        df_proy["fecha_creacion"] = pd.to_datetime(
            df_proy["fecha_creacion"], errors="coerce"
        )
        df_proy = df_proy.sort_values(
            by="fecha_creacion", ascending=False
        )

    columnas_tabla = [
        col for col in [
            "nombre_obra",
            "cliente",
            "estado",
            "ciudad",
            "provincia",
            "fecha_creacion"
        ]
        if col in df_proy.columns
    ]

    if not columnas_tabla:
        st.info("No hay columnas suficientes para mostrar una tabla.")
        return

    st.dataframe(
        df_proy[columnas_tabla].head(20),
        hide_index=True,
        use_container_width=True,
    )
