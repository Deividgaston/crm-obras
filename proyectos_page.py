import streamlit as st
from datetime import date, datetime

from crm_utils import (
    get_clientes,
    get_proyectos,
    add_proyecto,
    actualizar_proyecto,
    delete_proyecto,
    default_pasos_seguimiento,
    ensure_cliente_basico,
    filtrar_obras_importantes,
    importar_proyectos_desde_excel,
    generar_excel_obras_importantes,
)


def render_proyectos():
    st.title("🏗️ CRM de Proyectos")


    df_clientes = get_clientes()
    nombres_clientes = ["(sin asignar)"]
    if not df_clientes.empty and "empresa" in df_clientes.columns:
        nombres_clientes += sorted(df_clientes["empresa"].dropna().unique().tolist())

    # ---- Alta de proyecto manual ----
    with st.expander("➕ Añadir nuevo proyecto manualmente"):
        with st.form("form_proyecto"):
            nombre_obra = st.text_input("Nombre del proyecto / obra")
            cliente_principal = st.selectbox("Cliente principal (normalmente promotor)", nombres_clientes)
            tipo_proyecto = st.selectbox(
                "Tipo de proyecto",
                ["Residencial lujo", "Residencial", "Oficinas", "Hotel", "BTR", "Otro"]
            )
            ciudad = st.text_input("Ciudad")
            provincia = st.text_input("Provincia")
            arquitectura = st.text_input("Arquitectura")
            ingenieria = st.text_input("Ingeniería")
            prioridad = st.selectbox("Prioridad", ["Alta", "Media", "Baja"])
            potencial_eur = st.number_input(
                "Potencial estimado 2N (€)", min_value=0.0, step=10000.0, value=50000.0
            )
            estado_inicial = "Detectado"
            fecha_seg = st.date_input("Primera fecha de seguimiento", value=date.today())
            notas = st.text_area("Notas iniciales (fuente del proyecto, link, etc.)")


            guardar_proy = st.form_submit_button("Guardar proyecto")


        if guardar_proy:
            if not nombre_obra:
                st.warning("El nombre del proyecto es obligatorio.")
            else:
                promotor_nombre = None if cliente_principal == "(sin asignar)" else cliente_principal
                if promotor_nombre:
                    ensure_cliente_basico(promotor_nombre, "Promotora")
                ensure_cliente_basico(arquitectura or None, "Arquitectura")
                ensure_cliente_basico(ingenieria or None, "Ingeniería")


                add_proyecto({
                    "nombre_obra": nombre_obra,
                    "cliente_principal": promotor_nombre,
                    "promotora": promotor_nombre,
                    "tipo_proyecto": tipo_proyecto,
                    "ciudad": ciudad,
                    "provincia": provincia,
                    "arquitectura": arquitectura or None,
                    "ingenieria": ingenieria or None,
                    "prioridad": prioridad,
                    "potencial_eur": float(potencial_eur),
                    "estado": estado_inicial,
                    "fecha_seguimiento": fecha_seg.isoformat(),
                    "notas_seguimiento": notas,
                    "notas_historial": [],
                    "tareas": [],
                })
                st.success("Proyecto creado correctamente.")
                st.rerun()

    # ---- Datos de proyectos ----
    df_proy = get_proyectos()

    if df_proy.empty:
        st.info("Todavía no hay proyectos guardados en Firestore.")
        _render_import_export(df_proy_empty=True)
        return

    # ==========================
    # TABS (ventanas) en Proyectos
    # ==========================
    tab_resumen, tab_detalle, tab_duplicados, tab_import = st.tabs(
        ["📊 Resumen", "🔍 Detalle", "🧬 Duplicados", "📥 Importar / Exportar"]
    )

    # ---------- TAB RESUMEN ----------
    with tab_resumen:
        _render_resumen(df_proy)

    # ---------- TAB DETALLE ----------
    with tab_detalle:
        _render_detalle_proyecto(df_proy)

    # ---------- TAB DUPLICADOS ----------
    with tab_duplicados:
        _render_duplicados(df_proy)

    # ---------- TAB IMPORT / EXPORT ----------
    with tab_import:
        _render_import_export(df_proy_empty=False, df_proy=df_proy)


# ==========================
# RESUMEN: pipeline + tabla tipo Excel con filtros y borrar
# ==========================

