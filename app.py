import streamlit as st
from datetime import date, timedelta

# ===== IMPORTS DEL CRM (NO TOCAR) =====
from crm_utils import (
    get_clientes,
    get_proyectos,
    add_cliente,
    actualizar_proyecto,
)

from proyectos_page import render_proyectos
from buscar_page import render_buscar

# ---- Import robusto de la página de clientes ----
try:
    # Caso más habitual: función llamada render_clientes
    from clientes_page import render_clientes as _render_clientes_impl
except ImportError:
    try:
        # Plan B: si el fichero tiene la función render_clientes_page
        from clientes_page import render_clientes_page as _render_clientes_impl
    except ImportError:
        _render_clientes_impl = None


def render_clientes_wrapper():
    """
    Envuelve la función real de clientes para evitar ImportError.
    Si el módulo o la función no existen, mostramos un mensaje claro.
    """
    if _render_clientes_impl is None:
        st.error(
            "No se ha encontrado la función de clientes en `clientes_page.py`.\n\n"
            "Asegúrate de que exista una función llamada "
            "`render_clientes` **o** `render_clientes_page`."
        )
    else:
        _render_clientes_impl()


# ==========================
# CONFIGURACIÓN GENERAL
# ==========================
st.set_page_config(
    page_title="CRM Prescripción",
    layout="wide",
    page_icon="🏗️",
)

# ==========================
# ESTILO APPLE-LIKE (ajustado, encabezados más pequeños)
# ==========================
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
    background: #020617 !important; /* fondo oscuro elegante */
}

/* Contenedor principal */
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2.4rem;
    max-width: 1200px;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: rgba(15,23,42,0.98) !important;
    backdrop-filter: blur(18px);
    border-right: 1px solid rgba(148,163,184,0.35);
}
[data-testid="stSidebar"] * {
    color: #E5E7EB !important;
}

/* Títulos algo más pequeños para ganar espacio */
h1 {
    font-weight: 650 !important;
    letter-spacing: -0.03em;
    font-size: 1.55rem !important;
    margin-bottom: 0.35rem !important;
}
h2 {
    font-weight: 600 !important;
    letter-spacing: -0.02em;
    font-size: 1.25rem !important;
}
h3 {
    font-weight: 550 !important;
    font-size: 1.05rem !important;
}

/* Tarjetas */
.apple-card {
    padding: 14px 18px;
    background: radial-gradient(circle at top left, #0B1220 0%, #020617 70%);
    border-radius: 16px;
    border: 1px solid rgba(148,163,184,0.35);
    box-shadow: 0 18px 45px rgba(15,23,42,0.6);
    margin-bottom: 14px;
    color: #E5E7EB;
}

.apple-card-light {
    padding: 14px 18px;
    background: #020617;
    border-radius: 14px;
    border: 1px solid rgba(148,163,184,0.3);
    box-shadow: 0 12px 30px rgba(15,23,42,0.5);
    margin-bottom: 14px;
}

/* “Píldora” de sección */
.section-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 999px;
    background: rgba(59,130,246,0.12);
    color: #93C5FD;
    font-size: 0.75rem;
    font-weight: 500;
}

/* Métricas pequeñas tipo chips */
.chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 6px;
}
.chip {
    padding: 6px 10px;
    border-radius: 999px;
    border: 1px solid rgba(148,163,184,0.45);
    font-size: 0.74rem;
    color: #E5E7EB;
    background: rgba(15,23,42,0.9);
}

