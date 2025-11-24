import streamlit as st
import pandas as pd
from crm_utils import get_clientes, add_cliente


def _modo_compacto() -> bool:
    return bool(st.session_state.get("modo_compacto", False))


def render_clientes_page():
    compacto = _modo_compacto()

    st.markdown(
        """
        <div class="crm-card">
            <div class="section-badge">Relaciones</div>
            <h1 style="margin-top:4px; margin-bottom:4px;">Clientes</h1>
            <p class="text-muted" style="margin-bottom:0;">
                Gestiona ingenierías, arquitecturas, promotoras e integrators clave
                para la prescripción.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_clientes = get_clientes()

    total_clientes = 0 if df_clientes is None or df_clientes.empty else len(df_clientes)
    if df_clientes is not None and not df_clientes.empty and "tipo_cliente" in df_clientes.columns:
        resumen_tipo = (
            df_clientes["tipo_cliente"]
            .value_counts()
            .rename_axis("tipo")
            .reset_index(name="n")
        )
    else:
        resumen_tipo = None

    # Métricas pequeñas
    with st.container():
        st.markdown('<div class="crm-metric-row">', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="crm-metric-card">
                <div class="crm-metric-title">Clientes totales</div>
                <div class="crm-metric-value">{total_clientes}</div>
                <div class="crm-metric-sub">Contactos en el CRM</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if resumen_tipo is not None and not resumen_tipo.empty:
            top_tipo = resumen_tipo.iloc[0]
            st.markdown(
                f"""
                <div class="crm-metric-card">
                    <div class="crm-metric-title">Tipo dominante</div>
                    <div class="crm-metric-value" style="font-size:1.1rem;">{top_tipo['tipo']}</div>
                    <div class="crm-metric-sub">{int(top_tipo['n'])} contactos</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    tab_alta, tab_lista = st.tabs(
        ["➕ Alta cliente", "📋 Listado"]
    )

    # --------- Alta de cliente ----------
    with tab_alta:
        st.markdown('<div class="crm-card-light">', unsafe_allow_html=True)
        st.markdown("#### Añadir nuevo cliente", unsafe_allow_html=True)

        with st.form("form_cliente"):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre / persona de contacto")
                empresa = st.text_input("Empresa")
                tipo_cliente = st.selectbox(
                    "Tipo de cliente",
                    ["Ingeniería", "Promotora", "Arquitectura", "Integrator Partner", "Otro"],
                )
            with col2:
                email = st.text_input("Email")
                telefono = st.text_input("Teléfono")
                ciudad = st.text_input("Ciudad")
                provincia = st.text_input("Provincia")

            notas = st.text_area("Notas (proyectos, relación, info importante)")

            enviar = st.form_submit_button("Guardar cliente")

        if enviar:
            if not nombre and not empresa:
                st.warning("Pon al menos un nombre o una empresa.")
            else:
                try:
                    add_cliente(
                        {
                            "nombre": nombre,
                            "empresa": empresa,
                            "tipo_cliente": tipo_cliente,
                            "email": email,
                            "telefono": telefono,
                            "ciudad": ciudad,
                            "provincia": provincia,
                            "notas": notas,
                        }
                    )
                    st.success("Cliente guardado correctamente.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"No se pudo guardar el cliente: {e}")

        st.markdown("</div>", unsafe_allow_html=True)

    # --------- Listado ----------
    with tab_lista:
        st.markdown('<div class="crm-card-light">', unsafe_allow_html=True)
        st.markdown("#### Listado de clientes", unsafe_allow_html=True)

        if df_clientes is None or df_clientes.empty:
            st.info("Aún no hay clientes en el CRM.")
        else:
            columnas_escritorio = ["nombre", "empresa", "tipo_cliente", "email", "telefono", "ciudad", "provincia"]
            columnas_movil = ["empresa", "tipo_cliente", "ciudad", "telefono"]
            cols = columnas_movil if compacto else columnas_escritorio
            cols = [c for c in cols if c in df_clientes.columns]

            st.dataframe(
                df_clientes[cols],
                hide_index=True,
                use_container_width=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)