def _render_resumen(df_proy):
    st.subheader("📊 Pipeline de proyectos por estado")


    df = df_proy.copy()

    # --- Filtros superiores ---
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    # Filtro ciudad
    if "ciudad" in df.columns:
        ciudades = sorted([c for c in df["ciudad"].dropna().unique().tolist() if c])
    else:
        ciudades = []
    with col_f1:
        ciudad_sel = st.selectbox(
            "Ciudad",
            options=["Todas"] + ciudades,
            index=0,
        )

    # Filtro estado (seguimiento)
    if "estado" in df.columns:
        estados_list = sorted(df["estado"].dropna().unique().tolist())
    else:
        estados_list = []
    with col_f2:
        estado_sel = st.selectbox(
            "Estado / Seguimiento",
            options=["Todos"] + estados_list,
            index=0,
        )

    # Filtro tipo de proyecto
    if "tipo_proyecto" in df.columns:
        tipos_list = sorted([t for t in df["tipo_proyecto"].dropna().unique().tolist() if t])
    else:
        tipos_list = []
    with col_f3:
        tipo_sel = st.selectbox(
            "Tipo de proyecto",
            options=["Todos"] + tipos_list,
            index=0,
        )

    # Filtro prioridad
    if "prioridad" in df.columns:
        prioridades = sorted(df["prioridad"].dropna().unique().tolist())
    else:
        prioridades = []
    with col_f4:
        prioridad_sel = st.selectbox(
            "Prioridad",
            options=["Todas"] + prioridades,
            index=0,
        )

    # --- Aplicamos filtros ---
    mask = [True] * len(df)
    df = df.reset_index(drop=True)

    if ciudad_sel != "Todas" and "ciudad" in df.columns:
        mask = df["ciudad"].fillna("") == ciudad_sel
    else:
        mask = pd.Series([True] * len(df))

    if estado_sel != "Todos" and "estado" in df.columns:
        mask &= df["estado"].fillna("") == estado_sel

    if tipo_sel != "Todos" and "tipo_proyecto" in df.columns:
        mask &= df["tipo_proyecto"].fillna("") == tipo_sel

    if prioridad_sel != "Todas" and "prioridad" in df.columns:
        mask &= df["prioridad"].fillna("") == prioridad_sel

    df_filtrado = df[mask].copy()

    # --- Pipeline sobre el filtrado ---
    if not df_filtrado.empty and "estado" in df_filtrado.columns:
        estados = ["Detectado", "Seguimiento", "En Prescripción",
                   "Oferta Enviada", "Negociación", "Ganado", "Perdido"]
        counts = df_filtrado["estado"].value_counts()
        cols_pipe = st.columns(len(estados))
        for col, est in zip(cols_pipe, estados):
            col.metric(est, int(counts.get(est, 0)))
    else:
        st.info("No hay información de estados con los filtros aplicados.")


    st.markdown("### 📂 Lista de proyectos filtrados (selección a la izquierda, sin ID)")


    if df_filtrado.empty:
        st.warning("No hay proyectos que cumplan los filtros seleccionados.")
        return

    # --- Tabla sin ID visible, pero lo guardamos aparte ---
    df_ui = df_filtrado.reset_index(drop=True).copy()
    ids = df_ui["id"].tolist()   # Guardamos IDs para borrado
    df_ui = df_ui.drop(columns=["id"])  # OCULTAMOS el id visualmente


    # Insertamos columna borrar en la primera posición
    df_ui.insert(0, "🗑️ borrar", False)


    edited_df = st.data_editor(
        df_ui,
        column_config={
            "🗑️ borrar": st.column_config.CheckboxColumn(
                "🗑️ borrar",
                help="Marca proyectos y pulsa 'Eliminar seleccionados'",
                default=False,
            )
        },
        hide_index=True,
        use_container_width=True,
        key="tabla_proyectos_editor",
    )


    # ---- Borrar seleccionados ----
    if st.button("Eliminar seleccionados"):
        if "🗑️ borrar" not in edited_df.columns:
            st.error("No se ha encontrado la columna de selección.")
            return

        seleccionados = edited_df["🗑️ borrar"]

        if not seleccionados.any():
            st.warning("No hay proyectos marcados para borrar.")
            return

        total = 0
        for row_idx, marcado in seleccionados.items():
            if marcado:
                try:
                    delete_proyecto(ids[row_idx])   # Usamos el ID real
                    total += 1
                except Exception as e:
                    st.error(f"No se pudo borrar un proyecto: {e}")

        st.success(f"Proyectos eliminados: {total}")
        st.rerun()


