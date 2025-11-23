import streamlit as st
import pandas as pd
from crm_utils import get_clientes, add_cliente


# =========================================================
# PÁGINA PRINCIPAL DE CLIENTES
# =========================================================

def render_clientes():
    # === CABECERA APPLE BLUE COMPACTA ===
    st.markdown(
        """
        <div class="apple-card">
            <div class="section-badge">Relaciones B2B</div>
            <h3 style="margin-top: 6px; font-size:1.25rem;">Clientes · Arquitecturas · Ingenierías · Promotoras</h3>
            <p style="color:#9FB3D1; margin-bottom: 0; font-size:0.85rem;">
                Gestiona todos los agentes clave implicados en la prescripción:
                arquitectos, ingenieros, integradores, promotores y fondos.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_lista, tab_alta = st.tabs(
        ["📋 Listado de clientes", "➕ Añadir cliente"]
    )

    # =========================================================
    # TAB 1 — LISTADO COMPLETO
    # =========================================================
    with tab_lista:
        st.markdown(
            """
            <div class="apple-card-light">
                <div class="section-badge">Directorio</div>
                <h4 style="margin-top:8px; margin-bottom:4px; font-size:1.0rem;">📋 Listado de clientes</h4>
                <p style="color:#9CA3AF; margin-top:0; font-size:0.8rem;">
                    Todas las empresas y contactos del ecosistema profesional. 
                    Úsalos para asignarlos a proyectos y enriquecer la base de datos.
                </p>
            """,
            unsafe_allow_html=True,
        )

        df_clientes = get_clientes()

        if df_clientes is None or df_clientes.empty:
            st.info("Aún no hay clientes en el CRM.")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            cols_mostrar = [
                "empresa",
                "nombre",
                "tipo_cliente",
                "email",
                "telefono",
                "ciudad",
                "provincia",
            ]
            cols_mostrar = [c for c in cols_mostrar if c in df_clientes.columns]

            st.dataframe(
                df_clientes[cols_mostrar],
                hide_index=True,
                use_container_width=True,
            )

            st.markdown("</div>", unsafe_allow_html=True)

    # =========================================================
    # TAB 2 — AÑADIR CLIENTE
    # =========================================================
    with tab_alta:
        st.markdown(
            """
            <div class="apple-card-light">
                <div class="section-badge">Nuevo registro</div>
                <h4 style="margin-top:8px; margin-bottom:4px; font-size:1.0rem;">➕ Alta de cliente</h4>
                <p style="color:#9CA3AF; margin-top:0; font-size:0.8rem;">
                    Crea un nuevo agente clave (ingeniería, arquitectura, promotora, fondo o integrator).
                    El CRM usará esta información para vincularlo a proyectos y enriquecer referencias.
                </p>
            """,
            unsafe_allow_html=True,
        )

        with st.form("form_cliente"):
            col1, col2 = st.columns(2)

            with col1:
                nombre = st.text_input("Nombre / Persona de contacto")
                empresa = st.text_input("Empresa")
                tipo_cliente = st.selectbox(
                    "Tipo de cliente",
                    ["Ingeniería", "Promotora", "Arquitectura", "Integrator Partner", "Fondo", "Otro"],
                )
                ciudad = st.text_input("Ciudad")
                provincia = st.text_input("Provincia")

            with col2:
                email = st.text_input("Email")
                telefono = st.text_input("Teléfono")
                notas = st.text_area(
                    "Notas (relación, proyectos en los que participa, comentarios)",
                    height=110
                )

            guardar = st.form_submit_button("💾 Guardar cliente")

        if guardar:
            if not empresa and not nombre:
                st.warning("Debes introducir como mínimo un nombre o una empresa.")
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
