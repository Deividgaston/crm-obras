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

try:
    from style_injector import inject_apple_style
except Exception:
    def inject_apple_style():
        pass


# =====================================================
# CACHÉ FIREBASE
# =====================================================

@st.cache_data(show_spinner=False)
def load_proyectos() -> pd.DataFrame | None:
    return get_proyectos()


@st.cache_data(show_spinner=False)
def load_clientes() -> pd.DataFrame | None:
    return get_clientes()


def invalidate_proyectos_cache():
    load_proyectos.clear()


def invalidate_clientes_cache():
    load_clientes.clear()


# =====================================================
# UTILS
# =====================================================

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
# FORMULARIO EDICIÓN
# =====================================================

def _render_edit_form(row_data: dict, proy_id: str):
    df_clientes = load_clientes()
    nombres_clientes = ["(sin asignar)"]
    if df_clientes is not None and not df_clientes.empty and "empresa" in df_clientes.columns:
        nombres_clientes += sorted(df_clientes["empresa"].dropna().unique().tolist())

    fecha_seg_default = _parse_fecha_iso(row_data.get("fecha_seguimiento")) or date.today()

    with st.form(f"form_edit_proyecto_{proy_id}"):
        col1, col2 = st.columns(2)

        with col1:
            nombre_obra = st.text_input(
                "Nombre del proyecto / obra",
                value=row_data.get("nombre_obra", ""),
            )
            cliente_principal = st.selectbox(
                "Cliente principal (promotor)",
                nombres_clientes,
                index=(
                    nombres_clientes.index(row_data.get("cliente_principal"))
                    if row_data.get("cliente_principal") in nombres_clientes
                    else 0
                ),
            )
            tipo_opciones = ["Residencial lujo", "Residencial", "Oficinas", "Hotel", "BTR", "Otro"]
            tipo_proyecto = st.selectbox(
                "Tipo de proyecto",
                tipo_opciones,
                index=tipo_opciones.index(row_data.get("tipo_proyecto", "Residencial lujo"))
                if row_data.get("tipo_proyecto") in tipo_opciones
                else 0,
            )
            ciudad = st.text_input("Ciudad", value=row_data.get("ciudad", ""))
            provincia = st.text_input("Provincia", value=row_data.get("provincia", ""))

        with col2:
            arquitectura = st.text_input(
                "Arquitectura",
                value=row_data.get("arquitectura", "") or "",
            )
            ingenieria = st.text_input(
                "Ingeniería",
                value=row_data.get("ingenieria", "") or "",
            )
            prioridad_opciones = ["Alta", "Media", "Baja"]
            prioridad = st.selectbox(
                "Prioridad",
                prioridad_opciones,
                index=prioridad_opciones.index(row_data.get("prioridad", "Media")),
            )
            potencial_eur = st.number_input(
                "Potencial estimado 2N (€)",
                min_value=0.0,
                step=10_000.0,
                value=float(row_data.get("potencial_eur", 50_000.0) or 0.0),
            )
            fecha_seg = st.date_input(
                "Fecha de seguimiento",
                value=fecha_seg_default,
            )

        notas = st.text_area(
            "Notas de seguimiento",
            value=row_data.get("notas_seguimiento", "") or "",
        )

        guardar = st.form_submit_button("💾 Guardar cambios")

    if guardar:
        if not nombre_obra:
            st.warning("El nombre del proyecto es obligatorio.")
            return

        promotor_nombre = None if cliente_principal == "(sin asignar)" else cliente_principal

        data_update = {
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
            "fecha_seguimiento": fecha_seg.isoformat(),
            "notas_seguimiento": notas,
        }

        try:
            actualizar_proyecto(proy_id, data_update)
            invalidate_proyectos_cache()
            st.success("Proyecto actualizado correctamente.")
            st.rerun()
        except Exception as e:
            st.error(f"No se pudo actualizar el proyecto: {e}")


