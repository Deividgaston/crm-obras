import streamlit as st

from crm_utils import get_clientes, add_cliente


def render_clientes():
    st.title("👤 CRM de Clientes")


    with st.expander("➕ Añadir nuevo cliente"):
        with st.form("form_cliente"):
            nombre = st.text_input("Nombre / Persona de contacto")
            empresa = st.text_input("Empresa (promotora, ingeniería, arquitectura, integrador)")
            tipo_cliente = st.selectbox(
                "Tipo de cliente",
                ["Ingeniería", "Promotora", "Arquitectura", "Integrator Partner", "Otro"],
            )
            email = st.text_input("Email")
            telefono = st.text_input("Teléfono")
            ciudad = st.text_input("Ciudad")
            provincia = st.text_input("Provincia")
            notas = st.text_area("Notas (relación, proyectos, info relevante)")


            enviar = st.form_submit_button("Guardar cliente")


        if enviar:
            if not nombre and not empresa:
                st.warning("Pon al menos un nombre o una empresa.")
            else:
                add_cliente({
                    "nombre": nombre or None,
                    "empresa": empresa or None,
                    "tipo_cliente": tipo_cliente,
                    "email": email or None,
                    "telefono": telefono or None,
                    "ciudad": ciudad or None,
                    "provincia": provincia or None,
                    "notas": notas or None,
                })
                st.success("Cliente guardado correctamente.")
                st.rerun()


    st.subheader("📋 Listado de clientes")


    df_clientes = get_clientes()
    if df_clientes.empty:
        st.info("Aún no hay clientes en el CRM.")
        return


    cols_mostrar = ["empresa", "tipo_cliente", "nombre", "email", "telefono", "ciudad", "provincia"]
    cols_mostrar = [c for c in cols_mostrar if c in df_clientes.columns]


    col_f1, col_f2 = st.columns(2)
    with col_f1:
        tipo_sel = st.selectbox(
            "Filtrar por tipo de cliente",
            ["Todos"] + sorted(df_clientes["tipo_cliente"].dropna().unique().tolist()),
        )
    with col_f2:
        ciudad_sel = st.selectbox(
            "Filtrar por ciudad",
            ["Todas"] + sorted(df_clientes["ciudad"].dropna().unique().tolist()),
        )


    df = df_clientes.copy()
    if tipo_sel != "Todos":
        df = df[df["tipo_cliente"] == tipo_sel]
    if ciudad_sel != "Todas":
        df = df[df["ciudad"] == ciudad_sel]


    st.dataframe(df[cols_mostrar], hide_index=True, use_container_width=True)
