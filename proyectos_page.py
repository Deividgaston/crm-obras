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
    """Convierte string ISO a date o devuelve None."""
    if isinstance(valor, (date, datetime)):
        return valor.date() if isinstance(valor, datetime) else valor
    if isinstance(valor, str) and valor.strip():
        try:
            return datetime.fromisoformat(valor).date()
        except Exception:
            return None
    return None


# =====================================================
# HELPERS PARA DIALOG DE EDICIÓN
# =====================================================

def _render_edit_form(row_data: dict, proy_id: str):
    """Formulario de edición reutilizable (se usa en dialog o inline)."""
    df_clientes = get_clientes()
    nombres_clientes = ["(sin asignar)"]
    if df_clientes is not None and not df_clientes.empty and "empresa" in df_clientes.columns:
        nombres_clientes = ["(sin asignar)"] + sorted(df_clientes["empresa"].dropna().unique().tolist())

    with st.form(f"edit_form_{proy_id}"):
        col1, col2 = st.columns(2)

        with col1:
            nombre_obra = st.text_input(
                "Nombre obra",
                value=row_data.get("nombre_obra", "") or "",
                key=f"nombre_obra_{proy_id}",
            )
            cliente_principal = st.selectbox(
                "Cliente principal",
                options=nombres_clientes,
                index=nombres_clientes.index(row_data.get("cliente_principal", "(sin asignar)"))
                if row_data.get("cliente_principal") in nombres_clientes
                else 0,
                key=f"cliente_principal_{proy_id}",
            )
            estado = st.selectbox(
                "Estado / Seguimiento",
                ["Detectado", "Seguimiento", "En Prescripción", "Oferta Enviada", "Negociación", "Ganado", "Perdido", "Paralizado"],
                index=["Detectado", "Seguimiento", "En Prescripción", "Oferta Enviada", "Negociación", "Ganado", "Perdido", "Paralizado"].index(
                    row_data.get("estado", "Detectado")
                ),
                key=f"estado_{proy_id}",
            )
            prioridad = st.selectbox(
                "Prioridad",
                ["Baja", "Media", "Alta", "Crítica"],
                index=["Baja", "Media", "Alta", "Crítica"].index(row_data.get("prioridad", "Media")),
                key=f"prioridad_{proy_id}",
            )

        with col2:
            ciudad = st.text_input(
                "Ciudad",
                value=row_data.get("ciudad", "") or "",
                key=f"ciudad_{proy_id}",
            )
            provincia = st.text_input(
                "Provincia",
                value=row_data.get("provincia", "") or "",
                key=f"provincia_{proy_id}",
            )
            potencial_eur = st.number_input(
                "Potencial (EUR)",
                value=float(row_data.get("potencial_eur", 0) or 0),
                min_value=0.0,
                step=10000.0,
                key=f"potencial_{proy_id}",
            )
            fecha_cierre_estimada = st.date_input(
                "Fecha cierre estimada",
                value=_parse_fecha_iso(row_data.get("fecha_cierre_estimada")) or date.today(),
                key=f"fecha_cierre_{proy_id}",
            )

        col3, col4 = st.columns(2)
        with col3:
            tipo_proyecto = st.selectbox(
                "Tipo de proyecto",
                ["Residencial", "Terciario", "Mixto", "Otro"],
                index=["Residencial", "Terciario", "Mixto", "Otro"].index(
                    row_data.get("tipo_proyecto", "Residencial")
                ),
                key=f"tipo_proyecto_{proy_id}",
            )

        with col4:
            fuente = st.text_input(
                "Fuente (contacto, partner, evento...)",
                value=row_data.get("fuente", "") or "",
                key=f"fuente_{proy_id}",
            )

        notas = st.text_area(
            "Notas de seguimiento",
            value=row_data.get("notas", "") or "",
            key=f"notas_{proy_id}",
        )

        submitted = st.form_submit_button("Guardar cambios", use_container_width=True)

    if submitted:
        data_update = {
            "nombre_obra": nombre_obra.strip(),
            "cliente_principal": None if cliente_principal == "(sin asignar)" else cliente_principal,
            "estado": estado,
            "prioridad": prioridad,
            "ciudad": ciudad.strip(),
            "provincia": provincia.strip(),
            "potencial_eur": float(potencial_eur),
            "fecha_cierre_estimada": fecha_cierre_estimada.isoformat() if fecha_cierre_estimada else None,
            "tipo_proyecto": tipo_proyecto,
            "fuente": fuente.strip(),
            "notas": notas.strip(),
        }
        actualizar_proyecto(proy_id, data_update)
        st.success("Proyecto actualizado correctamente.")
        st.experimental_rerun()


