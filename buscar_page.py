import re
from datetime import date, datetime
from typing import Tuple, List

import pandas as pd
import streamlit as st

from data_cache import load_proyectos

try:
    from style_injector import inject_apple_style
except Exception:
    def inject_apple_style():
        pass


def _parse_date(value):
    if not value:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).date()
        except Exception:
            return None
    return None


def _render_result_table(df: pd.DataFrame, caption: str = ""):
    if caption:
        st.caption(caption)

    if df.empty:
        st.info("No hay resultados con los criterios seleccionados.")
        return

    columnas = [
        "nombre_obra",
        "cliente_principal",
        "ciudad",
        "provincia",
        "tipo_proyecto",
        "estado",
        "prioridad",
        "potencial_eur",
    ]
    columnas = [c for c in columnas if c in df.columns]

    df_tabla = df[columnas].copy()
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
        }
    )

    html_tabla = df_tabla.to_html(
        index=False,
        classes="crm-table",
        border=0,
        justify="left",
    )
    st.markdown(html_tabla, unsafe_allow_html=True)


def _buscar_por_filtros(df: pd.DataFrame):
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.markdown(
        '<h4 style="color:#032D60;margin:0 0 4px 0;">Búsqueda rápida por filtros</h4>',
        unsafe_allow_html=True,
    )

    if df.empty:
        st.info("Todavía no hay proyectos en la base de datos.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        ciudades = (
            sorted(df["ciudad"].dropna().unique().tolist())
            if "ciudad" in df.columns
            else []
        )
        ciudad_sel = st.selectbox("Ciudad", ["Todas"] + ciudades)

    with col2:
        tipos = (
            sorted(df["tipo_proyecto"].dropna().unique().tolist())
            if "tipo_proyecto" in df.columns
            else []
        )
        tipo_sel = st.selectbox("Tipo de proyecto", ["Todos"] + tipos)

    with col3:
        prioridades = (
            sorted(df["prioridad"].dropna().unique().tolist())
            if "prioridad" in df.columns
            else []
        )
        prioridad_sel = st.selectbox("Prioridad", ["Todas"] + prioridades)

    with col4:
        estados = (
            sorted(df["estado"].dropna().unique().tolist())
            if "estado" in df.columns
            else []
        )
        estado_sel = st.selectbox("Estado / Seguimiento", ["Todos"] + estados)

    col5, col6 = st.columns(2)
    with col5:
        promotores = (
            sorted(df["cliente_principal"].dropna().unique().tolist())
            if "cliente_principal" in df.columns
            else []
        )
        promotor_sel = st.selectbox("Cliente principal", ["Todos"] + promotores)

    with col6:
        potencial_min = st.number_input(
            "Potencial mínimo (€)",
            min_value=0.0,
            step=50000.0,
            value=0.0,
        )

    df_f = df.copy()

    if ciudad_sel != "Todas" and "ciudad" in df_f.columns:
        df_f = df_f[df_f["ciudad"] == ciudad_sel]
    if tipo_sel != "Todos" and "tipo_proyecto" in df_f.columns:
        df_f = df_f[df_f["tipo_proyecto"] == tipo_sel]
    if prioridad_sel != "Todas" and "prioridad" in df_f.columns:
        df_f = df_f[df_f["prioridad"] == prioridad_sel]
    if estado_sel != "Todos" and "estado" in df_f.columns:
        df_f = df_f[df_f["estado"] == estado_sel]
    if promotor_sel != "Todos" and "cliente_principal" in df_f.columns:
        df_f = df_f[df_f["cliente_principal"] == promotor_sel]
    if potencial_min and "potencial_eur" in df_f.columns:
        df_f = df_f[df_f["potencial_eur"].fillna(0) >= float(potencial_min)]

    st.markdown("<hr style='margin:8px 0 6px 0;border-color:#d8dde6;'>", unsafe_allow_html=True)
    _render_result_table(df_f, "Resultados filtrados:")

    st.markdown("</div>", unsafe_allow_html=True)


def _extraer_umbral_potencial(prompt: str) -> float | None:
    text = prompt.lower().replace(".", "")
    match = re.search(r"(\d+)\s*(k|m|millones)?", text)
    if not match:
        return None
    cantidad = float(match.group(1))
    sufijo = match.group(2)
    if sufijo == "k":
        cantidad *= 1_000
    elif sufijo in ("m", "millones"):
        cantidad *= 1_000_000
    return cantidad


def _match_valor(text_prompt: str, valores: List[str]) -> str | None:
    text = text_prompt.lower()
    for v in valores:
        if not isinstance(v, str):
            continue
        if v.lower() in text:
            return v
    return None


def _normalizar_estado(prompt: str) -> str | None:
    p = prompt.lower()
    if "ganad" in p:
        return "Ganado"
    if "perdid" in p:
        return "Perdido"
    if "negoci" in p:
        return "Negociación"
    if "oferta" in p:
        return "Oferta Enviada"
    if "prescrip" in p:
        return "En Prescripción"
    if "seguim" in p:
        return "Seguimiento"
    if "detect" in p:
        return "Detectado"
    return None


