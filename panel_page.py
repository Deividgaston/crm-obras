import streamlit as st
from datetime import date, datetime, timedelta
from typing import List, Dict, Any

from data_cache import load_proyectos

try:
    from style_injector import inject_apple_style
except Exception:
    def inject_apple_style():
        pass


# =====================================================
# UTILIDADES FECHAS
# =====================================================

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

def _extraer_acciones(df) -> List[Dict[str, Any]]:
    acciones: List[Dict[str, Any]] = []

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

    acciones = sorted(acciones, key=lambda x: x["fecha"])
    return acciones


def _particionar_acciones(acciones: List[Dict[str, Any]]):
    hoy = date.today()
    en_7 = hoy + timedelta(days=7)

    atrasadas, hoy_list, prox7 = [], [], []

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
        f'<div style="font-size:13px;font-weight:600;color:#032D60;margin:4px 0 2px 0;">{titulo}</div>',
        unsafe_allow_html=True,
    )

    if not acciones:
        st.caption("Sin acciones.")
        return

    for acc in acciones:
        fecha_txt = acc["fecha"].strftime("%d/%m/%Y")
        st.markdown(
            f"""
            <div class="apple-card-light" style="margin-bottom:6px;padding:6px 8px;">
                <div style="font-size:11px;color:#5A6872;">
                    {fecha_txt} · <strong>{acc['tipo']}</strong>
                </div>
                <div style="font-size:12.5px;font-weight:600;color:#032D60;">
                    {acc['proyecto']}
                </div>
                <div style="font-size:11px;color:#5A6872;">
                    {acc['cliente']} · {acc['ciudad']} · Estado: {acc['estado']}
                </div>
                {"<div style='font-size:11px;margin-top:2px;'>" + acc["descripcion"] + "</div>" if acc["descripcion"] else ""}
            </div>
            """,
            unsafe_allow_html=True,
        )


# =====================================================
# PANEL (DISEÑO COMPACTO BASE PARA TODAS LAS PÁGINAS)
# =====================================================

def render_panel():
    inject_apple_style()

    # ===== Estilos extra para diseño compacto reutilizable =====
    st.markdown(
        """
        <style>
        .crm-compact-header {
            display:flex;
            align-items:center;
            justify-content:space-between;
            padding:4px 0 6px 0;
            border-bottom:1px solid #d8dde6;
            margin-bottom:6px;
        }
        .crm-compact-header-left {
            display:flex;
            flex-direction:column;
            gap:0;
        }
        .crm-compact-title {
            font-size:18px;
            font-weight:600;
            color:#032D60;
            margin:0;
            padding:0;
        }
        .crm-compact-subtitle {
            font-size:11px;
            color:#5A6872;
            margin:0;
            padding:0;
        }
        .crm-compact-tag {
            font-size:11px;
            padding:2px 8px;
            border-radius:999px;
            background:#e5f2ff;
            color:#032D60;
            border:1px solid #c5dcf5;
            white-space:nowrap;
        }
        .crm-compact-metrics {
            margin-bottom:4px;
        }
        .crm-compact-metrics .stMetric {
            padding-top:0;
            padding-bottom:0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ===== CABECERA COMPACTA =====
    st.markdown(
        """
        <div class="crm-compact-header">
            <div class="crm-compact-header-left">
                <div class="crm-compact-title">Panel</div>
                <div class="crm-compact-subtitle">
                    Agenda de seguimientos y tareas · vista rápida de qué hacer hoy.
                </div>
            </div>
            <div class="crm-compact-tag">Vista · Agenda</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df = load_proyectos()

    if df is None or df.empty:
        st.info("Todavía no hay proyectos en la base de datos.")
        return

    acciones = _extraer_acciones(df)
    atrasadas, hoy_list, prox7 = _particionar_acciones(acciones)

    total_acc = len(acciones)
    total_atrasadas = len(atrasadas)
    total_hoy = len(hoy_list)
    total_prox7 = len(prox7)

    # ===== MÉTRICAS MUY COMPACTAS =====
    st.markdown('<div class="apple-card-light crm-compact-metrics">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Acciones", total_acc)
    col2.metric("Retrasadas", total_atrasadas)
    col3.metric("Hoy", total_hoy)
    col4.metric("Próx. 7 días", total_prox7)
    st.markdown("</div>", unsafe_allow_html=True)

    # ===== LISTAS EN TRES COLUMNAS (COMPACTO) =====
    st.markdown(
        "<div style='margin-top:4px;'>",
        unsafe_allow_html=True,
    )

    col_a, col_b, col_c = st.columns([1.1, 1, 1])

    with col_a:
        _render_lista_acciones("📌 Retrasadas", atrasadas)

    with col_b:
        _render_lista_acciones("📅 Hoy", hoy_list)

    with col_c:
        _render_lista_acciones("🔜 Próximos 7 días", prox7)

    st.markdown("</div>", unsafe_allow_html=True)
