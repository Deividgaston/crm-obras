import streamlit as st
import pandas as pd
from crm_utils import get_proyectos, get_clientes

try:
    from style_injector import inject_apple_style
except Exception:
    def inject_apple_style():
        pass


# ============================
# HELPERS
# ============================

@st.cache_data(show_spinner=False)
def load_proyectos():
    return get_proyectos()


@st.cache_data(show_spinner=False)
def load_clientes():
    return get_clientes()


def _to_df(data):
    if data is None:
        return pd.DataFrame()
    if isinstance(data, pd.DataFrame):
        return data.copy()
    if isinstance(data, list):
        return pd.DataFrame(data)
    return pd.DataFrame(data)


# ============================
# RENDER PRINCIPAL
# ============================

def render_buscar():
    inject_apple_style()

    # -------------------------------------
    # CABECERA SALESFORCE
    # -------------------------------------
    st.markdown(
        """
        <div class="apple-card">
            <div class="badge">Buscador</div>
            <h3 style="margin-top:2px; margin-bottom:2px;">Buscador avanzado</h3>
            <p>Encuentra proyectos o clientes rápidamente usando filtros combinados.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -------------------------------------
    # CARGA DE DATOS
    # -------------------------------------
    df_proy = _to_df(load_proyectos())
    df_cli = _to_df(load_clientes())

    if df_proy.empty and df_cli.empty:
        st.info("No hay datos disponibles para buscar.")
        return

    # -------------------------------------
    # BÚSQUEDA
    # -------------------------------------

    col_query, col_tipo = st.columns([4, 2])
    with col_query:
        query = st.text_input(
            "Buscar",
            placeholder="Ej: Marbella, HCP, BTR, Promotora X, Residencial lujo…",
        )

    with col_tipo:
        tipo_busqueda = st.selectbox(
            "Buscar en",
            ["Proyectos", "Clientes", "Todo"],
        )

    st.markdown("---")

    # -------------------------------------
    # RESULTADOS
    # -------------------------------------
    if not query:
        st.caption("Escribe algo para buscar…")
        return

    query_low = query.lower().strip()

    def match(df: pd.DataFrame):
        df2 = df.copy()
        columns = df2.columns
        mask = pd.Series(False, index=df2.index)

        for c in columns:
            mask |= df2[c].astype(str).str.lower().str.contains(query_low, na=False)

        return df2[mask]

    # ========== BUSCAR EN PROYECTOS ==========
    if tipo_busqueda in ["Proyectos", "Todo"] and not df_proy.empty:
        st.markdown("#### 🔵 Resultados en proyectos")

        res_proy = match(df_proy)

        if res_proy.empty:
            st.info("Sin coincidencias en proyectos.")
        else:
            columnas_preferidas = [
                "nombre_obra",
                "cliente_principal",
                "ciudad",
                "provincia",
                "tipo_proyecto",
                "estado",
                "prioridad",
                "potencial_eur",
                "fecha_seguimiento",
            ]

            cols_finales = [c for c in columnas_preferidas if c in res_proy.columns]

            st.dataframe(
                res_proy[cols_finales],
                use_container_width=True,
                hide_index=True,
            )

    st.markdown("---")

    # ========== BUSCAR EN CLIENTES ==========
    if tipo_busqueda in ["Clientes", "Todo"] and not df_cli.empty:
        st.markdown("#### 🔵 Resultados en clientes")

        res_cli = match(df_cli)

        if res_cli.empty:
            st.info("Sin coincidencias en clientes.")
        else:
            columnas_preferidas = [
                "empresa",
                "persona_contacto",
                "telefono",
                "email",
                "ciudad",
                "sector",
            ]
            cols2 = [c for c in columnas_preferidas if c in res_cli.columns]

            st.dataframe(
                res_cli[cols2],
                use_container_width=True,
                hide_index=True,
            )

    # -------------------------------------
    # SIN RESULTADOS EN NINGÚN SITIO
    # -------------------------------------
    if query and tipo_busqueda == "Todo":
        if (
            (not df_cli.empty and res_cli.empty)
            and (not df_proy.empty and res_proy.empty)
        ):
            st.error("No se encontraron coincidencias.")

