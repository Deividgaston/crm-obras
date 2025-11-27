import streamlit as st
import pandas as pd
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


# =====================================================
# FORMULARIO EDICIÓN (MODAL FLOTANTE)
# =====================================================

def _render_edit_form(row_data: dict, proy_id: str):
    df_clientes = load_clientes()
    nombres_clientes = ["(sin asignar)"]
    if df_clientes is not None and not df_clientes.empty and "empresa" in df_clientes.columns:
        nombres_clientes += sorted(df_clientes["empresa"].dropna().unique().tolist())

    fecha_seg_default = _parse_fecha_iso(row_data.get("fecha_seguimiento")) or date.today()

    tareas_existentes = row_data.get("tareas")
    if not isinstance(tareas_existentes, list):
        tareas_existentes = []

    with st.form(f"form_edit_proyecto_{proy_id}"):
        col1, col2 = st.columns(2)

        # -------- COLUMNA 1 --------
        with col1:
            nombre_obra = st.text_input(
                "Nombre del proyecto / obra",
                value=row_data.get("nombre_obra", "") or "",
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
            ciudad = st.text_input("Ciudad", value=row_data.get("ciudad", "") or "")
            provincia = st.text_input("Provincia", value=row_data.get("provincia", "") or "")

        # -------- COLUMNA 2 --------
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
            estado = st.selectbox(
                "Estado / Seguimiento",
                ESTADOS_PIPELINE,
                index=ESTADOS_PIPELINE.index(row_data.get("estado", "Detectado"))
                if row_data.get("estado") in ESTADOS_PIPELINE
                else 0,
            )
            potencial_eur = st.number_input(
                "Potencial estimado 2N (€)",
                min_value=0.0,
                step=10_000.0,
                value=float(row_data.get("potencial_eur", 50_000.0) or 0.0),
            )
            fecha_seg = st.date_input(
                "Próxima fecha de seguimiento",
                value=fecha_seg_default,
            )

        # Comentario de seguimiento (se guarda como notas_seguimiento)
        comentario_seguimiento = st.text_area(
            "Comentario de seguimiento",
            value=row_data.get("notas_seguimiento", "") or "",
        )

        st.markdown(
            "<hr style='margin-top:8px;margin-bottom:8px;border-color:#e5e7eb;'>",
            unsafe_allow_html=True,
        )

        # -------- NUEVA TAREA (comentario + fecha) --------
        st.markdown("**Asignar nueva tarea a esta obra (opcional)**")
        colt1, colt2 = st.columns([2, 1])
        with colt1:
            comentario_tarea = st.text_area(
                "Comentario de tarea",
                value="",
                placeholder="Ej. Llamar a promotora para cerrar condiciones",
                height=70,
            )
        with colt2:
            fecha_tarea = st.date_input(
                "Fecha de tarea",
                value=date.today() + timedelta(days=7),
            )

        colg, cold = st.columns(2)
        with colg:
            guardar = st.form_submit_button("💾 Guardar cambios", use_container_width=True)
        with cold:
            borrar = st.form_submit_button("🗑️ Borrar proyecto", use_container_width=True)

    # ---- LÓGICA BORRAR ----
    if borrar:
        try:
            delete_proyecto(proy_id)
            invalidate_proyectos_cache()
            st.success("Proyecto borrado correctamente.")
            st.rerun()
        except Exception as e:
            st.error(f"No se pudo borrar el proyecto: {e}")
        return

    # ---- LÓGICA GUARDAR ----
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
            "estado": estado,
            "potencial_eur": float(potencial_eur),
            "fecha_seguimiento": fecha_seg.isoformat(),
            "notas_seguimiento": comentario_seguimiento,
        }

        # Añadir nueva tarea si se ha rellenado comentario
        if comentario_tarea.strip():
            nueva_tarea = {
                "comentario": comentario_tarea.strip(),
                "fecha": fecha_tarea.isoformat(),
            }
            data_update["tareas"] = tareas_existentes + [nueva_tarea]

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
            st.caption("Modifica los datos del proyecto, el seguimiento y las tareas.")
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
# FILTROS (compactos)
# =====================================================

