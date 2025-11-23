import streamlit as st
from crm_utils import get_clientes, add_cliente


def render_clientes():
    st.title("👤 CRM de Clientes (ingenierías, promotoras, arquitectos, integrators)")

    # Alta de cliente
    with st.expander("➕ Añadir nuevo cliente"):
        with st.form("form_cliente"):
            nombre = st.text_input("Nombre / Persona de contacto")
            empresa = st.text_input("Empresa")
            tipo_cliente = st.selectbox(
                "Tipo de cliente",
                ["Ingeniería", "Promotora", "Arquitectura", "Integrator Partner", "Otro"]
            )
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
                add_cliente({
                    "nombre": nombre,
                    "empresa": empresa,
                    "tipo_cliente": tipo_cliente,
                    "email": email,
                    "telefono": telefono,
                    "ciudad": ciudad,
                    "provincia": provincia,
                    "notas": notas,
                })
                st.success("Cliente guardado correctamente.")
                st.rerun()

    st.subheader("📋 Listado de clientes")

    df_clientes = get_clientes()
    if df_clientes.empty:
        st.info("Aún no hay clientes en el CRM.")
    else:
        cols_mostrar = ["nombre", "empresa", "tipo_cliente", "email", "telefono", "ciudad", "provincia"]
        cols_mostrar = [c for c in cols_mostrar if c in df_clientes.columns]
        st.dataframe(df_clientes[cols_mostrar], hide_index=True, use_container_width=True)
