import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import date, timedelta, datetime
import json

# ==========================
# CONFIGURACIÓN STREAMLIT
# ==========================
st.set_page_config(page_title="CRM Prescripción 2N", layout="wide", page_icon="🏗️")

# ==========================
# FIREBASE (usa st.secrets["firebase_key"])
# ==========================
if not firebase_admin._apps:
    try:
        secret_str = st.secrets["firebase_key"]  # viene del secrets.toml
        key_dict = json.loads(secret_str)
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    except KeyError:
        st.error("Error: no se encontró 'firebase_key' en los Secrets de Streamlit.")
        st.stop()
    except json.JSONDecodeError:
        st.error("ERROR DE FORMATO (JSON): El contenido de la clave no es JSON válido.")
        st.caption("Revisa el panel de Secrets: firebase_key debe contener el JSON del service account.")
        st.stop()
    except Exception as e:
        st.error(f"Error general de Firebase: {e}")
        st.stop()

db = firestore.client()

# ==========================
# FUNCIONES AUXILIARES
# ==========================

def normalize_fecha(value):
    """Convierte Timestamp / datetime / date / str en date o None."""
    if value is None:
        return None
    if hasattr(value, "to_datetime"):
        value = value.to_datetime()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            return None
    return None


def default_pasos_seguimiento():
    """Plantilla de pasos para seguir un proyecto."""
    nombres = [
        "Identificar agentes clave (promotora / ingeniería / arquitectura / integrador)",
        "Primer contacto (llamada / email)",
        "Enviar dossier y referencias de 2N",
        "Programar reunión / demo con el cliente",
        "Preparar y enviar memoria técnica / oferta económica",
        "Seguimiento, ajustes y cierre (prescripción / adjudicación)"
    ]
    return [{"nombre": n, "completado": False} for n in nombres]


# ---- CLIENTES ----

def get_clientes():
    docs = db.collection("clientes").stream()
    items = []
    for d in docs:
        data = d.to_dict()
        data["id"] = d.id
        data["fecha_alta"] = normalize_fecha(data.get("fecha_alta"))
        items.append(data)
    if not items:
        return pd.DataFrame()
    df = pd.DataFrame(items)
    return df


def add_cliente(data):
    data["fecha_alta"] = datetime.utcnow()
    db.collection("clientes").add(data)


# ---- PROYECTOS (colección 'obras') ----

def get_proyectos():
    docs = db.collection("obras").stream()
    items = []
    for d in docs:
        data = d.to_dict()
        data["id"] = d.id
        data["fecha_creacion"] = normalize_fecha(data.get("fecha_creacion"))
        data["fecha_seguimiento"] = normalize_fecha(data.get("fecha_seguimiento"))
        items.append(data)
    if not items:
        return pd.DataFrame()
    df = pd.DataFrame(items)
    return df


def add_proyecto(data):
    data["fecha_creacion"] = datetime.utcnow()
    if "fecha_seguimiento" not in data or data["fecha_seguimiento"] is None:
        data["fecha_seguimiento"] = datetime.utcnow()
    db.collection("obras").add(data)


def actualizar_proyecto(proyecto_id, data):
    db.collection("obras").document(proyecto_id).update(data)


# ==========================
# MENÚ LATERAL
# ==========================
st.sidebar.title("🏗️ CRM Prescripción 2N")
menu = st.sidebar.radio("Ir a:", ["Panel de Control", "Clientes", "Proyectos"])

# ==========================
# PANEL DE CONTROL
# ==========================
if menu == "Panel de Control":
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
                    st.write(f"**Cliente principal:** {row.get('cliente_principal', '—')}")
                    st.write(f"**Estado:** {row.get('estado', '—')}")
                    st.write(f"**Notas:** {row.get('notas_seguimiento', '')}")
                    if st.button("Posponer 1 semana", key=f"posponer_{row['id']}"):
                        nueva_fecha = hoy + timedelta(days=7)
                        actualizar_proyecto(row["id"], {"fecha_seguimiento": nueva_fecha})
                        st.success("Pospuesto 1 semana.")
                        st.rerun()
    else:
        st.info("Todavía no hay proyectos en el sistema.")

