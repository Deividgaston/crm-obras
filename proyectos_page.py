import streamlit as st
import pandas as pd

from data_cache import load_proyectos

try:
    from style_injector import inject_apple_style
except Exception:
    def inject_apple_style():
        pass


# =====================================================
# UTILIDADES
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


def _contar_por_estado(df: pd.DataFrame) -> dict:
    if "estado" not in df.columns:
        return {e: 0 for e in ESTADOS_PIPELINE}
    conteo = df["estado"].value_counts().to_dict()
    return {e: int(conteo.get(e, 0)) for e in ESTADOS_PIPELINE}


# =====================================================
# PÁGINA DE PROYECTOS
# =====================================================
def render_proyectos():
    inject_apple_style()

    # ===== ESTILOS COMPACTOS =====
    st.markdown(
        """
        <style>
        .crm-compact-header {
            display:flex;
            align-items:center;
            justify-content:space-between;
            padding:0 0 6px 0;
            margin:0 0 6px 0;
            border-bottom:1px solid #d8dde6;
        }

        .crm-compact-title {
            font-size:16px;
            font-weight:600;
            color:#032D60;
            margin:0;
            padding:0;
            line-height:16px;
        }

        .crm-compact-subtitle {
            font-size:11px;
            color:#5A6872;
            margin:0;
            padding:0;
            line-height:12px;
        }

        .crm-tag-big {
            font-size:13px;
            font-weight:500;
            padding:4px 12px;
            border-radius:14px;
            background:#e5f2ff;
            border:1px solid #b7d4f5;
            color:#032D60;
            display:flex;
            align-items:center;
            height:28px;
            white-space:nowrap;
        }

        .crm-small-metric .stMetric {
            padding-top:0 !important;
            padding-bottom:0 !important;
            margin-top:-4px;
        }

        /* Dataframe más integrado con el fondo claro */
        .stDataFrame div[data-testid="stGrid"] {
            border-radius:6px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ===== CABECERA =====
    st.markdown(
        """
        <div class="crm-compact-header">
            <div>
                <div class="crm-compact-title">Proyectos</div>
                <div class="crm-compact-subtitle">
                    Vista general del pipeline de obras y filtros por ciudad, estado y prioridad.
                </div>
            </div>
            <div class="crm-tag-big">Vista · General</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ===== CARGA DE DATOS =====
    df = load_proyectos()

    if df is None or df.empty:
        st.info("Todavía no hay proyectos en la base de datos.")
        return

    # ===== FILTROS SUPERIORES =====
    st.markdown(
        "<div style='font-size:11px;color:#5A6872;margin-bottom:2px;'>Filtros rápidos</div>",
        unsafe_allow_html=True,
    )

    col_ciudad, col_estado, col_tipo, col_prioridad = st.columns(4)

    # Valores únicos seguros
    ciudades = sorted([c for c in df.get("ciudad", pd.Series()).dropna().unique()])
    estados = sorted([c for c in df.get("estado", pd.Series()).dropna().unique()])
    tipos = sorted([c for c in df.get("tipo_proyecto", pd.Series()).dropna().unique()])
    prioridades = sorted([c for c in df.get("prioridad", pd.Series()).dropna().unique()])

    with col_ciudad:
        ciudad_sel = st.selectbox(
            "Ciudad",
            options=["Todas"] + ciudades,
            index=0,
        )

    with col_estado:
        estado_sel = st.selectbox(
            "Estado / Seguimiento",
            options=["Todos"] + estados,
            index=0,
        )

    with col_tipo:
        tipo_sel = st.selectbox(
            "Tipo de proyecto",
            options=["Todos"] + tipos,
            index=0,
        )

    with col_prioridad:
        prioridad_sel = st.selectbox(
            "Prioridad",
            options=["Todas"] + prioridades,
            index=0,
        )

    # Aplicar filtros
    df_filtrado = df.copy()

    if ciudad_sel != "Todas" and "ciudad" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["ciudad"] == ciudad_sel]

    if estado_sel != "Todos" and "estado" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["estado"] == estado_sel]

    if tipo_sel != "Todos" and "tipo_proyecto" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["tipo_proyecto"] == tipo_sel]

    if prioridad_sel != "Todas" and "prioridad" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["prioridad"] == prioridad_sel]

    # ===== MODO DE VISTA (DE MOMENTO SOLO TABLA FUNCIONAL) =====
    st.markdown(
        "<div style='font-size:11px;color:#5A6872;margin-top:6px;'>Modo de vista</div>",
        unsafe_allow_html=True,
    )
    modo = st.radio(
        "",
        options=["Tabla", "Seguimientos", "Tareas", "Kanban"],
        horizontal=True,
        index=0,
        label_visibility="collapsed",
    )

    # ===== METRICAS PIPELINE =====
    conteo_estados = _contar_por_estado(df_filtrado)

    st.markdown('<div class="apple-card-light crm-small-metric">', unsafe_allow_html=True)
    (
        c1,
        c2,
        c3,
        c4,
        c5,
        c6,
        c7,
        c8,
    ) = st.columns(8)

    c1.metric("Detectado", conteo_estados["Detectado"])
    c2.metric("Seguimiento", conteo_estados["Seguimiento"])
    c3.metric("En Prescripción", conteo_estados["En Prescripción"])
    c4.metric("Oferta Enviada", conteo_estados["Oferta Enviada"])
    c5.metric("Negociación", conteo_estados["Negociación"])
    c6.metric("Ganado", conteo_estados["Ganado"])
    c7.metric("Perdido", conteo_estados["Perdido"])
    c8.metric("Paralizado", conteo_estados["Paralizado"])

    st.markdown("</div>", unsafe_allow_html=True)

    # ===== CONTENIDO SEGÚN MODO =====
    if modo == "Tabla":
        st.markdown(
            "<div style='font-size:11px;color:#5A6872;margin-top:6px;margin-bottom:2px;'>Vista general de proyectos</div>",
            unsafe_allow_html=True,
        )

        # Ordenar columnas importantes al principio si existen
        cols_preferidas = [
            "nombre_obra",
            "cliente_principal",
            "ciudad",
            "provincia",
            "estado",
            "prioridad",
            "tipo_proyecto",
            "potencial_eur",
        ]
        cols_existentes = [c for c in cols_preferidas if c in df_filtrado.columns]
        otras = [c for c in df_filtrado.columns if c not in cols_existentes]

        df_mostrado = df_filtrado[cols_existentes + otras]

        st.dataframe(
            df_mostrado,
            use_container_width=True,
            hide_index=True,
            height=420,
        )

    elif modo == "Seguimientos":
        st.info("La vista de Seguimientos se apoyará en los mismos datos, pero aún no está afinada. Usa de momento la vista Tabla.")

    elif modo == "Tareas":
        st.info("La vista de Tareas se implementará a partir de los datos de tareas de cada proyecto. De momento, utiliza la vista Tabla.")

    elif modo == "Kanban":
        st.info("La vista Kanban se integrará más adelante. Por ahora la vista Tabla te muestra toda la información necesaria.")
