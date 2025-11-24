def _vista_tabla(df_filtrado: pd.DataFrame):
    # --------- PIPELINE POR ESTADO ----------
    st.markdown("#### 🧪 Pipeline (conteo por estado)")
    if not df_filtrado.empty and "estado" in df_filtrado.columns:
        estados = [
            "Detectado",
            "Seguimiento",
            "En Prescripción",
            "Oferta Enviada",
            "Negociación",
            "Ganado",
            "Perdido",
            "Paralizado",
        ]
        counts = df_filtrado["estado"].value_counts()
        cols_pipe = st.columns(len(estados))
        for col, est in zip(cols_pipe, estados):
            col.metric(est, int(counts.get(est, 0)))
    else:
        st.info("No hay información de estados con los filtros aplicados.")

    # --------- TABLA PRINCIPAL ---------
    st.markdown("#### 📂 Lista de proyectos filtrados")

    if df_filtrado.empty:
        st.warning("No hay proyectos que cumplan los filtros seleccionados.")
        return

    # df_raw mantiene todos los campos, incluido id, para poder editar
    df_raw = df_filtrado.reset_index(drop=True).copy()
    ids = df_raw["id"].tolist()

    # Estado de selección persistente por proyecto (en sesión)
    sel_key = "seleccion_proyectos"
    if sel_key not in st.session_state:
        st.session_state[sel_key] = {}
    sel_state = st.session_state[sel_key]

    # Inicializamos en False los que no existan aún
    for pid in ids:
        sel_state.setdefault(pid, False)

    # df_ui es lo que mostramos en la tabla (sin id)
    df_ui = df_raw.drop(columns=["id"])

    # columna seleccionar con el estado actual
    df_ui["seleccionar"] = [sel_state.get(pid, False) for pid in ids]

    # Reordenamos columnas: primero nombre_obra, luego seleccionar y después resto
    cols = list(df_ui.columns)
    if "nombre_obra" in cols:
        cols.remove("nombre_obra")
        cols.insert(0, "nombre_obra")
    if "seleccionar" in cols:
        cols.remove("seleccionar")
        insert_pos = 1 if "nombre_obra" in cols else 0
        cols.insert(insert_pos, "seleccionar")

    st.markdown(
        "<p style='font-size:0.82rem; color:#9CA3AF;'>"
        "Selecciona una o varias obras y usa los iconos superiores para editar o borrar."
        "</p>",
        unsafe_allow_html=True,
    )

    # Contenedor para los iconos de acciones (se mostrará visualmente encima de la tabla)
    actions_container = st.container()

    # Tabla editable
    edited_df = st.data_editor(
        df_ui[cols],
        column_config={
            "seleccionar": st.column_config.CheckboxColumn(
                "Seleccionar",
                help="Selecciona una obra para acciones rápidas",
                default=False,
            ),
        },
        hide_index=True,
        use_container_width=True,
        key="tabla_proyectos_editor",
    )

    # Actualizamos el estado de selección con lo que haya marcado el usuario
    if "seleccionar" in edited_df.columns:
        edited_df = edited_df.reset_index(drop=True)
        for idx, pid in enumerate(ids):
            try:
                sel_state[pid] = bool(edited_df.loc[idx, "seleccionar"])
            except Exception:
                sel_state[pid] = False

    # Ahora pintamos los iconos de acción en el contenedor (queda por encima de la tabla)
    with actions_container:
        col_txt, col_sel_all, col_edit, col_delete = st.columns([3, 1, 0.7, 0.7])

        with col_txt:
            st.markdown(
                "<span style='font-size:0.8rem; color:#6B7280;'>"
                "Acciones rápidas sobre la selección:"
                "</span>",
                unsafe_allow_html=True,
            )

        # Botón "Seleccionar todos"
        with col_sel_all:
            if st.button("☑️", help="Seleccionar todos los proyectos visibles", key="btn_select_all"):
                for pid in ids:
                    sel_state[pid] = True
                # Forzamos recarga para que se refleje en la tabla
                st.rerun()

        # Botón icono Editar
        with col_edit:
            if st.button("✏️", help="Editar el primer proyecto seleccionado", key="btn_edit_icon"):
                seleccionados_ids = [pid for pid in ids if sel_state.get(pid)]
                if not seleccionados_ids:
                    st.warning("No hay ninguna obra seleccionada.")
                else:
                    first_id = seleccionados_ids[0]
                    idx = ids.index(first_id)
                    row_data = df_raw.iloc[idx].to_dict()
                    _open_edit_dialog(row_data, first_id)

        # Botón icono Borrar
        with col_delete:
            if st.button("🗑️", help="Borrar proyectos seleccionados", key="btn_delete_icon"):
                seleccionados_ids = [pid for pid in ids if sel_state.get(pid)]
                if not seleccionados_ids:
                    st.warning("No hay proyectos marcados para borrar.")
                else:
                    total = 0
                    for pid in seleccionados_ids:
                        try:
                            delete_proyecto(pid)
                            total += 1
                            sel_state.pop(pid, None)
                        except Exception as e:
                            st.error(f"No se pudo borrar un proyecto: {e}")
                    st.success(f"Proyectos eliminados: {total}")
                    st.rerun()
