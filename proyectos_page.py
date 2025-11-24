import streamlit as st
import pandas as pd
import altair as alt
from datetime import date, datetime, timedelta

from crm_utils import (
    get_clientes,
    get_proyectos,
    add_proyecto,
    actualizar_proyecto,
    delete_proyecto,
    default_pasos_seguimiento,
    filtrar_obras_importantes,
    importar_proyectos_desde_excel,
    generar_excel_obras_importantes,
)


def _parse_fecha_iso(valor):
    if not valor:
        return None
    if isinstance(valor, date) and not isinstance(valor, datetime):
        return valor
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, str):
        try:
            return datetime.fromisoformat(valor).date()
        except Exception:
            return None
    return None


# =====================================================
# PÁGINA PRINCIPAL DE PROYECTOS
# =====================================================

def render_proyectos():
    st.markdown(
        """
        <div class="apple-card">
            <div class="section-badge">Proyectos</div>
            <h1 style="margin-top:4px; margin-bottom:4px;">Pipeline de prescripción</h1>
            <p style="color:#9CA3AF; margin-bottom:0; font-size:0.9rem;">
                Gestiona obras, estados de seguimiento y tareas vinculadas.
                Usa la vista analítica para ver dónde está el valor y la vista de tareas
                para no dejar ningún proyecto enfriarse.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_proy = get_proyectos()

    if df_proy is None or df_proy.empty:
        st.info("Todavía no hay proyectos guardados en Firestore.")
        _render_import_export(df_proy_empty=True)
        return

    tab_vista, tab_dash, tab_duplicados, tab_import, tab_alta = st.tabs(
        [
            "📁 Vista general",
            "📊 Dashboard analítico",
            "🧬 Duplicados",
            "📥 Importar / Exportar",
            "➕ Alta proyecto",
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

    with tab_alta:
        _render_alta_manual()


# =====================================================
# VISTA GENERAL (tabla + vistas rápidas)
# =====================================================

def _aplicar_filtros_basicos(df: pd.DataFrame, key_prefix: str):
    df = df.copy()

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


def _render_vista_general(df_proy: pd.DataFrame):
    st.markdown("### Pipeline y vista rápida")

    df_filtrado = _aplicar_filtros_basicos(df_proy, key_prefix="vista")

    # “Pastillas” de vista rápida
    try:
        vista = st.segmented_control(
            "Modo de vista",
            ["Tabla", "Seguimientos", "Tareas"],
            default="Tabla",
        )
    except Exception:
        vista = st.radio(
            "Modo de vista",
            ["Tabla", "Seguimientos", "Tareas"],
            horizontal=True,
        )

    if vista == "Tabla":
        _vista_tabla(df_filtrado)
    elif vista == "Seguimientos":
        _vista_seguimientos(df_filtrado)
    else:
        _vista_tareas(df_filtrado)


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

    df_ui = df_filtrado.reset_index(drop=True).copy()
    ids = df_ui["id"].tolist()
    df_ui = df_ui.drop(columns=["id"])

    # columna seleccionar
    df_ui.insert(0, "seleccionar", False)

    st.markdown(
        "<p style='font-size:0.82rem; color:#9CA3AF;'>Selecciona una obra y usa los botones inferiores para verla en detalle o borrarla.</p>",
        unsafe_allow_html=True,
    )

    edited_df = st.data_editor(
        df_ui,
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

    col_acc1, col_acc2 = st.columns(2)

    with col_acc1:
        if st.button("➡️ Ver proyecto seleccionado en detalle"):
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
                    st.success("Proyecto seleccionado. Ve a la pestaña '➕ Alta proyecto' si lo quieres editar.")
    with col_acc2:
        if st.button("🗑️ Borrar proyectos seleccionados"):
            if "seleccionar" not in edited_df.columns:
                st.error("No se ha encontrado la columna 'seleccionar'.")
            else:
                seleccionados = edited_df["seleccionar"]
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


def _vista_seguimientos(df_filtrado: pd.DataFrame):
    st.markdown("#### 🧭 Seguimientos por fecha")

    if df_filtrado.empty:
        st.info("No hay proyectos con los filtros actuales.")
        return

    hoy = date.today()

    registros = []
    for _, row in df_filtrado.iterrows():
        fecha_seg = _parse_fecha_iso(row.get("fecha_seguimiento"))
        if not fecha_seg:
            continue
        registros.append(
            {
                "id": row["id"],
                "Proyecto": row.get("nombre_obra", "Sin nombre"),
                "Cliente": row.get("cliente_principal", "—"),
                "Ciudad": row.get("ciudad", "—"),
                "Estado": row.get("estado", "Detectado"),
                "Fecha_seguimiento": fecha_seg,
                "Prioridad": row.get("prioridad", "Media"),
            }
        )

    if not registros:
        st.info("No hay fechas de seguimiento registradas en estos proyectos.")
        return

    df_seg = pd.DataFrame(registros)
    df_seg = df_seg.sort_values("Fecha_seguimiento")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.dataframe(
            df_seg[["Proyecto", "Cliente", "Ciudad", "Estado", "Fecha_seguimiento", "Prioridad"]],
            hide_index=True,
            use_container_width=True,
        )

    with col2:
        st.markdown("##### Acciones rápidas")
        st.caption("Selecciona una obra abajo para posponer 1 semana su seguimiento.")

        opciones = {
            f"{r['Proyecto']} ({r['Fecha_seguimiento'].strftime('%d/%m/%y')})": r["id"]
            for _, r in df_seg.iterrows()
        }
        if opciones:
            seleccion = st.selectbox("Proyecto", list(opciones.keys()))
            if st.button("⏰ Posponer 1 semana"):
                proy_id = opciones[seleccion]
                nueva_fecha = (hoy + timedelta(days=7)).isoformat()
                try:
                    actualizar_proyecto(proy_id, {"fecha_seguimiento": nueva_fecha})
                    st.success(f"Seguimiento pospuesto a {nueva_fecha}.")
                    st.rerun()
                except Exception as e:
                    st.error(f"No se pudo actualizar: {e}")


def _vista_tareas(df_filtrado: pd.DataFrame):
    st.markdown("#### ✅ Tareas abiertas por proyecto")

    registros = []

    for _, row in df_filtrado.iterrows():
        tareas = row.get("tareas") or []
        for t in tareas:
            fecha_lim = _parse_fecha_iso(t.get("fecha_limite"))
            registros.append(
                {
                    "Proyecto": row.get("nombre_obra", "Sin nombre"),
                    "Cliente": row.get("cliente_principal", "—"),
                    "Ciudad": row.get("ciudad", "—"),
                    "Título": t.get("titulo", "(sin título)"),
                    "Tipo": t.get("tipo", "Tarea"),
                    "Fecha_límite": fecha_lim,
                    "Completada": bool(t.get("completado", False)),
                }
            )

    if not registros:
        st.info("Todavía no hay tareas registradas en los proyectos.")
        return

    df_t = pd.DataFrame(registros)
    df_t = df_t.sort_values(["Completada", "Fecha_límite"], ascending=[True, True])

    st.dataframe(
        df_t,
        hide_index=True,
        use_container_width=True,
    )


# =====================================================
# DASHBOARD ANALÍTICO
# =====================================================

def _render_dashboard(df_proy: pd.DataFrame):
    st.subheader("📈 Dashboard de obras")

    df_filtrado = _aplicar_filtros_basicos(df_proy, key_prefix="dash")

    if df_filtrado.empty:
        st.info("No hay datos para mostrar en el dashboard con estos filtros.")
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


# =====================================================
# DUPLICADOS
# =====================================================

def _render_duplicados(df_proy: pd.DataFrame):
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
        st.success(
            "No se han detectado proyectos duplicados por nombre + cliente + ciudad + provincia. ✅"
        )
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


# =====================================================
# IMPORTAR / EXPORTAR
# =====================================================

def _render_import_export(df_proy_empty: bool, df_proy=None):
    st.subheader("📤 Exportar / 📥 Importar")

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
        "Sube el Excel que te genero desde ChatGPT. "
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


# =====================================================
# ALTA MANUAL
# =====================================================

def _render_alta_manual():
    st.subheader("➕ Alta manual de proyecto")

    df_clientes = get_clientes()
    nombres_clientes = ["(sin asignar)"]
    if df_clientes is not None and not df_clientes.empty and "empresa" in df_clientes.columns:
        nombres_clientes += sorted(df_clientes["empresa"].dropna().unique().tolist())

    with st.form("form_proyecto_alta"):
        col1, col2 = st.columns(2)
        with col1:
            nombre_obra = st.text_input("Nombre del proyecto / obra")
            cliente_principal = st.selectbox(
                "Cliente principal (promotor)",
                nombres_clientes,
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
                    "estado": "Detectado",
                    "fecha_seguimiento": fecha_seg.isoformat(),
                    "notas_seguimiento": notas,
                    "notas_historial": [],
                    "tareas": [],
                }
            )
            st.success("Proyecto creado correctamente.")
            st.rerun()
