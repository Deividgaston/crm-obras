import streamlit as st
import pandas as pd
from crm_utils import get_proyectos, get_clientes

# Intentamos cargar estilo si existe
try:
    from style_injector import inject_apple_style
except:
    def inject_apple_style():
        pass


# ===============================================================
# RENDER PRINCIPAL BUSCADOR
# ===============================================================
def render_buscar():
    inject_apple_style()

    st.title("🔎 Buscar en el CRM")
    st.markdown("<br>", unsafe_allow_html=True)

    # -------------------------------
    # LECTURA SEGURA FIRESTORE
    # -------------------------------
    with st.spinner("Cargando datos…"):
        try:
            proyectos = get_proyectos()   # cacheado 60s
            clientes = get_clientes()     # cacheado 60s
        except Exception as e:
            st.error(
                "❌ Error cargando datos desde Firestore.\n"
                "Es posible que la cuota gratuita esté agotada."
            )
            st.code(str(e))
            return

    df_p = pd.DataFrame(proyectos) if proyectos else pd.DataFrame()
    df_c = pd.DataFrame(clientes) if clientes else pd.DataFrame()

    # -----------------------------------------------------------
    # BÚSQUEDA
    # -----------------------------------------------------------
    st.markdown("### 🧭 Buscador global")

    query = st.text_input("Introduce texto para buscar en obras y clientes:")

    colf1, colf2 = st.columns(2)
    with colf1:
        filtro_estado = st.multiselect(
            "Estado de obra",
            df_p["estado"].dropna().unique().tolist() if not df_p.empty else []
        )
    with colf2:
        filtro_ciudad = st.multiselect(
            "Ciudad",
            df_p["ciudad"].dropna().unique().tolist() if ("ciudad" in df_p.columns) else []
        )

    # Sin búsqueda todavía
    if not query and not filtro_estado and not filtro_ciudad:
        st.info("Utiliza el buscador o los filtros para comenzar.")
        return

    # -----------------------------------------------------------
    # FILTRO PROYECTOS
    # -----------------------------------------------------------
    st.markdown("## 📁 Resultados en proyectos")

    if df_p.empty:
        st.warning("No hay proyectos registrados aún.")
    else:
        dfp = df_p.copy()

        # por texto
        if query:
            q = query.lower()
            dfp = dfp[
                dfp.apply(
                    lambda row: q in str(row).lower(),
                    axis=1
                )
            ]

        # por estado
        if filtro_estado:
            dfp = dfp[dfp["estado"].isin(filtro_estado)]

        # por ciudad
        if filtro_ciudad and "ciudad" in dfp.columns:
            dfp = dfp[dfp["ciudad"].isin(filtro_ciudad)]

        if dfp.empty:
            st.warning("No hay resultados en proyectos.")
        else:
            columnas_proy = [
                col for col in [
                    "nombre_obra",
                    "cliente",
                    "estado",
                    "ciudad",
                    "provincia",
                    "fecha_creacion"
                ]
                if col in dfp.columns
            ]

            st.dataframe(
                dfp[columnas_proy],
                hide_index=True,
                use_container_width=True,
            )

    # -----------------------------------------------------------
    # FILTRO CLIENTES
    # -----------------------------------------------------------
    st.markdown("## 👥 Resultados en clientes")

    if df_c.empty:
        st.info("No hay clientes registrados.")
    else:
        dfc = df_c.copy()

        if query:
            q = query.lower()
            dfc = dfc[
                dfc.apply(
                    lambda row: q in str(row).lower(),
                    axis=1
                )
            ]

        if dfc.empty:
            st.warning("No hay resultados en clientes.")
        else:
            columnas_clientes = [
                col for col in ["nombre", "empresa", "telefono", "email", "fecha_creacion"]
                if col in dfc.columns
            ]

            st.dataframe(
                dfc[columnas_clientes],
                hide_index=True,
                use_container_width=True,
            )
