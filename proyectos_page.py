import streamlit as st
import pandas as pd
from datetime import datetime
from crm_utils import (
    get_proyectos,
    add_proyecto,
    actualizar_proyecto,
    delete_proyecto,
)
from style_injector import inject_apple_style

# -----------------------------------------------------------
# RENDER PRINCIPAL
# -----------------------------------------------------------
def render_proyectos():
    inject_apple_style()

    st.title("📁 Proyectos")
    st.markdown("<br>", unsafe_allow_html=True)

    proyectos = get_proyectos()
    df = pd.DataFrame(proyectos)

    if df.empty:
        st.info("No hay proyectos creados todavía.")
        _boton_crear()
        return

    df = df.sort_values(by="fecha_creacion", ascending=False).reset_index(drop=True)

    _vista_filtros(df)
    _boton_crear()


# -----------------------------------------------------------
# BOTÓN PARA CREAR NUEVO PROYECTO
# -----------------------------------------------------------
def _boton_crear():
    st.markdown("---")
    if st.button("➕ Crear nuevo proyecto", use_container_width=True):
        _open_nuevo_dialog()


# -----------------------------------------------------------
# FILTROS DE LA PÁGINA
# -----------------------------------------------------------
def _vista_filtros(df):
    st.markdown("### 🔍 Filtros")
    estados = df["estado"].dropna().unique().tolist()
    estados.sort()

    col1, col2 = st.columns(2)
    with col1:
        estado_filtrado = st.multiselect("Estado", estados)
    with col2:
        texto = st.text_input("Buscar por nombre de obra:")

    df_filtrado = df.copy()

    if estado_filtrado:
        df_filtrado = df_filtrado[df_filtrado["estado"].isin(estado_filtrado)]

    if texto.strip():
        df_filtrado = df_filtrado[df_filtrado["nombre_obra"].str.contains(texto, case=False)]

    _vista_tabla(df_filtrado)


