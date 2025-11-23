import streamlit as st
from datetime import date

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
                })
                st.success("Proyecto creado correctamente.")
                st.rerun()

    # ---- Listado y gestión de proyectos ----
    df_proy = get_proyectos()

    if df_proy.empty:
        st.info("Todavía no hay proyectos guardados en Firestore.")
        _render_import_excel()
        return

    # ===== AVISO DE DUPLICADOS =====
    _render_duplicados(df_proy)

    # ===== LISTADO GENERAL CON BORRADO RÁPIDO =====
    st.subheader("📂 Todos los proyectos")
    cols_tabla = [
        "nombre_obra", "cliente_principal", "tipo_proyecto",
        "ciudad", "provincia", "prioridad", "potencial_eur",
        "estado", "fecha_creacion", "fecha_seguimiento"
    ]
    cols_tabla = [c for c in cols_tabla if c in df_proy.columns]
    st.dataframe(
        df_proy[cols_tabla].sort_values("fecha_creacion", ascending=False),
        hide_index=True,
        use_container_width=True
    )

    st.markdown("#### 🗑️ Borrar proyectos rápidamente")
    for _, row in df_proy.sort_values("fecha_creacion", ascending=False).iterrows():
        c1, c2 = st.columns([6, 1])
        with c1:
            st.write(
                f"- {row.get('nombre_obra','(sin nombre)')} "
                f"({row.get('cliente_principal','—')} – {row.get('ciudad','—')})"
            )
        with c2:
            if st.button("🗑️ Borrar", key=f"del_row_{row['id']}"):
                delete_proyecto(row["id"])
                st.success("Proyecto borrado.")
                st.rerun()

    # ===== DETALLE DE PROYECTO =====
    _render_detalle_proyecto(df_proy)

    # ===== EXPORTAR EXCEL OBRAS IMPORTANTES =====
    st.markdown("### 📤 Exportar Excel de obras importantes")
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

    # ===== IMPORTAR DESDE EXCEL =====
    _render_import_excel()


def _render_duplicados(df_proy):
    st.markdown("### ⚠️ Revisión de posibles proyectos duplicados")

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


def _render_detalle_proyecto(df_proy):
    st.markdown("### 🔍 Detalle y edición de un proyecto")

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
        notas_det = st.text_area("Notas de seguimiento", value=proy.get("notas_seguimiento", ""))

        st.markdown("##### Checklist de pasos")
        pasos = proy.get("pasos_seguimiento")
        if not pasos:
            if st.checkbox("Crear checklist base para este proyecto", key=f"chk_crear_pasos_{proy['id']}"):
                pasos = default_pasos_seguimiento()
        estados_check = []
        if pasos:
            for i, paso in enumerate(pasos):
                chk = st.checkbox(
                    paso.get("nombre", f"Paso {i+1}"),
                    value=paso.get("completado", False),
                    key=f"detalle_chk_{proy['id']}_{i}"
                )
                estados_check.append(chk)

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            guardar_det = st.form_submit_button("💾 Guardar cambios")
        with col_btn2:
            borrar_det = st.form_submit_button("🗑️ Borrar este proyecto")

    if guardar_det:
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
        }

        if pasos and estados_check:
            for i, chk in enumerate(estados_check):
                pasos[i]["completado"] = chk
            update_data["pasos_seguimiento"] = pasos

        actualizar_proyecto(proy["id"], update_data)
        st.success("Cambios guardados en el proyecto.")
        st.rerun()

    if borrar_det:
        delete_proyecto(proy["id"])
        st.success("Proyecto borrado.")
        st.rerun()


def _render_import_excel():
    st.markdown("### 📥 Importar proyectos desde Excel (ChatGPT)")
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
