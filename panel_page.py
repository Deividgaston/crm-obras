import streamlit as st
import pandas as pd
from data_cache import load_panel
from style_injector import inject_apple_style


def render_panel():
    inject_apple_style()

    # ============================
    # CABECERA CON TÍTULO MEJORADO
    # ============================
    st.markdown(
        """
        <div style="margin-bottom:18px;">
            <h1 style="
                font-size:40px;
                margin-bottom:0;
                color:#032D60;
                font-weight:700;
            ">
                Panel
            </h1>
            <div style="
                font-size:15px;
                color:#5A6872;
                margin-top:0px;
            ">
                Agenda de seguimientos y tareas del día
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ============================
    # CARGAR DATOS DEL PANEL
    # ============================
    df = load_panel()

    if df is None or df.empty:
        st.info("Todavía no hay acciones registradas.")
        return

    # ============================
    # MÉTRICAS SUPERIORES
    # ============================
    col1, col2, col3, col4 = st.columns(4)

    total = len(df)
    retrasadas = len(df[df["estado"] == "Retrasada"])
    hoy = len(df[df["es_hoy"] == True])
    proximos = len(df[df["es_prox7"] == True])

    col1.metric("Acciones", total)
    col2.metric("Retrasadas", retrasadas)
    col3.metric("Hoy", hoy)
    col4.metric("Próx. 7 días", proximos)

    st.markdown("<hr style='margin:15px 0;'>", unsafe_allow_html=True)

    # ============================
    # LISTADOS POR SECCIÓN
    # ============================

    ## 1. Retrasadas
    st.markdown("<h3 style='color:#C92A2A; font-size:20px;'>⚠ Retrasadas</h3>", unsafe_allow_html=True)
    df_retrasadas = df[df["estado"] == "Retrasada"]

    if df_retrasadas.empty:
        st.write("Sin acciones retrasadas.")
    else:
        _pintar_cards(df_retrasadas)

    ## 2. Hoy
    st.markdown("<h3 style='margin-top:25px; font-size:20px;'>📌 Hoy</h3>", unsafe_allow_html=True)
    df_hoy = df[df["es_hoy"] == True]

    if df_hoy.empty:
        st.write("Sin acciones para hoy.")
    else:
        _pintar_cards(df_hoy)

    ## 3. Próximos 7 días
    st.markdown("<h3 style='margin-top:25px; font-size:20px;'>📅 Próximos 7 días</h3>", unsafe_allow_html=True)
    df_prox = df[df["es_prox7"] == True]

    if df_prox.empty:
        st.write("Sin acciones próximas.")
    else:
        _pintar_cards(df_prox)


def _pintar_cards(df):
    """
    Renderiza tarjetas limpias y ordenadas
    """
    for _, row in df.iterrows():
        st.markdown(
            f"""
            <div style="
                background:white;
                padding:14px 18px;
                border-radius:12px;
                margin-bottom:12px;
                border:1px solid #E5E8EB;
            ">
                <div style="font-size:13px; color:#5A6872;">
                    {row['fecha']} · {row['tipo']}
                </div>

                <div style="font-size:17px; font-weight:600; margin:3px 0 4px 0;">
                    {row['nombre']}
                </div>

                <div style="font-size:13px;">
                    {row['cliente']} · {row['ciudad']} ({row['provincia']}) · {row['estado']}
                </div>

                <div style="font-size:13px; color:#334155; margin-top:6px;">
                    {row['descripcion']}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