def _open_edit_dialog(row_data: dict, proy_id: str):
    if hasattr(st, "dialog"):
        @st.dialog("✏️ Editar proyecto")
        def _dlg():
            st.caption("Modifica los datos del proyecto y guarda los cambios.")
            _render_edit_form(row_data, proy_id)

        _dlg()
    else:
        st.markdown(
            """
            <div class="apple-card-light">
                <div class="badge">Edición</div>
                <h3>✏️ Editar proyecto seleccionado</h3>
            """,
            unsafe_allow_html=True,
        )
        _render_edit_form(row_data, proy_id)
        st.markdown("</div>", unsafe_allow_html=True)


# =====================================================
# FILTROS
# =====================================================

def _aplicar_filtros_basicos(df: pd.DataFrame, key_prefix: str) -> pd.DataFrame:
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

    if ciudad_sel != "Todas":
        df = df[df["ciudad"] == ciudad_sel]
    if estado_sel != "Todos" and "estado" in df.columns:
        df = df[df["estado"] == estado_sel]
    if tipo_sel != "Todos" and "tipo_proyecto" in df.columns:
        df = df[df["tipo_proyecto"] == tipo_sel]
    if prioridad_sel != "Todas" and "prioridad" in df.columns:
        df = df[df["prioridad"] == prioridad_sel]

    return df


# =====================================================
# VISTAS: TABLA / SEGUIMIENTOS / TAREAS / KANBAN
# =====================================================

def _vista_tabla(df_filtrado: pd.DataFrame):
    st.markdown(
        '<h5 style="color:#032D60;margin-bottom:4px;">Pipeline por estado</h5>',
        unsafe_allow_html=True,
    )

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
        for i, estado in enumerate(estados):
            with cols_pipe[i]:
                valor = int(counts.get(estado, 0))
                st.metric(label=estado, value=valor)

    st.markdown(
        "<hr style='margin-top:8px;margin-bottom:8px;border-color:#d8dde6;'>",
        unsafe_allow_html=True,
    )

    if df_filtrado.empty:
        st.info("No hay proyectos con los filtros actuales.")
        return

    # -------- Tabla propia HTML (crm-table) --------
    columnas = [
        "nombre_obra",
        "cliente_principal",
        "ciudad",
        "provincia",
        "estado",
        "prioridad",
        "potencial_eur",
    ]
    columnas = [c for c in columnas if c in df_filtrado.columns]

    df_tabla = df_filtrado[columnas].copy()
    df_tabla = df_tabla.rename(
        columns={
            "nombre_obra": "Proyecto",
            "cliente_principal": "Cliente principal",
            "ciudad": "Ciudad",
            "provincia": "Provincia",
            "estado": "Estado",
            "prioridad": "Prioridad",
            "potencial_eur": "Potencial (€)",
        }
    )

    html_tabla = df_tabla.to_html(
        index=False,
        classes="crm-table",
        border=0,
        justify="left",
    )
    st.markdown(html_tabla, unsafe_allow_html=True)

    # -------- Selector para acciones --------
    opciones = {}
    for _, row in df_filtrado.iterrows():
        etiqueta = f"{row.get('nombre_obra', 'Sin nombre')} — {row.get('ciudad', '—')} ({row.get('cliente_principal', '—')})"
        opciones[etiqueta] = row["id"]

    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("Selecciona una obra para editarla o borrarla:")

    col_sel, col_edit, col_del = st.columns([3, 1, 1])

    with col_sel:
        seleccion = st.selectbox(
            "",
            ["(ninguna)"] + list(opciones.keys()),
            index=0,
            label_visibility="collapsed",
            key="proyecto_seleccionado_tabla",
        )

    with col_edit:
        if st.button("✏️ Editar"):
            if seleccion == "(ninguna)":
                st.warning("Primero selecciona una obra.")
            else:
                proy_id = opciones[seleccion]
                row_data = df_filtrado[df_filtrado["id"] == proy_id].iloc[0].to_dict()
                _open_edit_dialog(row_data, proy_id)

    with col_del:
        if st.button("🗑️ Borrar"):
            if seleccion == "(ninguna)":
                st.warning("Primero selecciona una obra.")
            else:
                proy_id = opciones[seleccion]
                try:
                    delete_proyecto(proy_id)
                    invalidate_proyectos_cache()
                    st.success("Proyecto borrado.")
                    st.rerun()
                except Exception as e:
                    st.error(f"No se pudo borrar el proyecto: {e}")


