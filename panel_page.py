import streamlit as st
from datetime import date, datetime, timedelta
from typing import List, Dict, Any

from data_cache import load_proyectos

try:
    from style_injector import inject_apple_style
except Exception:
    def inject_apple_style():
        pass


# -------------------------------
# FECHAS
# -------------------------------
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


# -------------------------------
# EXTRAER ACCIONES
# -------------------------------
def _extraer_acciones(df):
    acciones = []
    for _, row in df.iterrows():
        nom = row.get("nombre_obra", "Sin nombre")
        cli = row.get("cliente_principal", "—")
        cdd = row.get("ciudad", "—")
        est = row.get("estado", "Detectado")

        seg_f = _parse_fecha(row.get("fecha_seguimiento"))
        if seg_f:
            acciones.append({
                "tipo": "Seguimiento",
                "fecha": seg_f,
                "proyecto": nom,
                "cliente": cli,
                "ciudad": cdd,
                "estado": est,
                "descripcion": row.get("notas_seguimiento", "") or "",
            })

        # TAREAS
        tareas = row.get("tareas") or []
        for t in tareas:
            if not isinstance(t, dict) or t.get("completado"):
                continue
            f = _parse_fecha(t.get("fecha_limite"))
            if f:
                acciones.append({
                    "tipo": t.get("tipo", "Tarea"),
                    "fecha": f,
                    "proyecto": nom,
                    "cliente": cli,
                    "ciudad": cdd,
                    "estado": est,
                    "descripcion": t.get("titulo", "") or "",
                })

    acciones.sort(key=lambda x: x["fecha"])
    return acciones


def _particionar(acciones):
    hoy = date.today()
    en7 = hoy + timedelta(days=7)
    atras = [x for x in acciones if x["fecha"] < hoy]
    hoy_l = [x for x in acciones if x["fecha"] == hoy]
    prox = [x for x in acciones if hoy < x["fecha"] <= en7]
    return atras, hoy_l, prox


# -------------------------------
# RENDER LISTA
# -------------------------------
def _render_lista(titulo, acciones):
    st.markdown(f"""
        <div style="font-size:12px;font-weight:600;color:#032D60;margin-bottom:3px;">
            {titulo}
        </div>
    """, unsafe_allow_html=True)

    if not acciones:
        st.caption("Sin acciones.")
        return

    for acc in acciones:
        fecha = acc["fecha"].strftime("%d/%m/%Y")
        st.markdown(
            f"""
            <div class="apple-card-light" style="margin-bottom:4px;padding:6px 8px;">
                <div style="font-size:11px;color:#5A6872;">
                    {fecha} · <strong>{acc["tipo"]}</strong>
                </div>
                <div style="font-size:13px;font-weight:600;color:#032D60;">
                    {acc["proyecto"]}
                </div>
                <div style="font-size:11px;color:#5A6872;">
                    {acc["cliente"]} · {acc["ciudad"]} · {acc["estado"]}
                </div>
                {f"<div style='font-size:10px;margin-top:4px;'>{acc['descripcion']}</div>" if acc["descripcion"] else ""}
            </div>
            """,
            unsafe_allow_html=True
        )


# -------------------------------
# PÁGINA PANEL
# -------------------------------
def render_panel():

    inject_apple_style()

    # --- ESTILOS ---
    st.markdown("""
        <style>
        .crm-header {
            display:flex;
            align-items:center;
            justify-content:space-between;
            padding:2px 0 6px 0;
            margin-bottom:6px;
            border-bottom:1px solid #d8dde6;
        }
        .crm-titulo {
            font-size:16px;
            font-weight:600;
            color:#032D60;
        }
        .crm-subtitulo {
            font-size:11px;
            color:#5A6872;
            margin-top:-2px;
        }
        .crm-tag-big {
            font-size:13px;
            font-weight:500;
            padding:5px 14px;
            border-radius:14px;
            background:#e5f2ff;
            border:1px solid #b7d4f5;
            color:#032D60;
            height:30px;
            display:flex;
            align-items:center;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- CABECERA ---
    st.markdown("""
        <div class="crm-header">
            <div>
                <div class="crm-titulo">Panel</div>
                <div class="crm-subtitulo">Agenda de seguimientos y tareas del día</div>
            </div>
            <div class="crm-tag-big">Vista · Agenda</div>
        </div>
    """, unsafe_allow_html=True)

    # --- DATOS ---
    df = load_proyectos()
    if df is None or df.empty:
        st.info("Todavía no hay proyectos.")
        return

    acciones = _extraer_acciones(df)
    atras, hoy_l, prox7 = _particionar(acciones)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Acciones", len(acciones))
    col2.metric("Retrasadas", len(atras))
    col3.metric("Hoy", len(hoy_l))
    col4.metric("Próx. 7 días", len(prox7))

    colA, colB, colC = st.columns([1.1, 1, 1])

    with colA: _render_lista("📌 Retrasadas", atras)
    with colB: _render_lista("📅 Hoy", hoy_l)
    with colC: _render_lista("🔜 Próx. 7 días", prox7)
