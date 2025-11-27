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


# ==========================
# CACHE FIREBASE
# ==========================

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


# ==========================
# HELPERS
# ==========================

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


def _hoy() -> date:
    return date.today()


ESTADOS_PIPELINE = [
    "Detectado",
    "En Prescripción",
    "Oferta Enviada",
    "Negociación",
    "Ganado",
    "Perdido",
    "Paralizado",
]


# ==========================
# PÁGINA PRINCIPAL
# ==========================

def render_proyectos():
    # Estilo general tipo Salesforce, más compacto
    st.markdown(
        """
        <style>
        .crm-main-title {
            font-size: 24px;
            font-weight: 700;
            color: #16325C;
            margin-bottom: 0.15rem;
        }
        .crm-subtitle {
            font-size: 12px;
            color: #5A6872;
            margin-bottom: 0.5rem;
        }
        .crm-kpi-label {
            font-size: 11px;
            color: #5A6872;
            margin-bottom: 0.05rem;
        }
        .crm-kpi-value {
            font-size: 22px;
            font-weight: 700;
            color: #16325C;
        }
        .crm-section-title {
            font-size: 16px;
            font-weight: 600;
            color: #16325C;
            margin-top: 0.25rem;
            margin-bottom: 0.05rem;
        }
        .crm-section-sub {
            font-size: 11px;
            color: #5A6872;
            margin-bottom: 0.35rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="crm-main-title">Proyectos</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="crm-subtitle">'
        'Vista general en tabla · Filtra, selecciona, edita o borra'
        '</div>',
        unsafe_allow_html=True,
    )

    df_proy = load_proyectos()
    df_clientes = load_clientes()

    if df_proy is None or df_proy.empty:
        st.info("Todavía no hay proyectos cargados.")
        _bloque_importacion(df_clientes)
        return

    # Normalizar columnas mínimas
    if "estado" not in df_proy.columns:
        df_proy["estado"] = "Detectado"
    if "tipo" not in df_proy.columns:
        df_proy["tipo"] = "Residencial"
    if "prioridad" not in df_proy.columns:
        df_proy["prioridad"] = "Media"

    # =====================
    # FILTROS SUPERIORES
    # =====================
    col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns([1.2, 1.2, 1.2, 1.2, 0.8])

    with col_f1:
        ciudades = sorted(df_proy["ciudad"].dropna().unique().tolist()) if "ciudad" in df_proy.columns else []
        ciudad_sel = st.selectbox(
            "Ciudad",
            options=["Todas"] + ciudades,
            index=0,
        )

    with col_f2:
        estados = sorted(df_proy["estado"].dropna().unique().tolist())
        estado_sel = st.selectbox(
            "Estado / Seguimiento",
            options=["Todos"] + estados,
            index=0,
        )

    with col_f3:
        tipos = sorted(df_proy["tipo"].dropna().unique().tolist())
        tipo_sel = st.selectbox(
            "Tipo de proyecto",
            options=["Todos"] + tipos,
            index=0,
        )

    with col_f4:
        prioridades = sorted(df_proy["prioridad"].dropna().unique().tolist())
        prioridad_sel = st.selectbox(
            "Prioridad",
            options=["Todas"] + prioridades,
            index=0,
        )

    with col_f5:
        st.selectbox("Vista", options=["Vista · Tabla"], index=0)

    df_filtrado = df_proy.copy()

    if ciudad_sel != "Todas" and "ciudad" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["ciudad"] == ciudad_sel]
    if estado_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["estado"] == estado_sel]
    if tipo_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["tipo"] == tipo_sel]
    if prioridad_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado["prioridad"] == prioridad_sel]

    if df_filtrado.empty:
        st.warning("No hay proyectos que coincidan con los filtros seleccionados.")
        _bloque_importacion(df_clientes)
        return

    # =====================
    # KPIs COMPACTOS
    # =====================
    col_k1, col_k2, col_k3 = st.columns(3)
    total = len(df_filtrado)
    seguimiento = (df_filtrado["estado"] != "Detectado").sum()
    ganados = (df_filtrado["estado"] == "Ganado").sum()

    with col_k1:
        st.markdown('<div class="crm-kpi-label">Total</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="crm-kpi-value">{int(total)}</div>', unsafe_allow_html=True)
    with col_k2:
        st.markdown('<div class="crm-kpi-label">Seguimiento</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="crm-kpi-value">{int(seguimiento)}</div>', unsafe_allow_html=True)
    with col_k3:
        st.markdown('<div class="crm-kpi-label">Ganados</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="crm-kpi-value">{int(ganados)}</div>', unsafe_allow_html=True)

    st.markdown("<hr style='margin:4px 0 4px 0;border-color:#d8dde6;'>", unsafe_allow_html=True)

    _vista_tabla(df_filtrado, df_clientes)


# ==========================
# VISTA TABLA + ACCIONES
# ==========================

def _vista_tabla(df_filtrado: pd.DataFrame, df_clientes: pd.DataFrame | None):
    st.markdown(
        '<div class="crm-section-title">Vista general de proyectos</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="crm-section-sub">'
        'Selecciona proyectos con el check y usa los iconos para editar o borrar.'
        '</div>',
        unsafe_allow_html=True,
    )

    if df_filtrado.empty:
        st.info("No hay proyectos para mostrar.")
        return

    # Columnas a mostrar
    columnas = [
        "id",
        "nombre_obra",
        "cliente_principal",
        "ciudad",
        "provincia",
        "estado",
        "prioridad",
        "tipo",
        "potencial_eur",
    ]
    columnas = [c for c in columnas if c in df_filtrado.columns]
    if "id" not in columnas:
        st.error("Falta la columna 'id' en los proyectos.")
        return

    df_tabla = df_filtrado[columnas].copy()

    # Renombrado para vista
    df_tabla = df_tabla.rename(
        columns={
            "nombre_obra": "Proyecto",
            "cliente_principal": "Cliente",
            "ciudad": "Ciudad",
            "provincia": "Provincia",
            "estado": "Estado",
            "prioridad": "Prioridad",
            "tipo": "Tipo",
            "potencial_eur": "Potencial (€)",
        }
    )

    # Añadir columna de selección y ponerla la primera
    df_tabla["Seleccionar"] = False
    df_tabla = df_tabla.set_index("id")
    cols = df_tabla.columns.tolist()
    if "Seleccionar" in cols:
        cols = ["Seleccionar"] + [c for c in cols if c != "Seleccionar"]
        df_tabla = df_tabla[cols]

    # Barra de iconos compacta
    col_spacer, col_edit, col_del = st.columns([0.8, 0.08, 0.08])
    with col_edit:
        editar_clicked = st.button("✏️", key="btn_editar_tabla", help="Editar proyecto seleccionado")
    with col_del:
        borrar_clicked = st.button("🗑️", key="btn_borrar_tabla", help="Borrar proyecto(s) seleccionados")

    # Estilo CLARO solo para el editor (aunque el tema sea oscuro)
    st.markdown(
        """
        <style>
        div[data-testid="stDataEditor"] table {
            background-color: #FFFFFF !important;
            color: #16325C !important;
        }
        div[data-testid="stDataEditor"] thead tr th {
            background-color: #E5E7EB !important;
            color: #111827 !important;
        }
        div[data-testid="stDataEditor"] tbody tr:nth-child(even) {
            background-color: #F5F7FA !important;
        }
        div[data-testid="stDataEditor"] tbody tr:nth-child(odd) {
            background-color: #FFFFFF !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Editor con checkbox solo en la primera columna
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

    # IDs seleccionados
    seleccionados = df_edit[df_edit["Seleccionar"]].index.tolist()

    # --- EDITAR ---
    if editar_clicked:
        if len(seleccionados) == 0:
            st.warning("Selecciona una única obra para editar.")
        elif len(seleccionados) > 1:
            st.warning("Solo puedes editar una obra a la vez.")
        else:
            proy_id = seleccionados[0]
            row_data = df_filtrado[df_filtrado["id"] == proy_id].iloc[0].to_dict()
            _open_edit_dialog(row_data, proy_id, df_clientes)

    # --- BORRAR (confirmación) ---
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


# ==========================
# DIÁLOGO EDICIÓN / ALTA
# ==========================

def _open_edit_dialog(row_data: dict | None, proy_id: str | None, df_clientes: pd.DataFrame | None):
    titulo = "Alta de proyecto" if row_data is None else "Edición de proyecto"

    if hasattr(st, "dialog"):
        @st.dialog(titulo)
        def _dlg():
            _render_edit_form(row_data, proy_id, df_clientes)
        _dlg()
    else:
        st.markdown(f"### {titulo}")
        _render_edit_form(row_data, proy_id, df_clientes)


def _render_edit_form(row_data: dict | None, proy_id: str | None, df_clientes: pd.DataFrame | None):
    # Valores iniciales
    nombre_obra = row_data.get("nombre_obra", "") if row_data else ""
    cliente_principal = row_data.get("cliente_principal", "") if row_data else ""
    ciudad = row_data.get("ciudad", "") if row_data else ""
    provincia = row_data.get("provincia", "") if row_data else ""
    estado = row_data.get("estado", "Detectado") if row_data else "Detectado"
    prioridad = row_data.get("prioridad", "Media") if row_data else "Media"
    tipo = row_data.get("tipo", "Residencial") if row_data else "Residencial"
    potencial_eur = row_data.get("potencial_eur", 0) if row_data else 0

    seguimiento_comentario = row_data.get("seguimiento_comentario", "") if row_data else ""
    seguimiento_fecha = _parse_fecha_iso(row_data.get("seguimiento_fecha")) if row_data else None

    tarea_comentario = row_data.get("tarea_comentario", "") if row_data else ""
    tarea_fecha = _parse_fecha_iso(row_data.get("tarea_fecha")) if row_data else None

    with st.form("form_proyecto", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            nombre_obra = st.text_input("Nombre de la obra", value=nombre_obra)
            ciudad = st.text_input("Ciudad", value=ciudad)
            estado = st.selectbox(
                "Estado",
                options=ESTADOS_PIPELINE,
                index=ESTADOS_PIPELINE.index(estado) if estado in ESTADOS_PIPELINE else 0,
            )
            tipo = st.selectbox(
                "Tipo de proyecto",
                options=["Residencial", "Terciario", "Mixto"],
                index=["Residencial", "Terciario", "Mixto"].index(tipo)
                if tipo in ["Residencial", "Terciario", "Mixto"]
                else 0,
            )

        with col2:
            # Clientes desde Firestore
            if df_clientes is not None and not df_clientes.empty:
                opciones_clientes = sorted(df_clientes["nombre"].dropna().unique().tolist()) \
                    if "nombre" in df_clientes.columns else []
                opciones_clientes = [""] + opciones_clientes
            else:
                opciones_clientes = [""]

            if cliente_principal not in opciones_clientes:
                opciones_clientes = [cliente_principal] + [c for c in opciones_clientes if c != cliente_principal]

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

        st.markdown("---")
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
                "seguimiento_fecha": seguimiento_fecha.isoformat() if seguimiento_fecha else None,
                "tarea_comentario": tarea_comentario,
                "tarea_fecha": tarea_fecha.isoformat() if tarea_fecha else None,
            }

            try:
                if proy_id:
                    actualizar_proyecto(proy_id, payload)
                    st.success("Proyecto actualizado correctamente.")
                else:
                    # Alta rápida si no hay id
                    add_proyecto(payload)
                    st.success("Proyecto creado correctamente.")

                invalidate_proyectos_cache()
                st.rerun()
            except Exception as e:
                st.error(f"No se pudo guardar el proyecto: {e}")


# ==========================
# IMPORT / EXPORT
# ==========================

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
