import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from typing import List, Dict, Any

from crm_utils import (
    get_proyectos,
)

try:
    from style_injector import inject_apple_style
except Exception:
    def inject_apple_style():
        pass


# =====================================================
# CARGA CACHÉ FIREBASE
# =====================================================

@st.cache_data(show_spinner=False)
def load_proyectos_panel() -> pd.DataFrame | None:
    """Carga de proyectos para el panel (cacheado)."""
    return get_proyectos()


def _parse_fecha(value) -> date | None:
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


# =====================================================
# CONSTRUCCIÓN DE AGENDA
# =====================================================

def _extraer_acciones(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Devuelve una lista de acciones:
    - Seguimientos (por fecha_seguimiento)
    - Tareas con fecha_límite y no completadas
    """
    acciones: List[Dict[str, Any]] = []
    hoy = date.today()

    for _, row in df.iterrows():
        nombre = row.get("nombre_obra", "Sin nombre")
        cliente = row.get("cliente_principal", "—")
        ciudad = row.get("ciudad", "—")
        estado = row.get("estado", "Detectado")
        proy_id = row.get("id")

        # Seguimiento
        fecha_seg = _parse_fecha(row.get("fecha_seguimiento"))
        if fecha_seg:
            acciones.append(
                {
                    "tipo": "Seguimiento",
                    "fecha": fecha_seg,
                    "proyecto": nombre,
                    "cliente": cliente,
                    "ciudad": ciudad,
                    "estado": estado,
                    "id": proy_id,
                    "descripcion": row.get("notas_seguimiento", "") or "",
                }
            )

        # Tareas
        tareas = row.get("tareas") or []
        for t in tareas:
            if not isinstance(t, dict):
                continue
            if t.get("completado"):
                continue
            fecha_lim = _parse_fecha(t.get("fecha_limite"))
            if not fecha_lim:
                continue
            acciones.append(
                {
                    "tipo": t.get("tipo", "Tarea"),
                    "fecha": fecha_lim,
                    "proyecto": nombre,
                    "cliente": cliente,
                    "ciudad": ciudad,
                    "estado": estado,
                    "id": proy_id,
                    "descripcion": t.get("titulo", "") or "",
                }
            )

    # Ordenamos por fecha
    acciones = sorted(acciones, key=lambda x: x["fecha"])
    return acciones


def _particionar_acciones(acciones: List[Dict[str, Any]]):
    hoy = date.today()
    en_7 = hoy + timedelta(days=7)

    atrasadas = []
    hoy_list = []
    prox7 = []

    for acc in acciones:
        f = acc["fecha"]
        if f < hoy:
            atrasadas.append(acc)
        elif f == hoy:
            hoy_list.append(acc)
        elif hoy < f <= en_7:
            prox7.append(acc)

    return atrasadas, hoy_list, prox7


def _render_lista_acciones(titulo: str, acciones: List[Dict[str, Any]]):
    st.markdown(
        f'<h5 style="color:#032D60;margin:6px 0 4px 0;">{titulo}</h5>',
        unsafe_allow_html=True,
    )

    if not acciones:
        st.caption("Sin acciones.")
        return

    for acc in acciones:
        fecha_txt = acc["fecha"].strftime("%d/%m/%Y")
        st.markdown(
            f"""
            <div class="apple-card-light" style="margin-bottom:8px;">
                <div style="font-size:12px;color:#5A6872;">
                    {fecha_txt} · <strong>{acc['tipo']}</strong>
                </div>
                <div style="font-size:13px;font-weight:600;color:#032D60;">
                    {acc['proyecto']}
                </div>
                <div style="font-size:12px;color:#5A6872;">
                    {acc['cliente']} · {acc['ciudad']} · Estado: {acc['estado']}
                </div>
                {"<div style='font-size:12px;margin-top:3px;'>" + acc["descripcion"] + "</div>" if acc["descripcion"] else ""}
            </div>
            """,
            unsafe_allow_html=True,
        )


# =====================================================
# PANEL PRINCIPAL
# =====================================================

def render_panel():
    inject_apple_style()

    st.markdown(
        """
        <div class="apple-card">
            <div class="badge">Agenda</div>
            <h3 style="margin-top:2px; margin-bottom:2px;">Agenda de acciones</h3>
            <p>
                Seguimientos y tareas pendientes ordenadas por urgencia. Vista rápida para saber
                qué hacer hoy, qué está retrasado y qué viene en la semana.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df = load_proyectos_panel()

    if df is None or df.empty:
        st.info("Todavía no hay proyectos en la base de datos.")
        return

    # Construimos agenda
    acciones = _extraer_acciones(df)
    atrasadas, hoy_list, prox7 = _particionar_acciones(acciones)

    total_acc = len(acciones)
    total_atrasadas = len(atrasadas)
    total_hoy = len(hoy_list)
    total_prox7 = len(prox7)

    # Métricas compactas en estilo Salesforce
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.markdown(
        '<h4 style="color:#032D60;margin:0 0 6px 0;">Resumen rápido</h4>',
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total acciones", total_acc)
    with col2:
        st.metric("Retrasadas", total_atrasadas)
    with col3:
        st.metric("Hoy", total_hoy)
    with col4:
        st.metric("Próx. 7 días", total_prox7)

    st.markdown("<hr style='margin:8px 0 10px 0;border-color:#d8dde6;'>", unsafe_allow_html=True)

    # Listas de acciones
    col_a, col_b, col_c = st.columns([1.2, 1, 1])

    with col_a:
        _render_lista_acciones("📌 Retrasadas", atrasadas)

    with col_b:
        _render_lista_acciones("📅 Hoy", hoy_list)

    with col_c:
        _render_lista_acciones("🔜 Próximos 7 días", prox7)

    st.markdown("</div>", unsafe_allow_html=True)
