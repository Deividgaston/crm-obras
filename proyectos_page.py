import streamlit as st
import pandas as pd
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
    ciudades = sorted(df["ciudad"].dropna().unique().tolist()) if "ciudad" in df.columns else []
    with col_f1:
        ciudad_sel = st.selectbox("Ciudad", ["Todas"] + ciudades)

    # Filtro estado
    estados_list = sorted(df["estado"].dropna().unique().tolist()) if "estado" in df.columns else []
    with col_f2:
        estado_sel = st.selectbox("Estado / Seguimiento", ["Todos"] + estados_list)

    # Filtro tipo de proyecto
    tipos_list = sorted(df["tipo_proyecto"].dropna().unique().tolist()) if "tipo_proyecto" in df.columns else []
    with col_f3:
        tipo_sel = st.selectbox("Tipo de proyecto", ["Todos"] + tipos_list)

    # Filtro prioridad
    prioridades = sorted(df["prioridad"].dropna().unique().tolist()) if "prioridad" in df.columns else []
    with col_f4:
        prioridad_sel = st.selectbox("Prioridad", ["Todas"] + prioridades)

    # --- Aplicamos filtros ---
    mask = pd.Series([True] * len(df))

    if ciudad_sel != "Todas":
        mask &= df["ciudad"].fillna("") == ciudad_sel

    if estado_sel != "Todos":
        mask &= df["estado"].fillna("") == estado_sel

    if tipo_sel != "Todos":
        mask &= df["tipo_proyecto"].fillna("") == tipo_sel

    if prioridad_sel != "Todas":
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
    ids = df_ui["id"].tolist()
    df_ui = df_ui.drop(columns=["id"])

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
        seleccionados = edited_df["🗑️ borrar"]
        if not seleccionados.any():
            st.warning("No hay proyectos marcados para borrar.")
            return

        total = 0
        for row_idx, marcado in seleccionados.items():
            if marcado:
                try:
                    delete_proyecto(ids[row_idx])
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
    key_cols = ["nombre_obra", "cliente_principal", "ciudad", "provincia"]
    key_cols = [c for c in key_cols if c in df_tmp.columns]

    if not key_cols:
        st.info("No hay suficientes campos para detectar duplicados automáticamente.")
        return

    df_tmp["dup_key"] = df_tmp[key_cols].astype(str).agg(" | ".join, axis=1)
    duplicated_mask = df_tmp["dup_key"].duplicated(keep=False)
    df_dups = df_tmp[duplicated_mask].copy()

    if df_dups.empty:
        st.success("No se han detectado proyectos duplicados. ✔️")
        return

    grupos = df_dups["dup_key"].unique()
    st.warning(f"Se han detectado {len(grupos)} grupos de duplicados.")

    for g in grupos:
        grupo_df = df_dups[df_dups["dup_key"] == g]
        titulo = grupo_df.iloc[0].get("nombre_obra", "")
        with st.expander(f"Posibles duplicados: {titulo}"):

            show_cols = [c for c in ["id", "nombre_obra", "cliente_principal", "ciudad",
                                     "provincia", "estado", "fecha_creacion", "fecha_seguimiento"]
                         if c in grupo_df.columns]

            st.dataframe(grupo_df[show_cols], hide_index=True)

            for _, row in grupo_df.iterrows():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"• {row['nombre_obra']} ({row['cliente_principal']})")
                with col2:
                    if st.button("🗑️ Borrar este proyecto", key=f"del_dup_{row['id']}"):
                        delete_proyecto(row["id"])
                        st.rerun()


# ==========================
# DETALLE + TIMELINE + TAREAS + CHECKLIST
# ==========================

