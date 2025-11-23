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
    """Página principal de Proyectos con interfaz más intuitiva."""
    inject_apple_style()

    # CABECERA
    st.markdown(
        """
        <div class="apple-card">
            <div class="section-badge">Proyectos</div>
            <h1 style="margin-top: 6px;">CRM de Proyectos</h1>
            <p style="color:#9FB3D1; margin-bottom: 0;">
                Vista unificada: filtros, pipeline, lista y detalle del proyecto en la misma pantalla.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_clientes = get_clientes()
    df_proy = get_proyectos()
    if df_proy is None:
        df_proy = pd.DataFrame()

    # Alta rápida arriba
    _bloque_alta_proyecto(df_clientes)

    if df_proy.empty:
        st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
        st.info("Todavía no hay proyectos creados en Firestore.")
        _render_import_export(df_proy_empty=True)
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # Pestañas: vista general + extras
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
    with st.expander("➕ Añadir nuevo proyecto"):
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
# FILTROS REUTILIZABLES
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
# VISTA GENERAL (LISTA + DETALLE)
# =====================================================

def _render_vista_general(df_proy: pd.DataFrame):
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.subheader("📂 Lista de proyectos + detalle")

    df_filtrado = _aplicar_filtros_basicos(df_proy, key_prefix="vista")

    if df_filtrado.empty:
        st.info("No hay proyectos que cumplan los filtros seleccionados.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # Pipeline métricas
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

    # Pipeline visual
    st.markdown("### 🔁 Pipeline visual Apple (clic para filtrar)", unsafe_allow_html=True)

    filtro_estado = st.session_state.get("vista_estado_pipeline", "Todos")
    if "estado" in df_filtrado.columns:
        counts = df_filtrado["estado"].value_counts()

        estado_cfg = {
            "Detectado":       ("⚪", "rgba(148,163,184,0.16)", "#E5E7EB"),
            "Seguimiento":     ("🔵", "rgba(59,130,246,0.16)", "#BFDBFE"),
            "En Prescripción": ("🟣", "rgba(129,140,248,0.16)", "#DDD6FE"),
            "Oferta Enviada":  ("🟡", "rgba(250,204,21,0.22)", "#FCD34D"),
            "Negociación":     ("🟠", "rgba(249,115,22,0.20)", "#FDBA74"),
            "Paralizado":      ("⚫", "rgba(107,114,128,0.16)", "#9CA3AF"),
            "Ganado":          ("🟢", "rgba(34,197,94,0.18)", "#86EFAC"),
            "Perdido":         ("🔴", "rgba(248,113,113,0.20)", "#FCA5A5"),
        }
        orden_estados = list(estado_cfg.keys())

        cols_pills = st.columns(len(orden_estados) + 1)

        with cols_pills[0]:
            if st.button("🔁 Todos", key="vista_pill_todos"):
                st.session_state["vista_estado_pipeline"] = "Todos"
                st.rerun()

        for idx, est in enumerate(orden_estados, start=1):
            emoji, bg, color = estado_cfg[est]
            count = int(counts.get(est, 0))
            style = (
                f"background:{bg};color:{color};border-radius:999px;"
                f"padding:6px 12px;font-size:0.80rem;font-weight:600;"
                f"cursor:pointer;border:1px solid transparent;"
            )
            if filtro_estado == est:
                style += "box-shadow:0 0 0 2px var(--pill-shadow);"
            pill_html = f"""
            <div style="{style}">
                {emoji} {est} <span style="margin-left:4px;"><b>{count}</b></span>
            </div>
            """
            with cols_pills[idx]:
                if st.button(" ", key=f"vista_pill_{est}"):
                    st.session_state["vista_estado_pipeline"] = est
                    st.rerun()
                st.markdown(pill_html, unsafe_allow_html=True)

        if filtro_estado != "Todos":
            st.caption(f"Filtro de pipeline activo: **{filtro_estado}**")
    else:
        st.caption("No hay estados definidos para este conjunto de proyectos.")

    # Aplicar filtro de pipeline a la lista
    if filtro_estado != "Todos" and "estado" in df_filtrado.columns:
        df_lista = df_filtrado[df_filtrado["estado"] == filtro_estado].copy()
    else:
        df_lista = df_filtrado.copy()

    if df_lista.empty:
        st.warning("No hay proyectos tras aplicar el filtro de pipeline.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    col_left, col_right = st.columns([1.25, 1.75])

    # Izquierda: tabla
    with col_left:
        st.markdown("#### 📋 Lista de proyectos", unsafe_allow_html=True)
        df_ui = df_lista.reset_index(drop=True).copy()
        ids = df_ui["id"].tolist()
        df_ui = df_ui.drop(columns=["id"])

        df_ui.insert(0, "Seleccionar", False)
        df_ui.insert(1, "Borrar", False)

        edited_df = st.data_editor(
            df_ui,
            column_config={
                "Seleccionar": st.column_config.CheckboxColumn(
                    "✔", help="Marca un proyecto para ver su detalle a la derecha"
                ),
                "Borrar": st.column_config.CheckboxColumn(
                    "🗑", help="Marca proyectos a eliminar"
                ),
            },
            hide_index=True,
            use_container_width=True,
            key="vista_tabla_proyectos",
        )

        seleccionados = edited_df["Seleccionar"]
        idx_sel = None
        for i, v in seleccionados.items():
            if v:
                idx_sel = i
                break

        if idx_sel is None:
            if "detalle_proyecto_id" in st.session_state:
                try:
                    idx_sel = df_lista.reset_index(drop=True).index[
                        df_lista.reset_index(drop=True)["id"] == st.session_state["detalle_proyecto_id"]
                    ][0]
                except Exception:
                    idx_sel = 0
            else:
                idx_sel = 0
        else:
            st.session_state["detalle_proyecto_id"] = ids[idx_sel]

        if st.button("🗑️ Eliminar proyectos marcados", key="vista_btn_borrar"):
            marcados = edited_df["Borrar"]
            if not marcados.any():
                st.warning("No hay proyectos marcados para borrar.")
            else:
                total = 0
                for i, marcado in marcados.items():
                    if marcado:
                        delete_proyecto(ids[i])
                        total += 1
                st.success(f"Proyectos eliminados: {total}")
                st.rerun()

    # Derecha: detalle
    with col_right:
        st.markdown("#### 🔍 Detalle del proyecto seleccionado", unsafe_allow_html=True)
        df_lista_reset = df_lista.reset_index(drop=True)
        if idx_sel < 0 or idx_sel >= len(df_lista_reset):
            idx_sel = 0
        proy = df_lista_reset.iloc[idx_sel]
        _panel_detalle_proyecto(proy)

    st.markdown("</div>", unsafe_allow_html=True)


# =====================================================
# PANEL DETALLE (USADO EN VISTA GENERAL)
# =====================================================

def _panel_detalle_proyecto(proy_row: pd.Series):
    proy = proy_row

    notas_historial = proy.get("notas_historial") or []
    tareas = proy.get("tareas") or []
    pasos = proy.get("pasos_seguimiento") or []

    st.markdown(
        f"**{proy.get('nombre_obra','(sin nombre)')}** – "
        f"{proy.get('cliente_principal','—')} ({proy.get('ciudad','—')})",
        unsafe_allow_html=True,
    )

    with st.form(f"form_detalle_inline_{proy['id']}"):
        col_a, col_b = st.columns(2)
        with col_a:
            nombre_det = st.text_input(
                "Nombre del proyecto",
                value=proy.get("nombre_obra", ""),
            )
            tipo_det = st.text_input(
                "Tipo de proyecto",
                value=proy.get("tipo_proyecto", ""),
            )
            promotor_det = st.text_input(
                "Promotor (cliente principal)",
                value=proy.get("cliente_principal", ""),
            )
            ciudad_det = st.text_input(
                "Ciudad",
                value=proy.get("ciudad", ""),
            )
            provincia_det = st.text_input(
                "Provincia",
                value=proy.get("provincia", ""),
            )
        with col_b:
            arquitectura_det = st.text_input(
                "Arquitectura",
                value=proy.get("arquitectura", ""),
            )
            ingenieria_det = st.text_input(
                "Ingeniería",
                value=proy.get("ingenieria", ""),
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
                "Paralizado",
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
            "Notas generales de seguimiento",
            value=proy.get("notas_seguimiento", ""),
        )

        st.markdown("##### 📝 Historial de notas", unsafe_allow_html=True)
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
                st.markdown(f"**[{tipo_txt}] {fecha_txt}**")
                st.write(texto_txt)
        else:
            st.caption("Todavía no hay notas históricas.")

        st.markdown("**Añadir nueva nota**")
        nueva_nota_tipo = st.selectbox(
            "Tipo de nota",
            ["Nota", "Llamada", "Reunión", "Visita", "Otro"],
            key=f"tipo_nota_inline_{proy['id']}",
        )
        nueva_nota_texto = st.text_area(
            "Texto de la nota",
            key=f"texto_nota_inline_{proy['id']}",
            placeholder="Ejemplo: Reunión con promotora, pendiente de memoria...",
        )

        st.markdown("##### ✅ Tareas", unsafe_allow_html=True)
        tareas_actualizadas = []
        if tareas:
            for i, t in enumerate(tareas):
                cols_t = st.columns([0.08, 0.52, 0.20, 0.20])
                with cols_t[0]:
                    completado = st.checkbox(
                        "",
                        value=t.get("completado", False),
                        key=f"chk_tarea_inline_{proy['id']}_{i}",
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

        st.markdown("**Añadir nueva tarea**")
        nueva_tarea_titulo = st.text_input(
            "Título de la tarea",
            key=f"titulo_tarea_inline_{proy['id']}",
            placeholder="Ejemplo: Llamar a la ingeniería...",
        )
        nueva_tarea_tipo = st.selectbox(
            "Tipo de tarea",
            ["Llamada", "Email", "Reunión", "Visita", "Otro"],
            key=f"tipo_tarea_inline_{proy['id']}",
        )
        nueva_tarea_fecha = st.date_input(
            "Fecha límite de la tarea",
            value=date.today(),
            key=f"fecha_tarea_inline_{proy['id']}",
        )

        st.markdown("##### 🧭 Checklist de pasos", unsafe_allow_html=True)
        estados_check_pasos = []
        if not pasos:
            if st.checkbox(
                "Crear checklist base",
                key=f"chk_crear_pasos_inline_{proy['id']}",
            ):
                pasos = default_pasos_seguimiento()
        if pasos:
            for i, paso in enumerate(pasos):
                chk = st.checkbox(
                    paso.get("nombre", f"Paso {i+1}"),
                    value=paso.get("completado", False),
                    key=f"detalle_chk_inline_{proy['id']}_{i}",
                )
                estados_check_pasos.append(chk)

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            guardar_det = st.form_submit_button("💾 Guardar cambios")
        with col_btn2:
            borrar_det = st.form_submit_button("🗑️ Borrar proyecto")

    if guardar_det:
        if nueva_nota_texto.strip():
            notas_historial.append(
                {
                    "fecha": datetime.utcnow().isoformat(timespec="seconds"),
                    "tipo": nueva_nota_tipo,
                    "texto": nueva_nota_texto.strip(),
                }
            )
        if tareas_actualizadas is None:
            tareas_actualizadas = []

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
        st.success("Cambios guardados.")
        st.rerun()

    if borrar_det:
        delete_proyecto(proy["id"])
        st.success("Proyecto borrado.")
        st.rerun()


# =====================================================
# DASHBOARD ANALÍTICO
# =====================================================

def _render_dashboard(df_proy: pd.DataFrame):
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.subheader("📈 Dashboard analítico de obras")

    df_filtrado = _aplicar_filtros_basicos(df_proy, key_prefix="dash")

    if df_filtrado.empty:
        st.info("No hay datos para mostrar con los filtros actuales.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    if "potencial_eur" not in df_filtrado.columns:
        df_filtrado["potencial_eur"] = 0

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
            "Agrupar por",
            agrupacion_opciones,
            index=0,
            key="dash_agrupacion",
        )
    with col_d2:
        metrica = st.radio(
            "Métrica",
            ["Número de obras", "Potencial total (€)"],
            key="dash_metrica",
        )

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
        if group_col not in df_plot.columns:
            st.info("No hay datos válidos para esta agrupación.")
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
    st.subheader("🧬 Detección de proyectos duplicados")

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
        st.success("No hay proyectos duplicados. ✅")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    grupos = df_dups["dup_key"].unique()
    st.warning(f"Hay {len(grupos)} grupos de proyectos duplicados.")
    st.caption("Revisa y elimina los que sobren.")

    for g in grupos:
        grupo = df_dups[df_dups["dup_key"] == g]
        nombre = grupo.iloc[0].get("nombre_obra", "Proyecto")

        with st.expander(f"Posibles duplicados – {nombre}"):
            cols_show = [
                "id", "nombre_obra", "cliente_principal", "ciudad",
                "provincia", "estado", "fecha_creacion", "fecha_seguimiento"
            ]
            cols_show = [c for c in cols_show if c in grupo.columns]
            st.dataframe(grupo[cols_show], hide_index=True, use_container_width=True)

            for _, row in grupo.iterrows():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(
                        f"• {row.get('nombre_obra','')} "
                        f"({row.get('cliente_principal','—')} – {row.get('ciudad','—')})"
                    )
                with col2:
                    if st.button("🗑️ Borrar", key=f"del_dup_{row['id']}"):
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
        importantes = filtrar_obras_importantes(df_proy)
        if importantes.empty:
            st.info("No hay obras importantes (prioridad Alta o potencial ≥ 50k).")
        else:
            output = generar_excel_obras_importantes(df_proy)
            fecha_str = date.today().isoformat()
            st.download_button(
                label=f"⬇️ Descargar Excel ({fecha_str})",
                data=output,
                file_name=f"obras_importantes_{fecha_str}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    st.markdown("#### Importar proyectos desde Excel (ChatGPT)")
    st.caption(
        "Sube el Excel que genera ChatGPT. "
        "Fechas formato dd/mm/aa o dd/mm/aaaa. "
        "La columna Promotora_Fondo se usará como cliente principal."
    )

    uploaded = st.file_uploader(
        "Subir archivo .xlsx",
        type=["xlsx"],
        key="uploader_import",
    )

    if uploaded is not None:
        try:
            df_preview = pd.read_excel(uploaded)
            st.write("Vista previa:")
            st.dataframe(df_preview.head(), use_container_width=True)

            if st.button("🚀 Importar proyectos"):
                creados = importar_proyectos_desde_excel(uploaded)
                st.success(f"Importación completada. Proyectos creados: {creados}")
                st.rerun()
        except Exception as e:
            st.error(f"Error leyendo el Excel: {e}")
    else:
        st.info("Sube un Excel para importarlo.")

    st.markdown("</div>", unsafe_allow_html=True)