# -----------------------------------------------------------
# TABLA PRINCIPAL CON CHECKLIST + ICONOS ARRIBA
# -----------------------------------------------------------
def _vista_tabla(df_filtrado: pd.DataFrame):

    st.markdown("#### 🧪 Pipeline (conteo por estado)")
    if not df_filtrado.empty and "estado" in df_filtrado.columns:
        estados = [
            "Detectado", "Seguimiento", "En Prescripción", "Oferta Enviada",
            "Negociación", "Ganado", "Perdido", "Paralizado",
        ]
        counts = df_filtrado["estado"].value_counts()
        cols_pipe = st.columns(len(estados))
        for col, est in zip(cols_pipe, estados):
            col.metric(est, int(counts.get(est, 0)))
    else:
        st.info("No hay información para mostrar en el pipeline.")

    st.markdown("#### 📂 Lista de proyectos")

    if df_filtrado.empty:
        st.warning("No hay proyectos con esos filtros.")
        return

    df_raw = df_filtrado.reset_index(drop=True).copy()
    ids = df_raw["id"].tolist()

    sel_key = "seleccion_proyectos"
    if sel_key not in st.session_state:
        st.session_state[sel_key] = {}

    sel_state = st.session_state[sel_key]

    for pid in ids:
        sel_state.setdefault(pid, False)

    df_ui = df_raw.drop(columns=["id"])
    df_ui["seleccionar"] = [sel_state.get(pid, False) for pid in ids]

    cols = list(df_ui.columns)
    if "nombre_obra" in cols:
        cols.remove("nombre_obra")
        cols.insert(0, "nombre_obra")

    if "seleccionar" in cols:
        cols.remove("seleccionar")
        cols.insert(1, "seleccionar")

    # ------------------- ACCIONES ARRIBA -------------------
    actions = st.container()
    with actions:
        col_txt, col_sel_all, col_edit, col_delete = st.columns([3, 1, 0.7, 0.7])

        with col_txt:
            st.markdown(
                "<span style='font-size:0.8rem; color:#6B7280;'>"
                "Acciones rápidas:"
                "</span>",
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
            if st.button("✏️", help="Editar proyecto seleccionado"):
                seleccionados = [pid for pid in ids if sel_state.get(pid)]
                if not seleccionados:
                    st.warning("Selecciona un proyecto para editar.")
                else:
                    first = seleccionados[0]
                    idx = ids.index(first)
                    datos = df_raw.iloc[idx].to_dict()
                    _open_edit_dialog(datos, first)

        # Borrar
        with col_delete:
            if st.button("🗑️", help="Borrar proyectos seleccionados"):
                seleccionados = [pid for pid in ids if sel_state.get(pid)]
                if not seleccionados:
                    st.warning("Selecciona uno o más proyectos.")
                else:
                    total = 0
                    for pid in seleccionados:
                        try:
                            delete_proyecto(pid)
                            sel_state.pop(pid, None)
                            total += 1
                        except:
                            pass
                    st.success(f"Eliminados {total} proyectos.")
                    st.rerun()

    # ------------------- TABLA -------------------
    edited_df = st.data_editor(
        df_ui[cols],
        column_config={
            "seleccionar": st.column_config.CheckboxColumn(
                "Seleccionar",
                help="Selecciona este proyecto",
                default=False,
            )
        },
        hide_index=True,
        use_container_width=True,
        key="tabla_proyectos",
    )

    if "seleccionar" in edited_df.columns:
        edited_df = edited_df.reset_index(drop=True)
        for idx, pid in enumerate(ids):
            sel_state[pid] = bool(edited_df.loc[idx, "seleccionar"])


# -----------------------------------------------------------
# CREAR NUEVO PROYECTO
# -----------------------------------------------------------
def _open_nuevo_dialog():

    with st.form("nuevo_proyecto_form"):
        st.markdown("### ➕ Nuevo proyecto")

        nombre = st.text_input("Nombre de la obra")
        cliente = st.text_input("Cliente")
        estado = st.selectbox(
            "Estado",
            ["Detectado", "Seguimiento", "En Prescripción", "Oferta Enviada",
             "Negociación", "Ganado", "Perdido", "Paralizado"],
        )
        notas = st.text_area("Notas")
        enviado = st.form_submit_button("Guardar")

        if enviado:
            if not nombre:
                st.warning("El nombre es obligatorio.")
                return

            add_proyecto({
                "nombre_obra": nombre,
                "cliente": cliente,
                "estado": estado,
                "notas": notas,
                "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M"),
            })

            st.success("Proyecto creado correctamente.")
            st.rerun()


# -----------------------------------------------------------
# EDITAR PROYECTO
# -----------------------------------------------------------
def _open_edit_dialog(row_data, proyecto_id):

    with st.form(f"editar_proyecto_{proyecto_id}"):
        st.markdown("### ✏️ Editar proyecto")

        nombre = st.text_input("Nombre de la obra", row_data.get("nombre_obra", ""))
        cliente = st.text_input("Cliente", row_data.get("cliente", ""))
        estado = st.selectbox(
            "Estado",
            ["Detectado", "Seguimiento", "En Prescripción", "Oferta Enviada",
             "Negociación", "Ganado", "Perdido", "Paralizado"],
            index=_index_estado(row_data.get("estado")),
        )
        notas = st.text_area("Notas", row_data.get("notas", ""))

        enviado = st.form_submit_button("Guardar cambios")

        if enviado:
            actualizar_proyecto(proyecto_id, {
                "nombre_obra": nombre,
                "cliente": cliente,
                "estado": estado,
                "notas": notas,
            })
            st.success("Proyecto actualizado.")
            st.rerun()


def _index_estado(valor):
    estados = [
        "Detectado", "Seguimiento", "En Prescripción", "Oferta Enviada",
        "Negociación", "Ganado", "Perdido", "Paralizado",
    ]
    try:
        return estados.index(valor)
    except:
        return 0