def _vista_seguimientos(df_filtrado: pd.DataFrame):
    st.markdown(
        '<h5 style="color:#032D60;margin-bottom:4px;">Seguimientos por fecha</h5>',
        unsafe_allow_html=True,
    )

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
        st.info("No hay fechas de seguimiento registradas.")
        return

    df_seg = pd.DataFrame(registros)
    df_seg = df_seg.sort_values("Fecha_seguimiento")

    st.dataframe(
        df_seg,
        hide_index=True,
        use_container_width=True,
    )

    opciones = {f"{r['Proyecto']} ({r['Fecha_seguimiento']})": r["id"] for _, r in df_seg.iterrows()}

    col1, col2 = st.columns(2)
    with col1:
        seleccion = st.selectbox(
            "Selecciona un proyecto para posponer el seguimiento",
            ["(ninguno)"] + list(opciones.keys()),
        )

    with col2:
        if st.button("⏰ Posponer 1 semana") and seleccion != "(ninguno)":
            proy_id = opciones[seleccion]
            nueva_fecha = (hoy + timedelta(days=7)).isoformat()
            try:
                actualizar_proyecto(proy_id, {"fecha_seguimiento": nueva_fecha})
                invalidate_proyectos_cache()
                st.success(f"Seguimiento pospuesto a {nueva_fecha}.")
                st.rerun()
            except Exception as e:
                st.error(f"No se pudo actualizar: {e}")


def _vista_tareas(df_filtrado: pd.DataFrame):
    st.markdown(
        '<h5 style="color:#032D60;margin-bottom:4px;">Tareas abiertas por proyecto</h5>',
        unsafe_allow_html=True,
    )

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
        st.info("No hay tareas abiertas en los proyectos filtrados.")
        return

    df_tareas = pd.DataFrame(registros)
    df_tareas = df_tareas.sort_values(
        ["Completada", "Fecha_límite"],
        ascending=[True, True],
    )

    st.dataframe(
        df_tareas,
        hide_index=True,
        use_container_width=True,
    )


# =====================================================
# KANBAN PIPELINE
# =====================================================

ESTADOS_PIPELINE = [
    "Detectado",
    "Seguimiento",
    "En Prescripción",
    "Oferta Enviada",
    "Negociación",
    "Ganado",
    "Perdido",
    "Paralizado",
]


