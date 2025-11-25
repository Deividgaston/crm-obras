import streamlit as st
import pandas as pd
from datetime import datetime, date
from crm_utils import (
    get_proyectos,
    add_proyecto,
    actualizar_proyecto,
    delete_proyecto,
)

try:
    from style_injector import inject_apple_style
except Exception:
    def inject_apple_style():
        pass


# ===============================================================
# HELPERS
# ===============================================================
def _safe_parse_date(valor):
    """Intenta parsear un valor a date (para el formulario de edición)."""
    from datetime import datetime, date, timedelta

    if not valor:
        return None

    if isinstance(valor, date) and not isinstance(valor, datetime):
        return valor

    if isinstance(valor, datetime):
        return valor.date()

    if isinstance(valor, (int, float)):
        base = datetime(1899, 12, 30)
        try:
            return (base + timedelta(days=float(valor))).date()
        except Exception:
            return None

    if isinstance(valor, str):
        valor = valor.strip()
        if not valor:
            return None
        formatos = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%d/%m/%Y",
            "%d-%m-%Y",
        ]
        for fmt in formatos:
            try:
                return datetime.strptime(valor, fmt).date()
            except ValueError:
                continue

    return None


def _index_estado(valor):
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
    try:
        return estados.index(valor)
    except Exception:
        return 0


def _index_prioridad(valor):
    prioridades = ["Alta", "Media", "Baja"]
    try:
        return prioridades.index(valor)
    except Exception:
        return 1  # Media por defecto


# ===============================================================
# RENDER PRINCIPAL
# ===============================================================
def render_proyectos():
    """
    Página principal de proyectos:
    - Cabecera tipo Apple
    - Filtros
    - Pipeline por estado
    - Tabla con selección + acciones
    - Formulario de nuevo proyecto
    """
    inject_apple_style()

    # Cabecera Apple card
    st.markdown(
        """
        <div class="apple-card">
            <div class="badge">Gestión de obras</div>
            <h1 style="margin-top:4px; margin-bottom:4px;">📁 Proyectos</h1>
            <p style="font-size:0.9rem; color:#9ca3af; margin-bottom:0;">
                Aquí concentras todas las obras en prescripción: estado, prioridad, 
                potencial 2N y datos clave de promotoras, ingenierías y arquitecturas.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---- Cargar proyectos (una sola lectura, cacheada en crm_utils) ----
    with st.spinner("Cargando proyectos…"):
        try:
            proyectos = get_proyectos()
        except Exception as e:
            st.error("❌ Error cargando proyectos desde Firestore.")
            st.code(str(e))
            return

    df = pd.DataFrame(proyectos)

    if df.empty:
        st.info("No hay proyectos creados todavía.")
        _boton_crear()
        return

    # Orden por fecha creación si existe
    if "fecha_creacion" in df.columns:
        df["fecha_creacion"] = pd.to_datetime(
            df["fecha_creacion"], errors="coerce"
        )
        df = df.sort_values(by="fecha_creacion", ascending=False)

    df = df.reset_index(drop=True)

    _vista_filtros(df)
    _boton_crear()


# ===============================================================
# BOTÓN CREAR NUEVO PROYECTO
# ===============================================================
def _boton_crear():
    st.markdown("---")
    if st.button("➕ Crear nuevo proyecto", use_container_width=True):
        _open_nuevo_dialog()


# ===============================================================
# FILTROS
# ===============================================================
def _vista_filtros(df: pd.DataFrame):
    st.markdown(
        """
        <div class="apple-card-light">
            <div class="badge">Filtros</div>
            <h3 style="margin-top:8px; margin-bottom:4px;">🔍 Filtro rápido de proyectos</h3>
            <p class="small-caption">
                Filtra por estado y busca por nombre de obra. Así te centras solo en el
                tramo del pipeline que quieras empujar hoy.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    estados = sorted(df["estado"].dropna().unique().tolist()) if "estado" in df.columns else []

    col1, col2 = st.columns(2)
    with col1:
        estado_filtrado = st.multiselect("Estado", estados, default=estados)
    with col2:
        texto = st.text_input("Buscar por nombre de obra o cliente:")

    df_filtrado = df.copy()

    if estado_filtrado and "estado" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["estado"].isin(estado_filtrado)]

    if texto.strip():
        texto_low = texto.lower()
        columnas_busqueda = []
        for col in ["nombre_obra", "cliente", "cliente_principal", "promotora", "ciudad", "provincia"]:
            if col in df_filtrado.columns:
                columnas_busqueda.append(col)

        if columnas_busqueda:
            mask = pd.Series(False, index=df_filtrado.index)
            for col in columnas_busqueda:
                mask = mask | df_filtrado[col].astype(str).str.lower().str.contains(texto_low)
            df_filtrado = df_filtrado[mask]

    _vista_tabla(df_filtrado)


