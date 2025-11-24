import streamlit as st
import pandas as pd

from crm_utils import (
    get_clientes,
    add_cliente,
    actualizar_cliente,
    delete_cliente,
)


def render_clientes_page():
    st.markdown(
        """
        <div class="apple-card">
            <div class="section-badge">Relaciones</div>
            <h1 style="margin-top:4px; margin-bottom:4px;">Clientes</h1>
            <p style="color:#9CA3AF; margin-bottom:0; font-size:0.9rem;">
                Gestiona ingenierías, arquitecturas, promotoras e integrators clave
                para la prescripción.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Alta de cliente
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.markdown("#### ➕ Añadir nuevo cliente", unsafe_allow_html=True)

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
                st.rerun()
            except Exception as e:
                st.error(f"No se pudo guardar el cliente: {e}")

    st.markdown("</div>", unsafe_allow_html=True)

    # Listado + posibilidad de borrar
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.markdown("#### 📋 Listado de clientes", unsafe_allow_html=True)

    df_clientes = get_clientes()
    if df_clientes is None or df_clientes.empty:
        st.info("Aún no hay clientes en el CRM.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    df_ui = df_clientes.copy()
    ids = df_ui["id"].tolist()
    df_ui = df_ui.drop(columns=["id"])

    df_ui.insert(0, "borrar", False)

    edited = st.data_editor(
        df_ui,
        column_config={
            "borrar": st.column_config.CheckboxColumn(
                "🗑️", help="Marca para borrar el cliente seleccionado", default=False
            ),
        },
        hide_index=True,
        use_container_width=True,
        key="clientes_editor",
    )

    if st.button("Eliminar clientes marcados"):
        if "borrar" not in edited.columns:
            st.error("No se ha encontrado la columna 'borrar'.")
        else:
            sel = edited["borrar"]
            if not sel.any():
                st.warning("No hay clientes marcados para borrar.")
            else:
                total = 0
                for row_idx, marcado in sel.items():
                    if marcado:
                        try:
                            delete_cliente(ids[row_idx])
                            total += 1
                        except Exception as e:
                            st.error(f"No se pudo borrar un cliente: {e}")
                st.success(f"Clientes eliminados: {total}")
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