def _vista_kanban(df_filtrado: pd.DataFrame):
    st.markdown(
        '<h5 style="color:#032D60;margin-bottom:4px;">Kanban del pipeline</h5>',
        unsafe_allow_html=True,
    )

    if df_filtrado.empty:
        st.info("No hay proyectos con los filtros actuales.")
        return

    if "estado" not in df_filtrado.columns:
        st.error("Los proyectos no tienen campo 'estado'.")
        return

    cols = st.columns(len(ESTADOS_PIPELINE))

    for idx, estado in enumerate(ESTADOS_PIPELINE):
        with cols[idx]:
            st.markdown(
                f"""
                <div style="
                    font-size:13px;
                    font-weight:600;
                    color:#032D60;
                    margin-bottom:6px;
                ">
                    {estado}
                </div>
                """,
                unsafe_allow_html=True,
            )

            subset = df_filtrado[df_filtrado["estado"] == estado]

            if subset.empty:
                st.markdown(
                    """
                    <div class="apple-card-light" style="padding:8px; text-align:center;">
                        <span style="color:#5A6872;">Sin proyectos</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                continue

            for _, row in subset.iterrows():
                nombre = row.get("nombre_obra", "Sin nombre")
                cliente = row.get("cliente_principal", "—")
                ciudad = row.get("ciudad", "—")
                potencial = row.get("potencial_eur", 0)
                prioridad = row.get("prioridad", "Media")

                st.markdown(
                    f"""
                    <div class="apple-card-light" style="
                        padding:8px 10px;
                        margin-bottom:8px;
                        border-left:4px solid #0170D2;
                    ">
                        <div style="font-size:12.5px; font-weight:600;">
                            {nombre}
                        </div>
                        <div style="font-size:12px; color:#5A6872;">
                            {cliente} — {ciudad}
                        </div>
                        <div style="font-size:11.5px; margin-top:3px;">
                            <strong>Potencial:</strong> {potencial:,.0f} €
                        </div>
                        <div style="font-size:11.5px;">
                            <strong>Prioridad:</strong> {prioridad}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


# =====================================================
# VISTA GENERAL
# =====================================================

def _render_vista_general(df_proy: pd.DataFrame):
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.markdown(
        '<h4 style="color:#032D60;margin:0 0 4px 0;">Vista general de proyectos</h4>',
        unsafe_allow_html=True,
    )

    df_filtrado = _aplicar_filtros_basicos(df_proy, key_prefix="vista_general")

    st.markdown("<hr style='margin:8px 0 6px 0;border-color:#d8dde6;'>", unsafe_allow_html=True)

    st.markdown(
        '<div style="font-size:12px;color:#5A6872;margin-bottom:4px;">Modo de vista</div>',
        unsafe_allow_html=True,
    )

    vista = st.radio(
        "",
        ["Tabla", "Seguimientos", "Tareas", "Kanban"],
        horizontal=True,
        key="vista_general_radio",
        label_visibility="collapsed",
    )

    if vista == "Tabla":
        _vista_tabla(df_filtrado)
    elif vista == "Seguimientos":
        _vista_seguimientos(df_filtrado)
    elif vista == "Tareas":
        _vista_tareas(df_filtrado)
    else:
        _vista_kanban(df_filtrado)

    st.markdown("</div>", unsafe_allow_html=True)


# =====================================================
# RESTO DE PESTAÑAS (igual que antes)
# =====================================================

def _render_dashboard(df_proy: pd.DataFrame):
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.markdown(
        '<h4 style="color:#032D60;margin:0 0 4px 0;">Obras importantes (dashboard)</h4>',
        unsafe_allow_html=True,
    )

    if df_proy.empty:
        st.info("No hay proyectos para mostrar en el dashboard.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    df_imp = filtrar_obras_importantes(df_proy)
    if df_imp.empty:
        st.info("No hay obras importantes según el criterio definido.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    group_col = st.selectbox(
        "Agrupar por",
        ["provincia", "ciudad", "tipo_proyecto"],
        index=0,
    )

    if group_col not in df_imp.columns:
        st.warning(f"No existe la columna '{group_col}' en los datos.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    df_group = (
        df_imp.groupby(group_col)
        .agg(
            num_obras=("id", "count"),
            potencial_total=("potencial_eur", "sum"),
        )
        .reset_index()
    )

    col1, col2 = st.columns(2)

    with col1:
        st.caption("Número de obras por grupo")
        chart_count = (
            alt.Chart(df_group)
            .mark_bar()
            .encode(
                x=alt.X(f"{group_col}:N", sort="-y", title=group_col.capitalize()),
                y=alt.Y("num_obras:Q", title="Número de obras"),
                tooltip=[group_col, "num_obras", "potencial_total"],
            )
            .properties(height=320)
        )
        st.altair_chart(chart_count, use_container_width=True)

    with col2:
        st.caption("Potencial total por grupo (€)")
        chart_potencial = (
            alt.Chart(df_group)
            .mark_bar()
            .encode(
                x=alt.X(f"{group_col}:N", sort="-y", title=group_col.capitalize()),
                y=alt.Y("potencial_total:Q", title="Potencial total (€)"),
                tooltip=[group_col, "num_obras", "potencial_total"],
            )
            .properties(height=320)
        )
        st.altair_chart(chart_potencial, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)


def _render_duplicados(df_proy: pd.DataFrame):
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.markdown(
        '<h4 style="color:#032D60;margin:0 0 4px 0;">Posibles proyectos duplicados</h4>',
        unsafe_allow_html=True,
    )

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
        st.success("No se han detectado proyectos duplicados.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    st.caption("Revisa los grupos de proyectos que parecen duplicados:")

    for key, group in df_dups.groupby("dup_key"):
        st.markdown(f"**Grupo:** {key}")
        st.dataframe(
            group.drop(columns=["dup_key"]),
            use_container_width=True,
            hide_index=True,
        )

        for _, row in group.iterrows():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"- {row.get('nombre_obra', 'Sin nombre')} ({row.get('id')})")
            with col2:
                if st.button("🗑️ Borrar", key=f"del_dup_{row['id']}"):
                    delete_proyecto(row["id"])
                    invalidate_proyectos_cache()
                    st.success("Proyecto borrado.")
                    st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def _render_import_export(df_proy_empty: bool, df_proy: pd.DataFrame | None = None):
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.markdown(
        '<h4 style="color:#032D60;margin:0 0 4px 0;">Importar / Exportar proyectos</h4>',
        unsafe_allow_html=True,
    )

    if not df_proy_empty and df_proy is not None:
        st.markdown("##### Exportar obras importantes a Excel")
        try:
            excel_bytes = generar_excel_obras_importantes(df_proy)
            st.download_button(
                "⬇️ Descargar Excel de obras importantes",
                data=excel_bytes,
                file_name="obras_importantes.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
            )
        except Exception as e:
            st.error(f"No se pudo generar el Excel: {e}")

    st.markdown("---")
    st.markdown("##### Importar proyectos desde Excel")

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

            if st.button("🚀 Importar proyectos"):
                creados = importar_proyectos_desde_excel(uploaded_file)
                invalidate_proyectos_cache()
                st.success(f"Importación completada. Proyectos creados: {creados}")
                st.rerun()
        except Exception as e:
            st.error(f"Error leyendo el Excel: {e}")
    else:
        st.info("Sube un Excel para poder importarlo.")

    st.markdown("</div>", unsafe_allow_html=True)


def _render_alta_manual():
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.markdown(
        '<h4 style="color:#032D60;margin:0 0 4px 0;">Alta manual de proyecto</h4>',
        unsafe_allow_html=True,
    )

    df_clientes = load_clientes()
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
            arquitectura = st.text_input("Arquitectura (opcional)")
            ingenieria = st.text_input("Ingeniería (opcional)")
            prioridad = st.selectbox("Prioridad", ["Alta", "Media", "Baja"], index=1)
            potencial_eur = st.number_input(
                "Potencial estimado 2N (€)",
                min_value=0.0,
                step=10_000.0,
                value=50_000.0,
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
                    "tareas": default_pasos_seguimiento() if callable(default_pasos_seguimiento) else [],
                }
            )
            invalidate_proyectos_cache()
            st.success("Proyecto creado correctamente.")
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# =====================================================
# PÁGINA PRINCIPAL
# =====================================================

def render_proyectos():
    inject_apple_style()

    st.markdown(
        """
        <div class="apple-card">
            <div class="badge">Proyectos</div>
            <h3 style="margin-top:2px; margin-bottom:2px;">Pipeline de prescripción</h3>
            <p>
                Gestiona el ciclo completo de las obras: estados, seguimientos, tareas y análisis
                de potencial. Usa las pestañas para navegar por la vista general, el dashboard,
                la limpieza de duplicados y la importación de datos.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_proy = load_proyectos()

    if df_proy is None or df_proy.empty:
        st.info("Todavía no hay proyectos guardados en Firestore.")
        _render_import_export(df_proy_empty=True)
        _render_alta_manual()
        return

    tab_vista, tab_dash, tab_duplicados, tab_import, tab_alta = st.tabs(
        [
            "📁 Vista general",
            "📊 Dashboard",
            "🧬 Duplicados",
            "📤/📥 Importar / Exportar",
            "➕ Alta manual",
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