# =====================================================
# HELPERS IMPORT / EXPORT
# =====================================================

def _render_import_export(df_proy: pd.DataFrame | None = None, df_proy_empty: bool = False):
    st.markdown(
        """
        <div class="apple-card" style="margin-top: 1rem;">
            <div class="section-badge">Datos</div>
            <h3 style="margin: 4px 0;">Importar / Exportar</h3>
            <p style="color:#9CA3AF; font-size:0.9rem; margin-bottom:0;">
                Carga proyectos desde un Excel o descarga un listado de las obras importantes
                para trabajar offline o reportar.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_imp, col_exp = st.columns([1, 1])

    with col_imp:
        st.subheader("Importar desde Excel", anchor=False)
        archivo = st.file_uploader(
            "Selecciona un fichero Excel (.xlsx)",
            type=["xlsx"],
            key="upload_proyectos",
        )
        if archivo is not None:
            try:
                df_import = pd.read_excel(archivo)
                num_importados = importar_proyectos_desde_excel(df_import)
                st.success(f"Se han importado / actualizado {num_importados} proyectos.")
                st.info("Recarga la página para ver los nuevos datos.")
            except Exception as e:
                st.error(f"Ocurrió un error al importar: {e}")

    with col_exp:
        st.subheader("Exportar obras importantes", anchor=False)
        if df_proy is not None and not df_proy_empty and not df_proy.empty:
            try:
                df_filtrado = filtrar_obras_importantes(df_proy)
            except Exception:
                df_filtrado = df_proy.copy()
        else:
            df_filtrado = None

        if df_filtrado is None or df_filtrado.empty:
            st.caption("No hay suficientes datos para generar el Excel de obras importantes.")
        else:
            if st.button("Descargar Excel de obras importantes", use_container_width=True):
                try:
                    bytes_excel = generar_excel_obras_importantes(df_filtrado)
                    st.download_button(
                        "Descargar fichero",
                        data=bytes_excel,
                        file_name="obras_importantes.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.error(f"No se ha podido generar el Excel: {e}")


# =====================================================
# VISTAS
# =====================================================

def _render_vista_tabla(df_proy: pd.DataFrame):
    st.markdown(
        """
        <div class="apple-card">
            <div class="section-badge">Vista</div>
            <h3 style="margin: 4px 0;">Listado de proyectos</h3>
            <p style="color:#9CA3AF; font-size:0.9rem; margin-bottom:0;">
                Tabla completa con filtros por ciudad, estado, tipo de proyecto y prioridad.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    with col_f1:
        ciudades = ["Todas"] + sorted(df_proy["ciudad"].dropna().unique().tolist())
        filtro_ciudad = st.selectbox("Ciudad", ciudades, key="filtro_ciudad")

    with col_f2:
        estados = ["Todos"] + sorted(df_proy["estado"].dropna().unique().tolist())
        filtro_estado = st.selectbox("Estado", estados, key="filtro_estado")

    with col_f3:
        tipos = ["Todos"] + sorted(df_proy["tipo_proyecto"].dropna().unique().tolist())
        filtro_tipo = st.selectbox("Tipo de proyecto", tipos, key="filtro_tipo")

    with col_f4:
        prioridades = ["Todas"] + sorted(df_proy["prioridad"].dropna().unique().tolist())
        filtro_prioridad = st.selectbox("Prioridad", prioridades, key="filtro_prioridad")

    df_filtrado = df_proy.copy()

    if filtro_ciudad != "Todas":
        df_filtrado = df_filtrado[df_filtrado["ciudad"] == filtro_ciudad]
    if filtro_estado != "Todos":
        df_filtrado = df_filtrado[df_filtrado["estado"] == filtro_estado]
    if filtro_tipo != "Todos":
        df_filtrado = df_filtrado[df_filtrado["tipo_proyecto"] == filtro_tipo]
    if filtro_prioridad != "Todas":
        df_filtrado = df_filtrado[df_filtrado["prioridad"] == filtro_prioridad]

    st.dataframe(
        df_filtrado[
            [
                "nombre_obra",
                "cliente_principal",
                "ciudad",
                "provincia",
                "estado",
                "prioridad",
                "tipo_proyecto",
                "potencial_eur",
                "fecha_cierre_estimada",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Haz scroll horizontal para ver todas las columnas. "
        "Los filtros se aplican de forma combinada."
    )


def _render_vista_analitica(df_proy: pd.DataFrame):
    st.markdown(
        """
        <div class="apple-card">
            <div class="section-badge">Analítica</div>
            <h3 style="margin: 4px 0;">Distribución y potencial</h3>
            <p style="color:#9CA3AF; font-size:0.9rem; margin-bottom:0;">
                Gráficos rápidos para entender dónde está el volumen de proyectos y el potencial económico.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        if "estado" in df_proy.columns:
            df_estados = (
                df_proy.groupby("estado")
                .agg(num=("estado", "count"))
                .reset_index()
                .sort_values("num", ascending=False)
            )

            chart_estados = (
                alt.Chart(df_estados)
                .mark_bar()
                .encode(
                    x=alt.X("estado:N", sort="-y", title="Estado"),
                    y=alt.Y("num:Q", title="Nº de proyectos"),
                    tooltip=["estado", "num"],
                )
                .properties(height=280)
            )

            st.altair_chart(chart_estados, use_container_width=True)
        else:
            st.caption("No hay datos suficientes para mostrar la distribución por estado.")

    with col2:
        if "tipo_proyecto" in df_proy.columns and "potencial_eur" in df_proy.columns:
            df_tipo_pot = (
                df_proy.groupby("tipo_proyecto")
                .agg(potencial_total=("potencial_eur", "sum"))
                .reset_index()
            )

            chart_tipo = (
                alt.Chart(df_tipo_pot)
                .mark_arc(innerRadius=40)
                .encode(
                    theta=alt.Theta("potencial_total:Q", title="Potencial total (EUR)"),
                    color=alt.Color("tipo_proyecto:N", title="Tipo de proyecto"),
                    tooltip=["tipo_proyecto", "potencial_total"],
                )
                .properties(height=280)
            )

            st.altair_chart(chart_tipo, use_container_width=True)
        else:
            st.caption("No hay datos suficientes para mostrar el potencial por tipo de proyecto.")

    st.markdown("---")

    if "prioridad" in df_proy.columns and "potencial_eur" in df_proy.columns:
        df_priority = (
            df_proy.groupby("prioridad")
            .agg(
                potencial_total=("potencial_eur", "sum"),
                num=("prioridad", "count"),
            )
            .reset_index()
        )

        left, right = st.columns([2, 1])

        with left:
            chart_priority = (
                alt.Chart(df_priority)
                .mark_bar()
                .encode(
                    x=alt.X("prioridad:N", sort=["Crítica", "Alta", "Media", "Baja"], title="Prioridad"),
                    y=alt.Y("potencial_total:Q", title="Potencial total (EUR)"),
                    tooltip=["prioridad", "potencial_total", "num"],
                )
                .properties(height=260)
            )
            st.altair_chart(chart_priority, use_container_width=True)

        with right:
            st.metric(
                "Potencial total estimado",
                f"{df_proy['potencial_eur'].sum():,.0f} €".replace(",", "."),
            )
            st.metric(
                "Nº de proyectos activos",
                str(len(df_proy)),
            )
            df_ganados = df_proy[df_proy["estado"] == "Ganado"] if "estado" in df_proy.columns else pd.DataFrame()
            st.metric(
                "Proyectos ganados",
                str(len(df_ganados)),
            )


def _render_vista_tareas(df_proy: pd.DataFrame):
    st.markdown(
        """
        <div class="apple-card">
            <div class="section-badge">Tareas</div>
            <h3 style="margin: 4px 0;">Seguimientos pendientes</h3>
            <p style="color:#9CA3AF; font-size:0.9rem; margin-bottom:0;">
                Lista de acciones y seguimientos por obra, ordenadas por urgencia y fecha.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    hoy = date.today()
    df_tareas = df_proy.copy()

    if "fecha_cierre_estimada" in df_tareas.columns:
        df_tareas["fecha_cierre_estimada"] = pd.to_datetime(
            df_tareas["fecha_cierre_estimada"], errors="coerce"
        )
    else:
        df_tareas["fecha_cierre_estimada"] = pd.NaT

    df_tareas["dias_hasta_cierre"] = (df_tareas["fecha_cierre_estimada"] - pd.Timestamp(hoy)).dt.days

    df_tareas["prioridad_num"] = df_tareas["prioridad"].map(
        {"Crítica": 1, "Alta": 2, "Media": 3, "Baja": 4}
    )
    df_tareas["prioridad_num"] = df_tareas["prioridad_num"].fillna(5)

    df_tareas = df_tareas.sort_values(
        by=["prioridad_num", "dias_hasta_cierre"],
        ascending=[True, True],
    )

    for _, row in df_tareas.iterrows():
        with st.expander(
            f"{row.get('nombre_obra', 'Sin nombre')} · {row.get('ciudad','')} "
            f"· {row.get('estado', '')} · {row.get('prioridad', '')}"
        ):
            st.write("**Cliente principal:**", row.get("cliente_principal", "No asignado"))
            st.write("**Tipo de proyecto:**", row.get("tipo_proyecto", "No definido"))
            st.write(
                "**Fecha cierre estimada:**",
                row.get("fecha_cierre_estimada", "Sin definir"),
            )
            st.write(
                "**Potencial estimado:**",
                f"{row.get('potencial_eur', 0):,.0f} €".replace(",", "."),
            )
            st.write("**Notas / siguiente acción:**")
            st.write(row.get("notas", "Sin notas registradas"))

            st.markdown(
                """
                <p style="color:#9CA3AF; font-size:0.8rem;">
                Revisa esta obra y define la próxima acción clara (llamada, email, visita, demo...).
                </p>
                """,
                unsafe_allow_html=True,
            )


def _render_vista_kanban(df_proy: pd.DataFrame):
    st.markdown(
        """
        <div class="apple-card">
            <div class="section-badge">Pipeline</div>
            <h3 style="margin: 4px 0;">Vista Kanban simplificada</h3>
            <p style="color:#9CA3AF; font-size:0.9rem; margin-bottom:0;">
                Reparto de proyectos por columnas de estado para entender el flujo completo.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    columnas = [
        "Detectado",
        "Seguimiento",
        "En Prescripción",
        "Oferta Enviada",
        "Negociación",
        "Ganado",
        "Perdido",
        "Paralizado",
    ]

    col_objs = st.columns(len(columnas))

    for estado, col in zip(columnas, col_objs):
        with col:
            st.markdown(
                f"""
                <div style="
                    background-color:#F3F4F6;
                    border-radius:10px;
                    padding:8px;
                    min-height:120px;
                ">
                    <div style="font-weight:600; margin-bottom:4px;">{estado}</div>
                """,
                unsafe_allow_html=True,
            )

            df_estado = df_proy[df_proy["estado"] == estado]

            if df_estado.empty:
                st.caption("Sin proyectos")
            else:
                for _, row in df_estado.iterrows():
                    st.markdown(
                        f"""
                        <div style="
                            background-color:white;
                            border-radius:8px;
                            padding:6px;
                            margin-bottom:6px;
                            box-shadow:0 1px 3px rgb(0 0 0 / 0.08);
                            font-size:0.78rem;
                        ">
                            <div style="font-weight:600;">{row.get('nombre_obra','Obra sin nombre')}</div>
                            <div style="color:#6B7280;">{row.get('ciudad','')} · {row.get('provincia','')}</div>
                            <div style="color:#6B7280;">
                                Potencial: {row.get('potencial_eur',0):,.0f} €</div>
                        </div>
                        """.replace(",", "."),
                        unsafe_allow_html=True,
                    )

            st.markdown("</div>", unsafe_allow_html=True)


# =====================================================
# CREAR NUEVO PROYECTO
# =====================================================

def _render_alta_manual():
    st.markdown(
        """
        <div class="apple-card">
            <div class="section-badge">Nuevo</div>
            <h3 style="margin: 4px 0;">Alta manual de proyecto</h3>
            <p style="color:#9CA3AF; font-size:0.9rem; margin-bottom:0;">
                Crea una nueva obra con los campos mínimos para empezar a hacer seguimiento.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_clientes = get_clientes()
    nombres_clientes = ["(sin asignar)"]
    if df_clientes is not None and not df_clientes.empty and "empresa" in df_clientes.columns:
        nombres_clientes = ["(sin asignar)"] + sorted(df_clientes["empresa"].dropna().unique().tolist())

    with st.form("alta_manual_proyecto"):
        col1, col2 = st.columns(2)

        with col1:
            nombre_obra = st.text_input("Nombre obra *", key="alta_nombre_obra")
            cliente_principal = st.selectbox(
                "Cliente principal",
                options=nombres_clientes,
                key="alta_cliente_principal",
            )
            ciudad = st.text_input("Ciudad", key="alta_ciudad")
            provincia = st.text_input("Provincia", key="alta_provincia")

        with col2:
            tipo_proyecto = st.selectbox(
                "Tipo de proyecto",
                ["Residencial", "Terciario", "Mixto", "Otro"],
                key="alta_tipo_proyecto",
            )
            estado = st.selectbox(
                "Estado / Seguimiento",
                ["Detectado", "Seguimiento", "En Prescripción", "Oferta Enviada", "Negociación", "Ganado", "Perdido", "Paralizado"],
                index=0,
                key="alta_estado",
            )
            prioridad = st.selectbox(
                "Prioridad",
                ["Baja", "Media", "Alta", "Crítica"],
                index=1,
                key="alta_prioridad",
            )

        col3, col4 = st.columns(2)

        with col3:
            potencial_eur = st.number_input(
                "Potencial (EUR)",
                min_value=0.0,
                step=10000.0,
                value=0.0,
                key="alta_potencial",
            )

        with col4:
            fecha_cierre_estimada = st.date_input(
                "Fecha cierre estimada (opcional)",
                value=date.today() + timedelta(days=180),
                key="alta_fecha_cierre",
            )

        notas = st.text_area(
            "Notas / Próxima acción",
            key="alta_notas",
            help="Describe brevemente el contexto y cuál es el siguiente paso.",
        )

        submitted = st.form_submit_button("Crear proyecto", use_container_width=True)

    if submitted:
        if not nombre_obra.strip():
            st.error("El campo 'Nombre obra' es obligatorio.")
            return

        data = {
            "nombre_obra": nombre_obra.strip(),
            "cliente_principal": None if cliente_principal == "(sin asignar)" else cliente_principal,
            "ciudad": ciudad.strip(),
            "provincia": provincia.strip(),
            "tipo_proyecto": tipo_proyecto,
            "estado": estado,
            "prioridad": prioridad,
            "potencial_eur": float(potencial_eur),
            "fecha_cierre_estimada": fecha_cierre_estimada.isoformat() if fecha_cierre_estimada else None,
            "fuente": None,
            "notas": notas.strip(),
            "fecha_creacion": datetime.utcnow().isoformat(),
            "pasos_seguimiento": default_pasos_seguimiento(),
        }

        nuevo_id = add_proyecto(data)
        if nuevo_id:
            st.success("Proyecto creado correctamente.")
        else:
            st.error("No se ha podido crear el proyecto.")
        st.experimental_rerun()


# =====================================================
# LISTADO Y EDICIÓN EN TABLA
# =====================================================

def _render_edicion_proyectos(df_proy: pd.DataFrame):
    st.markdown(
        """
        <div class="apple-card">
            <div class="section-badge">Edición</div>
            <h3 style="margin: 4px 0;">Editar proyectos existentes</h3>
            <p style="color:#9CA3AF; font-size:0.9rem; margin-bottom:0;">
                Localiza un proyecto y abre la ficha de edición para actualizar sus datos principales.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df_proy.empty:
        st.info("Todavía no hay proyectos para editar.")
        return

    col_buscar, col_estado = st.columns([2, 1])

    with col_buscar:
        texto_busqueda = st.text_input(
            "Buscar por nombre, cliente o ciudad",
            key="buscar_edicion",
            placeholder="Ej. 'Higuerón', 'Lucas Fox', 'Málaga'...",
        )

    with col_estado:
        estados = ["Todos"] + sorted(df_proy["estado"].dropna().unique().tolist())
        estado_sel = st.selectbox("Filtrar por estado", estados, key="estado_edicion")

    df_filtrado = df_proy.copy()

    if texto_busqueda.strip():
        mask = (
            df_filtrado["nombre_obra"].fillna("").str.contains(texto_busqueda, case=False)
            | df_filtrado["cliente_principal"].fillna("").str.contains(texto_busqueda, case=False)
            | df_filtrado["ciudad"].fillna("").str.contains(texto_busqueda, case=False)
        )
        df_filtrado = df_filtrado[mask]

    if estado_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado["estado"] == estado_sel]

    df_filtrado = df_filtrado.sort_values("nombre_obra")

    st.caption(f"{len(df_filtrado)} proyectos encontrados.")

    for idx, row in df_filtrado.iterrows():
        proy_id = row.get("id")
        if not proy_id:
            continue

        with st.expander(
            f"{row.get('nombre_obra','(Sin nombre)')} · {row.get('ciudad','')} "
            f"· {row.get('estado','')} · {row.get('prioridad','')}"
        ):
            st.write("**Cliente principal:**", row.get("cliente_principal", "No asignado"))
            st.write("**Tipo de proyecto:**", row.get("tipo_proyecto", "No definido"))
            st.write(
                "**Potencial estimado:**",
                f"{row.get('potencial_eur', 0):,.0f} €".replace(",", "."),
            )
            st.write("**Notas actuales:**")
            st.write(row.get("notas", "Sin notas registradas"))

            col_editar, col_borrar = st.columns([3, 1])

            with col_editar:
                with st.expander("Editar proyecto", expanded=False):
                    _render_edit_form(row.to_dict(), proy_id)

            with col_borrar:
                st.markdown("### ")
                if st.button("Borrar", key=f"borrar_{proy_id}", type="secondary"):
                    delete_proyecto(proy_id)
                    st.success("Proyecto borrado correctamente.")
                    st.experimental_rerun()


# =====================================================
# RENDER PRINCIPAL
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
        _render_alta_manual()
        return

    if "fecha_cierre_estimada" in df_proy.columns:
        df_proy["fecha_cierre_estimada"] = pd.to_datetime(
            df_proy["fecha_cierre_estimada"], errors="coerce"
        ).dt.date
    else:
        df_proy["fecha_cierre_estimada"] = None

    columnas_por_defecto = [
        "nombre_obra",
        "cliente_principal",
        "ciudad",
        "provincia",
        "tipo_proyecto",
        "estado",
        "prioridad",
        "potencial_eur",
        "fecha_cierre_estimada",
    ]
    for col in columnas_por_defecto:
        if col not in df_proy.columns:
            df_proy[col] = None

    st.markdown(
        """
        <style>
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            padding-top: 4px;
            padding-bottom: 4px;
            padding-left: 12px;
            padding-right: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Vista general", "Analítica", "Tareas", "Kanban", "Alta / Edición"]
    )

    with tab1:
        _render_vista_tabla(df_proy)

    with tab2:
        _render_vista_analitica(df_proy)

    with tab3:
        _render_vista_tareas(df_proy)

    with tab4:
        _render_vista_kanban(df_proy)

    with tab5:
        subtab1, subtab2, subtab3 = st.tabs(
            ["Alta manual", "Edición", "Importar / Exportar"]
        )
        with subtab1:
            _render_alta_manual()
        with subtab2:
            _render_edicion_proyectos(df_proy)
        with subtab3:
            _render_import_export(df_proy=df_proy, df_proy_empty=False)
