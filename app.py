import streamlit as st
from datetime import date, timedelta

# ⬇️ ENVOLVEMOS EL IMPORT DE crm_utils EN UN try/except
try:
    from crm_utils import (
        get_clientes,
        get_proyectos,
        add_cliente,
        add_proyecto,
        actualizar_proyecto,
        delete_proyecto,
        default_pasos_seguimiento,
        filtrar_obras_importantes,
        importar_proyectos_desde_excel,
        generar_excel_obras_importantes,
    )
except Exception as e:
    st.error(
        "❌ Error al importar `crm_utils.py`.\n\n"
        "Comprueba que el fichero `crm_utils.py` está en el mismo directorio que `app.py` "
        "y que las credenciales de Firebase (`firebase_key`) en `st.secrets` son correctas.\n\n"
        f"Detalle técnico: {type(e).__name__}: {e}"
    )
    st.stop()

# A partir de aquí, el resto de tu app.py como lo tenías
from proyectos_page import render_proyectos
from buscar_page import render_buscar
from clientes_page import render_clientes_page



# ======================================================
# CONFIGURACIÓN GENERAL + ESTILO
# ======================================================

inicializar_firebase_si_necesario()

st.set_page_config(
    page_title="CRM Prescripción",
    layout="wide",
    page_icon="🏗️",
)

