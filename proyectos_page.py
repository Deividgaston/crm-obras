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


def render_proyectos():
    # Activamos estilo Apple
    inject_apple_style()

    # Cabecera estilo Apple
    st.markdown(
        """
        <div class="apple-card">
            <div class="section-badge">Proyectos</div>
            <h1 style="margin-top: 6px;">CRM de Proyectos</h1>
            <p style="color:#6B7280; margin-bottom: 0;">
                Gestiona todo el pipeline de obras: detección, prescripción, oferta, negociación,
                ganadas y perdidas. Alta rápida, dashboard y control de duplicados.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # =============== CLIENTES PARA ALTA RÁPIDA ===============
    df_clientes = get_clientes()
    nombres_clientes = ["(sin asignar)"]
    if not df_clientes.empty and "empresa" in df_clientes.columns:
        nombres_clientes += sorted(df_clientes["empresa"].dropna().unique().tolist())

    # =============== ALTA MANUAL DE PROYECTOS ===============
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    with st.expander("➕ Añadir nuevo proyecto manualmente"):
        with st.form("form_proyecto"):
            col1, col2 = st.columns(2)
            with col1:
                nombre_obra = st.text_input("Nombre del proyecto / obra")
                cliente_principal = st.selectbox(
                    "Cliente principal (normalmente promotor)", nombres_clientes
                )
                tipo_proyecto = st.selectbox(
                    "Tipo de proyecto",
                    ["Residencial lujo", "Residencial", "Oficinas", "Hotel", "BTR", "Otro"],
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
                estado_inicial = "Detectado"
                fecha_seg = st.date_input(
                    "Primera fecha de seguimiento", value=date.today()
                )

            notas = st.text_area("Notas iniciales (fuente del proyecto, link, etc.)")

            guardar_proy = st.form_submit_button("Guardar proyecto")

        if guardar_proy:
            if not nombre_obra:
                st.warning("El nombre del proyecto es obligatorio.")
            else:
                promotor_nombre = (
                    None if cliente_principal == "(sin asignar)" else cliente_principal
                )
                if promotor_nombre:
                    ensure_cliente_basico(promotor_nombre, "Promotora")
                ensure_cliente_basico(arquitectura or None, "Arquitectura")
                ensure_cliente_basico(ingenieria or None, "Ingeniería")

                add_proyecto(
                    {
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
                    }
                )
                st.success("Proyecto creado correctamente.")
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # =============== DATOS DE PROYECTOS ===============
    df_proy = get_proyectos()

    if df_proy.empty:
        st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
        st.info("Todavía no hay proyectos guardados en Firestore.")
        _render_import_export(df_proy_empty=True)
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # =============== PESTAÑAS ===============
    tab_dash, tab_resumen, tab_detalle, tab_duplicados, tab_import = st.tabs(
        [
            "📈 Dashboard",
            "📋 Lista / Resumen",
            "🔍 Detalle",
            "🧬 Duplicados",
            "📥 Importar / Exportar",
        ]
    )

    with tab_dash:
        _render_dashboard(df_proy)

    with tab_resumen:
        _render_resumen(df_proy)

    with tab_detalle:
        _render_detalle_proyecto(df_proy)

    with tab_duplicados:
        _render_duplicados(df_proy)

    with tab_import:
        _render_import_export(df_proy_empty=False, df_proy=df_proy)


# =====================================================
# FILTROS COMUNES
# =====================================================
def _aplicar_filtros_basicos(df: pd.DataFrame, key_prefix: str):
    """
    Devuelve df_filtrado usando los mismos filtros básicos,
    pero con keys únicos por pestaña gracias al key_prefix.
    """
    df = df.copy()

    st.markdown("##### 🎯 Filtros rápidos", unsafe_allow_html=True)
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    ciudades = (
        sorted(df["ciudad"].dropna().unique().tolist())
        if "ciudad" in df.columns
        else []
    )
    with col_f1:
        ciudad_sel = st.selectbox(
            "Ciudad",
            ["Todas"] + ciudades,
            key=f"{key_prefix}_ciudad",
        )

    estados_list = (
        sorted(df["estado"].dropna().unique().tolist())
        if "estado" in df.columns
        else []
    )
    with col_f2:
        estado_sel = st.selectbox(
            "Estado / Seguimiento",
            ["Todos"] + estados_list,
            key=f"{key_prefix}_estado",
        )

    tipos_list = (
        sorted(df["tipo_proyecto"].dropna().unique().tolist())
        if "tipo_proyecto" in df.columns
        else []
    )
    with col_f3:
        tipo_sel = st.selectbox(
            "Tipo de proyecto",
            ["Todos"] + tipos_list,
            key=f"{key_prefix}_tipo",
        )

    prioridades = (
        sorted(df["prioridad"].dropna().unique().tolist())
        if "prioridad" in df.columns
        else []
    )
    with col_f4:
        prioridad_sel = st.selectbox(
            "Prioridad",
            ["Todas"] + prioridades,
            key=f"{key_prefix}_prioridad",
        )

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
    return df_filtrado


# =====================================================
# DASHBOARD
# =====================================================
def _render_dashboard(df_proy: pd.DataFrame):
    st.markdown(
        '<div class="apple-card-light">',
        unsafe_allow_html=True,
    )
    st.subheader("📈 Dashboard de obras")

    # Prefijo "dash" para las keys de los filtros
    df_filtrado = _aplicar_filtros_basicos(df_proy, key_prefix="dash")

    if df_filtrado.empty:
        st.info("No hay datos para mostrar en el dashboard con estos filtros.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    if "potencial_eur" not in df_filtrado.columns:
        df_filtrado["potencial_eur"] = 0.0

    agrupacion_opciones = [
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

    col_d1, col_d2 = st.columns([2, 1])
    with col_d1:
        agrupacion = st.selectbox(
            "Agrupar por", agrupacion_opciones, index=0, key="dash_agrupacion"
        )
    with col_d2:
        metrica = st.radio(
            "Métrica",
            ["Número de obras", "Potencial total (€)"],
            horizontal=False,
            key="dash_metrica",
        )

    df_plot = df_filtrado.copy()

    if agrupacion == "Rango de potencial (€)":
        potencial = df_plot["potencial_eur"].fillna(0)
        bins = [0, 50000, 100000, 200000, 500000, 1_000_000_000]
        labels = ["< 50k", "50k-100k", "100k-200k", "200k-500k", "> 500k"]
        df_plot["rango_potencial"] = pd.cut(
            potencial, bins=bins, labels=labels, include_lowest=True
        )
        group_col = "rango_potencial"
        titulo_eje = "Rango de potencial (€)"
    else:
        group_col = dim_map.get(agrupacion)
        if group_col not in df_plot.columns:
            st.info("No hay datos suficientes para esta agrupación.")
            st.markdown("</div>", unsafe_allow_html=True)
            return
        titulo_eje = agrupacion

    agg_df = (
        df_plot.groupby(group_col)
        .agg(
            num_obras=("id", "count"),
            potencial_total=("potencial_eur", "sum"),
        )
        .reset_index()
    )

    if agg_df.empty:
        st.info("No hay datos para esta agrupación.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    if metrica == "Número de obras":
        y_field = "num_obras"
        y_title = "Número de obras"
    else:
        y_field = "potencial_total"
        y_title = "Potencial total (€)"

    chart = (
        alt.Chart(agg_df)
        .mark_bar()
        .encode(
            x=alt.X(f"{group_col}:N", sort="-y", title=titulo_eje),
            y=alt.Y(f"{y_field}:Q", title=y_title),
            tooltip=[group_col, "num_obras", "potencial_total"],
        )
        .properties(height=350)
    )

    st.altair_chart(chart, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# =====================================================
# LISTA / RESUMEN: pipeline + tabla + seleccionar/borrar
# =====================================================
def _render_resumen(df_proy: pd.DataFrame):
    # Pipeline
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.subheader("📋 Resumen y lista de proyectos")

    # Prefijo "res" para filtros de esta pestaña
    df_filtrado = _aplicar_filtros_basicos(df_proy, key_prefix="res")

    st.markdown("### 🧪 Pipeline (conteo por estado)", unsafe_allow_html=True)
    if not df_filtrado.empty and "estado" in df_filtrado.columns:
        estados = [
            "Detectado",
            "Seguimiento",
            "En Prescripción",
            "Oferta Enviada",
            "Negociación",
            "Ganado",
            "Perdido",
        ]
        counts = df_filtrado["estado"].value_counts()
        cols_pipe = st.columns(len(estados))
        for col, est in zip(cols_pipe, estados):
            col.metric(est, int(counts.get(est, 0)))
    else:
        st.info("No hay información de estados con los filtros aplicados.")

    st.markdown("</div>", unsafe_allow_html=True)

    # Tabla
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.markdown("### 📂 Lista de proyectos filtrados", unsafe_allow_html=True)

    if df_filtrado.empty:
        st.warning("No hay proyectos que cumplan los filtros seleccionados.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    df_ui = df_filtrado.reset_index(drop=True).copy()
    ids = df_ui["id"].tolist()
    df_ui = df_ui.drop(columns=["id"])

    df_ui.insert(0, "seleccionar", False)
    df_ui.insert(1, "borrar", False)

    edited_df = st.data_editor(
        df_ui,
        column_config={
            "seleccionar": st.column_config.CheckboxColumn(
                "Seleccionar",
                help="Selecciona una obra y pulsa 'Ver en Detalle'",
                default=False,
            ),
            "borrar": st.column_config.CheckboxColumn(
                "Borrar",
                help="Marca proyectos y pulsa 'Eliminar seleccionados'",
                default=False,
            ),
        },
        hide_index=True,
        use_container_width=True,
        key="tabla_proyectos_editor",
    )

    col_acc1, col_acc2 = st.columns(2)

    with col_acc1:
        if st.button("➡️ Ver proyecto seleccionado en Detalle"):
            if "seleccionar" not in edited_df.columns:
                st.error("No se ha encontrado la columna 'seleccionar'.")
            else:
                seleccionados = edited_df["seleccionar"]
                idxs = [i for i, v in seleccionados.items() if v]
                if not idxs:
                    st.warning("No hay ninguna obra seleccionada.")
                else:
                    idx = idxs[0]
                    st.session_state["detalle_proyecto_id"] = ids[idx]
                    st.success(
                        "Proyecto seleccionado. Ve a la pestaña 'Detalle' para verlo."
                    )

    with col_acc2:
        if st.button("🗑️ Eliminar seleccionados"):
            if "borrar" not in edited_df.columns:
                st.error("No se ha encontrado la columna 'borrar'.")
            else:
                seleccionados = edited_df["borrar"]
                if not seleccionados.any():
                    st.warning("No hay proyectos marcados para borrar.")
                else:
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

    st.markdown("</div>", unsafe_allow_html=True)


# =====================================================
# DETALLE + TIMELINE + TAREAS + CHECKLIST
# =====================================================
def _render_detalle_proyecto(df_proy: pd.DataFrame):
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.subheader("🔍 Detalle y edición de un proyecto")

    df_proy_sorted = (
        df_proy.sort_values("fecha_creacion", ascending=False)
        .reset_index(drop=True)
    )

    if df_proy_sorted.empty:
        st.info("No hay proyectos para mostrar en detalle.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    if "detalle_proyecto_id" in st.session_state:
        detalle_id = st.session_state["detalle_proyecto_id"]
        try:
            idx_from_id = df_proy_sorted.index[df_proy_sorted["id"] == detalle_id][0]
            st.session_state["detalle_select"] = idx_from_id
        except Exception:
            if "detalle_select" not in st.session_state:
                st.session_state["detalle_select"] = 0

    if "detalle_select" in st.session_state:
        if st.session_state["detalle_select"] >= len(df_proy_sorted):
            st.session_state["detalle_select"] = 0

    opciones = [
        f"{r['nombre_obra']} – {r.get('cliente_principal','—')} ({r.get('ciudad','—')})"
        for _, r in df_proy_sorted.iterrows()
    ]

    idx_sel = st.selectbox(
        "Selecciona un proyecto para ver/editar el detalle",
        options=list(range(len(df_proy_sorted))),
        format_func=lambda i: opciones[i] if 0 <= i < len(opciones) else "",
        key="detalle_select",
    )

    proy = df_proy_sorted.iloc[idx_sel]
    st.markdown(
        f"#### Proyecto seleccionado: **{proy['nombre_obra']}**",
        unsafe_allow_html=True,
    )

    notas_historial = proy.get("notas_historial") or []
    tareas = proy.get("tareas") or []
    pasos = proy.get("pasos_seguimiento") or []

    with st.form(f"form_detalle_{proy['id']}"):
        col_a, col_b = st.columns(2)
        with col_a:
            nombre_det = st.text_input(
                "Nombre del proyecto", value=proy.get("nombre_obra", "")
            )
            tipo_det = st.text_input(
                "Tipo de proyecto", value=proy.get("tipo_proyecto", "")
            )
            promotor_det = st.text_input(
                "Promotor (cliente principal)", value=proy.get("cliente_principal", "")
            )
            ciudad_det = st.text_input("Ciudad", value=proy.get("ciudad", ""))
            provincia_det = st.text_input(
                "Provincia", value=proy.get("provincia", "")
            )
        with col_b:
            arquitectura_det = st.text_input(
                "Arquitectura", value=proy.get("arquitectura", "")
            )
            ingenieria_det = st.text_input(
                "Ingeniería", value=proy.get("ingenieria", "")
            )
            prioridad_det = st.selectbox(
                "Prioridad",
                ["Alta", "Media", "Baja"],
                index=["Alta", "Media", "Baja"].index(
                    proy.get("prioridad", "Media")
                    if proy.get("prioridad") in ["Alta", "Media", "Baja"]
                    else "Media"
                ),
            )
            potencial_det = st.number_input(
                "Potencial 2N (€)",
                min_value=0.0,
                step=10000.0,
                value=float(proy.get("potencial_eur", 0.0))
                if proy.get("potencial_eur") is not None
                else 0.0,
            )
            estados_posibles = [
                "Detectado",
                "Seguimiento",
                "En Prescripción",
                "Oferta Enviada",
                "Negociación",
                "Ganado",
                "Perdido",
            ]
            estado_actual = proy.get("estado", "Detectado")
            if estado_actual not in estados_posibles:
                estado_actual = "Detectado"
            estado_det = st.selectbox(
                "Estado",
                estados_posibles,
                index=estados_posibles.index(estado_actual),
            )

        fecha_seg_det = st.date_input(
            "Próxima fecha de seguimiento",
            value=proy.get("fecha_seguimiento") or date.today(),
        )
        notas_det = st.text_area(
            "Notas generales de seguimiento", value=proy.get("notas_seguimiento", "")
        )

        # Historial de notas
        st.markdown("##### 📝 Historial de notas del proyecto", unsafe_allow_html=True)
        if notas_historial:
            try:
                notas_historial_sorted = sorted(
                    notas_historial,
                    key=lambda x: x.get("fecha", ""),
                    reverse=True,
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
            placeholder="Ejemplo: Llamada con la promotora, pendiente de enviar oferta...",
        )

        # Tareas
        st.markdown("##### ✅ Tareas asociadas al proyecto", unsafe_allow_html=True)
        tareas_actualizadas = []
        if tareas:
            for i, tarea in enumerate(tareas):
                cols_t = st.columns([0.05, 0.45, 0.25, 0.25])
                with cols_t[0]:
                    completado = st.checkbox(
                        "",
                        value=tarea.get("completado", False),
                        key=f"chk_tarea_{proy['id']}_{i}",
                    )
                with cols_t[1]:
                    st.write(tarea.get("titulo", "(sin título)"))
                with cols_t[2]:
                    st.write(tarea.get("fecha_limite", ""))
                with cols_t[3]:
                    st.write(tarea.get("tipo", "Tarea"))
                tareas_actualizadas.append(
                    {
                        "titulo": tarea.get("titulo", ""),
                        "fecha_limite": tarea.get("fecha_limite", None),
                        "completado": completado,
                        "tipo": tarea.get("tipo", "Tarea"),
                    }
                )
        else:
            st.caption("No hay tareas creadas todavía.")

        st.markdown("**Añadir nueva tarea**")
        nueva_tarea_titulo = st.text_input(
            "Título de la tarea",
            key=f"titulo_tarea_{proy['id']}",
            placeholder="Ejemplo: Llamar a la ingeniería para revisar planos...",
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

        # Checklist de pasos
        st.markdown("##### 🧭 Checklist de pasos de seguimiento", unsafe_allow_html=True)
        estados_check_pasos = []
        if not pasos:
            if st.checkbox(
                "Crear checklist base para este proyecto",
                key=f"chk_crear_pasos_{proy['id']}",
            ):
                pasos = default_pasos_seguimiento()
        if pasos:
            for i, paso in enumerate(pasos):
                chk = st.checkbox(
                    paso.get("nombre", f"Paso {i+1}"),
                    value=paso.get("completado", False),
                    key=f"detalle_chk_{proy['id']}_{i}",
                )
                estados_check_pasos.append(chk)

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            guardar_det = st.form_submit_button(
                "💾 Guardar cambios (datos, notas, tareas)"
            )
        with col_btn2:
            borrar_det = st.form_submit_button("🗑️ Borrar este proyecto")

    if guardar_det:
        if nueva_nota_texto.strip():
            notas_historial.append(
                {
                    "fecha": datetime.utcnow().isoformat(timespec="seconds"),
                    "tipo": nueva_nota_tipo,
                    "texto": nueva_nota_texto.strip(),
                }
            )

        if nueva_tarea_titulo.strip():
            tareas_actualizadas.append(
                {
                    "titulo": nueva_tarea_titulo.strip(),
                    "fecha_limite": nueva_tarea_fecha.isoformat(),
                    "completado": False,
                    "tipo": nueva_tarea_tipo,
                }
            )

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
        st.success(
            "Cambios guardados en el proyecto (datos, notas, tareas y pasos)."
        )
        st.rerun()

    if borrar_det:
        delete_proyecto(proy["id"])
        st.success("Proyecto borrado.")
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
# =====================================================
# DUPLICADOS
# =====================================================
def _render_duplicados(df_proy: pd.DataFrame):
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.subheader("🧬 Revisión de posibles proyectos duplicados")

    df_tmp = df_proy.copy()
    key_cols_all = ["nombre_obra", "cliente_principal", "ciudad", "provincia"]
    key_cols = [c for c in key_cols_all if c in df_tmp.columns]

    if not key_cols:
        st.info("No hay suficientes campos para detectar duplicados automáticamente.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    df_tmp["dup_key"] = df_tmp[key_cols].astype(str).agg(" | ".join, axis=1)
    duplicated_mask = df_tmp["dup_key"].duplicated(keep=False)
    df_dups = df_tmp[duplicated_mask].copy()

    if df_dups.empty:
        st.success(
            "No se han detectado proyectos duplicados por nombre + cliente + ciudad + provincia. ✅"
        )
        st.markdown("</div>", unsafe_allow_html=True)
        return

    grupos = df_dups["dup_key"].unique()
    st.warning(
        f"Se han detectado {len(grupos)} grupos de proyectos que podrían estar duplicados."
    )
    st.caption("Revisa y borra los que sobren para mantener limpio el CRM.")

    for g in grupos:
        grupo_df = df_dups[df_dups["dup_key"] == g]
        titulo = grupo_df.iloc[0].get("nombre_obra", "Proyecto sin nombre")
        with st.expander(f"Posibles duplicados: {titulo}"):
            show_cols = [
                "id",
                "nombre_obra",
                "cliente_principal",
                "ciudad",
                "provincia",
                "estado",
                "fecha_creacion",
                "fecha_seguimiento",
            ]
            show_cols = [c for c in show_cols if c in grupo_df.columns]
            st.dataframe(
                grupo_df[show_cols], hide_index=True, use_container_width=True
            )

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

    st.markdown("</div>", unsafe_allow_html=True)


# =====================================================
# IMPORTAR / EXPORTAR
# =====================================================
def _render_import_export(df_proy_empty: bool, df_proy=None):
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.subheader("📤 Exportar / 📥 Importar proyectos")

    if not df_proy_empty and df_proy is not None:
        st.markdown("#### Exportar Excel de obras importantes")
        df_importantes = filtrar_obras_importantes(df_proy)
        if df_importantes.empty:
            st.info(
                "No hay obras importantes según criterios (prioridad Alta o potencial ≥ 50k€)."
            )
        else:
            output = generar_excel_obras_importantes(df_proy)
            fecha_str = date.today().isoformat()
            st.download_button(
                label=f"⬇️ Descargar Excel obras importantes ({fecha_str})",
                data=output,
                file_name=f"obras_importantes_{fecha_str}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    st.markdown("#### Importar proyectos desde Excel (ChatGPT)")
    st.caption(
        "Sube el Excel que te genera ChatGPT. "
        "Formato de fechas: 30/11/25 o 30/11/2025 (dd/mm/aa). "
        "El campo Promotora_Fondo se usará como cliente principal (promotor)."
    )

    uploaded_file = st.file_uploader(
        "Sube aquí el archivo .xlsx con los proyectos",
        type=["xlsx"],
        key="uploader_import",
    )

    if uploaded_file is not None:
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

    st.markdown("</div>", unsafe_allow_html=True)