# ==========================
# CLIENTES
# ==========================
elif menu == "Clientes":
    st.title("👤 CRM de Clientes (ingenierías, promotoras, arquitectos, integrators)")

    # Alta de cliente
    with st.expander("➕ Añadir nuevo cliente"):
        with st.form("form_cliente"):
            nombre = st.text_input("Nombre / Persona de contacto")
            empresa = st.text_input("Empresa")
            tipo_cliente = st.selectbox(
                "Tipo de cliente",
                ["Ingeniería", "Promotora", "Arquitectura", "Integrator Partner", "Otro"]
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

    st.subheader("📋 Listado de clientes")

    df_clientes = get_clientes()
    if df_clientes.empty:
        st.info("Aún no hay clientes en el CRM.")
    else:
        cols_mostrar = ["nombre", "empresa", "tipo_cliente", "email", "telefono", "ciudad", "provincia"]
        cols_mostrar = [c for c in cols_mostrar if c in df_clientes.columns]
        st.dataframe(df_clientes[cols_mostrar], hide_index=True, use_container_width=True)

# ==========================
# PROYECTOS
# ==========================
elif menu == "Proyectos":
    st.title("🏗️ CRM de Proyectos")

    df_clientes = get_clientes()
    nombres_clientes = ["(sin asignar)"]
    if not df_clientes.empty and "empresa" in df_clientes.columns:
        nombres_clientes += sorted(df_clientes["empresa"].dropna().unique().tolist())

    # ---- Alta de proyecto ----
    with st.expander("➕ Añadir nuevo proyecto"):
        with st.form("form_proyecto"):
            nombre_obra = st.text_input("Nombre del proyecto / obra")
            cliente_principal = st.selectbox("Cliente principal", nombres_clientes)
            tipo_proyecto = st.selectbox("Tipo de proyecto", ["Residencial lujo", "Residencial", "Oficinas", "Hotel", "BTR", "Otro"])
            ciudad = st.text_input("Ciudad")
            provincia = st.text_input("Provincia")
            estado_inicial = "Detectado"
            fecha_seg = st.date_input("Primera fecha de seguimiento", value=date.today() + timedelta(days=7))
            notas = st.text_area("Notas iniciales (fuente del proyecto, link, etc.)")

            guardar_proy = st.form_submit_button("Guardar proyecto")

        if guardar_proy:
            if not nombre_obra:
                st.warning("El nombre del proyecto es obligatorio.")
            else:
                add_proyecto({
                    "nombre_obra": nombre_obra,
                    "cliente_principal": None if cliente_principal == "(sin asignar)" else cliente_principal,
                    "tipo_proyecto": tipo_proyecto,
                    "ciudad": ciudad,
                    "provincia": provincia,
                    "estado": estado_inicial,
                    "fecha_seguimiento": fecha_seg,
                    "notas_seguimiento": notas,
                })
                st.success("Proyecto creado correctamente.")
                st.rerun()

    # ---- Listados y filtros ----
    df_proy = get_proyectos()

    if df_proy.empty:
        st.info("Todavía no hay proyectos.")
    else:
        tab_nuevos, tab_seguimiento, tab_todos = st.tabs(
            ["🆕 Nuevos esta semana", "📌 En seguimiento", "📂 Todos"]
        )

        hoy = date.today()
        hace_7_dias = hoy - timedelta(days=7)

        # 1) NUEVOS ESTA SEMANA
        with tab_nuevos:
            st.subheader("🆕 Proyectos nuevos detectados esta semana")
            if "fecha_creacion" not in df_proy.columns:
                st.info("Aún no se ha guardado fecha_creacion en los proyectos nuevos.")
            else:
                nuevos = df_proy[
                    df_proy["fecha_creacion"].notna()
                    & (df_proy["fecha_creacion"] >= hace_7_dias)
                ].copy()

                if nuevos.empty:
                    st.info("No hay proyectos nuevos esta semana.")
                else:
                    for _, row in nuevos.sort_values("fecha_creacion", ascending=False).iterrows():
                        with st.expander(f"🆕 {row['nombre_obra']} ({row.get('cliente_principal', 'sin cliente')})"):
                            st.write(f"**Tipo:** {row.get('tipo_proyecto', '—')}")
                            st.write(f"**Zona:** {row.get('ciudad','')} ({row.get('provincia','')})")
                            st.write(f"**Estado actual:** {row.get('estado','Detectado')}")
                            st.write(f"**Fecha creación:** {row.get('fecha_creacion','—')}")
                            st.write(f"**Notas:** {row.get('notas_seguimiento','')}")

                            if st.button("➡️ Pasar a SEGUIMIENTO", key=f"seguir_{row['id']}"):
                                pasos = default_pasos_seguimiento()
                                actualizar_proyecto(row["id"], {
                                    "estado": "Seguimiento",
                                    "pasos_seguimiento": pasos
                                })
                                st.success("Proyecto movido a Seguimiento y pasos creados.")
                                st.rerun()

        # 2) PROYECTOS EN SEGUIMIENTO
        with tab_seguimiento:
            st.subheader("📌 Proyectos en seguimiento")
            en_seg = df_proy[df_proy["estado"].isin(["Seguimiento", "En Prescripción", "Oferta Enviada", "Negociación"])]

            if en_seg.empty:
                st.info("No hay proyectos en seguimiento todavía.")
            else:
                for _, row in en_seg.sort_values("fecha_seguimiento", ascending=True).iterrows():
                    with st.expander(f"📌 {row['nombre_obra']} – siguiente seguimiento {row.get('fecha_seguimiento','—')}"):
                        st.write(f"**Cliente:** {row.get('cliente_principal','—')}")
                        st.write(f"**Tipo:** {row.get('tipo_proyecto','—')}")
                        st.write(f"**Estado:** {row.get('estado','—')}")
                        st.write(f"**Notas de seguimiento:** {row.get('notas_seguimiento','')}")

                        # Checklist de pasos
                        pasos = row.get("pasos_seguimiento")
                        if not pasos:
                            if st.button("Crear checklist de pasos", key=f"crear_pasos_{row['id']}"):
                                pasos = default_pasos_seguimiento()
                                actualizar_proyecto(row["id"], {"pasos_seguimiento": pasos})
                                st.success("Checklist creado.")
                                st.rerun()
                        else:
                            st.markdown("#### ✅ Pasos de seguimiento")
                            estados = []
                            for i, paso in enumerate(pasos):
                                checked = st.checkbox(
                                    paso.get("nombre", f"Paso {i+1}"),
                                    value=paso.get("completado", False),
                                    key=f"chk_{row['id']}_{i}"
                                )
                                estados.append(checked)

                            if st.button("💾 Guardar pasos", key=f"save_pasos_{row['id']}"):
                                for i, chk in enumerate(estados):
                                    pasos[i]["completado"] = chk
                                actualizar_proyecto(row["id"], {"pasos_seguimiento": pasos})
                                st.success("Pasos actualizados.")
                                st.rerun()

                        # Cambiar fecha de seguimiento
                        nueva_fecha = st.date_input(
                            "Nueva fecha de seguimiento",
                            value=row.get("fecha_seguimiento") or hoy,
                            key=f"fecha_seg_{row['id']}"
                        )
                        if st.button("Actualizar fecha de seguimiento", key=f"upd_fecha_{row['id']}"):
                            actualizar_proyecto(row["id"], {"fecha_seguimiento": nueva_fecha})
                            st.success("Fecha de seguimiento actualizada.")
                            st.rerun()

        # 3) TODOS LOS PROYECTOS
        with tab_todos:
            st.subheader("📂 Todos los proyectos")
            cols = ["nombre_obra", "cliente_principal", "tipo_proyecto", "ciudad", "provincia", "estado", "fecha_creacion", "fecha_seguimiento"]
            cols = [c for c in cols if c in df_proy.columns]
            st.dataframe(df_proy[cols].sort_values("fecha_creacion", ascending=False), hide_index=True, use_container_width=True)