# ---------- Estilos globales ----------
st.markdown(
    """
<style>
/* Fuente tipo SF / Inter */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Fondo general dark azul */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
    background: radial-gradient(circle at top left, #020617 0%, #020617 40%, #020617 100%) !important;
}

/* Contenedor principal */
.block-container {
    padding-top: 1.0rem;
    padding-bottom: 2.5rem;
    max-width: 1300px;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #020617;
    border-right: 1px solid rgba(148,163,184,0.25);
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span {
    color: #E5E7EB !important;
}

/* Top bar & cards */
.crm-top-bar {
    padding: 10px 18px;
    border-radius: 18px;
    background: linear-gradient(135deg, #020617 0%, #020617 50%, #020617 100%);
    border: 1px solid rgba(148,163,184,0.35);
    box-shadow: 0 22px 50px rgba(15,23,42,0.75);
    margin-bottom: 14px;
}

.crm-metric-row {
    display: flex;
    gap: 16px;
    margin-top: 8px;
}
.crm-metric-card {
    flex: 1;
    padding: 12px 16px;
    border-radius: 14px;
    background: radial-gradient(circle at top left, #020617 0%, #020617 70%);
    border: 1px solid rgba(148,163,184,0.4);
}
.crm-metric-title {
    font-size: 0.70rem;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    color: #9CA3AF;
}
.crm-metric-value {
    font-size: 1.4rem;
    font-weight: 650;
    color: #F9FAFB;
    margin-top: 2px;
}
.crm-metric-sub {
    font-size: 0.78rem;
    color: #9CA3AF;
    margin-top: 2px;
}

/* Tarjetas de contenido */
.crm-card {
    padding: 14px 16px;
    border-radius: 16px;
    background: radial-gradient(circle at top left, #020617 0%, #020617 70%);
    border: 1px solid rgba(148,163,184,0.45);
    box-shadow: 0 16px 35px rgba(15,23,42,0.65);
    margin-bottom: 14px;
}
.crm-card-light {
    padding: 14px 16px;
    border-radius: 16px;
    background: #020617;
    border: 1px solid rgba(148,163,184,0.32);
    margin-bottom: 14px;
}

/* Títulos */
h1 {
    font-size: 1.35rem !important;
    font-weight: 640 !important;
    letter-spacing: -0.03em;
    color: #F9FAFB !important;
    margin-bottom: 0.15rem !important;
}
h2 {
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em;
    color: #E5E7EB !important;
}
h3 {
    font-size: 0.96rem !important;
    font-weight: 580 !important;
    color: #E5E7EB !important;
}

/* Badges */
.section-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 9px;
    border-radius: 999px;
    background: rgba(59,130,246,0.23);
    color: #BFDBFE;
    font-size: 0.70rem;
    font-weight: 500;
    text-transform: uppercase;
}

/* Texto pequeño gris */
.text-muted {
    font-size: 0.8rem;
    color: #9CA3AF;
}

/* Checklist status pills */
.status-pill {
    display: inline-flex;
    align-items: center;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 500;
}
.status-green { background: rgba(34,197,94,0.12); color:#22C55E; }
.status-red   { background: rgba(248,113,113,0.12); color:#F97373; }
.status-amber { background: rgba(251,191,36,0.12); color:#FBBF24; }

/* Tab labels algo más compactos */
button[data-baseweb="tab"] > div {
    font-size: 0.86rem;
}

/* Dataframes oscuros */
[data-testid="stDataFrame"] {
    background-color: #020617 !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# ======================================================
# FUNCIONES AUXILIARES
# ======================================================


def _formato_millones(euros: float) -> str:
    if euros is None:
        return "0 €"
    try:
        millones = euros / 1_000_000
        if millones >= 1:
            return f"{millones:,.1f} M€".replace(",", ".")
        return f"{euros:,.0f} €".replace(",", ".")
    except Exception:
        return str(euros)


def _get_modo_compacto() -> bool:
    """Lee el toggle global de la barra lateral."""
    return bool(st.session_state.get("modo_compacto", False))


# ======================================================
# PANEL DE CONTROL (Dashboard principal)
# ======================================================

def render_panel_control():
    compacto = _get_modo_compacto()

    df_clientes = get_clientes()
    df_proyectos = get_proyectos()

    if df_proyectos is None:
        df_proyectos = df_clientes = None

    # --------- Métricas generales ----------
    total_clientes = 0 if df_clientes is None or df_clientes.empty else len(df_clientes)
    total_proyectos = 0 if df_proyectos is None or df_proyectos.empty else len(df_proyectos)

    proyectos_activos = 0
    potencial_total = 0.0
    seg_atrasados = 0
    tareas_abiertas = 0

    if df_proyectos is not None and not df_proyectos.empty:
        activos_mask = ~df_proyectos["estado"].isin(["Ganado", "Perdido"])
        proyectos_activos = int(activos_mask.sum())

        if "potencial_eur" in df_proyectos.columns:
            potencial_total = float(df_proyectos["potencial_eur"].fillna(0).sum())

        hoy = date.today()
        if "fecha_seguimiento" in df_proyectos.columns:
            seg_atrasados = int(
                df_proyectos[
                    df_proyectos["fecha_seguimiento"].notna()
                    & (df_proyectos["fecha_seguimiento"] <= hoy)
                    & (~df_proyectos["estado"].isin(["Ganado", "Perdido"]))
                ].shape[0]
            )

        # Tareas
        for _, row in df_proyectos.iterrows():
            tareas = row.get("tareas") or []
            for t in tareas:
                if not t.get("completado", False):
                    tareas_abiertas += 1

    # ---------- TOP BAR ----------
    with st.container():
        st.markdown(
            """
            <div class="crm-top-bar">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <div class="section-badge">Agenda &amp; Pipeline</div>
                        <h1>CRM Prescripción</h1>
                        <p class="text-muted" style="margin-top:2px;">
                            Vista ejecutiva de proyectos, seguimientos y tareas.
                        </p>
                    </div>
                </div>
            """,
            unsafe_allow_html=True,
        )

        # Fila de métricas
        st.markdown('<div class="crm-metric-row">', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="crm-metric-card">
                <div class="crm-metric-title">Proyectos activos</div>
                <div class="crm-metric-value">{proyectos_activos}</div>
                <div class="crm-metric-sub">En seguimiento / prescripción / oferta</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="crm-metric-card">
                <div class="crm-metric-title">Potencial total</div>
                <div class="crm-metric-value">{_formato_millones(potencial_total)}</div>
                <div class="crm-metric-sub">Suma del potencial estimado 2N</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="crm-metric-card">
                <div class="crm-metric-title">Seguimientos atrasados</div>
                <div class="crm-metric-value">{seg_atrasados}</div>
                <div class="crm-metric-sub">Hasta hoy incluido</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="crm-metric-card">
                <div class="crm-metric-title">Tareas abiertas</div>
                <div class="crm-metric-value">{tareas_abiertas}</div>
                <div class="crm-metric-sub">Pendientes en todos los proyectos</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div></div>", unsafe_allow_html=True)

    st.markdown("")  # pequeño espacio

    # ========== BLOQUES PRINCIPALES ==========
    if df_proyectos is None or df_proyectos.empty:
        st.info("Todavía no hay proyectos en el CRM.")
        return

    hoy = date.today()
    dentro_14 = hoy + timedelta(days=14)

    # --- Hoy & atrasados ---
    pendientes = df_proyectos[
        df_proyectos["fecha_seguimiento"].notna()
        & (df_proyectos["fecha_seguimiento"] <= hoy)
        & (~df_proyectos["estado"].isin(["Ganado", "Perdido"]))
    ].copy()

    proximos = df_proyectos[
        df_proyectos["fecha_seguimiento"].notna()
        & (df_proyectos["fecha_seguimiento"] > hoy)
        & (df_proyectos["fecha_seguimiento"] <= dentro_14)
        & (~df_proyectos["estado"].isin(["Ganado", "Perdido"]))
    ].copy()

    pendientes = pendientes.sort_values("fecha_seguimiento")
    proximos = proximos.sort_values("fecha_seguimiento")

    # --- Top 10 obras por potencial ---
    df_top_obras = df_proyectos.copy()
    if "potencial_eur" in df_top_obras.columns:
        df_top_obras["potencial_eur"] = df_top_obras["potencial_eur"].fillna(0)
        df_top_obras = df_top_obras.sort_values("potencial_eur", ascending=False).head(10)
    else:
        df_top_obras["potencial_eur"] = 0

    # --- Top promotoras ---
    df_promotoras = df_proyectos.copy()
    if "cliente_principal" in df_promotoras.columns:
        df_promotoras["potencial_eur"] = df_promotoras.get("potencial_eur", 0).fillna(0)
        df_promotoras = (
            df_promotoras.groupby("cliente_principal", dropna=True)
            .agg(
                potencial_total=("potencial_eur", "sum"),
                proyectos=("id", "count"),
            )
            .reset_index()
            .sort_values("potencial_total", ascending=False)
            .head(10)
        )
    else:
        df_promotoras = None

    # Layout diferente según modo
    if not compacto:
        # ---------- Escritorio: dos columnas ----------
        col_left, col_right = st.columns([1.4, 1])

        # ---- Columna izquierda: Hoy y atrasados + Próximos 14 días ----
        with col_left:
            st.markdown(
                '<div class="crm-card"><h2>Hoy y atrasados</h2>',
                unsafe_allow_html=True,
            )
            if pendientes.empty:
                st.markdown(
                    "<p class='text-muted'>No tienes seguimientos atrasados. ✅</p>",
                    unsafe_allow_html=True,
                )
            else:
                for _, row in pendientes.iterrows():
                    nombre = row.get("nombre_obra", "Sin nombre")
                    ciudad = row.get("ciudad", "—")
                    cli = row.get("cliente_principal", "—")
                    estado = row.get("estado", "Detectado")
                    fecha_seg = row.get("fecha_seguimiento")
                    fecha_txt = fecha_seg.strftime("%d/%m/%y") if fecha_seg else "—"
                    st.markdown(
                        f"""
                        <div style="padding:6px 2px;border-bottom:1px solid rgba(55,65,81,0.6);">
                            <div style="display:flex;justify-content:space-between;">
                                <span style="color:#F9FAFB;font-weight:500;font-size:0.92rem;">{nombre}</span>
                                <span class="status-pill status-red">{fecha_txt}</span>
                            </div>
                            <div class="text-muted">
                                {ciudad} · {cli} · {estado}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            st.markdown("</div>", unsafe_allow_html=True)

            # Próximos 14 días
            st.markdown(
                '<div class="crm-card-light"><h3>Próximos 14 días</h3>',
                unsafe_allow_html=True,
            )
            if proximos.empty:
                st.markdown(
                    "<p class='text-muted'>No hay seguimientos en los próximos 14 días.</p>",
                    unsafe_allow_html=True,
                )
            else:
                for _, row in proximos.iterrows():
                    nombre = row.get("nombre_obra", "Sin nombre")
                    ciudad = row.get("ciudad", "—")
                    cli = row.get("cliente_principal", "—")
                    estado = row.get("estado", "Detectado")
                    fecha_seg = row.get("fecha_seguimiento")
                    fecha_txt = fecha_seg.strftime("%d/%m/%y") if fecha_seg else "—"
                    st.markdown(
                        f"""
                        <div style="padding:6px 2px;border-bottom:1px solid rgba(55,65,81,0.6);">
                            <div style="display:flex;justify-content:space-between;">
                                <span style="color:#F9FAFB;font-weight:500;font-size:0.90rem;">{nombre}</span>
                                <span class="status-pill status-amber">{fecha_txt}</span>
                            </div>
                            <div class="text-muted">
                                {ciudad} · {cli} · {estado}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            st.markdown("</div>", unsafe_allow_html=True)

        # ---- Columna derecha: Top obras + Top promotoras ----
        with col_right:
            st.markdown(
                '<div class="crm-card"><h2>Top 10 obras por potencial</h2>',
                unsafe_allow_html=True,
            )
            if df_top_obras.empty:
                st.markdown(
                    "<p class='text-muted'>No hay datos de potencial disponibles.</p>",
                    unsafe_allow_html=True,
                )
            else:
                for _, row in df_top_obras.iterrows():
                    nombre = row.get("nombre_obra", "Sin nombre")
                    ciudad = row.get("ciudad", "—")
                    pot = _formato_millones(float(row.get("potencial_eur", 0)))
                    st.markdown(
                        f"""
                        <div style="padding:6px 2px;border-bottom:1px solid rgba(55,65,81,0.6);display:flex;justify-content:space-between;">
                            <div>
                                <div style="color:#F9FAFB;font-weight:500;font-size:0.90rem;">{nombre}</div>
                                <div class="text-muted">{ciudad}</div>
                            </div>
                            <div style="font-weight:600;color:#E5E7EB;font-size:0.9rem;">{pot}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown(
                '<div class="crm-card-light"><h3>Top promotoras más activas</h3>',
                unsafe_allow_html=True,
            )
            if df_promotoras is None or df_promotoras.empty:
                st.markdown(
                    "<p class='text-muted'>Todavía no hay suficientes datos de promotoras.</p>",
                    unsafe_allow_html=True,
                )
            else:
                for _, row in df_promotoras.iterrows():
                    prom = row.get("cliente_principal", "—")
                    pot = _formato_millones(float(row.get("potencial_total", 0)))
                    n = int(row.get("proyectos", 0))
                    st.markdown(
                        f"""
                        <div style="padding:6px 2px;border-bottom:1px solid rgba(55,65,81,0.6);display:flex;justify-content:space-between;">
                            <div>
                                <div style="color:#F9FAFB;font-weight:500;font-size:0.90rem;">{prom}</div>
                                <div class="text-muted">{n} proyectos</div>
                            </div>
                            <div style="font-weight:600;color:#E5E7EB;font-size:0.9rem;">{pot}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            st.markdown("</div>", unsafe_allow_html=True)

    else:
        # ---------- Modo compacto (móvil) ----------
        with st.container():
            st.markdown('<div class="crm-card"><h2>Hoy & próximos días</h2>', unsafe_allow_html=True)
            if pendientes.empty and proximos.empty:
                st.markdown(
                    "<p class='text-muted'>No tienes seguimientos pendientes en los próximos días. ✅</p>",
                    unsafe_allow_html=True,
                )
            else:
                df_comp = (
                    pd.concat([pendientes.assign(_tipo="Hoy / Atrasado"), proximos.assign(_tipo="Próx. 14 días")])
                    .sort_values("fecha_seguimiento")
                )
                for _, row in df_comp.iterrows():
                    nombre = row.get("nombre_obra", "Sin nombre")
                    tipo = row.get("_tipo", "")
                    fecha_seg = row.get("fecha_seguimiento")
                    fecha_txt = fecha_seg.strftime("%d/%m/%y") if fecha_seg else "—"
                    st.markdown(
                        f"""
                        <div style="padding:4px 0;border-bottom:1px solid rgba(55,65,81,0.6);">
                            <div style="display:flex;justify-content:space-between;">
                                <span style="color:#F9FAFB;font-weight:500;font-size:0.88rem;">{nombre}</span>
                                <span class="status-pill status-amber">{fecha_txt}</span>
                            </div>
                            <div class="text-muted" style="font-size:0.76rem;">{tipo}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown('<div class="crm-card-light"><h3>Top obras por potencial</h3>', unsafe_allow_html=True)
            if df_top_obras.empty:
                st.markdown(
                    "<p class='text-muted'>Sin datos de potencial.</p>",
                    unsafe_allow_html=True,
                )
            else:
                for _, row in df_top_obras.head(5).iterrows():
                    nombre = row.get("nombre_obra", "Sin nombre")
                    pot = _formato_millones(float(row.get("potencial_eur", 0)))
                    st.markdown(
                        f"""
                        <div style="padding:4px 0;border-bottom:1px solid rgba(55,65,81,0.6);display:flex;justify-content:space-between;">
                            <span style="color:#F9FAFB;font-size:0.86rem;">{nombre}</span>
                            <span style="font-weight:600;color:#E5E7EB;font-size:0.86rem;">{pot}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            st.markdown("</div>", unsafe_allow_html=True)


# ======================================================
# MAIN
# ======================================================

def main():
    # ----- Sidebar -----
    with st.sidebar:
        st.markdown("### 🏗️ CRM Prescripción")
        st.caption("Tu cockpit de proyectos, clientes y scouting.")
        st.markdown("---")

        # Toggle global de modo compacto (móvil)
        compact_toggle = st.toggle(
            "Vista esencial (modo móvil)",
            value=st.session_state.get("modo_compacto", False),
        )
        st.session_state["modo_compacto"] = compact_toggle

        menu = st.radio(
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
