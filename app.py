import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import date, timedelta, datetime
import json

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="CRM Prescripción 2N", layout="wide", page_icon="🏗️")

# --- CONEXIÓN A FIREBASE (USANDO SECRET 'firebase_key') ---
if not firebase_admin._apps:
    try:
        # 1) Leer texto del secret: es un JSON completo
        secret_str = st.secrets["firebase_key"]

        # 2) Convertir ese texto JSON a diccionario
        key_dict = json.loads(secret_str)

        # 3) Inicializar Firebase con el diccionario
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)

    except KeyError:
        st.error("Error: La llave 'firebase_key' no se encontró en Streamlit Secrets.")
        st.caption("Ve a Settings → Secrets y asegúrate de haber pegado correctamente el JSON.")
        st.stop()
    except json.JSONDecodeError:
        st.error("ERROR DE FORMATO (JSON): El contenido de la clave no es JSON válido.")
        st.caption(
            "Revisa el secrets.toml. Debe tener la forma:\n\n"
            'firebase_key = """{ ...JSON del service account... }"""'
        )
        st.stop()
    except Exception as e:
        st.error(f"Error general de Firebase: {e}")
        st.stop()

# Cliente de Firestore
db = firestore.client()


# --- FUNCIONES AUXILIARES ---

def normalize_fecha(value):
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
        except:
            return None
    return None


def get_promotoras():
    docs = db.collection('promotoras').stream()
    items = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        items.append(data)
    if not items:
        return pd.DataFrame()
    return pd.DataFrame(items)


def get_obras():
    docs = db.collection('obras').stream()
    items = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        data["fecha_seguimiento"] = normalize_fecha(data.get("fecha_seguimiento"))
        items.append(data)
    if not items:
        return pd.DataFrame()
    df = pd.DataFrame(items)
    df["fecha_seguimiento"] = df["fecha_seguimiento"].apply(normalize_fecha)
    return df


# --- INTERFAZ PRINCIPAL ---

st.sidebar.title("🏗️ Prescripción 2N (Cloud)")
menu = st.sidebar.radio("Ir a:", ["Panel de Control", "Mis Obras", "Promotoras"])


# ===============================
# PANEL DE CONTROL
# ===============================
if menu == "Panel de Control":
    st.title("⚡ Panel de Control y Alertas")

    df_obras = get_obras()

    if not df_obras.empty:
        total_activas = len(df_obras[~df_obras["estado"].isin(["Ganada", "Perdida"])])
        revision = len(df_obras[df_obras["estado"] == "Revisión Planificada"])
    else:
        total_activas = 0
        revision = 0

    col1, col2 = st.columns(2)
    col1.metric("Obras Activas", total_activas)
    col2.metric("En Revisión", revision)

    st.divider()
    st.subheader("🚨 Alertas de Seguimiento")

    if not df_obras.empty:
        today = date.today()
        alertas = df_obras[
            df_obras["fecha_seguimiento"].notna()
            & (df_obras["fecha_seguimiento"] <= today)
            & (~df_obras["estado"].isin(["Ganada", "Perdida"]))
        ]

        if not alertas.empty:
            st.error(f"Tienes {len(alertas)} seguimientos pendientes.")

            for _, row in alertas.sort_values("fecha_seguimiento").iterrows():
                with st.expander(f"⏰ {row['nombre_obra']} – {row['fecha_seguimiento']}"):
                    st.write(f"**Promotora:** {row['promotora']}")
                    st.write(f"**Estado:** {row['estado']}")
                    st.write(f"**Nota:** {row.get('notas_seguimiento', '')}")

                    if st.button("Posponer 1 semana", key=f"posp_{row['id']}"):
                        nueva_fecha = date.today() + timedelta(days=7)
                        db.collection("obras").document(row["id"]).update({
                            "fecha_seguimiento": nueva_fecha
                        })
                        st.success("Pospuesto 1 semana.")
                        st.rerun()

        else:
            st.success("Todo al día ✔️")


# ===============================
# MIS OBRAS
# ===============================
elif menu == "Mis Obras":
    st.title("📁 Gestión de Obras")

    # AÑADIR NUEVA OBRA
    with st.expander("➕ Añadir Nueva Obra"):
        df_prom = get_promotoras()

        if df_prom.empty:
            st.warning("Debes crear una promotora primero.")
        else:
            lista_prom = df_prom["nombre"].tolist()

            with st.form("form_obra"):
                nom = st.text_input("Nombre Obra")
                prom = st.selectbox("Promotora", lista_prom)
                tipo = st.selectbox("Tipo", ["Residencial Lujo", "Oficinas", "BTR", "Otros"])
                arq = st.text_input("Arquitectura")
                ing = st.text_input("Ingeniería")
                fecha = st.date_input("Fecha seguimiento", value=date.today() + timedelta(days=7))
                notas = st.text_area("Notas")

                if st.form_submit_button("Guardar Obra"):
                    db.collection("obras").add({
                        "nombre_obra": nom,
                        "promotora": prom,
                        "tipo_activo": tipo,
                        "arquitectura": arq,
                        "ingenieria": ing,
                        "estado": "Detección",
                        "fecha_seguimiento": fecha,
                        "notas_seguimiento": notas
                    })
                    st.success("Obra creada correctamente.")
                    st.rerun()

    # LISTADO DE OBRAS
    st.subheader("Listado de Obras")
    df = get_obras()

    if df.empty:
        st.info("No hay obras todavía.")
    else:
        st.dataframe(df[["nombre_obra", "promotora", "estado", "fecha_seguimiento"]], hide_index=True)

        st.markdown("### ✏️ Editar Obras")
        for _, row in df.sort_values("fecha_seguimiento").iterrows():
            with st.expander(f"🧱 {row['nombre_obra']}"):
                nuevo_estado = st.selectbox(
                    "Estado",
                    ["Detección", "Revisión Planificada", "Llamada Realizada", "Reunión",
                     "Memoria Enviada", "En Prescripción", "Oferta Enviada",
                     "Negociación", "Ganada", "Perdida"],
                    index=0,
                    key=f"estado_{row['id']}"
                )

                nueva_fecha = st.date_input(
                    "Fecha seguimiento",
                    value=row["fecha_seguimiento"] or date.today(),
                    key=f"fecha_{row['id']}"
                )

                nuevas_notas = st.text_area(
                    "Notas",
                    value=row.get("notas_seguimiento", ""),
                    key=f"nota_{row['id']}"
                )

                if st.button("Guardar Cambios", key=f"save_{row['id']}"):
                    db.collection("obras").document(row["id"]).update({
                        "estado": nuevo_estado,
                        "fecha_seguimiento": nueva_fecha,
                        "notas_seguimiento": nuevas_notas
                    })
                    st.success("Obra actualizada.")
                    st.rerun()


# ===============================
# PROMOTORAS
# ===============================
elif menu == "Promotoras":
    st.title("🏢 Promotoras")

    # AÑADIR
    with st.form("form_prom"):
        nom = st.text_input("Nombre")
        tipo = st.selectbox("Tipo", ["Lujo", "Estándar", "Fondo"])
        pais = st.selectbox("País", ["España", "Portugal"])
        contacto = st.text_input("Contacto")
        email = st.text_input("Email")

        if st.form_submit_button("Crear Promotora"):
            db.collection("promotoras").add({
                "nombre": nom,
                "tipo": tipo,
                "pais": pais,
                "contacto": contacto,
                "email": email
            })
            st.success("Promotora creada.")
            st.rerun()

    df = get_promotoras()
    if not df.empty:
        st.dataframe(df, hide_index=True)
    else:
        st.info("No hay promotoras todavía.")