# ==========================
# DUPLICADOS
# ==========================

def _render_duplicados(df_proy):
    st.subheader("🧬 Revisión de posibles proyectos duplicados")


    df_tmp = df_proy.copy()
    key_cols_all = ["nombre_obra", "cliente_principal", "ciudad", "provincia"]
    key_cols = [c for c in key_cols_all if c in df_tmp.columns]

    if not key_cols:
        st.info("No hay suficientes campos para detectar duplicados automáticamente.")
        return

    df_tmp["dup_key"] = df_tmp[key_cols].astype(str).agg(" | ".join, axis=1)
    duplicated_mask = df_tmp["dup_key"].duplicated(keep=False)
    df_dups = df_tmp[duplicated_mask].copy()

    if df_dups.empty:
        st.success("No se han detectado proyectos duplicados por nombre + cliente + ciudad + provincia. ✅")
        return

    grupos = df_dups["dup_key"].unique()
    st.warning(f"Se han detectado {len(grupos)} grupos de proyectos que podrían estar duplicados.")
    st.caption("Revisa y borra los que sobren para mantener limpio el CRM.")


    for g in grupos:
        grupo_df = df_dups[df_dups["dup_key"] == g]
        titulo = grupo_df.iloc[0].get("nombre_obra", "Proyecto sin nombre")
        with st.expander(f"Posibles duplicados: {titulo}"):
            show_cols = ["id", "nombre_obra", "cliente_principal", "ciudad",
                         "provincia", "estado", "fecha_creacion", "fecha_seguimiento"]
            show_cols = [c for c in show_cols if c in grupo_df.columns]
            st.dataframe(grupo_df[show_cols], hide_index=True, use_container_width=True)

            for _, row in grupo_df.iterrows():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(
                        f"• {row.get('nombre_obra','')} "
                        f"({row.get('cliente_principal','—')} – {row.get('ciudad','—')})"
                    )
                with col2:
                    if st.button("🗑️ Borrar este proyecto", key=f"del_dup_{row['id']}"):
                        delete_proyecto(row["id"])
                        st.success("Proyecto borrado.")
                        st.rerun()


# ==========================
# DETALLE + TIMELINE + TAREAS + CHECKLIST
# ==========================

