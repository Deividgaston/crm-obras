import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime

from crm_utils import (
    get_clientes,
    get_proyectos,
    add_cliente,
    actualizar_proyecto,
)

from proyectos_page import render_proyectos
from buscar_page import render_buscar
from style_injector import inject_apple_style

# =====================================================
# CONFIG GENERAL
# =====================================================

st.set_page_config(
    page_title="CRM Prescripción",
    layout="wide",
    page_icon="🏗️",
)

inject_apple_style()


# =====================================================
# PANEL DE CONTROL
# =====================================================

def render_panel_control():
    # ----------- CABECERA APPLE -----------
    st.markdown("""
        <div class="apple-card">
            <div class="section-badge">Panel de Control</div>
            <h1 style="margin-top:6px;">CRM Prescripción</h1>
            <p style="color:#6B7280;margin-bottom:0;">
                Resumen general de tu actividad, seguimientos y pipeline.
            </p>
        </div>
    """, unsafe_allow_html=True)

    df_clientes = get_clientes()
    df_proyectos = get_proyectos()

    total_clientes = 0 if df_clientes is None or df_clientes.empty else len(df_clientes)
    total_proyectos = 0 if df_proyectos is None or df_proyectos.empty else len(df_proyectos)

    proyectos_activos = 0
    if df_proyectos is not None and not df_proyectos.empty:
        proyectos_activos = len(
            df_proyectos[
                ~df_proyectos["estado"].isin(["Ganado", "Perdido"])
            ]
        )

    # ----------- MÉTRICAS APPLE -----------
    st.markdown("<div class='metric-row'>", unsafe_allow_html=True)

    st.markdown(f"""
        <div class="metric-box">
            <div class="metric-title">Clientes Registrados</div>
            <div class="metric-value">{total_clientes}</div>
            <div class="metric-sub">Arquitecturas, ingenierías, promotoras</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="metric-box">
            <div class="metric-title">Proyectos Totales</div>
            <div class="metric-value">{total_proyectos}</div>
            <div class="metric-sub">Histórico global</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="metric-box">
            <div class="metric-title">Proyectos Activos</div>
            <div class="metric-value">{proyectos_activos}</div>
            <div class="metric-sub">Sin cerrar o perder</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # =====================================================
    # NUEVO DASHBOARD APPLE PROFESSIONAL (SEPARADO)
    # =====================================================

    st.markdown("""
        <div class="apple-card-light">
            <div class="section-badge">Dashboard Profesional</div>
            <h3 style="margin-top:10px;margin-bottom:4px;">📊 Radar de Actividad</h3>
            <p style="color:#6B7280;margin:0;font-size:0.9rem;">
                Visualiza el pulso de tus proyectos y seguimientos.
            </p>
        </div>
    """, unsafe_allow_html=True)

    if df_proyectos is None or df_proyectos.empty:
        st.info("No hay datos de proyectos todavía.")
        return

    # ---------- RADAR DE ESTADOS (BARRAS) ----------
    estados_orden = [
        "Detectado", "Seguimiento", "En Prescripción", "Oferta Enviada",
        "Negociación", "Paralizado", "Ganado", "Perdido"
    ]

    df_counts = (
        df_proyectos.groupby("estado")
        .size()
        .reset_index(name="cantidad")
    )

    df_counts["estado"] = pd.Categorical(
        df_counts["estado"], categories=estados_orden, ordered=True
    )

    df_counts = df_counts.sort_values("estado")

    st.bar_chart(df_counts.set_index("estado"))

    # ---------- SEGUIMIENTOS PRÓXIMOS ----------
    st.markdown("""
        <div class='apple-card-light'>
        <h4>⏱ Seguimientos próximos</h4>
        <p style="color:#6B7280;margin-top:-8px;">
            Revisa lo que te viene encima.
        </p>
    """, unsafe_allow_html=True)

    opciones = {
        "Hoy": 0,
        "3 días": 3,
        "7 días": 7,
        "2 semanas": 14,
        "1 mes": 30
    }

    col_f = st.columns(len(opciones))

    for label, dias in zip(opciones.keys(), opciones.values()):
        with col_f[list(opciones.keys()).index(label)]:
            if st.button(label):
                st.session_state["seg_filtro"] = dias

    dias_filtrar = st.session_state.get("seg_filtro", 7)

    hoy = date.today()
    limite = hoy + timedelta(days=dias_filtrar)

    df_seg = df_proyectos[
        df_proyectos["fecha_seguimiento"].notna()
        & (df_proyectos["fecha_seguimiento"] >= hoy)
        & (df_proyectos["fecha_seguimiento"] <= limite)
    ].copy()

    if df_seg.empty:
        st.info("No hay seguimientos próximos en este rango.")
    else:
        df_seg["dias_restantes"] = (
            df_seg["fecha_seguimiento"].apply(lambda x: (x - hoy).days)
        )

        st.dataframe(
            df_seg[[
                "nombre_obra", "cliente_principal", "estado",
                "fecha_seguimiento", "dias_restantes"
            ]],
            hide_index=True,
            use_container_width=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # ---------- MAPA DE CALOR DE ACTIVIDAD ----------
    st.markdown("""
        <div class='apple-card-light'>
        <h4>🗺 Actividad mensual</h4>
        <p style="color:#6B7280;margin-top:-8px;">
            Visión macOS-style de movimiento en 12 meses.
        </p>
    """, unsafe_allow_html=True)

    df_cal = df_proyectos.copy()
    df_cal["mes"] = df_cal["fecha_seguimiento"].apply(lambda x: x.replace(day=1))

    df_heat = df_cal.groupby("mes").size().reset_index(name="actividad")

    st.line_chart(
        df_heat.set_index("mes"),
        height=180
    )

    st.markdown("</div>", unsafe_allow_html=True)

    # ---------- ALERTAS INTELIGENTES ----------
    st.markdown("""
        <div class='apple-card-light'>
        <h4>⚠ Alertas inteligentes</h4>
        <p style="color:#6B7280;margin-top:-8px;">
            Riesgos y oportunidades de seguimiento.
        </p>
    """, unsafe_allow_html=True)

    alertas = []

    # Sin actividad 15 días
    df_old = df_proyectos[
        (hoy - df_proyectos["fecha_seguimiento"]) > timedelta(days=15)
    ]
    if not df_old.empty:
        alertas.append(f"🔸 {len(df_old)} proyectos sin actividad en > 15 días.")

    # Negociación sin movimientos
    df_neg = df_proyectos[df_proyectos["estado"] == "Negociación"]
    if not df_neg.empty:
        alertas.append(f"🟠 {len(df_neg)} proyectos en negociación requieren revisión.")

    # Paralizados
    df_par = df_proyectos[df_proyectos["estado"] == "Paralizado"]
    if not df_par.empty:
        alertas.append(f"⚫ {len(df_par)} proyectos están paralizados.")

    if not alertas:
        st.success("Todo bajo control. No hay alertas.")
    else:
        for a in alertas:
            st.warning(a)

    st.markdown("</div>", unsafe_allow_html=True)


# =====================================================
# CLIENTES
# =====================================================

def render_clientes():
    st.markdown("""
        <div class="apple-card">
            <div class="section-badge">Clientes</div>
            <h1 style="margin-top:6px;">Clientes</h1>
            <p style="color:#6B7280;margin-bottom:0;">
                Gestiona arquitectos, ingenierías, promotoras e integrators.
            </p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.subheader("➕ Añadir nuevo cliente")

    with st.form("form_cliente"):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre / persona de contacto")
            empresa = st.text_input("Empresa")
            tipo_cliente = st.selectbox(
                "Tipo de cliente",
                ["Ingeniería", "Promotora", "Arquitectura", "Integrator Partner", "Otro"],
            )
        with col2:
            email = st.text_input("Email")
            telefono = st.text_input("Teléfono")
            ciudad = st.text_input("Ciudad")
            provincia = st.text_input("Provincia")

        notas = st.text_area("Notas")

        enviar = st.form_submit_button("Guardar cliente")

    if enviar:
        add_cliente({
            "nombre": nombre,
            "empresa": empresa,
            "tipo_cliente": tipo_cliente,
            "email": email,
            "telefono": telefono,
            "ciudad": ciudad,
            "provincia": provincia,
            "notas": notas,
        })
        st.success("Cliente guardado correctamente.")
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.subheader("📋 Listado de clientes")

    df_clientes = get_clientes()

    if df_clientes is None or df_clientes.empty:
        st.info("No hay clientes todavía.")
    else:
        cols = ["nombre", "empresa", "tipo_cliente", "email", "telefono", "ciudad", "provincia"]
        cols = [c for c in cols if c in df_clientes.columns]
        st.dataframe(df_clientes[cols], hide_index=True, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)


# =====================================================
# MAIN
# =====================================================

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
        render_clientes()

    elif menu == "Proyectos":
        render_proyectos()

    elif menu == "Buscar":
        render_buscar()


if __name__ == "__main__":
    main()