/* Listado de agenda */
.agenda-item {
    padding: 8px 10px;
    border-radius: 10px;
    border: 1px solid rgba(31,41,55,0.9);
    background: radial-gradient(circle at top left, #0F172A 0%, #020617 70%);
    margin-bottom: 6px;
    font-size: 0.86rem;
}

/* Botones */
button[kind="primary"] {
    border-radius: 999px !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# ==========================
# PANEL DE CONTROL
# ==========================


def render_panel_control():
    # ---- Cabecera ----
    st.markdown(
        """
        <div class="apple-card">
            <div class="section-badge">Agenda</div>
            <h1>Qué tengo que hacer próximamente</h1>
            <p style="color:#9CA3AF; margin-bottom:0;">
                Vista rápida de seguimientos de obras: qué está atrasado y qué viene en las próximas semanas.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_proyectos = get_proyectos()

    if df_proyectos is None or df_proyectos.empty:
        st.info("Todavía no hay proyectos en el sistema.")
        return

    # Normalizar fecha_seguimiento a date
    def _parse_fecha(value):
        if value is None:
            return None
        if isinstance(value, date):
            return value
        try:
            # puede venir en string ISO 'YYYY-MM-DD'
            return date.fromisoformat(str(value)[:10])
        except Exception:
            return None

    df = df_proyectos.copy()
    df["fecha_seg_norm"] = df.get("fecha_seguimiento").apply(_parse_fecha)

    hoy = date.today()
    horizonte = hoy + timedelta(days=14)

    # Atrasados (hoy o antes)
    atrasados = df[
        (df["fecha_seg_norm"].notna())
        & (df["fecha_seg_norm"] <= hoy)
        & (~df["estado"].isin(["Ganado", "Perdido"]))
    ].sort_values("fecha_seg_norm")

    # Próximos 14 días
    proximos = df[
        (df["fecha_seg_norm"].notna())
        & (df["fecha_seg_norm"] > hoy)
        & (df["fecha_seg_norm"] <= horizonte)
        & (~df["estado"].isin(["Ganado", "Perdido"]))
    ].sort_values("fecha_seg_norm")

    # Chips pequeñas con números totales
    num_atrasados = len(atrasados)
    num_proximos = len(proximos)

    st.markdown(
        f"""
        <div class="apple-card-light">
            <div class="chip-row">
                <div class="chip">⏰ Seguimientos atrasados: <strong>{num_atrasados}</strong></div>
                <div class="chip">📅 Próximos 14 días: <strong>{num_proximos}</strong></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    # ---- Columna izquierda: atrasados ----
    with col1:
        st.markdown(
            """
            <div class="apple-card-light">
                <h3>⏰ Atrasados / para hoy</h3>
                <p style="color:#9CA3AF; font-size:0.85rem; margin-top:0;">
                    Proyectos que deberías haber tocado ya o que vencen hoy.
                </p>
            """,
            unsafe_allow_html=True,
        )

        if atrasados.empty:
            st.success("No tienes seguimientos atrasados. ✅")
        else:
            for _, row in atrasados.iterrows():
                nombre = row.get("nombre_obra", "Sin nombre")
                cliente = row.get("cliente_principal", "—")
                ciudad = row.get("ciudad", "—")
                f = row.get("fecha_seg_norm")
                estado = row.get("estado", "—")
                notas = row.get("notas_seguimiento", "")

                st.markdown(
                    f"""
                    <div class="agenda-item">
                        <strong>{f} · {nombre}</strong><br/>
                        <span style="color:#9CA3AF;">{cliente} · {ciudad} · {estado}</span><br/>
                        <span style="color:#9CA3AF; font-size:0.8rem;">{notas or "Sin notas"}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("</div>", unsafe_allow_html=True)

    # ---- Columna derecha: próximos ----
    with col2:
        st.markdown(
            """
            <div class="apple-card-light">
                <h3>📅 Próximos 14 días</h3>
                <p style="color:#9CA3AF; font-size:0.85rem; margin-top:0;">
                    Seguimientos planificados para las próximas dos semanas.
                </p>
            """,
            unsafe_allow_html=True,
        )

        if proximos.empty:
            st.info("No hay seguimientos programados en las próximas dos semanas.")
        else:
            for _, row in proximos.iterrows():
                nombre = row.get("nombre_obra", "Sin nombre")
                cliente = row.get("cliente_principal", "—")
                ciudad = row.get("ciudad", "—")
                f = row.get("fecha_seg_norm")
                estado = row.get("estado", "—")
                notas = row.get("notas_seguimiento", "")

                st.markdown(
                    f"""
                    <div class="agenda-item">
                        <strong>{f} · {nombre}</strong><br/>
                        <span style="color:#9CA3AF;">{cliente} · {ciudad} · {estado}</span><br/>
                        <span style="color:#9CA3AF; font-size:0.8rem;">{notas or "Sin notas"}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("</div>", unsafe_allow_html=True)


# ==========================
# PÁGINA: CLIENTES (wrapper)
# ==========================
def render_clientes_page():
    render_clientes_wrapper()


# ==========================
# MAIN
# ==========================
def main():
    with st.sidebar:
        st.markdown("### 🏗️ CRM Prescripción")
        st.caption("Tu cockpit de proyectos, clientes y scouting.")
        st.markdown("---")

    menu = st.sidebar.radio(
        "Ir a:",
        ["Panel de Control", "Clientes", "Proyectos", "Buscar"],
    )

    if menu == "Panel de Control":
        render_panel_control()
    elif menu == "Clientes":
        render_clientes_page()
    elif menu == "Proyectos":
        render_proyectos()
    elif menu == "Buscar":
        render_buscar()


if __name__ == "__main__":
    main()
