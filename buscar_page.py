import streamlit as st
import pandas as pd

from crm_utils import get_proyectos, get_clientes

try:
    from style_injector import inject_apple_style
except Exception:
    def inject_apple_style():
        pass


# ===============================================================
# RENDER PRINCIPAL BUSCADOR
# ===============================================================
def render_buscar():
    inject_apple_style()

    # Cabecera Apple
    st.markdown(
        """
        <div class="apple-card">
            <div class="badge">Buscador global</div>
            <h1 style="margin-top:4px; margin-bottom:4px;">🔎 Buscar en el CRM</h1>
            <p style="font-size:0.9rem; color:#9ca3af; margin-bottom:0;">
                Encuentra proyectos y clientes combinando texto libre, estado y ciudad.
                Ideal para localizar rápido una obra, promotora o contacto clave.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ================= CARGA DE DATOS (UNA VEZ) =================
    with st.spinner("Cargando datos de proyectos y clientes…"):
        try:
            proyectos = get_proyectos()
            clientes = get_clientes()
        except Exception as e:
            st.error("❌ Error cargando datos desde Firestore.")
            st.code(str(e))
            return

    df_p = pd.DataFrame(proyectos) if proyectos else pd.DataFrame()
    df_c = pd.DataFrame(clientes) if clientes else pd.DataFrame()

    # ================= FILTROS BÁSICOS =================
    st.markdown(
        """
        <div class="apple-card-light">
            <div class="badge">Filtros</div>
            <h3 style="margin-top:8px; margin-bottom:4px;">🎛️ Configurar búsqueda</h3>
            <p class="small-caption">
                Escribe texto libre y, si quieres, filtra por estado y ciudad para refinar la búsqueda.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        query = st.text_input(
            "Texto (obra, cliente, promotora, ciudad…)",
            placeholder="Ej: Fuengirola, Prime Invest, Marbella…",
        )

    estados_options = (
        sorted(df_p["estado"].dropna().unique().tolist())
        if not df_p.empty and "estado" in df_p.columns
        else []
    )
    ciudades_options = (
        sorted(df_p["ciudad"].dropna().unique().tolist())
        if not df_p.empty and "ciudad" in df_p.columns
        else []
    )

    with col2:
        estados_sel = st.multiselect("Estado de obra", options=estados_options, default=estados_options)
    with col3:
        ciudades_sel = st.multiselect("Ciudad", options=ciudades_options)

    # Si no hay nada, mostramos info y salimos
    if not query and not estados_sel and not ciudades_sel:
        st.info("Empieza escribiendo algo en el buscador o aplica algún filtro.")
        return

    # ================= BÚSQUEDA EN PROYECTOS =================
    st.markdown(
        """
        <div class="apple-card-light">
            <div class="badge">Resultados</div>
            <h3 style="margin-top:8px; margin-bottom:4px;">📁 Resultados en proyectos</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df_p.empty:
        st.warning("No hay proyectos registrados todavía.")
    else:
        dfp = df_p.copy()

        # Texto libre
        if query:
            q = query.lower()
            columnas_busq = [
                col
                for col in ["nombre_obra", "cliente", "cliente_principal", "promotora", "ciudad", "provincia", "notas"]
                if col in dfp.columns
            ]
            if columnas_busq:
                mask = pd.Series(False, index=dfp.index)
                for col in columnas_busq:
                    mask = mask | dfp[col].astype(str).str.lower().str.contains(q)
                dfp = dfp[mask]

        # Estado
        if estados_sel and "estado" in dfp.columns:
            dfp = dfp[dfp["estado"].isin(estados_sel)]

        # Ciudad
        if ciudades_sel and "ciudad" in dfp.columns:
            dfp = dfp[dfp["ciudad"].isin(ciudades_sel)]

        if dfp.empty:
            st.warning("No se han encontrado proyectos con estos criterios.")
        else:
            # Orden por fecha_creacion si existe
            if "fecha_creacion" in dfp.columns:
                dfp["fecha_creacion"] = pd.to_datetime(
                    dfp["fecha_creacion"], errors="coerce"
                )
                dfp = dfp.sort_values(by="fecha_creacion", ascending=False)

            columnas_proy = [
                col
                for col in [
                    "nombre_obra",
                    "cliente",
                    "cliente_principal",
                    "promotora",
                    "estado",
                    "ciudad",
                    "provincia",
                    "potencial_eur",
                    "fecha_creacion",
                ]
                if col in dfp.columns
            ]

            st.markdown(
                f"<p class='small-caption'>Se han encontrado <strong>{len(dfp)}</strong> proyectos.</p>",
                unsafe_allow_html=True,
            )

            st.dataframe(
                dfp[columnas_proy],
                hide_index=True,
                use_container_width=True,
            )

    # ================= BÚSQUEDA EN CLIENTES =================
    st.markdown(
        """
        <div class="apple-card-light" style="margin-top:1.5rem;">
            <div class="badge">Resultados</div>
            <h3 style="margin-top:8px; margin-bottom:4px;">👥 Resultados en clientes</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df_c.empty:
        st.info("No hay clientes registrados.")
    else:
        dfc = df_c.copy()

        if query:
            q = query.lower()
            columnas_busq_c = [
                col
                for col in ["nombre", "empresa", "ciudad", "telefono", "email", "notas"]
                if col in dfc.columns
            ]
            if columnas_busq_c:
                mask_c = pd.Series(False, index=dfc.index)
                for col in columnas_busq_c:
                    mask_c = mask_c | dfc[col].astype(str).str.lower().str.contains(q)
                dfc = dfc[mask_c]

        if dfc.empty:
            st.warning("No se han encontrado clientes con estos criterios.")
        else:
            columnas_clientes = [
                col
                for col in ["nombre", "empresa", "ciudad", "telefono", "email", "fecha_creacion"]
                if col in dfc.columns
            ]

            st.markdown(
                f"<p class='small-caption'>Se han encontrado <strong>{len(dfc)}</strong> clientes.</p>",
                unsafe_allow_html=True,
            )

            st.dataframe(
                dfc[columnas_clientes],
                hide_index=True,
                use_container_width=True,
            )