def _render_detalle_proyecto(df_proy):
    st.subheader("🔍 Detalle y edición de un proyecto (con timeline y tareas)")


    df_proy_sorted = df_proy.sort_values("fecha_creacion", ascending=False).reset_index(drop=True)
    opciones = [
        f"{r['nombre_obra']} – {r.get('cliente_principal','—')} ({r.get('ciudad','—')})"
        for _, r in df_proy_sorted.iterrows()
    ]
    idx_sel = st.selectbox(
        "Selecciona un proyecto para ver/editar el detalle",
        options=list(range(len(df_proy_sorted))),
        format_func=lambda i: opciones[i] if 0 <= i < len(opciones) else ""
    )

    proy = df_proy_sorted.iloc[idx_sel]
    st.markdown(f"#### Proyecto seleccionado: **{proy['nombre_obra']}**")


    # Sacamos listas existentes (notas_historial, tareas, pasos)
    notas_historial = proy.get("notas_historial") or []
    tareas = proy.get("tareas") or []
    pasos = proy.get("pasos_seguimiento") or []

    with st.form(f"form_detalle_{proy['id']}"):
        col_a, col_b = st.columns(2)
        with col_a:
            nombre_det = st.text_input("Nombre del proyecto", value=proy.get("nombre_obra", ""))
            tipo_det = st.text_input("Tipo de proyecto", value=proy.get("tipo_proyecto", ""))
            promotor_det = st.text_input("Promotor (cliente principal)", value=proy.get("cliente_principal", ""))
            ciudad_det = st.text_input("Ciudad", value=proy.get("ciudad", ""))
            provincia_det = st.text_input("Provincia", value=proy.get("provincia", ""))
        with col_b:
            arquitectura_det = st.text_input("Arquitectura", value=proy.get("arquitectura", ""))
            ingenieria_det = st.text_input("Ingeniería", value=proy.get("ingenieria", ""))
            prioridad_det = st.selectbox(
                "Prioridad",
                ["Alta", "Media", "Baja"],
                index=["Alta", "Media", "Baja"].index(proy.get("prioridad", "Media"))
                if proy.get("prioridad") in ["Alta", "Media", "Baja"] else 1,
            )
            potencial_det = st.number_input(
                "Potencial 2N (€)",
                min_value=0.0,
                step=10000.0,
                value=float(proy.get("potencial_eur", 0.0)) if proy.get("potencial_eur") is not None else 0.0,
            )
            estados_posibles = ["Detectado", "Seguimiento", "En Prescripción", "Oferta Enviada",
                                "Negociación", "Ganado", "Perdido"]
            estado_actual = proy.get("estado", "Detectado")
            if estado_actual not in estados_posibles:
                estado_actual = "Detectado"
            estado_det = st.selectbox("Estado", estados_posibles, index=estados_posibles.index(estado_actual))

        fecha_seg_det = st.date_input(
            "Próxima fecha de seguimiento",
            value=proy.get("fecha_seguimiento") or date.today()
        )
        notas_det = st.text_area("Notas generales de seguimiento", value=proy.get("notas_seguimiento", ""))


        st.markdown("##### 📝 Historial de notas del proyecto")
        if notas_historial:
            try:
                notas_historial_sorted = sorted(
                    notas_historial,
                    key=lambda x: x.get("fecha", ""),
                    reverse=True
                )
            except Exception:
                notas_historial_sorted = notas_historial

            for nota in notas_historial_sorted:
                fecha_txt = nota.get("fecha", "")
                tipo_txt = nota.get("tipo", "Nota")
                texto_txt = nota.get("texto", "")
                st.markdown(f"**[{tipo_txt}] {fecha_txt}**  ")
                st.write(texto_txt)
        else:
            st.caption("Todavía no hay notas históricas para este proyecto.")


        st.markdown("**Añadir nueva nota al historial**")
        nueva_nota_tipo = st.selectbox(
            "Tipo de nota",
            ["Nota", "Llamada", "Reunión", "Visita", "Otro"],
            key=f"tipo_nota_{proy['id']}",
        )
        nueva_nota_texto = st.text_area(
            "Texto de la nota",
            key=f"texto_nota_{proy['id']}",
            placeholder="Ejemplo: Llamada con la promotora, pendiente de enviar oferta..."
        )


        st.markdown("##### ✅ Tareas asociadas al proyecto")
        tareas_actualizadas = []
        if tareas:
            for i, tarea in enumerate(tareas):
                cols_t = st.columns([0.05, 0.45, 0.25, 0.25])
                with cols_t[0]:
                    completado = st.checkbox(
                        "",
                        value=tarea.get("completado", False),
                        key=f"chk_tarea_{proy['id']}_{i}"
                    )
                with cols_t[1]:
                    st.write(tarea.get("titulo", "(sin título)"))
                with cols_t[2]:
                    st.write(tarea.get("fecha_limite", ""))
                with cols_t[3]:
                    st.write(tarea.get("tipo", "Tarea"))
                tareas_actualizadas.append({
                    "titulo": tarea.get("titulo", ""),
                    "fecha_limite": tarea.get("fecha_limite", None),
                    "completado": completado,
                    "tipo": tarea.get("tipo", "Tarea"),
                })
        else:
            st.caption("No hay tareas creadas todavía.")


        st.markdown("**Añadir nueva tarea**")
        nueva_tarea_titulo = st.text_input(
            "Título de la tarea",
            key=f"titulo_tarea_{proy['id']}",
            placeholder="Ejemplo: Llamar a la ingeniería para revisar planos..."
        )
        nueva_tarea_tipo = st.selectbox(
            "Tipo de tarea",
            ["Llamada", "Email", "Reunión", "Visita", "Otro"],
            key=f"tipo_tarea_{proy['id']}",
        )
        nueva_tarea_fecha = st.date_input(
            "Fecha límite de la tarea",
            value=date.today(),
            key=f"fecha_tarea_{proy['id']}",
        )


        st.markdown("##### 🧭 Checklist de pasos de seguimiento")
        estados_check_pasos = []
        if not pasos:
            if st.checkbox("Crear checklist base para este proyecto", key=f"chk_crear_pasos_{proy['id']}"):
                pasos = default_pasos_seguimiento()
        if pasos:
            for i, paso in enumerate(pasos):
                chk = st.checkbox(
                    paso.get("nombre", f"Paso {i+1}"),
                    value=paso.get("completado", False),
                    key=f"detalle_chk_{proy['id']}_{i}"
                )
                estados_check_pasos.append(chk)


        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            guardar_det = st.form_submit_button("💾 Guardar cambios (datos, notas, tareas)")
        with col_btn2:
            borrar_det = st.form_submit_button("🗑️ Borrar este proyecto")


    if guardar_det:
        if nueva_nota_texto.strip():
            notas_historial.append({
                "fecha": datetime.utcnow().isoformat(timespec="seconds"),
                "tipo": nueva_nota_tipo,
                "texto": nueva_nota_texto.strip(),
            })


        if nueva_tarea_titulo.strip():
            tareas_actualizadas.append({
                "titulo": nueva_tarea_titulo.strip(),
                "fecha_limite": nueva_tarea_fecha.isoformat(),
                "completado": False,
                "tipo": nueva_tarea_tipo,
            })


        if pasos and estados_check_pasos:
            for i, chk in enumerate(estados_check_pasos):
                pasos[i]["completado"] = chk

        update_data = {
            "nombre_obra": nombre_det,
            "tipo_proyecto": tipo_det,
            "cliente_principal": promotor_det or None,
            "promotora": promotor_det or None,
            "ciudad": ciudad_det or None,
            "provincia": provincia_det or None,
            "arquitectura": arquitectura_det or None,
            "ingenieria": ingenieria_det or None,
            "prioridad": prioridad_det,
            "potencial_eur": float(potencial_det),
            "estado": estado_det,
            "fecha_seguimiento": fecha_seg_det.isoformat(),
            "notas_seguimiento": notas_det,
            "notas_historial": notas_historial,
            "tareas": tareas_actualizadas,
            "pasos_seguimiento": pasos,
        }

        actualizar_proyecto(proy["id"], update_data)
        st.success("Cambios guardados en el proyecto (datos, notas, tareas y pasos)."


        )
        st.rerun()

    if borrar_det:
        delete_proyecto(proy["id"])
        st.success("Proyecto borrado.")
        st.rerun()


