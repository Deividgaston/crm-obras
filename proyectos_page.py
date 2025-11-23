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
    ensure_cliente_basico,
    filtrar_obras_importantes,
    importar_proyectos_desde_excel,
    generar_excel_obras_importantes,
)


# =====================================================
# PÁGINA PRINCIPAL DE PROYECTOS
# =====================================================

def render_proyectos():
    st.markdown(
        """
        <div class="apple-card">
            <div class="section-badge">Pipeline</div>
            <h3 style="margin-top: 6px; font-size:1.25rem;">Proyectos & obras</h3>
            <p style="color:#9FB3D1; margin-bottom: 0; font-size:0.85rem;">
                Gestiona tu funnel de prescripción: vista general, análisis, duplicados e importación
                masiva de proyectos detectados con ChatGPT.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_proy = get_proyectos()

    tab_lista, tab_dash, tab_duplicados, tab_import, tab_alta = st.tabs(
        [
            "📂 Vista general",
            "📈 Dashboard analítico",
            "🧬 Duplicados",
            "📥 Importar / Exportar",
            "➕ Añadir proyecto",
        ]
    )

    with tab_lista:
        _render_resumen(df_proy)

    with tab_dash:
        _render_dashboard(df_proy)

    with tab_duplicados:
        _render_duplicados(df_proy)

    with tab_import:
        _render_import_export(df_proy_empty=df_proy is None or df_proy.empty, df_proy=df_proy)

    with tab_alta:
        _render_alta_manual()


# =====================================================
# FILTROS COMUNES (con prefijo de key para evitar duplicados)
# =====================================================

def _aplicar_filtros_basicos(df: pd.DataFrame, key_prefix: str):
    """
    Devuelve df_filtrado usando los mismos filtros básicos,
    pero con keys únicos por pestaña gracias al key_prefix.
    """
    if df is None or df.empty:
        return df

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


# =====================================================
# VISTA GENERAL: pipeline + tabla + acciones
# =====================================================

def _render_resumen(df_proy: pd.DataFrame):
    st.markdown(
        """
        <div class="apple-card-light">
            <div class="section-badge">Vista general</div>
            <h4 style="margin-top:8px; margin-bottom:4px; font-size:1.0rem;">📂 Pipeline y lista de proyectos</h4>
            <p style="color:#9CA3AF; margin-top:0; font-size:0.8rem;">
                Filtra por ciudad, estado, tipo y prioridad. Selecciona proyectos para ver detalle rápido,
                editar o borrar desde la tabla.
            </p>
        """,
        unsafe_allow_html=True,
    )

    if df_proy is None or df_proy.empty:
        st.info("Todavía no hay proyectos guardados en Firestore.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # --- Filtros básicos ---
    df_filtrado = _aplicar_filtros_basicos(df_proy, key_prefix="res")
    if df_filtrado is None or df_filtrado.empty:
        st.warning("No hay proyectos que cumplan los filtros seleccionados.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # --- Métricas pipeline por estado ---
    st.markdown("##### 🧪 Pipeline por estado")
    if "estado" in df_filtrado.columns:
        estados_orden = [
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
        cols_pipe = st.columns(len(estados_orden))
        for col, est in zip(cols_pipe, estados_orden):
            col.metric(est, int(counts.get(est, 0)))
    else:
        st.info("No hay información de estados con los filtros aplicados.")

    st.markdown("---")

    # --- Tabla principal ---
    st.markdown("##### 📋 Lista de proyectos filtrados")

    # Acciones (iconos) encima de la tabla
    col_acc1, col_acc2, col_acc3, _ = st.columns([0.25, 0.25, 0.25, 0.25])
    with col_acc1:
        ver_detalle_btn = st.button("🔍 Ver detalle rápido", key="btn_ver_detalle")
    with col_acc2:
        editar_btn = st.button("✏️ Editar seleccionado", key="btn_editar")
    with col_acc3:
        borrar_btn = st.button("🗑️ Borrar seleccionados", key="btn_borrar")

    df_ui = df_filtrado.reset_index(drop=True).copy()
    ids = df_ui["id"].tolist()

    # Columnas relevantes
    cols_mostrar = [
        "nombre_obra",
        "cliente_principal",
        "ciudad",
        "provincia",
        "tipo_proyecto",
        "prioridad",
        "potencial_eur",
        "estado",
        "fecha_seguimiento",
    ]
    cols_mostrar = [c for c in cols_mostrar if c in df_ui.columns]

    df_ui = df_ui[cols_mostrar]
    df_ui.insert(0, "seleccionar", False)

    edited_df = st.data_editor(
        df_ui,
        column_config={
            "seleccionar": st.column_config.CheckboxColumn(
                "Seleccionar",
                help="Marca la obra para ver detalle, editar o borrar.",
                default=False,
            ),
        },
        hide_index=True,
        use_container_width=True,
        key="tabla_proyectos_editor",
    )

    # Índices seleccionados
    if "seleccionar" in edited_df.columns:
        idxs_seleccionados = [
            i for i, v in edited_df["seleccionar"].items() if v
        ]
    else:
        idxs_seleccionados = []

    # ---- Acción: Ver detalle rápido (simplemente marca el proyecto seleccionado) ----
    if ver_detalle_btn:
        if not idxs_seleccionados:
            st.warning("Selecciona primero al menos un proyecto en la tabla.")
        else:
            idx = idxs_seleccionados[0]
            st.session_state["quick_view_proyecto_id"] = ids[idx]
            st.session_state["edit_modal_proyecto_id"] = None  # cerramos modal si hubiese
            st.success("Proyecto seleccionado para detalle rápido (ver tarjeta inferior).")

    # ---- Acción: Editar -> abre 'modal' flotante ----
    if editar_btn:
        if not idxs_seleccionados:
            st.warning("Selecciona primero un proyecto para editar.")
        else:
            idx = idxs_seleccionados[0]
            st.session_state["edit_modal_proyecto_id"] = ids[idx]
            st.session_state["quick_view_proyecto_id"] = ids[idx]

    # ---- Acción: Borrar ----
    if borrar_btn:
        if not idxs_seleccionados:
            st.warning("No hay proyectos marcados para borrar.")
        else:
            total = 0
            for row_idx in idxs_seleccionados:
                try:
                    delete_proyecto(ids[row_idx])
                    total += 1
                except Exception as e:
                    st.error(f"No se pudo borrar un proyecto: {e}")
            st.success(f"Proyectos eliminados: {total}")
            st.experimental_rerun()

    # ---- Tarjeta de detalle rápido / modal de edición ----
    proy_id = st.session_state.get("quick_view_proyecto_id")
    edit_id = st.session_state.get("edit_modal_proyecto_id")

    if proy_id:
        _render_quick_detail_and_modal(df_proy, proy_id, is_edit_mode=bool(edit_id))

    st.markdown("</div>", unsafe_allow_html=True)


def _render_quick_detail_and_modal(df_proy: pd.DataFrame, proyecto_id: str, is_edit_mode: bool):
    """
    Tarjeta inferior con detalle rápido.
    Si is_edit_mode=True, muestra formulario editable tipo modal
    dentro de la misma tarjeta.
    """
    if df_proy is None or df_proy.empty:
        return
    try:
        row = df_proy[df_proy["id"] == proyecto_id].iloc[0]
    except Exception:
        return

    st.markdown("---")
    st.markdown(
        """
        <div class="apple-card-light">
            <div class="section-badge">Detalle rápido</div>
        """,
        unsafe_allow_html=True,
    )

    # Datos básicos
    col_a, col_b = st.columns([1.4, 1])
    with col_a:
        st.markdown(
            f"**{row.get('nombre_obra', 'Sin nombre')}**  "
            f"· {row.get('tipo_proyecto','—')}  ",
        )
        st.caption(
            f"{row.get('cliente_principal','—')} · "
            f"{row.get('ciudad','—')} ({row.get('provincia','—')})"
        )
    with col_b:
        st.caption("Estado / prioridad")
        st.write(
            f"Estado: **{row.get('estado','—')}** · "
            f"Prioridad: **{row.get('prioridad','—')}**"
        )
        st.write(f"Potencial 2N: **{row.get('potencial_eur', 0):,.0f} €**".replace(",", "."))

    st.markdown("-----")

    # Si NO estamos en modo edición -> solo mostramos notas y próxima fecha
    if not is_edit_mode:
        st.markdown("**Próxima acción**")
        fecha_seg = row.get("fecha_seguimiento") or date.today()
        if isinstance(fecha_seg, str):
            try:
                fecha_seg = datetime.fromisoformat(fecha_seg).date()
            except Exception:
                fecha_seg = date.today()

        st.write(f"Próxima fecha de seguimiento: **{fecha_seg}**")
        st.write("Notas de seguimiento:")
        st.write(row.get("notas_seguimiento", "—"))

        if st.button("✏️ Editar este proyecto", key=f"btn_modal_{proyecto_id}"):
            st.session_state["edit_modal_proyecto_id"] = proyecto_id
            st.experimental_rerun()

        st.markdown("</div>", unsafe_allow_html=True)
        return

    # -------- MODO EDICIÓN (MODAL) --------
    st.markdown(
        "<p style='font-size:0.85rem; color:#9CA3AF;'>Edición rápida del proyecto. "
        "Para cambios más profundos podrás ampliarlo más adelante.</p>",
        unsafe_allow_html=True,
    )

    with st.form(f"form_modal_{proyecto_id}"):
        c1, c2 = st.columns(2)
        with c1:
            nombre_det = st.text_input(
                "Nombre del proyecto", value=row.get("nombre_obra", "")
            )
            tipo_det = st.text_input(
                "Tipo de proyecto", value=row.get("tipo_proyecto", "")
            )
            promotor_det = st.text_input(
                "Promotor (cliente principal)", value=row.get("cliente_principal", "")
            )
            ciudad_det = st.text_input("Ciudad", value=row.get("ciudad", ""))
        with c2:
            provincia_det = st.text_input(
                "Provincia", value=row.get("provincia", "")
            )
            prioridad_det = st.selectbox(
                "Prioridad",
                ["Alta", "Media", "Baja"],
                index=["Alta", "Media", "Baja"].index(
                    row.get("prioridad", "Media")
                    if row.get("prioridad") in ["Alta", "Media", "Baja"]
                    else "Media"
                ),
            )
            estados_posibles = [
                "Detectado",
                "Seguimiento",
                "En Prescripción",
                "Oferta Enviada",
                "Negociación",
                "Ganado",
                "Perdido",
                "Paralizado",
            ]
            estado_actual = row.get("estado", "Detectado")
            if estado_actual not in estados_posibles:
                estado_actual = "Detectado"
            estado_det = st.selectbox(
                "Estado",
                estados_posibles,
                index=estados_posibles.index(estado_actual),
            )
            potencial_det = st.number_input(
                "Potencial 2N (€)",
                min_value=0.0,
                step=10000.0,
                value=float(row.get("potencial_eur", 0.0))
                if row.get("potencial_eur") is not None
                else 0.0,
            )

        fecha_seg_val = row.get("fecha_seguimiento") or date.today()
        if isinstance(fecha_seg_val, str):
            try:
                fecha_seg_val = datetime.fromisoformat(fecha_seg_val).date()
            except Exception:
                fecha_seg_val = date.today()

        fecha_seg_det = st.date_input(
            "Próxima fecha de seguimiento",
            value=fecha_seg_val,
            key=f"fecha_seg_modal_{proyecto_id}",
        )
        notas_det = st.text_area(
            "Notas de seguimiento",
            value=row.get("notas_seguimiento", ""),
            height=100,
        )

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            guardar = st.form_submit_button("💾 Guardar cambios")
        with col_btn2:
            cancelar = st.form_submit_button("Cancelar")

    if guardar:
        update_data = {
            "nombre_obra": nombre_det,
            "tipo_proyecto": tipo_det,
            "cliente_principal": promotor_det or None,
            "promotora": promotor_det or None,
            "ciudad": ciudad_det or None,
            "provincia": provincia_det or None,
            "prioridad": prioridad_det,
            "potencial_eur": float(potencial_det),
            "estado": estado_det,
            "fecha_seguimiento": fecha_seg_det.isoformat(),
            "notas_seguimiento": notas_det,
        }
        try:
            actualizar_proyecto(proyecto_id, update_data)
            st.success("Cambios guardados correctamente.")
            st.session_state["edit_modal_proyecto_id"] = None
            st.experimental_rerun()
        except Exception as e:
            st.error(f"No se pudo actualizar el proyecto: {e}")

    if cancelar:
        st.session_state["edit_modal_proyecto_id"] = None
        st.experimental_rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# =====================================================
# DASHBOARD
# =====================================================

def _render_dashboard(df_proy: pd.DataFrame):
    st.markdown(
        """
        <div class="apple-card-light">
            <div class="section-badge">Analytics</div>
            <h4 style="margin-top:8px; margin-bottom:4px; font-size:1.0rem;">📈 Dashboard analítico</h4>
            <p style="color:#9CA3AF; margin-top:0; font-size:0.8rem;">
                Visualiza el número de obras y el potencial económico por estado, zona o tipo de proyecto.
            </p>
        """,
        unsafe_allow_html=True,
    )

    if df_proy is None or df_proy.empty:
        st.info("No hay datos de proyectos para mostrar en el dashboard.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    df_filtrado = _aplicar_filtros_basicos(df_proy, key_prefix="dash")
    if df_filtrado is None or df_filtrado.empty:
        st.info("No hay datos tras aplicar filtros.")
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
# DUPLICADOS
# =====================================================

def _render_duplicados(df_proy: pd.DataFrame):
    st.markdown(
        """
        <div class="apple-card-light">
            <div class="section-badge">Calidad de datos</div>
            <h4 style="margin-top:8px; margin-bottom:4px; font-size:1.0rem;">🧬 Revisión de posibles duplicados</h4>
            <p style="color:#9CA3AF; margin-top:0; font-size:0.8rem;">
                Detecta obras duplicadas por nombre + cliente principal + ciudad + provincia y deja sólo
                el registro que quieras mantener.
            </p>
        """,
        unsafe_allow_html=True,
    )

    if df_proy is None or df_proy.empty:
        st.info("No hay proyectos en el CRM para analizar duplicados.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

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
                        st.experimental_rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# =====================================================
# IMPORTAR / EXPORTAR
# =====================================================

def _render_import_export(df_proy_empty: bool, df_proy=None):
    st.markdown(
        """
        <div class="apple-card-light">
            <div class="section-badge">Integración con ChatGPT</div>
            <h4 style="margin-top:8px; margin-bottom:4px; font-size:1.0rem;">📥 Importar / 📤 Exportar proyectos</h4>
            <p style="color:#9CA3AF; margin-top:0; font-size:0.8rem;">
                Descarga un Excel con las obras más importantes o importa las que hayas generado
                desde la pestaña <strong>Buscar</strong> usando prompts en ChatGPT.
            </p>
        """,
        unsafe_allow_html=True,
    )

    # ---- Exportar obras importantes ----
    if not df_proy_empty and df_proy is not None:
        st.markdown("##### 📤 Exportar Excel de obras importantes")
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

        st.markdown("---")

    # ---- Importar Excel desde ChatGPT ----
    st.markdown("##### 📥 Importar proyectos desde Excel (ChatGPT)")
    st.caption(
        "Sube el Excel que te genero desde la pestaña **Buscar**. "
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
                st.experimental_rerun()
        except Exception as e:
            st.error(f"Error leyendo el Excel: {e}")
    else:
        st.info("Sube un Excel para poder importarlo.")

    st.markdown("</div>", unsafe_allow_html=True)


# =====================================================
# AÑADIR NUEVO PROYECTO (Pestaña propia)
# =====================================================

def _render_alta_manual():
    st.markdown(
        """
        <div class="apple-card-light">
            <div class="section-badge">Nuevo proyecto</div>
            <h4 style="margin-top:8px; margin-bottom:4px; font-size:1.0rem;">➕ Alta manual de proyecto</h4>
            <p style="color:#9CA3AF; margin-top:0; font-size:0.8rem;">
                Crea una nueva obra detectada manualmente (reuniones, llamadas, visitas, etc.)
                y empieza a hacerle seguimiento desde el CRM.
            </p>
        """,
        unsafe_allow_html=True,
    )

    df_clientes = get_clientes()
    nombres_clientes = ["(sin asignar)"]
    if df_clientes is not None and not df_clientes.empty and "empresa" in df_clientes.columns:
        nombres_clientes += sorted(df_clientes["empresa"].dropna().unique().tolist())

    with st.form("form_alta_manual"):
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
            fecha_seg = st.date_input(
                "Primera fecha de seguimiento", value=date.today() + timedelta(days=7)
            )

        notas = st.text_area("Notas iniciales (fuente del proyecto, link, etc.)")

        guardar_proy = st.form_submit_button("💾 Guardar proyecto")

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
                    "estado": "Detectado",
                    "fecha_seguimiento": fecha_seg.isoformat(),
                    "notas_seguimiento": notas,
                    "notas_historial": [],
                    "tareas": [],
                    "pasos_seguimiento": default_pasos_seguimiento(),
                }
            )
            st.success("Proyecto creado correctamente.")
            st.experimental_rerun()

    st.markdown("</div>", unsafe_allow_html=True)