def _aplicar_filtros_basicos(df: pd.DataFrame, key_prefix: str) -> pd.DataFrame:
    df = df.copy()
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    ciudades = sorted(df["ciudad"].dropna().unique().tolist()) if "ciudad" in df.columns else []
    estados_list = sorted(df["estado"].dropna().unique().tolist()) if "estado" in df.columns else []
    tipos_list = sorted(df["tipo_proyecto"].dropna().unique().tolist()) if "tipo_proyecto" in df.columns else []
    prioridades = sorted(df["prioridad"].dropna().unique().tolist()) if "prioridad" in df.columns else []

    with col_f1:
        st.markdown("<div style='font-size:11px;color:#4b5563;'>Ciudad</div>", unsafe_allow_html=True)
        ciudad_sel = st.selectbox(
            "",
            ["Todas"] + ciudades,
            key=f"{key_prefix}_ciudad",
            label_visibility="collapsed",
        )

    with col_f2:
        st.markdown("<div style='font-size:11px;color:#4b5563;'>Estado / Seguimiento</div>", unsafe_allow_html=True)
        estado_sel = st.selectbox(
            "",
            ["Todos"] + estados_list,
            key=f"{key_prefix}_estado",
            label_visibility="collapsed",
        )

    with col_f3:
        st.markdown("<div style='font-size:11px;color:#4b5563;'>Tipo de proyecto</div>", unsafe_allow_html=True)
        tipo_sel = st.selectbox(
            "",
            ["Todos"] + tipos_list,
            key=f"{key_prefix}_tipo",
            label_visibility="collapsed",
        )

    with col_f4:
        st.markdown("<div style='font-size:11px;color:#4b5563;'>Prioridad</div>", unsafe_allow_html=True)
        prioridad_sel = st.selectbox(
            "",
            ["Todas"] + prioridades,
            key=f"{key_prefix}_prioridad",
            label_visibility="collapsed",
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
# VISTA GENERAL (TABLA + SELECCIÓN)
# =====================================================

def _vista_general_tabla(df_proy: pd.DataFrame):
    # Fondo blanco y texto oscuro en el grid (dataframe y data_editor)
    st.markdown(
        """
        <style>
        * { user-select: text !important; }
        div[data-testid="stDataFrame"] table,
        div[data-testid="stDataEditor"] table {
            background-color: #ffffff !important;
            color: #111827 !important;
        }
        div[data-testid="stDataFrame"] table thead tr th,
        div[data-testid="stDataEditor"] table thead tr th {
            background-color: #f3f4f6 !important;
            color: #111827 !important;
        }
        div[data-testid="stDataFrame"] tbody tr td,
        div[data-testid="stDataEditor"] tbody tr td {
            border-bottom: 1px solid #e5e7eb !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="crm-header" style="
            display:flex;
            align-items:center;
            justify-content:space-between;
            margin:0 0 6px 0;
            padding:0 0 4px 0;
            border-bottom:1px solid #d8dde6;
        ">
            <div>
                <div class="crm-title" style="font-size:20px;font-weight:600;color:#032D60;margin:0;">
                    Proyectos
                </div>
                <div class="crm-sub" style="font-size:11px;color:#5A6872;margin-top:-2px;">
                    Vista general en tabla · Filtra, selecciona, edita o borra
                </div>
            </div>
            <div class="crm-tag-big" style="
                font-size:13px;font-weight:500;padding:4px 12px;border-radius:14px;
                background:#e5f2ff;border:1px solid #b7d4f5;color:#032D60;height:28px;
                display:flex;align-items:center;white-space:nowrap;">
                Vista · Tabla
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Filtros compactos
    df_filtrado = _aplicar_filtros_basicos(df_proy, key_prefix="vista_general")

    st.markdown(
        "<hr style='margin:6px 0 4px 0;border-color:#d8dde6;'>",
        unsafe_allow_html=True,
    )

    if df_filtrado.empty:
        st.info("No hay proyectos con los filtros actuales.")
        return

    # Métricas compactas
    colm1, colm2, colm3, colm4 = st.columns(4)
    if "estado" in df_filtrado.columns:
        counts = df_filtrado["estado"].value_counts()
    else:
        counts = {}

    total = len(df_filtrado)
    with colm1:
        st.metric("Total", total)
    with colm2:
        st.metric("Seguimiento", int(counts.get("Seguimiento", 0)))
    with colm3:
        st.metric("Oferta / Negociación", int(counts.get("Oferta Enviada", 0) + counts.get("Negociación", 0)))
    with colm4:
        st.metric("Ganados", int(counts.get("Ganado", 0)))

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

    # Tabla principal
    columnas = [
        "nombre_obra",
        "cliente_principal",
        "ciudad",
        "provincia",
        "tipo_proyecto",
        "estado",
        "prioridad",
        "potencial_eur",
        "fecha_seguimiento",
    ]
    columnas = [c for c in columnas if c in df_filtrado.columns]

    df_f = df_filtrado.reset_index(drop=True)
    df_tabla = df_f[columnas].copy()
    df_tabla = df_tabla.rename(
        columns={
            "nombre_obra": "Proyecto",
            "cliente_principal": "Cliente principal",
            "ciudad": "Ciudad",
            "provincia": "Provincia",
            "tipo_proyecto": "Tipo",
            "estado": "Estado",
            "prioridad": "Prioridad",
            "potencial_eur": "Potencial (€)",
            "fecha_seguimiento": "Fecha seg.",
        }
    )

    # Configuramos columnas como no editables, pero permitimos seleccionar filas
    column_config = {
        c: st.column_config.Column(disabled=True) for c in df_tabla.columns
    }

    st.caption("Haz clic en una fila para abrir el cuadro flotante de edición.")
    st.data_editor(
        df_tabla,
        key="tabla_proyectos",
        use_container_width=True,
        hide_index=True,
        disabled=False,               # <-- selección y clicks habilitados
        num_rows="fixed",
        column_config=column_config,
    )

    # --- Apertura automática del diálogo al seleccionar fila ---
    tabla_state = st.session_state.get("tabla_proyectos", {})
    sel_rows = tabla_state.get("selection", {}).get("rows", []) if isinstance(tabla_state, dict) else []

    if sel_rows:
        row_idx = sel_rows[0]
        last_idx = st.session_state.get("last_selected_row")
        if last_idx != row_idx and 0 <= row_idx < len(df_f):
            st.session_state["last_selected_row"] = row_idx
            proy_id = df_f.iloc[row_idx]["id"]
            row_data = df_f.iloc[row_idx].to_dict()
            _open_edit_dialog(row_data, proy_id)

    # Selector + botones explícitos (por si prefieres usarlos)
    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("También puedes seleccionar desde esta lista y usar los botones de acción:")

    opciones = {}
    for idx, row in df_f.iterrows():
        etiqueta = f"{row.get('nombre_obra', 'Sin nombre')} — {row.get('ciudad', '—')} ({row.get('cliente_principal', '—')})"
        opciones[etiqueta] = row["id"]

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
        if st.button("✏️ Editar", use_container_width=True):
            if seleccion == "(ninguna)":
                st.warning("Primero selecciona una obra.")
            else:
                proy_id = opciones[seleccion]
                row_data = df_f[df_f["id"] == proy_id].iloc[0].to_dict()
                _open_edit_dialog(row_data, proy_id)

    with col_del:
        if st.button("🗑️ Borrar", use_container_width=True):
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


# =====================================================
# DUPLICADOS
# =====================================================

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
        st.info("No hay suficientes campos para detectar duplicados.")
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


# =====================================================
# IMPORT / EXPORT
# =====================================================

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
                use_container_width=True,
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

            if st.button("🚀 Importar proyectos", use_container_width=True):
                creados = importar_proyectos_desde_excel(uploaded_file)
                invalidate_proyectos_cache()
                st.success(f"Importación completada. Proyectos creados/actualizados: {creados}")
                st.rerun()
        except Exception as e:
            st.error(f"Error leyendo el Excel: {e}")
    else:
        st.info("Sube un Excel para poder importarlo.")

    st.markdown("</div>", unsafe_allow_html=True)


# =====================================================
# ALTA MANUAL
# =====================================================

def _render_alta_manual():
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.markdown(
        '<h4 style="color:#032D60;margin:0 0 4px 0;">Alta rápida de proyecto</h4>',
        unsafe_allow_html=True,
    )

    df_clientes = load_clientes()
    nombres_clientes = ["(sin asignar)"]
    if df_clientes is not None and not df_clientes.empty and "empresa" in df_clientes.columns:
        nombres_clientes += sorted(df_clientes["empresa"].dropna().unique().tolist())

    with st.form("form_proyecto_alta"):
        col1, col2 = st.columns(2)
        with col1:
            nombre_obra = st.text_input("Nombre del proyecto / obra *")
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
            estado = st.selectbox("Estado inicial", ESTADOS_PIPELINE, index=0)
            potencial_eur = st.number_input(
                "Potencial estimado 2N (€)",
                min_value=0.0,
                step=10_000.0,
                value=50_000.0,
            )
            fecha_seg = st.date_input(
                "Primera fecha de seguimiento", value=date.today()
            )

        notas = st.text_area(
            "Comentario inicial de seguimiento",
            height=80,
        )

        guardar_proy = st.form_submit_button("Guardar proyecto", use_container_width=True)

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
                    "estado": estado,
                    "potencial_eur": float(potencial_eur),
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

    df_proy = load_proyectos()

    if df_proy is None or df_proy.empty:
        st.info("Todavía no hay proyectos guardados en Firestore.")
        tab_alta, tab_import = st.tabs(["➕ Alta manual", "📤/📥 Importar / Exportar"])
        with tab_alta:
            _render_alta_manual()
        with tab_import:
            _render_import_export(df_proy_empty=True)
        return

    tab_vista, tab_alta, tab_import, tab_duplicados = st.tabs(
        [
            "📁 Vista general (tabla)",
            "➕ Alta / edición",
            "📤/📥 Importar / Exportar",
            "🧬 Duplicados",
        ]
    )

    with tab_vista:
        _vista_general_tabla(df_proy)

    with tab_alta:
        _render_alta_manual()

    with tab_import:
        _render_import_export(df_proy_empty=False, df_proy=df_proy)

    with tab_duplicados:
        _render_duplicados(df_proy)