# ===============================================================
# TABLA PRINCIPAL + ACCIONES
# ===============================================================
def _vista_tabla(df_filtrado: pd.DataFrame):

    # ---------------- Pipeline ----------------
    st.markdown(
        """
        <div class="apple-card-light">
            <div class="badge">Pipeline</div>
            <h3 style="margin-top:8px; margin-bottom:4px;">🧪 Estado del pipeline</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not df_filtrado.empty and "estado" in df_filtrado.columns:
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
        st.info("No hay información de estados para mostrar el pipeline.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------- Tabla ----------------
    st.markdown(
        """
        <div class="apple-card-light">
            <div class="badge">Lista de proyectos</div>
            <h3 style="margin-top:8px; margin-bottom:4px;">📂 Proyectos filtrados</h3>
            <p class="small-caption">
                Selecciona uno o varios proyectos con el checkbox de la izquierda y utiliza
                los iconos superiores para editar o eliminar en bloque.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df_filtrado.empty:
        st.warning("No hay proyectos con esos filtros.")
        return

    df_raw = df_filtrado.reset_index(drop=True).copy()

    # Identificadores de proyecto
    if "id" in df_raw.columns:
        ids = df_raw["id"].tolist()
    else:
        # fallback por si acaso, aunque en tu Firestore siempre hay id
        ids = list(range(len(df_raw)))
        df_raw["id"] = ids

    # Estado de selección persistente en sesión
    sel_key = "seleccion_proyectos"
    if sel_key not in st.session_state:
        st.session_state[sel_key] = {}

    sel_state = st.session_state[sel_key]
    for pid in ids:
        sel_state.setdefault(pid, False)

    # Construcción de la tabla UI
    df_ui = df_raw.copy()

    # Creamos un campo visual de selección
    df_ui["seleccionar"] = [sel_state.get(pid, False) for pid in ids]

    # Quitamos el id de la vista pero lo mantenemos internamente
    df_ui_visual = df_ui.drop(columns=["id"])

    # Reordenamos columnas: nombre_obra primero, seleccionar después
    cols = list(df_ui_visual.columns)
    if "nombre_obra" in cols:
        cols.remove("nombre_obra")
        cols.insert(0, "nombre_obra")
    if "seleccionar" in cols:
        cols.remove("seleccionar")
        cols.insert(1, "seleccionar")

    actions_placeholder = st.empty()

    edited_df = st.data_editor(
        df_ui_visual[cols],
        column_config={
            "seleccionar": st.column_config.CheckboxColumn("Sel"),
        },
        hide_index=True,
        use_container_width=True,
        key="tabla_proyectos_editor",
    )

    edited_df = edited_df.reset_index(drop=True)

    # Actualizar selección en session_state
    if "seleccionar" in edited_df.columns:
        for idx, pid in enumerate(ids):
            try:
                sel_state[pid] = bool(edited_df.loc[idx, "seleccionar"])
            except Exception:
                sel_state[pid] = False

    # --------- Barra de acciones arriba ----------
    with actions_placeholder.container():
        col_txt, col_sel_all, col_edit, col_delete = st.columns([3, 1, 0.7, 0.7])

        with col_txt:
            st.markdown(
                "<span style='font-size:0.8rem; color:#6B7280;'>Acciones rápidas:</span>",
                unsafe_allow_html=True,
            )

        # Seleccionar todos
        with col_sel_all:
            if st.button("☑️", help="Seleccionar todos los proyectos visibles"):
                for pid in ids:
                    sel_state[pid] = True
                st.rerun()

        # Editar seleccionado
        with col_edit:
            if st.button("✏️", help="Editar el primer proyecto seleccionado"):
                marcados = [
                    i
                    for i, v in edited_df.get("seleccionar", pd.Series([])).items()
                    if v
                ]
                if not marcados:
                    st.warning("Selecciona al menos un proyecto para editar.")
                else:
                    idx = marcados[0]
                    proyecto_id = ids[idx]
                    datos = df_raw.iloc[idx].to_dict()
                    _open_edit_dialog(datos, proyecto_id)

        # Borrar seleccionados
        with col_delete:
            if st.button("🗑️", help="Borrar proyectos seleccionados"):
                marcados = [
                    i
                    for i, v in edited_df.get("seleccionar", pd.Series([])).items()
                    if v
                ]
                if not marcados:
                    st.warning("No hay proyectos seleccionados para borrar.")
                else:
                    eliminados = 0
                    for i in marcados:
                        try:
                            delete_proyecto(ids[i])
                            eliminados += 1
                        except Exception:
                            pass

                    st.success(f"Eliminados {eliminados} proyecto(s).")
                    # La propia delete_proyecto debería limpiar caché en crm_utils.
                    st.rerun()


# ===============================================================
# CREAR NUEVO PROYECTO
# ===============================================================
def _open_nuevo_dialog():
    with st.form("nuevo_proyecto_form"):
        st.markdown("### ➕ Nuevo proyecto")

        nombre = st.text_input("Nombre de la obra")
        cliente = st.text_input("Cliente / Promotora principal")
        provincia = st.text_input("Provincia")
        ciudad = st.text_input("Ciudad")

        col1, col2 = st.columns(2)
        with col1:
            estado = st.selectbox(
                "Estado",
                [
                    "Detectado",
                    "Seguimiento",
                    "En Prescripción",
                    "Oferta Enviada",
                    "Negociación",
                    "Ganado",
                    "Perdido",
                    "Paralizado",
                ],
            )
        with col2:
            prioridad = st.selectbox(
                "Prioridad",
                ["Alta", "Media", "Baja"],
                index=1,
            )

        potencial = st.number_input(
            "Potencial 2N (€)",
            min_value=0.0,
            step=1000.0,
            format="%.0f",
        )

        col3, col4 = st.columns(2)
        with col3:
            fecha_seg = st.date_input(
                "Fecha de seguimiento (opcional)",
                value=None,
                format="DD/MM/YYYY",
            )
        with col4:
            notas = st.text_area("Notas", height=80)

        enviado = st.form_submit_button("Guardar")

        if enviado:
            if not nombre:
                st.warning("El nombre de la obra es obligatorio.")
                return

            fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M")
            fecha_seguimiento_str = (
                fecha_seg.isoformat() if isinstance(fecha_seg, date) else ""
            )

            data = {
                "nombre_obra": nombre,
                "cliente": cliente,
                "cliente_principal": cliente,
                "promotora": cliente,
                "provincia": provincia,
                "ciudad": ciudad,
                "estado": estado,
                "prioridad": prioridad,
                "potencial_eur": float(potencial),
                "fecha_creacion": fecha_creacion,
                "fecha_seguimiento": fecha_seguimiento_str,
                "notas": notas,
            }

            add_proyecto(data)
            st.success("Proyecto creado correctamente.")
            st.rerun()


# ===============================================================
# EDITAR PROYECTO
# ===============================================================
def _open_edit_dialog(row_data: dict, proyecto_id: str):
    with st.form(f"editar_proyecto_{proyecto_id}"):
        st.markdown("### ✏️ Editar proyecto")

        nombre = st.text_input("Nombre de la obra", row_data.get("nombre_obra", ""))
        cliente = st.text_input(
            "Cliente / Promotora principal",
            row_data.get("cliente_principal")
            or row_data.get("promotora")
            or row_data.get("cliente", ""),
        )
        provincia = st.text_input("Provincia", row_data.get("provincia", ""))
        ciudad = st.text_input("Ciudad", row_data.get("ciudad", ""))

        col1, col2 = st.columns(2)
        with col1:
            estado = st.selectbox(
                "Estado",
                [
                    "Detectado",
                    "Seguimiento",
                    "En Prescripción",
                    "Oferta Enviada",
                    "Negociación",
                    "Ganado",
                    "Perdido",
                    "Paralizado",
                ],
                index=_index_estado(row_data.get("estado")),
            )
        with col2:
            prioridad = st.selectbox(
                "Prioridad",
                ["Alta", "Media", "Baja"],
                index=_index_prioridad(row_data.get("prioridad")),
            )

        potencial_val = 0.0
        try:
            potencial_val = float(row_data.get("potencial_eur", 0.0) or 0.0)
        except Exception:
            potencial_val = 0.0

        potencial = st.number_input(
            "Potencial 2N (€)",
            min_value=0.0,
            step=1000.0,
            format="%.0f",
            value=potencial_val,
        )

        fecha_seg_raw = row_data.get("fecha_seguimiento")
        fecha_seg_parsed = _safe_parse_date(fecha_seg_raw)
        fecha_seg = st.date_input(
            "Fecha de seguimiento (opcional)",
            value=fecha_seg_parsed,
            format="DD/MM/YYYY",
        )

        notas = st.text_area("Notas", row_data.get("notas", ""), height=80)

        enviado = st.form_submit_button("Guardar cambios")

        if enviado:
            if not nombre:
                st.warning("El nombre de la obra es obligatorio.")
                return

            fecha_seguimiento_str = (
                fecha_seg.isoformat() if isinstance(fecha_seg, date) else ""
            )

            data = {
                "nombre_obra": nombre,
                "cliente": cliente,
                "cliente_principal": cliente,
                "promotora": cliente,
                "provincia": provincia,
                "ciudad": ciudad,
                "estado": estado,
                "prioridad": prioridad,
                "potencial_eur": float(potencial),
                "fecha_seguimiento": fecha_seguimiento_str,
                "notas": notas,
            }

            actualizar_proyecto(proyecto_id, data)
            st.success("Proyecto actualizado.")
            st.rerun()
