import streamlit as st
from datetime import date, timedelta

# Funciones de acceso a datos (Firestore) y utilidades
from crm_utils import (
    get_clientes,
    get_proyectos,
    add_cliente,
    actualizar_proyecto,
)

# Páginas específicas
from proyectos_page import render_proyectos
from buscar_page import render_buscar


# ==========================
# CONFIGURACIÓN GENERAL
# ==========================
st.set_page_config(
    page_title="CRM Prescripción 2N",
    layout="wide",
    page_icon="🏗️",
)


# ==========================
# PÁGINA: PANEL DE CONTROL
# ==========================
def render_panel_control():
    st.title("⚡ Panel de Control")

    df_clientes = get_clientes()
    df_proyectos = get_proyectos()

    total_clientes = 0 if df_clientes is None or df_clientes.empty else len(df_clientes)
    total_proyectos = 0 if df_proyectos is None or df_proyectos.empty else len(df_proyectos)

    proyectos_activos = 0
    if df_proyectos is not None and not df_proyectos.empty and "estado" in df_proyectos.columns:
        proyectos_activos = len(
            df_proyectos[~df_proyectos["estado"].isin(["Ganado", "Perdido"])]
        )

    c1, c2, c3 = st.columns(3)
    c1.metric("Clientes en CRM", total_clientes)
    c2.metric("Proyectos totales", total_proyectos)
    c3.metric("Proyectos activos", proyectos_activos)

    st.divider()
    st.subheader("🚨 Seguimientos pendientes (hoy o pasados)")

    if df_proyectos is None or df_proyectos.empty or "fecha_seguimiento" not in df_proyectos.columns:
        st.info("Todavía no hay proyectos en el sistema o no hay fecha de seguimiento registrada.")
        return

    hoy = date.today()

    # Asumimos que crm_utils ya normaliza fecha_seguimiento a tipo date o None.
    pendientes = df_proyectos[
        df_proyectos["fecha_seguimiento"].notna()
        & (df_proyectos["fecha_seguimiento"] <= hoy)
        & (~df_proyectos["estado"].isin(["Ganado", "Perdido"]))
    ]

    if pendientes.empty:
        st.success("No tienes seguimientos atrasados. ✅")
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

            # Botón para posponer una semana
            if st.button("Posponer 1 semana", key=f"posponer_{row['id']}"):
                nueva_fecha = (hoy + timedelta(days=7)).isoformat()
                try:
                    actualizar_proyecto(row["id"], {"fecha_seguimiento": nueva_fecha})
                    st.success(f"Seguimiento pospuesto a {nueva_fecha}.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"No se pudo actualizar la fecha de seguimiento: {e}")


# ==========================
# PÁGINA: CLIENTES
# ==========================
def render_clientes():
    st.title("👤 CRM de Clientes (ingenierías, promotoras, arquitectos, integrators)")

    # Alta de cliente
    with st.expander("➕ Añadir nuevo cliente"):
        with st.form("form_cliente"):
            nombre = st.text_input("Nombre / Persona de contacto")
            empresa = st.text_input("Empresa")
            tipo_cliente = st.selectbox(
                "Tipo de cliente",
                ["Ingeniería", "Promotora", "Arquitectura", "Integrator Partner", "Otro"],
            )
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

    st.subheader("📋 Listado de clientes")

    df_clientes = get_clientes()
    if df_clientes is None or df_clientes.empty:
        st.info("Aún no hay clientes en el CRM.")
        return

    cols_mostrar = ["nombre", "empresa", "tipo_cliente", "email", "telefono", "ciudad", "provincia"]
    cols_mostrar = [c for c in cols_mostrar if c in df_clientes.columns]

    st.dataframe(
        df_clientes[cols_mostrar],
        hide_index=True,
        use_container_width=True,
    )


# ==========================
# MAIN
# ==========================
def main():
    st.sidebar.title("🏗️ CRM Prescripción 2N")

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
