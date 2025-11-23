import streamlit as st
from datetime import date

from crm_utils import get_clientes, get_proyectos


def render_panel_control():
    st.title("⚡ Panel de Control")

    df_clientes = get_clientes()
    df_proyectos = get_proyectos()

    total_clientes = len(df_clientes) if not df_clientes.empty else 0
    total_proyectos = len(df_proyectos) if not df_proyectos.empty else 0
    proyectos_activos = 0
    if not df_proyectos.empty and "estado" in df_proyectos.columns:
        proyectos_activos = len(df_proyectos[~df_proyectos["estado"].isin(["Ganado", "Perdido"])])

    c1, c2, c3 = st.columns(3)
    c1.metric("Clientes en CRM", total_clientes)
    c2.metric("Proyectos totales", total_proyectos)
    c3.metric("Proyectos activos", proyectos_activos)

    st.divider()
    st.subheader("🚨 Seguimientos pendientes (hoy o pasados)")

    if not df_proyectos.empty and "fecha_seguimiento" in df_proyectos.columns:
        hoy = date.today()
        pendientes = df_proyectos[
            df_proyectos["fecha_seguimiento"].notna()
            & (df_proyectos["fecha_seguimiento"] <= hoy)
            & (~df_proyectos["estado"].isin(["Ganado", "Perdido"]))
        ]

        if pendientes.empty:
            st.success("No tienes seguimientos atrasados. ✅")
        else:
            st.error(f"Tienes {len(pendientes)} proyectos con seguimiento pendiente.")
            for _, row in pendientes.sort_values("fecha_seguimiento").iterrows():
                with st.expander(f"⏰ {row.get('nombre_obra', 'Sin nombre')} – {row['fecha_seguimiento']}"):
                    st.write(f"**Cliente principal (promotor):** {row.get('cliente_principal', '—')}")
                    st.write(f"**Estado:** {row.get('estado', '—')}")
                    st.write(f"**Notas:** {row.get('notas_seguimiento', '')}")
    else:
        st.info("Todavía no hay proyectos en el sistema.")
