import streamlit as st
import pandas as pd
from datetime import date, timedelta

from crm_utils import (
    get_clientes,
    get_proyectos,
    add_cliente,
    actualizar_proyecto,
)

from proyectos_page import render_proyectos
    # (usa los helpers de crm_utils y el estilo apple)
from buscar_page import render_buscar
from style_injector import inject_apple_style


# ==========================
# CONFIG GENERAL
# ==========================

st.set_page_config(
    page_title="CRM Prescripción",
    layout="wide",
    page_icon="🏗️",
)

inject_apple_style()


# ==========================
# PANEL DE CONTROL
# ==========================

def render_panel_control():
    # Cabecera
    st.markdown("""
        <div class="apple-card">
            <div class="section-badge">Panel de Control</div>
            <h1 style="margin-top:6px;">CRM Prescripción</h1>
            <p style="color:#9FB3D1;margin-bottom:0;">
                Resumen general de clientes, proyectos y seguimientos.
            </p>
        </div>
    """, unsafe_allow_html=True)

    df_clientes = get_clientes()
    df_proyectos = get_proyectos()

    total_clientes = 0 if df_clientes is None or df_clientes.empty else len(df_clientes)
    total_proyectos = 0 if df_proyectos is None or df_proyectos.empty else len(df_proyectos)

    proyectos_activos = 0
    if df_proyectos is not None and not df_proyectos.empty and "estado" in df_proyectos.columns:
        proyectos_activos = len(
            df_proyectos[~df_proyectos["estado"].isin(["Ganado", "Perdido"])]
        )

    # Métricas
    st.markdown("<div class='metric-row'>", unsafe_allow_html=True)

    st.markdown(f"""
        <div class="metric-box">
            <div class="metric-title">Clientes en CRM</div>
            <div class="metric-value">{total_clientes}</div>
            <div class="metric-sub">Arquitecturas, ingenierías, promotoras, integrators</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="metric-box">
            <div class="metric-title">Proyectos totales</div>
            <div class="metric-value">{total_proyectos}</div>
            <div class="metric-sub">Histórico de oportunidades</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="metric-box">
            <div class="metric-title">Proyectos activos</div>
            <div class="metric-value">{proyectos_activos}</div>
            <div class="metric-sub">En seguimiento, prescripción u oferta</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Bloque Seguimientos
    st.markdown("""
        <div class="apple-card-light">
            <div class="section-badge">Seguimiento</div>
            <h3 style="margin-top:10px; margin-bottom:4px;">🚨 Seguimientos pendientes</h3>
            <p style="color:#9FB3D1; margin-top:0; font-size:0.9rem;">
                Proyectos con fecha de seguimiento hoy o atrasada.
            </p>
    """, unsafe_allow_html=True)

    if df_proyectos is None or df_proyectos.empty or "fecha_seguimiento" not in df_proyectos.columns:
        st.info("No hay proyectos con fecha de seguimiento registrada.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    hoy = date.today()
    pendientes = df_proyectos[
        df_proyectos["fecha_seguimiento"].notna()
        & (df_proyectos["fecha_seguimiento"] <= hoy)
        & (~df_proyectos["estado"].isin(["Ganado", "Perdido"]))
    ]

    if pendientes.empty:
        st.success("No tienes seguimientos atrasados. ✅")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    st.error(f"Tienes {len(pendientes)} proyectos con seguimiento pendiente.")

    pendientes = pendientes.sort_values("fecha_seguimiento")

    for _, row in pendientes.iterrows():
        nombre = row.get("nombre_obra", "Sin nombre")
        fecha_seg = row.get("fecha_seguimiento", "")
        cliente = row.get("cliente_principal", "—")
        estado = row.get("estado", "—")
        notas = row.get("notas_seguimiento", "")

        with st.expander(f"⏰ {nombre} – {fecha_seg} ({cliente})"):
            st.write(f"**Estado actual:** {estado}")
            st.write(f"**Notas:** {notas or '—'}")

            if st.button("Posponer 1 semana", key=f"posponer_{row['id']}"):
                nueva_fecha = (hoy + timedelta(days=7)).isoformat()
                try:
                    actualizar_proyecto(row["id"], {"fecha_seguimiento": nueva_fecha})
                    st.success(f"Seguimiento pospuesto a {nueva_fecha}.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"No se pudo actualizar la fecha de seguimiento: {e}")

    st.markdown("</div>", unsafe_allow_html=True)


# ==========================
# CLIENTES
# ==========================

def render_clientes():
    st.markdown("""
        <div class="apple-card">
            <div class="section-badge">Relaciones</div>
            <h1 style="margin-top:6px;">Clientes</h1>
            <p style="color:#9FB3D1;margin-bottom:0;">
                Gestiona ingenierías, arquitecturas, promotoras e integrators clave.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Alta de cliente
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

        notas = st.text_area("Notas (proyectos, relación, info importante)")

        enviar = st.form_submit_button("Guardar cliente")

    if enviar:
        if not nombre and not empresa:
            st.warning("Pon al menos un nombre o una empresa.")
        else:
            try:
                add_cliente(
                    {
                        "nombre": nombre,
                        "empresa": empresa,
                        "tipo_cliente": tipo_cliente,
                        "email": email,
                        "telefono": telefono,
                        "ciudad": ciudad,
                        "provincia": provincia,
                        "notas": notas,
                    }
                )
                st.success("Cliente guardado correctamente.")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"No se pudo guardar el cliente: {e}")

    st.markdown("</div>", unsafe_allow_html=True)

    # Listado
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.subheader("📋 Listado de clientes")

    df_clientes = get_clientes()
    if df_clientes is None or df_clientes.empty:
        st.info("Aún no hay clientes en el CRM.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    cols_mostrar = ["nombre", "empresa", "tipo_cliente", "email", "telefono", "ciudad", "provincia"]
    cols_mostrar = [c for c in cols_mostrar if c in df_clientes.columns]

    st.dataframe(
        df_clientes[cols_mostrar],
        hide_index=True,
        use_container_width=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)


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
        render_clientes()
    elif menu == "Proyectos":
        render_proyectos()
    elif menu == "Buscar":
        render_buscar()


if __name__ == "__main__":
    main()