# ==========================
# IMPORTAR / EXPORTAR
# ==========================

def _render_import_export(df_proy_empty: bool, df_proy=None):
    st.subheader("📤 Exportar / 📥 Importar")


    if not df_proy_empty and df_proy is not None:
        st.markdown("#### Exportar Excel de obras importantes")
        df_importantes = filtrar_obras_importantes(df_proy)
        if df_importantes.empty:
            st.info("No hay obras importantes según criterios (prioridad Alta o potencial ≥ 50k€).")
        else:
            output = generar_excel_obras_importantes(df_proy)
            fecha_str = date.today().isoformat()
            st.download_button(
                label=f"⬇️ Descargar Excel obras importantes ({fecha_str})",
                data=output,
                file_name=f"obras_importantes_{fecha_str}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    st.markdown("#### Importar proyectos desde Excel (ChatGPT)")
    st.caption(
        "Sube el Excel que te genero desde ChatGPT. "
        "Formato de fechas: 30/11/25 o 30/11/2025 (dd/mm/aa). "
        "El campo Promotora_Fondo se usará como cliente principal (promotor)."
    )

    uploaded_file = st.file_uploader(
        "Sube aquí el archivo .xlsx con los proyectos",
        type=["xlsx"],
        key="uploader_import"
    )

    if uploaded_file is not None:
        import pandas as pd
        try:
            df_preview = pd.read_excel(uploaded_file)
            st.write("Vista previa de los datos a importar:")
            st.dataframe(df_preview.head(), use_container_width=True)

            if st.button("🚀 Importar estos proyectos al CRM"):
                creados = importar_proyectos_desde_excel(uploaded_file)
                st.success(f"Importación completada. Proyectos creados: {creados}")
                st.rerun()
        except Exception as e:
            st.error(f"Error leyendo el Excel: {e}")
    else:
        st.info("Sube un Excel para poder importarlo.")
