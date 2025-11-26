import streamlit as st
from datetime import date, datetime, timedelta
from typing import List, Dict, Any

from data_cache import load_proyectos

try:
    from style_injector import inject_apple_style
except Exception:
    def inject_apple_style():
        pass


def _parse_fecha(v):
    if not v:
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    try:
        return datetime.fromisoformat(v).date()
    except:
        return None


def _extraer_acciones(df):
    acciones = []
    for _, row in df.iterrows():
        nombre = row.get("nombre_obra", "Sin nombre")
        cliente = row.get("cliente_principal", "—")
        ciudad = row.get("ciudad", "—")
        estado = row.get("estado", "Detectado")

        f1 = _parse_fecha(row.get("fecha_seguimiento"))
        if f1:
            acciones.append({
                "tipo": "Seguimiento",
                "fecha": f1,
                "proyecto": nombre,
                "cliente": cliente,
                "ciudad": ciudad,
                "estado": estado,
                "descripcion": row.get("notas_seguimiento", "") or "",
            })

        tareas = row.get("tareas") or []
        for t in tareas:
            if t.get("completado"):
                continue
            f2 = _parse_fecha(t.get("fecha_limite"))
            if f2:
                acciones.append({
                    "tipo": t.get("tipo", "Tarea"),
                    "fecha": f2,
                    "proyecto": nombre,
                    "cliente": cliente,
                    "ciudad": ciudad,
                    "estado": estado,
                    "descripcion": t.get("titulo", "") or "",
                })

    acciones.sort(key=lambda x: x["fecha"])
    return acciones


def _particionar(acciones):
    hoy = date.today()
    en7 = hoy + timedelta(days=7)
    return (
        [x for x in acciones if x["fecha"] < hoy],
        [x for x in acciones if x["fecha"] == hoy],
        [x for x in acciones if hoy < x["fecha"] <= en7],
    )


def _render_lista(title, acciones):
    st.markdown(
        f"<div style='font-size:12px;font-weight:600;color:#032D60;margin-bottom:3px;'>{title}</div>",
        unsafe_allow_html=True
    )

    if not acciones:
        st.caption("Sin acciones.")
        return

    for a in acciones:
        fecha = a["fecha"].strftime("%d/%m/%Y")
        st.markdown(f"""
            <div class='apple-card-light' style='margin-bottom:4px;padding:6px 8px;'>
                <div style='font-size:11px;color:#5A6872;'>{fecha} · <strong>{a["tipo"]}</strong></div>
                <div style='font-size:13px;font-weight:600;color:#032D60;'>{a["proyecto"]}</div>
                <div style='font-size:11px;color:#5A6872;'>{a["cliente"]} · {a["ciudad"]} · {a["estado"]}</div>
                {f"<div style='font-size:10px;margin-top:4px;'>{a['descripcion']}</div>" if a["descripcion"] else ""}
            </div>
        """, unsafe_allow_html=True)


def render_panel():

    inject_apple_style()

    st.markdown("""
        <style>
        .crm-header {
            display:flex;
            align-items:center;
            justify-content:space-between;
            margin:0;
            padding:0 0 4px 0;
            border-bottom:1px solid #d8dde6;
        }
        .crm-title {
            font-size:16px;
            font-weight:600;
            color:#032D60;
            margin:0;
        }
        .crm-sub {
            font-size:11px;
            color:#5A6872;
            margin-top:-2px;
        }
        .crm-tag-big {
            font-size:13px;
            font-weight:500;
            padding:4px 12px;
            border-radius:14px;
            background:#e5f2ff;
            border:1px solid #b7d4f5;
            color:#032D60;
            height:28px;
            display:flex;
            align-items:center;
        }
        </style>
    """, unsafe_allow_html=True)

    # CABECERA SIN ESPACIO ARRIBA
    st.markdown("""
        <div class='crm-header'>
            <div>
                <div class='crm-title'>Panel</div>
                <div class='crm-sub'>Agenda de seguimientos y tareas del día</div>
            </div>
            <div class='crm-tag-big'>Vista · Agenda</div>
        </div>
    """, unsafe_allow_html=True)

    df = load_proyectos()
    if df is None or df.empty:
        st.info("No hay datos todavía.")
        return

    acciones = _extraer_acciones(df)
    atras, hoy_l, prox = _particionar(acciones)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Acciones", len(acciones))
    c2.metric("Retrasadas", len(atras))
    c3.metric("Hoy", len(hoy_l))
    c4.metric("Próx. 7 días", len(prox))

    A, B, C = st.columns([1.1, 1, 1])
    with A: _render_lista("📌 Retrasadas", atras)
    with B: _render_lista("📅 Hoy", hoy_l)
    with C: _render_lista("🔜 Próx. 7 días", prox)