def _filtrar_por_prompt(df: pd.DataFrame, prompt: str) -> Tuple[pd.DataFrame, List[str]]:
    explicacion: List[str] = []
    df_f = df.copy()
    p = prompt.strip()
    if not p:
        return df_f, explicacion

    if "ciudad" in df_f.columns:
        ciudad = _match_valor(p, df_f["ciudad"].dropna().unique().tolist())
        if ciudad:
            df_f = df_f[df_f["ciudad"] == ciudad]
            explicacion.append(f"Ciudad = **{ciudad}**")

    if "provincia" in df_f.columns:
        prov = _match_valor(p, df_f["provincia"].dropna().unique().tolist())
        if prov and not df_f.empty:
            df_f = df_f[df_f["provincia"] == prov]
            explicacion.append(f"Provincia = **{prov}**")

    if "tipo_proyecto" in df_f.columns:
        tipo = _match_valor(p, df_f["tipo_proyecto"].dropna().unique().tolist())
        if tipo and not df_f.empty:
            df_f = df_f[df_f["tipo_proyecto"] == tipo]
            explicacion.append(f"Tipo de proyecto = **{tipo}**")

    if "prioridad" in df_f.columns:
        for key, valor in [("alta", "Alta"), ("media", "Media"), ("baja", "Baja")]:
            if key in p and valor in df_f["prioridad"].unique().tolist():
                df_f = df_f[df_f["prioridad"] == valor]
                explicacion.append(f"Prioridad = **{valor}**")
                break

    if "estado" in df_f.columns:
        est = _normalizar_estado(p)
        if est and est in df_f["estado"].unique().tolist():
            df_f = df_f[df_f["estado"] == est]
            explicacion.append(f"Estado = **{est}**")

    if "cliente_principal" in df_f.columns:
        prom = _match_valor(p, df_f["cliente_principal"].dropna().unique().tolist())
        if prom and not df_f.empty:
            df_f = df_f[df_f["cliente_principal"] == prom]
            explicacion.append(f"Cliente principal = **{prom}**")

    if "potencial_eur" in df_f.columns:
        umbral = _extraer_umbral_potencial(p)
        if umbral:
            df_f = df_f[df_f["potencial_eur"].fillna(0) >= umbral]
            explicacion.append(f"Potencial ≥ **{umbral:,.0f} €**")

    return df_f, explicacion


def _buscar_por_prompt(df: pd.DataFrame):
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.markdown(
        '<h4 style="color:#032D60;margin:0 0 4px 0;">Búsqueda inteligente por prompt</h4>',
        unsafe_allow_html=True,
    )

    if df.empty:
        st.info("Todavía no hay proyectos en la base de datos.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    st.markdown(
        """
        <p style="font-size:13px;color:#5A6872;">
        Escribe lo que quieres encontrar, por ejemplo:
        </p>
        <ul style="font-size:13px;color:#5A6872;margin-top:-8px;">
          <li>“obras residenciales de lujo en Madrid con potencial 300k”</li>
          <li>“proyectos en negociación en Málaga con prioridad alta”</li>
          <li>“hoteles en Barcelona ganados de más de 500k”</li>
        </ul>
        """,
        unsafe_allow_html=True,
    )

    prompt = st.text_area(
        "Prompt de búsqueda",
        value="Obras residenciales de lujo en Madrid con potencial 300k",
        height=80,
    )

    if st.button("🔎 Buscar", key="btn_buscar_prompt"):
        df_result, explicacion = _filtrar_por_prompt(df, prompt)

        if explicacion:
            st.markdown(
                "Filtros detectados a partir del prompt: " +
                ", ".join(explicacion)
            )
        else:
            st.caption("No se ha detectado ningún filtro concreto, mostrando todos los proyectos.")

        st.markdown("<hr style='margin:8px 0 6px 0;border-color:#d8dde6;'>", unsafe_allow_html=True)
        _render_result_table(df_result, "Resultados de la búsqueda:")

    st.markdown("</div>", unsafe_allow_html=True)


def render_buscar():
    inject_apple_style()

    st.markdown(
        """
        <div class="apple-card">
            <div class="badge">Scouting</div>
            <h3 style="margin-top:2px; margin-bottom:2px;">Buscar oportunidades de prescripción</h3>
            <p>
                Utiliza los filtros rápidos para localizar proyectos por ciudad, tipo, prioridad y estado,
                o escribe un prompt en lenguaje natural para que el CRM traduzca tu intención en filtros
                automáticos sobre la base de datos.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_proy = load_proyectos()
    if df_proy is None:
        st.info("No se han podido cargar los proyectos desde Firestore.")
        return

    tab_filtros, tab_prompt = st.tabs(
        ["🔍 Búsqueda por filtros", "🤖 Búsqueda por prompt"]
    )

    with tab_filtros:
        _buscar_por_filtros(df_proy)

    with tab_prompt:
        _buscar_por_prompt(df_proy)
