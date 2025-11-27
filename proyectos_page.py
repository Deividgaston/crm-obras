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

# ===================================
# CARGA / CACHE
# ===================================


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


# ===================================
# HELPERS DE FECHAS Y ESTADOS
# ===================================


def _parse_fecha_iso(fecha_str: str | None) -> date | None:
    if not fecha_str:
        return None
    try:
        return datetime.fromisoformat(fecha_str).date()
    except Exception:
        return None


def _hoy() -> date:
    return date.today()


def _es_retrasada(fecha: date | None) -> bool:
    if not fecha:
        return False
    return fecha < _hoy()


def _es_hoy(fecha: date | None) -> bool:
    if not fecha:
        return False
    return fecha == _hoy()


def _es_proximos_7_dias(fecha: date | None) -> bool:
    if not fecha:
        return False
    return _hoy() < fecha <= (_hoy() + timedelta(days=7))


def _etiqueta_estado(estado: str | None) -> str:
    if not estado:
        return "Detectado"
    return estado


# ===================================
# RENDER PRINCIPAL
# ===================================


def render_proyectos():
    st.markdown(
        """
        <style>
        /* Título principal */
        .crm-main-title {
            font-size: 28px;
            font-weight: 700;
            color: #16325C;
            margin-bottom: 0.35rem;
        }

        .crm-subtitle {
            font-size: 13px;
            color: #5A6872;
            margin-bottom: 1.2rem;
        }

        .crm-kpi-label {
            font-size: 11px;
            color: #5A6872;
            margin-bottom: 0.1rem;
        }

        .crm-kpi-value {
            font-size: 26px;
            font-weight: 700;
            color: #16325C;
        }

        .crm-section-title {
            font-size: 18px;
            font-weight: 600;
            color: #16325C;
            margin-top: 0.5rem;
            margin-bottom: 0.1rem;
        }

        .crm-section-sub {
            font-size: 12px;
            color: #5A6872;
            margin-bottom: 0.75rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="crm-main-title">Proyectos</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="crm-subtitle">'
        "Vista general en tabla · Filtra, selecciona, edita o borra"
        "</div>",
        unsafe_allow_html=True,
    )

    df_proy = load_proyectos()
    df_clientes = load_clientes()

    if df_proy is None or df_proy.empty:
        st.info("Todavía no hay proyectos cargados.")
        _bloque_importacion(df_clientes)
        return

    # Normalizamos columnas clave
    if "estado" not in df_proy.columns:
        df_proy["estado"] = "Detectado"

    # =========================
    # FILTROS SUPERIORES
    # =========================
    filtros_col1, filtros_col2, filtros_col3, filtros_col4, filtros_col5 = st.columns(
        [1.2, 1.2, 1.2, 1.2, 0.7]
    )

    with filtros_col1:
        ciudad_sel = st.selectbox(
            "Ciudad",
            options=["Todas"] + sorted(df_proy["ciudad"].dropna().unique().tolist()),
            index=0,
        )

    with filtros_col2:
        estado_sel = st.selectbox(
            "Estado / Seguimiento",
            options=["Todos"] + sorted(df_proy["estado"].dropna().unique().tolist()),
            index=0,
        )

    with filtros_col3:
        tipo_sel = st.selectbox(
            "Tipo de proyecto",
            options=["Todos"] + sorted(df_proy["tipo"].dropna().unique().tolist())
            if "tipo" in df_proy.columns
            else ["Todos"],
            index=0,
        )

    with filtros_col4:
        prioridad_sel = st.selectbox(
            "Prioridad",
            options=["Todas"] + sorted(df_proy["prioridad"].dropna().unique().tolist())
            if "prioridad" in df_proy.columns
            else ["Todas"],
            index=0,
        )

    with filtros_col5:
        vista_modo = st.selectbox("Vista", options=["Vista · Tabla"], index=0)

    # Aplicar filtros
    df_filtrado = df_proy.copy()

    if ciudad_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado["ciudad"] == ciudad_sel]

    if estado_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["estado"] == estado_sel]

    if tipo_sel != "Todos" and "tipo" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["tipo"] == tipo_sel]

    if prioridad_sel != "Todas" and "prioridad" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["prioridad"] == prioridad_sel]

    if df_filtrado.empty:
        st.warning("No hay proyectos que coincidan con los filtros seleccionados.")
        _bloque_importacion(df_clientes)
        return

    # =========================
    # KPIs RESUMEN
    # =========================
    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)

    total = len(df_filtrado)
    seguimiento = (df_filtrado["estado"] != "Detectado").sum()
    ganados = (df_filtrado["estado"] == "Ganado").sum()

    with kpi_col1:
        st.markdown('<div class="crm-kpi-label">Total</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="crm-kpi-value">{int(total)}</div>', unsafe_allow_html=True
        )

    with kpi_col2:
        st.markdown(
            '<div class="crm-kpi-label">Seguimiento</div>', unsafe_allow_html=True
        )
        st.markdown(
            f'<div class="crm-kpi-value">{int(seguimiento)}</div>',
            unsafe_allow_html=True,
        )

    with kpi_col3:
        st.markdown('<div class="crm-kpi-label">Ganados</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="crm-kpi-value">{int(ganados)}</div>', unsafe_allow_html=True
        )

    st.markdown("---")

    # =========================
    # VISTA TABLA (ÚNICA)
    # =========================
    _vista_tabla(df_filtrado, df_clientes)


# ===================================
# VISTA: TABLA CON EDICIÓN
# ===================================


def _vista_tabla(df_filtrado: pd.DataFrame, df_clientes: pd.DataFrame | None):
    st.markdown(
        '<div class="crm-section-title">Vista general de proyectos</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="crm-section-sub">'
        "Selecciona las obras, edítalas o bórralas desde la tabla."
        "</div>",
        unsafe_allow_html=True,
    )

    if df_filtrado.empty:
        st.info("No hay proyectos para mostrar.")
        return

    # -------- Tabla con selección y acciones --------
    columnas = [
        "id",
        "nombre_obra",
        "cliente_principal",
        "ciudad",
        "provincia",
        "estado",
        "prioridad",
        "potencial_eur",
    ]
    columnas = [c for c in columnas if c in df_filtrado.columns]

    if not columnas:
        st.info("No hay proyectos para mostrar en la tabla.")
        return

    df_tabla = df_filtrado[columnas].copy()

    # Renombrar columnas para la vista
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

    # Columna de selección
    df_tabla["Seleccionar"] = False

    # Usamos el id como índice interno y no lo mostramos
    if "id" in df_tabla.columns:
        df_tabla = df_tabla.set_index("id")

    # Barra de acciones con iconos
    col_blank, col_edit, col_del = st.columns([0.8, 0.1, 0.1])
    with col_edit:
        editar_clicked = st.button("✏️", key="btn_editar_tabla", help="Editar proyecto seleccionado")
    with col_del:
        borrar_clicked = st.button("🗑️", key="btn_borrar_tabla", help="Borrar proyecto seleccionado")

    # Estilo claro para el grid del editor
    st.markdown(
        """
        <style>
        div[data-testid="stDataFrame"] table {
            background-color: #FFFFFF !important;
            color: #16325C !important;
        }
        div[data-testid="stDataFrame"] tbody tr:nth-child(even) {
            background-color: #F5F7FA !important;
        }
        div[data-testid="stDataFrame"] tbody tr:nth-child(odd) {
            background-color: #FFFFFF !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    df_edit = st.data_editor(
        df_tabla,
        hide_index=True,
        use_container_width=True,
        key="editor_proyectos_tabla",
        column_config={
            "Seleccionar": st.column_config.CheckboxColumn(
                "",
                help="Seleccionar fila",
                default=False,
            ),
        },
        disabled=[c for c in df_tabla.columns if c != "Seleccionar"],
    )

    seleccionados = df_edit[df_edit["Seleccionar"]].index.tolist()

    # --- Acción editar ---
    if editar_clicked:
        if len(seleccionados) == 0:
            st.warning("Selecciona una única obra para editar.")
        elif len(seleccionados) > 1:
            st.warning("Solo puedes editar una obra a la vez.")
        else:
            proy_id = seleccionados[0]
            row_data = df_filtrado[df_filtrado["id"] == proy_id].iloc[0].to_dict()
            _open_edit_dialog(row_data, proy_id)

    # --- Acción borrar (con confirmación) ---
    if borrar_clicked:
        if not seleccionados:
            st.warning("Selecciona al menos una obra para borrar.")
        else:
            st.session_state["pending_delete_ids"] = seleccionados
            st.session_state["show_delete_confirm"] = True

    if st.session_state.get("show_delete_confirm"):
        ids = st.session_state.get("pending_delete_ids", [])

        if hasattr(st, "dialog"):
            @st.dialog("🗑️ Confirmar borrado")
            def _dlg_borrar():
                st.warning(
                    f"Vas a borrar {len(ids)} proyecto(s). Esta acción no se puede deshacer.",
                    icon="⚠️",
                )
                col_canc, col_ok = st.columns(2)
                with col_canc:
                    if st.button("Cancelar", key="cancelar_borrado"):
                        st.session_state["show_delete_confirm"] = False
                with col_ok:
                    if st.button("Confirmar", key="confirmar_borrado"):
                        try:
                            for proy_id in ids:
                                delete_proyecto(proy_id)
                            invalidate_proyectos_cache()
                            st.session_state["show_delete_confirm"] = False
                            st.success("Proyecto(s) borrado(s).")
                            st.rerun()
                        except Exception as e:
                            st.error(f"No se pudo borrar el proyecto: {e}")

            _dlg_borrar()
        else:
            st.warning(
                f"Vas a borrar {len(ids)} proyecto(s). Esta acción no se puede deshacer.",
                icon="⚠️",
            )
            col_canc, col_ok = st.columns(2)
            with col_canc:
                if st.button("Cancelar", key="cancelar_borrado_fallback"):
                    st.session_state["show_delete_confirm"] = False
            with col_ok:
                if st.button("Confirmar", key="confirmar_borrado_fallback"):
                    try:
                        for proy_id in ids:
                            delete_proyecto(proy_id)
                        invalidate_proyectos_cache()
                        st.session_state["show_delete_confirm"] = False
                        st.success("Proyecto(s) borrado(s).")
                        st.rerun()
                    except Exception as e:
                        st.error(f"No se pudo borrar el proyecto: {e}")


# ===================================
# DIALOGO EDICIÓN / ALTA
# ===================================


def _open_edit_dialog(row_data: dict | None, proy_id: str | None):
    """Abre un cuadro flotante (dialog) para alta / edición de proyecto."""

    titulo = "Alta de proyecto" if row_data is None else "Edición de proyecto"

    if hasattr(st, "dialog"):
        @st.dialog(titulo)
        def _dlg():
            _render_edit_form(row_data, proy_id)
        _dlg()
    else:
        st.markdown(f"### {titulo}")
        _render_edit_form(row_data, proy_id)


def _render_edit_form(row_data: dict | None, proy_id: str | None):
    df_clientes = load_clientes()

    nombre_obra = row_data.get("nombre_obra", "") if row_data else ""
    cliente_principal = row_data.get("cliente_principal", "") if row_data else ""
    ciudad = row_data.get("ciudad", "") if row_data else ""
    provincia = row_data.get("provincia", "") if row_data else ""
    estado = row_data.get("estado", "Detectado") if row_data else "Detectado"
    prioridad = row_data.get("prioridad", "Media") if row_data else "Media"
    tipo = row_data.get("tipo", "Residencial") if row_data else "Residencial"
    potencial_eur = row_data.get("potencial_eur", 0) if row_data else 0

    seguimiento_comentario = row_data.get("seguimiento_comentario", "") if row_data else ""
    seguimiento_fecha = (
        _parse_fecha_iso(row_data.get("seguimiento_fecha")) if row_data else None
    )

    tarea_comentario = row_data.get("tarea_comentario", "") if row_data else ""
    tarea_fecha = _parse_fecha_iso(row_data.get("tarea_fecha")) if row_data else None

    with st.form("form_proyecto", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            nombre_obra = st.text_input("Nombre de la obra", value=nombre_obra)
            ciudad = st.text_input("Ciudad", value=ciudad)
            estado = st.selectbox(
                "Estado",
                options=["Detectado", "En Prescripción", "Oferta Enviada", "Negociación", "Ganado", "Perdido", "Paralizado"],
                index=["Detectado", "En Prescripción", "Oferta Enviada", "Negociación", "Ganado", "Perdido", "Paralizado"].index(
                    estado
                ),
            )
            tipo = st.selectbox(
                "Tipo de proyecto",
                options=["Residencial", "Terciario", "Mixto"],
                index=["Residencial", "Terciario", "Mixto"].index(tipo)
                if tipo in ["Residencial", "Terciario", "Mixto"]
                else 0,
            )

        with col2:
            # Cliente principal
            opciones_clientes = (
                [""] + sorted(df_clientes["nombre"].dropna().unique().tolist())
                if df_clientes is not None and not df_clientes.empty
                else [""]
            )
            if cliente_principal not in opciones_clientes:
                opciones_clientes = [cliente_principal] + [
                    c for c in opciones_clientes if c != cliente_principal
                ]

            cliente_principal = st.selectbox(
                "Cliente principal",
                options=opciones_clientes,
                index=opciones_clientes.index(cliente_principal)
                if cliente_principal in opciones_clientes
                else 0,
            )

            provincia = st.text_input("Provincia", value=provincia)
            prioridad = st.selectbox(
                "Prioridad",
                options=["Alta", "Media", "Baja"],
                index=["Alta", "Media", "Baja"].index(prioridad)
                if prioridad in ["Alta", "Media", "Baja"]
                else 1,
            )
            potencial_eur = st.number_input(
                "Potencial (€)",
                min_value=0.0,
                step=10000.0,
                value=float(potencial_eur) if potencial_eur is not None else 0.0,
            )

        st.markdown("----")
        st.markdown("**Seguimiento**")

        col_seg_1, col_seg_2 = st.columns(2)
        with col_seg_1:
            seguimiento_fecha = st.date_input(
                "Fecha seguimiento",
                value=seguimiento_fecha or _hoy(),
            )
        with col_seg_2:
            seguimiento_comentario = st.text_area(
                "Comentario seguimiento",
                value=seguimiento_comentario,
                height=80,
            )

        st.markdown("**Tarea asociada**")
        col_tar_1, col_tar_2 = st.columns(2)
        with col_tar_1:
            tarea_fecha = st.date_input(
                "Fecha tarea",
                value=tarea_fecha or _hoy(),
            )
        with col_tar_2:
            tarea_comentario = st.text_area(
                "Descripción tarea",
                value=tarea_comentario,
                height=80,
            )

        st.markdown("---")
        col_guardar, col_cancel = st.columns(2)
        submitted = col_guardar.form_submit_button("💾 Guardar")
        cancel = col_cancel.form_submit_button("Cancelar")

        if cancel:
            st.stop()

        if submitted:
            if not nombre_obra:
                st.error("El nombre de la obra es obligatorio.")
                st.stop()

            payload = {
                "nombre_obra": nombre_obra,
                "cliente_principal": cliente_principal,
                "ciudad": ciudad,
                "provincia": provincia,
                "estado": estado,
                "prioridad": prioridad,
                "tipo": tipo,
                "potencial_eur": float(potencial_eur) if potencial_eur is not None else 0.0,
                "seguimiento_comentario": seguimiento_comentario,
                "seguimiento_fecha": seguimiento_fecha.isoformat()
                if seguimiento_fecha
                else None,
                "tarea_comentario": tarea_comentario,
                "tarea_fecha": tarea_fecha.isoformat() if tarea_fecha else None,
            }

            try:
                if proy_id:
                    actualizar_proyecto(proy_id, payload)
                    st.success("Proyecto actualizado correctamente.")
                else:
                    add_proyecto(payload)
                    st.success("Proyecto creado correctamente.")

                invalidate_proyectos_cache()
                st.rerun()
            except Exception as e:
                st.error(f"No se pudo guardar el proyecto: {e}")


# ===================================
# BLOQUE IMPORTACIÓN / EXPORTACIÓN
# ===================================


def _bloque_importacion(df_clientes: pd.DataFrame | None):
    st.markdown("### Importación / Exportación")

    col_imp, col_exp = st.columns(2)

    with col_imp:
        st.markdown("**Importar proyectos desde Excel**")
        fichero = st.file_uploader("Selecciona un fichero Excel", type=["xlsx", "xls"])

        if fichero is not None:
            if st.button("Importar", key="btn_importar_excel"):
                try:
                    importar_proyectos_desde_excel(fichero, df_clientes)
                    invalidate_proyectos_cache()
                    st.success("Proyectos importados correctamente.")
                    st.rerun()
                except Exception as e:
                    st.error(f"No se pudo importar: {e}")

    with col_exp:
        st.markdown("**Exportar obras importantes**")
        if st.button("Descargar Excel de obras importantes"):
            try:
                df_proy = load_proyectos()
                if df_proy is None or df_proy.empty:
                    st.warning("No hay datos para exportar.")
                    return
                df_imp = filtrar_obras_importantes(df_proy)
                if df_imp.empty:
                    st.warning("No se han encontrado obras importantes.")
                    return
                buffer = generar_excel_obras_importantes(df_imp)
                st.download_button(
                    "Descargar Excel",
                    data=buffer,
                    file_name="obras_importantes.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            except Exception as e:
                st.error(f"No se pudo generar el Excel: {e}")