def _render_detalle_proyecto(df_proy):
    st.subheader("🔍 Detalle y edición de un proyecto")

    df_sorted = df_proy.sort_values("fecha_creacion", ascending=False).reset_index(drop=True)

    opciones = [
        f"{r['nombre_obra']} – {r.get('cliente_principal','—')} ({r.get('ciudad','—')})"
        for _, r in df_sorted.iterrows()
    ]

    idx = st.selectbox(
        "Selecciona un proyecto",
        options=list(range(len(df_sorted))),
        format_func=lambda i: opciones[i]
    )

    proy = df_sorted.iloc[idx]

    st.markdown(f"### {proy['nombre_obra']}")

    notas_historial = proy.get("notas_historial") or []
    tareas = proy.get("tareas") or []
    pasos = proy.get("pasos_seguimiento") or []

    with st.form(f"form_detalle_{proy['id']}"):

        col1, col2 = st.columns(2)
        with col1:
            nombre_det = st.text_input("Nombre del proyecto", proy["nombre_obra"])
            tipo_det = st.text_input("Tipo de proyecto", proy.get("tipo_proyecto", ""))
            promotor_det = st.text_input("Promotor", proy.get("cliente_principal", ""))
            ciudad_det = st.text_input("Ciudad", proy.get("ciudad", ""))
            provincia_det = st.text_input("Provincia", proy.get("provincia", ""))

        with col2:
            arquitectura_det = st.text_input("Arquitectura", proy.get("arquitectura", ""))
            ingenieria_det = st.text_input("Ingeniería", proy.get("ingenieria", ""))
            prioridad_det = st.selectbox(
                "Prioridad",
                ["Alta", "Media", "Baja"],
                index=["Alta", "Media", "Baja"].index(proy.get("prioridad", "Media"))
            )
            potencial_det = st.number_input(
                "Potencial (€)",
                min_value=0.0, step=10000.0,
                value=float(proy.get("potencial_eur", 0.0))
            )
            estado_det = st.selectbox(
                "Estado",
                ["Detectado", "Seguimiento", "En Prescripción", "Oferta Enviada",
                 "Negociación", "Ganado", "Perdido"],
                index=["Detectado", "Seguimiento", "En Prescripción",
                       "Oferta Enviada", "Negociación", "Ganado", "Perdido"]
                .index(proy.get("estado", "Detectado"))
            )

        fecha_seg_det = st.date_input(
            "Próxima fecha de seguimiento",
            proy.get("fecha_seguimiento") or date.today()
        )

        notas_det = st.text_area("Notas generales", proy.get("notas_seguimiento", ""))

        # Timeline de notas
        st.markdown("### 📝 Historial de notas")
        for nota in sorted(notas_historial, key=lambda x: x.get("fecha", ""), reverse=True):
            st.markdown(f"**[{nota['tipo']}] {nota['fecha']}**")
            st.write(nota["texto"])

        nueva_nota_tipo = st.selectbox("Tipo de nota", ["Nota", "Llamada", "Reunión", "Visita", "Otro"])
        nueva_nota_texto = st.text_area("Nueva nota")

        # Tareas
        st.markdown("### 📋 Tareas")
        tareas_actualizadas = []
        for i, tarea in enumerate(tareas):
            cols = st.columns([0.05, 0.6, 0.2, 0.15])
            with cols[0]:
                comp = st.checkbox("", value=tarea.get("completado", False), key=f"tk{i}")
            with cols[1]:
                st.write(tarea.get("titulo", ""))
            with cols[2]:
                st.write(tarea.get("fecha_limite", ""))
            with cols[3]:
                st.write(tarea.get("tipo", ""))
            tareas_actualizadas.append({
                "titulo": tarea.get("titulo"),
                "fecha_limite": tarea.get("fecha_limite"),
                "completado": comp,
                "tipo": tarea.get("tipo"),
            })

        nueva_tarea_titulo = st.text_input("Título nueva tarea")
        nueva_tarea_tipo = st.selectbox("Tipo Tarea", ["Llamada", "Email", "Reunión", "Visita", "Otro"])
        nueva_tarea_fecha = st.date_input("Fecha límite", date.today())

        # Checklist
        st.markdown("### 🧭 Checklist de pasos")
        if not pasos:
            if st.checkbox("Crear checklist base"):
                pasos = default_pasos_seguimiento()

        estados_pas = []
        for i, paso in enumerate(pasos):
            chk = st.checkbox(paso["nombre"], paso.get("completado", False), key=f"ps{i}")
            estados_pas.append(chk)

        colg1, colg2 = st.columns(2)
        with colg1:
            guardar = st.form_submit_button("💾 Guardar cambios")
        with colg2:
            borrar = st.form_submit_button("🗑️ Borrar proyecto")

    if guardar:
        if nueva_nota_texto.strip():
            notas_historial.append({
                "fecha": datetime.utcnow().isoformat(),
                "tipo": nueva_nota_tipo,
                "texto": nueva_nota_texto.strip(),
            })

        if nueva_tarea_titulo.strip():
            tareas_actualizadas.append({
                "titulo": nueva_tarea_titulo.strip(),
                "fecha_limite": nueva_tarea_fecha.isoformat(),
                "tipo": nueva_tarea_tipo,
                "completado": False,
            })

        for i, chk in enumerate(estados_pas):
            pasos[i]["completado"] = chk

        actualizar_proyecto(proy["id"], {
            "nombre_obra": nombre_det,
            "tipo_proyecto": tipo_det,
            "cliente_principal": promotor_det,
            "promotora": promotor_det,
            "ciudad": ciudad_det,
            "provincia": provincia_det,
            "arquitectura": arquitectura_det,
            "ingenieria": ingenieria_det,
            "prioridad": prioridad_det,
            "potencial_eur": potencial_det,
            "estado": estado_det,
            "fecha_seguimiento": fecha_seg_det.isoformat(),
            "notas_seguimiento": notas_det,
            "notas_historial": notas_historial,
            "tareas": tareas_actualizadas,
            "pasos_seguimiento": pasos,
        })

        st.success("Proyecto actualizado.")
        st.rerun()

    if borrar:
        delete_proyecto(proy["id"])
        st.success("Proyecto eliminado.")
        st.rerun()


# ==========================
# IMPORTAR / EXPORTAR
# ==========================

def _render_import_export(df_proy_empty: bool, df_proy=None):
    st.subheader("📤 Exportar / 📥 Importar")

    if not df_proy_empty:
        st.markdown("#### Exportar Excel de obras importantes")
        df_imp = filtrar_obras_importantes(df_proy)
        if df_imp.empty:
            st.info("No hay obras importantes.")
        else:
            output = generar_excel_obras_importantes(df_proy)
            fecha = date.today().isoformat()
            st.download_button(
                f"⬇️ Descargar Excel ({fecha})",
                output,
                file_name=f"obras_importantes_{fecha}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    st.markdown("#### Importar proyectos desde Excel (ChatGPT)")

    uploaded = st.file_uploader("Sube archivo Excel", type=["xlsx"], key="import_proj")

    if uploaded:
        import pandas as pd
        try:
            df_preview = pd.read_excel(uploaded)
            st.dataframe(df_preview)

            if st.button("🚀 Importar al CRM"):
                creados = importar_proyectos_desde_excel(uploaded)
                st.success(f"Proyectos creados: {creados}")
                st.rerun()
        except Exception as e:
            st.error(f"Error al leer Excel: {e}")

