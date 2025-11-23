import streamlit as st
import pandas as pd
import altair as alt
from datetime import date, datetime

from style_injector import inject_apple_style

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


# =====================================================
# PÁGINA PRINCIPAL DE PROYECTOS
# =====================================================

def render_proyectos():
    """Página principal de Proyectos."""
    inject_apple_style()

    # CABECERA (título más compacto)
    st.markdown(
        """
        <div class="apple-card">
            <div class="section-badge">Proyectos</div>
            <h2 style="margin-top: 6px; font-size:1.55rem;">CRM de Proyectos</h2>
            <p style="color:#9FB3D1; margin-bottom: 0; font-size:0.9rem;">
                Vista unificada para filtrar, revisar el pipeline, listar y editar proyectos.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_clientes = get_clientes()
    df_proy = get_proyectos()
    if df_proy is None:
        df_proy = pd.DataFrame()

    # Alta rápida
    _bloque_alta_proyecto(df_clientes)

    if df_proy.empty:
        st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
        st.info("Todavía no hay proyectos creadados en Firestore.")
        _render_import_export(df_proy_empty=True)
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # Pestañas
    tab_vista, tab_dash, tab_duplicados, tab_import = st.tabs(
        [
            "📂 Vista general",
            "📈 Dashboard analítico",
            "🧬 Duplicados",
            "📥 Importar / Exportar",
        ]
    )

    with tab_vista:
        _render_vista_general(df_proy)

    with tab_dash:
        _render_dashboard(df_proy)

    with tab_duplicados:
        _render_duplicados(df_proy)

    with tab_import:
        _render_import_export(df_proy_empty=False, df_proy=df_proy)


# =====================================================
# ALTA DE PROYECTO
# =====================================================

def _bloque_alta_proyecto(df_clientes):
    nombres_clientes = ["(sin asignar)"]
    if df_clientes is not None and not df_clientes.empty and "empresa" in df_clientes.columns:
        nombres_clientes += sorted(df_clientes["empresa"].dropna().unique().tolist())

    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.markdown("#### ➕ Añadir nuevo proyecto", unsafe_allow_html=True)

    with st.form("form_proyecto"):
        col1, col2 = st.columns(2)
        with col1:
            nombre_obra = st.text_input("Nombre del proyecto / obra")
            cliente_principal = st.selectbox(
                "Cliente principal (promotor)",
                nombres_clientes,
            )
            tipo_proyecto = st.selectbox(
                "Tipo de proyecto",
                ["Residencial lujo", "Residencial", "BTR", "Oficinas", "Hotel", "Industrial", "Otro"],
            )
            ciudad = st.text_input("Ciudad")
            provincia = st.text_input("Provincia")
        with col2:
            arquitectura = st.text_input("Arquitectura")
            ingenieria = st.text_input("Ingeniería")
            prioridad = st.selectbox("Prioridad", ["Alta", "Media", "Baja"])
            potencial_eur = st.number_input(
                "Potencial estimado 2N (€)",
                min_value=0.0,
                step=10000.0,
                value=50000.0,
            )
            fecha_seg = st.date_input(
                "Primera fecha de seguimiento",
                value=date.today(),
            )

        notas = st.text_area("Notas iniciales (fuente del proyecto, link, etc.)")
        guardar = st.form_submit_button("Guardar proyecto")

    if guardar:
        if not nombre_obra.strip():
            st.warning("Debes introducir el nombre del proyecto.")
        else:
            cli = None if cliente_principal == "(sin asignar)" else cliente_principal
            if cli:
                ensure_cliente_basico(cli, "Promotora")
            ensure_cliente_basico(arquitectura or None, "Arquitectura")
            ensure_cliente_basico(ingenieria or None, "Ingeniería")

            add_proyecto(
                {
                    "nombre_obra": nombre_obra,
                    "cliente_principal": cli,
                    "promotora": cli,
                    "tipo_proyecto": tipo_proyecto,
                    "ciudad": ciudad,
                    "provincia": provincia,
                    "arquitectura": arquitectura or None,
                    "ingenieria": ingenieria or None,
                    "prioridad": prioridad,
                    "potencial_eur": float(potencial_eur),
                    "estado": "Detectado",
                    "fecha_seguimiento": fecha_seg.isoformat(),
                    "notas_seguimiento": notas,
                    "notas_historial": [],
                    "tareas": [],
                    "pasos_seguimiento": [],
                }
            )
            st.success("Proyecto creado correctamente.")
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# =====================================================
# FILTROS
# =====================================================

def _aplicar_filtros_basicos(df: pd.DataFrame, key_prefix: str):
    df = df.copy()

    st.markdown("##### 🎯 Filtros rápidos", unsafe_allow_html=True)
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    ciudades = sorted(df["ciudad"].dropna().unique().tolist()) if "ciudad" in df.columns else []
    with col_f1:
        ciudad_sel = st.selectbox(
            "Ciudad",
            ["Todas"] + ciudades,
            key=f"{key_prefix}_ciudad",
        )

    estados_list = sorted(df["estado"].dropna().unique().tolist()) if "estado" in df.columns else []
    if "Paralizado" not in estados_list:
        estados_list.append("Paralizado")
    with col_f2:
        estado_sel = st.selectbox(
            "Estado / Seguimiento",
            ["Todos"] + estados_list,
            key=f"{key_prefix}_estado",
        )

    tipos_list = sorted(df["tipo_proyecto"].dropna().unique().tolist()) if "tipo_proyecto" in df.columns else []
    with col_f3:
        tipo_sel = st.selectbox(
            "Tipo de proyecto",
            ["Todos"] + tipos_list,
            key=f"{key_prefix}_tipo",
        )

    prioridades = sorted(df["prioridad"].dropna().unique().tolist()) if "prioridad" in df.columns else []
    with col_f4:
        prioridad_sel = st.selectbox(
            "Prioridad",
            ["Todas"] + prioridades,
            key=f"{key_prefix}_prioridad",
        )

    mask = pd.Series(True, index=df.index)

    if ciudad_sel != "Todas":
        mask &= df["ciudad"].fillna("") == ciudad_sel
    if estado_sel != "Todos":
        mask &= df["estado"].fillna("") == estado_sel
    if tipo_sel != "Todos":
        mask &= df["tipo_proyecto"].fillna("") == tipo_sel
    if prioridad_sel != "Todas":
        mask &= df["prioridad"].fillna("") == prioridad_sel

    return df[mask].copy()


# =====================================================
# VISTA GENERAL (TABLA + MODAL DE EDICIÓN)
# =====================================================

def _render_vista_general(df_proy: pd.DataFrame):
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.subheader("📂 Lista de proyectos")

    df_filtrado = _aplicar_filtros_basicos(df_proy, key_prefix="vista")

    if df_filtrado.empty:
        st.info("No hay proyectos que cumplan los filtros seleccionados.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # Pipeline métrico sencillo
    st.markdown("### 🧪 Pipeline (métricas por estado)", unsafe_allow_html=True)
    estados_base = [
        "Detectado",
        "Seguimiento",
        "En Prescripción",
        "Oferta Enviada",
        "Negociación",
        "Paralizado",
        "Ganado",
        "Perdido",
    ]

    if "estado" in df_filtrado.columns:
        counts = df_filtrado["estado"].value_counts()
        cols = st.columns(len(estados_base))
        for col, est in zip(cols, estados_base):
            col.metric(est, int(counts.get(est, 0)))
    else:
        st.caption("No hay columna de estado en los proyectos.")

    # -------- TABLA A TODO EL ANCHO --------
    df_lista = df_filtrado.copy()

    df_ui = df_lista.reset_index(drop=True).copy()
    ids = df_ui["id"].tolist()
    df_ui = df_ui.drop(columns=["id"])

    # Solo una columna de selección
    df_ui.insert(0, "Seleccionar", False)

    edited_df = st.data_editor(
        df_ui,
        column_config={
            "Seleccionar": st.column_config.CheckboxColumn(
                "✔",
                help="Marca la fila sobre la que quieres editar o eliminar",
                default=False,
            ),
        },
        hide_index=True,
        use_container_width=True,
        key="vista_tabla_proyectos",
    )

    # Determinar fila seleccionada
    selected_indices = [i for i, v in edited_df["Seleccionar"].items() if v]
    selected_id = None
    selected_row = None

    if len(selected_indices) > 1:
        st.warning("Hay varias filas seleccionadas. Solo se usará la primera.")
    if selected_indices:
        idx = selected_indices[0]
        selected_id = ids[idx]
        selected_row = df_lista.reset_index(drop=True).iloc[idx]

    # -------- BOTONES DE ACCIÓN BAJO LA TABLA --------
    col_acc1, col_acc2 = st.columns(2)
    with col_acc1:
        if st.button(
            "✏️ Editar seleccionado",
            use_container_width=True,
            disabled=selected_id is None,
        ):
            if selected_id is None:
                st.warning("Selecciona primero un proyecto en la tabla.")
            else:
                st.session_state["edit_proyecto_id"] = selected_id
                st.session_state["show_edit_modal"] = True
                st.rerun()

    with col_acc2:
        if st.button(
            "🗑️ Eliminar seleccionado",
            use_container_width=True,
            disabled=selected_id is None,
        ):
            if selected_id is None:
                st.warning("Selecciona primero un proyecto en la tabla.")
            else:
                delete_proyecto(selected_id)
                st.success("Proyecto eliminado.")
                st.rerun()

    # -------- MODAL FLOANTE DE EDICIÓN --------
    if st.session_state.get("show_edit_modal") and st.session_state.get("edit_proyecto_id"):
        edit_id = st.session_state["edit_proyecto_id"]

        # Buscamos el proyecto en el DF filtrado (por si han cambiado filtros)
        df_reset = df_lista.reset_index(drop=True)
        match = df_reset[df_reset["id"] == edit_id]
        if match.empty:
            # Si no está, cerramos modal
            st.session_state["show_edit_modal"] = False
            st.session_state["edit_proyecto_id"] = None
        else:
            proy = match.iloc[0]
            with st.modal("Editar proyecto"):
                _panel_detalle_proyecto(proy)

    st.markdown("</div>", unsafe_allow_html=True)


# =====================================================
# PANEL DETALLE (USADO DENTRO DEL MODAL)
# =====================================================

def _panel_detalle_proyecto(proy):
    notas_historial = proy.get("notas_historial") or []
    tareas = proy.get("tareas") or []
    pasos = proy.get("pasos_seguimiento") or []

    st.markdown(
        f"**{proy.get('nombre_obra','(sin nombre)')} – {proy.get('cliente_principal','—')}**",
        unsafe_allow_html=True,
    )
    st.caption(f"Ciudad: {proy.get('ciudad','—')} · Provincia: {proy.get('provincia','—')}")

    with st.form(f"form_detalle_modal_{proy['id']}"):
        col_a, col_b = st.columns(2)

        with col_a:
            nombre_det = st.text_input("Nombre del proyecto", value=proy.get("nombre_obra", ""))
            tipo_det = st.text_input("Tipo de proyecto", value=proy.get("tipo_proyecto", ""))
            promotor_det = st.text_input("Promotor", value=proy.get("cliente_principal", ""))
            ciudad_det = st.text_input("Ciudad", value=proy.get("ciudad", ""))
            provincia_det = st.text_input("Provincia", value=proy.get("provincia", ""))

        with col_b:
            arquitectura_det = st.text_input("Arquitectura", value=proy.get("arquitectura", ""))
            ingenieria_det = st.text_input("Ingeniería", value=proy.get("ingenieria", ""))
            prioridad_det = st.selectbox(
                "Prioridad",
                ["Alta", "Media", "Baja"],
                index=["Alta", "Media", "Baja"].index(proy.get("prioridad", "Media")),
            )
            potencial_det = st.number_input(
                "Potencial 2N (€)",
                min_value=0.0,
                step=10000.0,
                value=float(proy.get("potencial_eur", 0.0) or 0.0),
            )
            estado_det = st.selectbox(
                "Estado",
                ["Detectado", "Seguimiento", "En Prescripción", "Oferta Enviada",
                 "Negociación", "Paralizado", "Ganado", "Perdido"],
                index=["Detectado", "Seguimiento", "En Prescripción", "Oferta Enviada",
                       "Negociación", "Paralizado", "Ganado", "Perdido"].index(
                    proy.get("estado", "Detectado"))
            )

        fecha_seg_val = proy.get("fecha_seguimiento") or date.today()
        if isinstance(fecha_seg_val, str):
            try:
                fecha_seg_val = datetime.fromisoformat(fecha_seg_val).date()
            except Exception:
                fecha_seg_val = date.today()

        fecha_seg_det = st.date_input(
            "Próxima fecha de seguimiento",
            value=fecha_seg_val,
        )
        notas_det = st.text_area(
            "Notas generales de seguimiento",
            value=proy.get("notas_seguimiento", ""),
        )

        # ---- Historial de notas ----
        st.markdown("##### 📝 Historial de notas")
        if notas_historial:
            for nota in sorted(notas_historial, key=lambda x: x.get("fecha", ""), reverse=True):
                st.write(f"**[{nota.get('tipo','Nota')}] {nota.get('fecha','')}**")
                st.write(nota.get("texto", ""))
        else:
            st.caption("Sin notas aún.")

        nueva_nota_tipo = st.selectbox(
            "Tipo de nota",
            ["Nota", "Llamada", "Reunión", "Visita", "Otro"],
            key=f"tipo_nota_{proy['id']}",
        )
        nueva_nota_texto = st.text_area(
            "Nueva nota",
            key=f"texto_nota_{proy['id']}",
            placeholder="Ejemplo: llamada con la promotora, pendiente de oferta...",
        )

        # ---- Tareas ----
        st.markdown("##### ☑️ Tareas")
        tareas_actualizadas = []
        if tareas:
            for i, t in enumerate(tareas):
                cols_t = st.columns([0.08, 0.52, 0.20, 0.20])
                with cols_t[0]:
                    completado = st.checkbox(
                        "",
                        value=t.get("completado", False),
                        key=f"chk_tarea_modal_{proy['id']}_{i}",
                    )
                with cols_t[1]:
                    st.write(t.get("titulo", "(sin título)"))
                with cols_t[2]:
                    st.write(t.get("fecha_limite", ""))
                with cols_t[3]:
                    st.write(t.get("tipo", "Tarea"))

                tareas_actualizadas.append(
                    {
                        "titulo": t.get("titulo", ""),
                        "fecha_limite": t.get("fecha_limite", None),
                        "completado": completado,
                        "tipo": t.get("tipo", "Tarea"),
                    }
                )
        else:
            st.caption("No hay tareas todavía.")

        nueva_tarea_titulo = st.text_input(
            "Añadir tarea nueva",
            key=f"titulo_tarea_{proy['id']}",
        )
        nueva_tarea_tipo = st.selectbox(
            "Tipo de tarea nueva",
            ["Llamada", "Email", "Reunión", "Visita", "Otro"],
            key=f"tipo_tarea_{proy['id']}",
        )
        nueva_tarea_fecha = st.date_input(
            "Fecha límite nueva",
            value=date.today(),
            key=f"fecha_tarea_{proy['id']}",
        )

        # ---- Checklist ----
        st.markdown("##### 🧭 Checklist de pasos")
        if not pasos:
            if st.checkbox(
                "Crear checklist base",
                key=f"chk_crear_pasos_{proy['id']}",
            ):
                pasos = default_pasos_seguimiento()

        estados_check_pasos = []
        for i, paso in enumerate(pasos):
            chk = st.checkbox(
                paso.get("nombre", f"Paso {i+1}"),
                value=paso.get("completado", False),
                key=f"chk_paso_{proy['id']}_{i}",
            )
            estados_check_pasos.append(chk)

        col1, col2 = st.columns(2)
        guardar_det = col1.form_submit_button("💾 Guardar cambios")
        cancelar_det = col2.form_submit_button("Cancelar")

    if cancelar_det:
        # Cerrar modal sin guardar
        st.session_state["show_edit_modal"] = False
        st.session_state["edit_proyecto_id"] = None
        st.rerun()

    if guardar_det:
        # Nueva nota
        if nueva_nota_texto.strip():
            notas_historial.append(
                {
                    "fecha": datetime.utcnow().isoformat(timespec="seconds"),
                    "tipo": nueva_nota_tipo,
                    "texto": nueva_nota_texto.strip(),
                }
            )

        # Nueva tarea
        if nueva_tarea_titulo.strip():
            tareas_actualizadas.append(
                {
                    "titulo": nueva_tarea_titulo.strip(),
                    "fecha_limite": nueva_tarea_fecha.isoformat(),
                    "completado": False,
                    "tipo": nueva_tarea_tipo,
                }
            )

        # Checklist
        if pasos and estados_check_pasos:
            for i, chk in enumerate(estados_check_pasos):
                pasos[i]["completado"] = chk

        actualizar_proyecto(
            proy["id"],
            {
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
            },
        )

        # Cerramos modal y refrescamos
        st.session_state["show_edit_modal"] = False
        st.session_state["edit_proyecto_id"] = None
        st.success("Proyecto actualizado.")
        st.rerun()


# =====================================================
# DASHBOARD ANALÍTICO
# =====================================================

def _render_dashboard(df_proy: pd.DataFrame):
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.subheader("📈 Dashboard analítico")

    df_filtrado = _aplicar_filtros_basicos(df_proy, key_prefix="dash")

    if df_filtrado.empty:
        st.info("No hay datos.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    if "potencial_eur" not in df_filtrado.columns:
        df_filtrado["potencial_eur"] = 0

    opciones = [
        "Estado / Seguimiento",
        "Ciudad",
        "Provincia",
        "Tipo de proyecto",
        "Prioridad",
        "Rango de potencial (€)",
    ]
    dim_map = {
        "Estado / Seguimiento": "estado",
        "Ciudad": "ciudad",
        "Provincia": "provincia",
        "Tipo de proyecto": "tipo_proyecto",
        "Prioridad": "prioridad",
    }

    col1, col2 = st.columns([2, 1])
    with col1:
        agrupacion = st.selectbox("Agrupar por", opciones)
    with col2:
        metrica = st.radio("Métrica", ["Número de obras", "Potencial total (€)"])

    df_plot = df_filtrado.copy()

    if agrupacion == "Rango de potencial (€)":
        potencial = df_plot["potencial_eur"].fillna(0)
        bins = [0, 50000, 100000, 200000, 500000, 1_000_000_000]
        labels = ["<50k", "50k-100k", "100k-200k", "200k-500k", ">500k"]
        df_plot["rango_potencial"] = pd.cut(
            potencial,
            bins=bins,
            labels=labels,
            include_lowest=True,
        )
        group_col = "rango_potencial"
        titulo_eje = "Rango de potencial"
    else:
        group_col = dim_map.get(agrupacion)
        titulo_eje = agrupacion

    agg_df = (
        df_plot.groupby(group_col)
        .agg(
            num_obras=("id", "count"),
            potencial_total=("potencial_eur", "sum"),
        )
        .reset_index()
    )

    if metrica == "Número de obras":
        y_field = "num_obras"
        y_title = "Número de obras"
    else:
        y_field = "potencial_total"
        y_title = "Potencial total (€)"

    chart = (
        alt.Chart(agg_df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X(f"{group_col}:N", sort="-y", title=titulo_eje),
            y=alt.Y(f"{y_field}:Q", title=y_title),
            tooltip=[group_col, "num_obras", "potencial_total"],
            color=alt.Color(f"{group_col}:N", legend=None),
        )
        .properties(height=340)
    )

    st.altair_chart(chart, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


# =====================================================
# DUPLICADOS
# =====================================================

def _render_duplicados(df_proy: pd.DataFrame):
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.subheader("🧬 Duplicados")

    df_tmp = df_proy.copy()
    key_cols = ["nombre_obra", "cliente_principal", "ciudad", "provincia"]
    key_cols = [c for c in key_cols if c in df_tmp.columns]

    if not key_cols:
        st.info("No hay columnas suficientes para detectar duplicados.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    df_tmp["dup_key"] = df_tmp[key_cols].astype(str).agg(" | ".join, axis=1)
    mask = df_tmp["dup_key"].duplicated(keep=False)
    df_dups = df_tmp[mask].copy()

    if df_dups.empty:
        st.success("No se han detectado proyectos duplicados.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    grupos = df_dups["dup_key"].unique()
    st.warning(f"Hay {len(grupos)} grupos de posibles duplicados:")

    for g in grupos:
        grupo = df_dups[df_dups["dup_key"] == g]
        nombre = grupo.iloc[0].get("nombre_obra", "(sin nombre)")

        with st.expander(f"Duplicados – {nombre}"):
            cols = ["id", "nombre_obra", "cliente_principal", "ciudad",
                    "provincia", "estado", "fecha_creacion", "fecha_seguimiento"]
            cols = [c for c in cols if c in grupo.columns]
            st.dataframe(grupo[cols], hide_index=True, use_container_width=True)

            for _, row in grupo.iterrows():
                if st.button("🗑️ Borrar", key=f"dup_del_{row['id']}"):
                    delete_proyecto(row["id"])
                    st.success("Proyecto borrado.")
                    st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# =====================================================
# IMPORTAR / EXPORTAR
# =====================================================

def _render_import_export(df_proy_empty, df_proy=None):
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.subheader("📤 Exportar / 📥 Importar proyectos")

    if not df_proy_empty and df_proy is not None:
        st.markdown("#### Exportar Excel de obras importantes")
        importantes = filtrar_obras_importantes(df_proy)
        if importantes.empty:
            st.info("No hay obras importantes según los criterios definidos.")
        else:
            output = generar_excel_obras_importantes(df_proy)
            fecha_str = date.today().isoformat()
            st.download_button(
                "⬇️ Descargar Excel de obras importantes",
                data=output,
                file_name=f"obras_importantes_{fecha_str}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    st.markdown("#### Importar proyectos desde Excel generado con ChatGPT")
    st.caption(
        "Formato de fechas: dd/mm/aa o dd/mm/aaaa. "
        "El campo 'Promotora_Fondo' se usará como cliente principal (promotor)."
    )

    uploaded = st.file_uploader("Sube un archivo .xlsx", type=["xlsx"])

    if uploaded:
        try:
            prev = pd.read_excel(uploaded)
            st.write("Vista previa:")
            st.dataframe(prev.head(), use_container_width=True)

            if st.button("🚀 Importar estos proyectos"):
                creados = importar_proyectos_desde_excel(uploaded)
                st.success(f"Importación completada. Proyectos creados: {creados}")
                st.rerun()

        except Exception as e:
            st.error(f"Error leyendo el Excel: {e}")

    st.markdown("</div>", unsafe_allow_html=True)
