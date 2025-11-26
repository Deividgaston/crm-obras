import streamlit as st
import pandas as pd
from datetime import datetime

try:
    from style_injector import inject_apple_style
except Exception:
    def inject_apple_style():
        pass


# Estados ordenados tipo Salesforce / pipeline
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


def render_kanban(df: pd.DataFrame):
    inject_apple_style()

    st.markdown(
        """
        <div class="apple-card">
            <div class="badge">Kanban</div>
            <h3 style="margin-top:2px; margin-bottom:2px;">Pipeline Kanban</h3>
            <p>Visualiza tus proyectos en columnas por estado, estilo Salesforce.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df is None or df.empty:
        st.info("No hay proyectos disponibles.")
        return

    if "estado" not in df.columns:
        st.error("Los proyectos no tienen campo 'estado'.")
        return

    # Crear las columnas del Kanban
    num_cols = len(ESTADOS_PIPELINE)
    col_objs = st.columns(num_cols)

    # Agrupar proyectos por estado
    for idx, estado in enumerate(ESTADOS_PIPELINE):
        with col_objs[idx]:
            st.markdown(
                f"""
                <div style='
                    font-weight:600;
                    font-size:14px;
                    margin-bottom:8px;
                    color:#032D60;
                '>{estado}</div>
                """,
                unsafe_allow_html=True,
            )

            subset = df[df["estado"] == estado]

            if subset.empty:
                st.markdown(
                    f"""
                    <div class='apple-card-light' style='text-align:center; padding:8px;'>
                        <span style='color:#5A6872;'>Sin proyectos</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                continue

            # Render cards estilo Salesforce
            for _, row in subset.iterrows():
                nombre = row.get("nombre_obra", "Sin nombre")
                cliente = row.get("cliente_principal", "—")
                ciudad = row.get("ciudad", "—")
                potencial = row.get("potencial_eur", 0)
                prioridad = row.get("prioridad", "Media")

                st.markdown(
                    f"""
                    <div class="apple-card-light" style="
                        padding:10px;
                        margin-bottom:10px;
                        border-left:4px solid #0170D2;
                    ">
                        <div style="font-weight:600; font-size:13px;">{nombre}</div>

                        <div style="font-size:12px; color:#5A6872;">
                            {cliente} — {ciudad}
                        </div>

                        <div style="font-size:12px; margin-top:4px;">
                            <strong>Potencial:</strong> {potencial:,.0f} €
                        </div>

                        <div style="font-size:12px;">
                            <strong>Prioridad:</strong> {prioridad}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
