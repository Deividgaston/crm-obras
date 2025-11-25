import streamlit as st
import pandas as pd
from datetime import datetime

from crm_utils import (
    get_clientes,
    add_cliente,
    actualizar_cliente,
    delete_cliente,
)

try:
    from style_injector import inject_apple_style
except Exception:
    def inject_apple_style():
        pass


# ===============================================================
# RENDER PRINCIPAL
# ===============================================================
def render_clientes():
    inject_apple_style()

    # Cabecera Apple
    st.markdown(
        """
        <div class="apple-card">
            <div class="badge">Base de datos</div>
            <h1 style="margin-top:4px; margin-bottom:4px;">👥 Clientes</h1>
            <p style="font-size:0.9rem; color:#9ca3af; margin-bottom:0;">
                Lista completa de contactos clave: arquitectos, ingenierías, promotoras,
                integradores y partners. Desde aquí puedes gestionarlos todos.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Cargar datos (una sola lectura cacheada en crm_utils)
    with st.spinner("Cargando clientes…"):
        try:
            clientes = get_clientes()
        except Exception as e:
            st.error("❌ Error obteniendo clientes desde Firestore.")
            st.code(str(e))
            return

    df = pd.DataFrame(clientes)

    if df.empty:
        st.info("Todavía no hay clientes creados.")
        _boton_crear()
        return

    df = df.sort_values(by="fecha_creacion", ascending=False).reset_index(drop=True)

    _vista_filtros(df)
    _boton_crear()


# ===============================================================
# BOTÓN CREAR NUEVO CLIENTE
# ===============================================================
def _boton_crear():
    st.markdown("---")
    if st.button("➕ Añadir nuevo cliente", use_container_width=True):
        _open_nuevo_dialog()


# ===============================================================
# FILTROS
# ===============================================================
def _vista_filtros(df):

    st.markdown(
        """
        <div class="apple-card-light">
            <div class="badge">Filtros</div>
            <h3 style="margin-top:8px; margin-bottom:4px;">🔍 Buscar cliente</h3>
            <p class="small-caption">
                Filtra por empresa, persona, teléfono, email o ciudad.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    texto = st.text_input("Buscar… (nombre, empresa, ciudad, email, teléfono)")

    df_filtrado = df.copy()

    if texto.strip():
        t = texto.lower()
        columnas = ["nombre", "empresa", "ciudad", "telefono", "email"]
        mask = pd.Series(False, index=df_filtrado.index)
        for col in columnas:
            if col in df_filtrado.columns:
                mask = mask | df_filtrado[col].astype(str).str.lower().str.contains(t)
        df_filtrado = df_filtrado[mask]

    _vista_tabla(df_filtrado)


# ===============================================================
# TABLA PRINCIPAL + ACCIONES
# ===============================================================
def _vista_tabla(df_filtrado):

    st.markdown(
        """
        <div class="apple-card-light">
            <div class="badge">Listado</div>
            <h3 style="margin-top:8px; margin-bottom:4px;">📋 Clientes encontrados</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df_filtrado.empty:
        st.warning("No hay resultados con los filtros aplicados.")
        return

    df_raw = df_filtrado.reset_index(drop=True).copy()

    # Extraemos IDs
    ids = df_raw.get("id", pd.Series(range(len(df_raw)))).tolist()

    # Selección persistente
    sel_key = "seleccion_clientes"
    if sel_key not in st.session_state:
        st.session_state[sel_key] = {}

    sel_state = st.session_state[sel_key]
    for pid in ids:
        sel_state.setdefault(pid, False)

    # Construir tabla
    df_ui = df_raw.copy()

    df_ui["seleccionar"] = [sel_state.get(pid, False) for pid in ids]
    df_visual = df_ui.drop(columns=["id"], errors="ignore")

    # Ordenar columnas
    cols = list(df_visual.columns)
    if "nombre" in cols:
        cols.remove("nombre")
        cols.insert(0, "nombre")
    if "seleccionar" in cols:
        cols.remove("seleccionar")
        cols.insert(1, "seleccionar")

    actions_placeholder = st.empty()

    tabla_editada = st.data_editor(
        df_visual[cols],
        column_config={
            "seleccionar": st.column_config.CheckboxColumn("Sel"),
        },
        hide_index=True,
        use_container_width=True,
        key="tabla_clientes_editor",
    )

    tabla_editada = tabla_editada.reset_index(drop=True)

    # Actualizar session_state
    if "seleccionar" in tabla_editada.columns:
        for idx, pid in enumerate(ids):
            try:
                sel_state[pid] = bool(tabla_editada.loc[idx, "seleccionar"])
            except Exception:
                sel_state[pid] = False

    # ---- Barra de acciones ----
    with actions_placeholder.container():
        col_txt, col_sel_all, col_edit, col_delete = st.columns([3, 1, 0.7, 0.7])

        with col_txt:
            st.markdown(
                "<span style='font-size:0.8rem; color:#6B7280;'>Acciones rápidas:</span>",
                unsafe_allow_html=True,
            )

        # Seleccionar todos
        with col_sel_all:
            if st.button("☑️", help="Seleccionar todos"):
                for pid in ids:
                    sel_state[pid] = True
                st.rerun()

        # Editar
        with col_edit:
            if st.button("✏️", help="Editar cliente"):
                marcados = [
                    i for i, v in tabla_editada["seleccionar"].items() if v
                ]
                if not marcados:
                    st.warning("Selecciona un cliente.")
                else:
                    idx = marcados[0]
                    _open_edit_dialog(df_raw.iloc[idx].to_dict(), ids[idx])

        # Borrar
        with col_delete:
            if st.button("🗑️", help="Borrar seleccionados"):
                marcados = [
                    i for i, v in tabla_editada["seleccionar"].items() if v
                ]
                if not marcados:
                    st.warning("No hay clientes seleccionados.")
                else:
                    eliminados = 0
                    for i in marcados:
                        try:
                            delete_cliente(ids[i])
                            eliminados += 1
                        except Exception:
                            pass
                    st.success(f"Eliminados {eliminados} clientes.")
                    st.rerun()


# ===============================================================
# CREAR CLIENTE
# ===============================================================
def _open_nuevo_dialog():
    with st.form("nuevo_cliente_form"):
        st.markdown("### ➕ Nuevo cliente")

        nombre = st.text_input("Nombre completo")
        empresa = st.text_input("Empresa")
        ciudad = st.text_input("Ciudad")
        telefono = st.text_input("Teléfono")
        email = st.text_input("Email")
        notas = st.text_area("Notas", height=80)

        enviado = st.form_submit_button("Guardar")

        if enviado:
            if not nombre:
                st.warning("El nombre es obligatorio.")
                return

            data = {
                "nombre": nombre,
                "empresa": empresa,
                "ciudad": ciudad,
                "telefono": telefono,
                "email": email,
                "notas": notas,
                "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }

            add_cliente(data)
            st.success("Cliente creado correctamente.")
            st.rerun()


# ===============================================================
# EDITAR CLIENTE
# ===============================================================
def _open_edit_dialog(row_data, cliente_id):
    with st.form(f"editar_cliente_{cliente_id}"):
        st.markdown("### ✏️ Editar cliente")

        nombre = st.text_input("Nombre completo", row_data.get("nombre", ""))
        empresa = st.text_input("Empresa", row_data.get("empresa", ""))
        ciudad = st.text_input("Ciudad", row_data.get("ciudad", ""))
        telefono = st.text_input("Teléfono", row_data.get("telefono", ""))
        email = st.text_input("Email", row_data.get("email", ""))
        notas = st.text_area("Notas", row_data.get("notas", ""), height=80)

        enviado = st.form_submit_button("Guardar cambios")

        if enviado:
            data = {
                "nombre": nombre,
                "empresa": empresa,
                "ciudad": ciudad,
                "telefono": telefono,
                "email": email,
                "notas": notas,
            }

            actualizar_cliente(cliente_id, data)
            st.success("Cliente actualizado.")
            st.rerun()
