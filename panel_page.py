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
# EXTRACCIÓN DE ACCIONES
# =====================================================
def _extraer_acciones(df) -> List[Dict[str, Any]]:
    acciones = []

    for _, row in df.iterrows():
        nombre = row.get("nombre_obra", "Sin nombre")
        cliente = row.get("cliente_principal", "—")
        ciudad = row.get("ciudad", "—")
        estado = row.get("estado", "Detectado")
        proy_id = row.get("id")

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

        tareas = row.get("tareas") or []
        for t in tareas:
            if not isinstance(t, dict) or t.get("completado"):
                continue
            fecha_lim = _parse_fecha(t.get("fecha_limite"))
            if fecha_lim:
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

    acciones.sort(key=lambda x: x["fecha"])
    return acciones


def _particionar_acciones(acciones: List[Dict[str, Any]]):
    hoy = date.today()
    en_7 = hoy + timedelta(days=7)

    atrasadas = [x for x in acciones if x["fecha"] < hoy]
    hoy_list = [x for x in acciones if x["fecha"] == hoy]
    prox7 = [x for x in acciones if hoy < x["fecha"] <= en_7]
    return atrasadas, hoy_list, prox7


def _render_lista_acciones(titulo: str, acciones: List[Dict[str, Any]]):
    st.markdown(
        f'<div style="font-size:12px;font-weight:600;color:#032D60;margin-bottom:2px;">{titulo}</div>',
        unsafe_allow_html=True,
    )

    if not acciones:
        st.caption("Sin acciones.")
        return

    for acc in acciones:
        fecha = acc["fecha"].strftime("%d/%m/%Y")
        st.markdown(
            f"""
            <div class="apple-card-light" style="margin-bottom:4px;padding:5px 7px;">
                <div style="font-size:10px;color:#5A6872;">
                    {fecha} · <strong>{acc['tipo']}</strong>
                </div>
                <div style="font-size:12px;font-weight:600;color:#032D60;margin:0;">
                    {acc['proyecto']}
                </div>
                <div style="font-size:10.5px;color:#5A6872;">
                    {acc['cliente']} · {acc['ciudad']} · {acc['estado']}
                </div>
                {"<div style='font-size:10px;margin-top:2px;'>" + acc["descripcion"] + "</div>" if acc["descripcion"] else ""}
            </div>
            """,
            unsafe_allow_html=True,
        )


# =====================================================
# PANEL (DISEÑO ULTRA COMPACTO + TAG GRANDE)
# =====================================================
def render_panel():
    inject_apple_style()

    # ===== ESTILOS =====
    st.markdown(
        """
        <style>
        .crm-compact-header {
            display:flex;
            align-items:center;
            justify-content:space-between;
            padding:2px 0 6px 0;
            margin-bottom:6px;
            border-bottom:1px solid #d8dde6;
        }

        .crm-compact-title {
            font-size:15px;
            font-weight:600;
            color:#032D60;
            margin:0;
            padding:0;
            line-height:15px;
        }

        .crm-compact-subtitle {
            font-size:11px;
            color:#5A6872;
            margin:0;
            padding:0;
            line-height:12px;
        }

        /* ★ TAG GRANDE TIPO SALESFORCE ★ */
        .crm-tag-big {
            font-size:13px;
            font-weight:500;
            padding:4px 12px;
            border-radius:14px;
            background:#e5f2ff;
            border:1px solid #b7d4f5;
            color:#032D60;
            display:flex;
            align-items:center;
            height:28px;
        }

        .crm-small-metric .stMetric {
            padding-top:0 !important;
            padding-bottom:0 !important;
            margin-top:-4px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ===== CABECERA =====
    st.markdown(
        """
        <div class="crm-compact-header">
            <div>
                <div class="crm-compact-title">Panel</div>
                <div class="crm-compact-subtitle">Agenda de seguimientos y tareas del día</div>
            </div>

            <div class="crm-tag-big">Vista · Agenda</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ===== DATOS =====
    df = load_proyectos()

    if df is None or df.empty:
        st.info("Todavía no hay proyectos.")
        return

    acciones = _extraer_acciones(df)
    atrasadas, hoy_list, prox7 = _particionar_acciones(acciones)

    # ===== MÉTRICAS =====
    st.markdown('<div class="apple-card-light crm-small-metric">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Acciones", len(acciones))
    col2.metric("Retrasadas", len(atrasadas))
    col3.metric("Hoy", len(hoy_list))
    col4.metric("Próx. 7 días", len(prox7))
    st.markdown("</div>", unsafe_allow_html=True)

    # ===== LISTAS =====
    colA, colB, colC = st.columns([1.1, 1, 1])
    with colA:
        _render_lista_acciones("📌 Retrasadas", atrasadas)
    with colB:
        _render_lista_acciones("📅 Hoy", hoy_list)
    with colC:
        _render_lista_acciones("🔜 Próx. 7 días", prox7)
