import streamlit as st
import pandas as pd
from datetime import datetime
from crm_utils import (
    get_clientes,
    add_cliente,
    actualizar_cliente,
    delete_cliente,
)

# Intentamos cargar estilo si existe
try:
    from style_injector import inject_apple_style
except:
    def inject_apple_style():
        pass


# ===============================================================
# RENDER PRINCIPAL
# ===============================================================
def render_clientes():
    inject_apple_style()

    st.title("👥 Clientes")
    st.markdown("<br>", unsafe_allow_html=True)

    # Lectura protegida de Firestore
    with st.spinner("Cargando clientes…"):
        try:
            clientes = get_clientes()  # cacheado
        except Exception as e:
            st.error("❌ Error cargando clientes (posible cuota Firebase agotada).")
            st.code(str(e))
            return

    df = pd.DataFrame(clientes)

    if df.empty:
        st.info("No hay clientes creados todavía.")
        _boton_crear_cliente()
        return

    df = df.sort_values(by="fecha_creacion", ascending=False).reset_index(drop=True)

    _vista_tabla(df)
    _boton_crear_cliente()


# ===============================================================
# BOTÓN CREAR NUEVO CLIENTE
# ===============================================================
def _boton_crear_cliente():
    st.markdown("---")
    if st.button("➕ Crear nuevo cliente", use_container_width=True):
        _open_nuevo_cliente()


# ===============================================================
# TABLA PRINCIPAL
# ===============================================================
def _vista_tabla(df):

    st.markdown("### 📋 Lista de clientes")

    if df.empty:
        st.warning("No hay clientes registrados.")
        return

    # Añadir checkbox de selección
    ids = df["id"].tolist()

    sel_key = "seleccion_clientes"
    if sel_key not in st.session_state:
        st.session_state[sel_key] = {}

    sel_state = st.session_state[sel_key]
    for pid in ids:
        sel_state.setdefault(pid, False)

    df_ui = df.drop(columns=["id"]).copy()
    df_ui["seleccionar"] = [sel_state.get(pid, False) for pid in ids]

    cols = list(df_ui.columns)
    cols.remove("seleccionar")
    cols.insert(0, "seleccionar")

    # Placeholder de botones
    actions_placeholder = st.empty()

    # Render de tabla
    edited_df = st.data_editor(
        df_ui[cols],
        column_config={"seleccionar": st.column_config.CheckboxColumn("Sel")},
        hide_index=True,
        use_container_width=True,
        key="tabla_clientes_editor",
    )

    edited_df = edited_df.reset_index(drop=True)

    # Actualizar selección
    for idx, pid in enumerate(ids):
        sel_state[pid] = bool(edited_df.loc[idx, "seleccionar"])

    # Botones arriba
    with actions_placeholder.container():
        col_txt, col_sel_all, col_edit, col_delete = st.columns([3, 1, 0.7, 0.7])

        with col_txt:
            st.markdown(
                "<span style='font-size:0.8rem; color:#6B7280;'>Acciones:</span>",
                unsafe_allow_html=True,
            )

        # Marcar todos
        with col_sel_all:
            if st.button("☑️", help="Seleccionar todos"):
                for pid in ids:
                    sel_state[pid] = True

        # Editar
        with col_edit:
            if st.button("✏️", help="Editar el primer cliente seleccionado"):
                marcados = [i for i, v in edited_df["seleccionar"].items() if v]
                if not marcados:
                    st.warning("Selecciona un cliente.")
                else:
                    idx = marcados[0]
                    cliente_id = ids[idx]
                    datos = df.iloc[idx].to_dict()
                    _open_editar_cliente(datos, cliente_id)

        # Borrar
        with col_delete:
            if st.button("🗑️", help="Borrar clientes seleccionados"):
                marcados = [i for i, v in edited_df["seleccionar"].items() if v]

                if not marcados:
                    st.warning("Selecciona uno o más clientes.")
                else:
                    eliminados = 0
                    for i in marcados:
                        try:
                            delete_cliente(ids[i])
                            eliminados += 1
                        except:
                            pass

                    st.success(f"Eliminados {eliminados} clientes.")
                    st.cache_data.clear()
                    st.experimental_rerun()


# ===============================================================
# CREAR CLIENTE
# ===============================================================
def _open_nuevo_cliente():

    with st.form("nuevo_cliente_form"):
        st.markdown("### ➕ Nuevo cliente")

        nombre = st.text_input("Nombre del cliente")
        empresa = st.text_input("Empresa / Promotora")
        telefono = st.text_input("Teléfono")
        email = st.text_input("Email")
        notas = st.text_area("Notas")

        enviado = st.form_submit_button("Guardar")

        if enviado:
            if not nombre:
                st.warning("El nombre es obligatorio.")
                return

            add_cliente({
                "nombre": nombre,
                "empresa": empresa,
                "telefono": telefono,
                "email": email,
                "notas": notas,
                "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M"),
            })

            st.success("Cliente creado correctamente.")
            st.experimental_rerun()


# ===============================================================
# EDITAR CLIENTE
# ===============================================================
def _open_editar_cliente(row_data, cliente_id):

    with st.form(f"editar_cliente_{cliente_id}"):
        st.markdown("### ✏️ Editar cliente")

        nombre = st.text_input("Nombre", row_data.get("nombre"))
        empresa = st.text_input("Empresa", row_data.get("empresa"))
        telefono = st.text_input("Teléfono", row_data.get("telefono"))
        email = st.text_input("Email", row_data.get("email"))
        notas = st.text_area("Notas", row_data.get("notas"))

        enviado = st.form_submit_button("Guardar cambios")

        if enviado:
            actualizar_cliente(cliente_id, {
                "nombre": nombre,
                "empresa": empresa,
                "telefono": telefono,
                "email": email,
                "notas": notas,
            })

            st.success("Cliente actualizado.")
            st.experimental_rerun()
