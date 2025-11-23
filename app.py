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
        st.caption("Ve a Settings → Secrets y asegúrate de haber subido el archivo secrets.toml con la clave firebase_key.")
        st.stop()
    except json.JSONDecodeError:
        st.error("ERROR DE FORMATO (JSON): El contenido de la clave no es JSON válido.")
        st.caption(
            "Revisa el secrets.toml en Streamlit. Debe tener la forma:\n\n"
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
    """
    Normaliza cualquier tipo (Timestamp, str, datetime, date, None)
    a un objeto date o None.
    """
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


def get_promotoras():
    docs = db.collection('promotoras').stream()
    items = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        items.append(data)

    if not items:
        return pd.DataFrame()

    return pd.DataFrame(items)


def get_obras():
    docs = db.collection('obras').stream()
    items = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id

        # Normalizar fecha_seguimiento
        if 'fecha_seguimiento' in data:
            data['fecha_seguimiento'] = normalize_fecha(data['fecha_seguimiento'])
        else:
            data['fecha_seguimiento'] = None

        items.append(data)

    if not items:
        return pd.DataFrame()

    df = pd.DataFrame(items)

    if 'fecha_seguimiento' in df.columns:
        df['fecha_seguimiento'] = df['fecha_seguimiento'].apply(normalize_fecha)

    return df


# --- INTERFAZ PRINCIPAL ---

st.sidebar.title("🏗️ Prescripción 2N (Cloud)")
menu = st.sidebar.radio("Ir a:", ["Panel de Control", "Mis Obras", "Promotoras"])

# 1. PANEL DE CONTROL
if menu == "Panel de Control":
    st.title("⚡ Panel de Control y Alertas")

    df_obras = get_obras()

    if not df_obras.empty and 'estado' in df_obras.columns:
        total = len(df_obras[~df_obras['estado'].isin(['Ganada', 'Perdida'])])
        revision = len(df_obras[df_obras['estado'] == 'Revisión Planificada'])
    else:
        total, revision = 0, 0

    col1, col2 = st.columns(2)
    col1.metric("Obras Activas", total)
    col2.metric("En Revisión", revision)

    st.divider()
    st.subheader("🚨 Alertas de Seguimiento")

    if not df_obras.empty and 'fecha_seguimiento' in df_obras.columns:
        today = date.today()

        alerta_df = df_obras[
            df_obras['fecha_seguimiento'].notna()
            & (df_obras['fecha_seguimiento'] <= today)
            & (~df_obras['estado'].isin(['Ganada', 'Perdida']))
        ].sort_values('fecha_seguimiento')

        if not alerta_df.empty:
            st.error(f"Tienes {len(alerta_df)} seguimientos pendientes.")
            for _, row in alerta_df.iterrows():
                fecha_seg = row['fecha_seguimiento']
                fecha_seg_str = fecha_seg.isoformat() if isinstance(fecha_seg, date) else str(fecha_seg)

                with st.expander(f"⏰ {row.get('nombre_obra', 'Sin nombre')} - {fecha_seg_str}"):
                    st.write(f"**Promotora:** {row.get('promotora', '')}")
                    st.write(f"**Estado:** {row.get('estado', '')}")
                    st.write(f"**Nota:** {row.get('notas_seguimiento', '')}")

                    if st.button("✅ Posponer 1 semana", key=f"posponer_{row['id']}"):
                        next_week = date.today() + timedelta(days=7)
                        db.collection('obras').document(row['id']).update({
                            'fecha_seguimiento': next_week
                        })
                        st.success("Seguimiento pospuesto 1 semana.")
                        st.rerun()
        else:
            st.success("✅ Todo al día, no hay seguimientos pendientes.")
    else:
        st.info("No hay obras registradas todavía o falta la fecha de seguimiento.")

# 2. MIS OBRAS
elif menu == "Mis Obras":
    st.title("Gestión de Obras")

    # --- ALTA DE NUEVA OBRA ---
    with st.expander("➕ Añadir Nueva Obra"):
        df_proms = get_promotoras()
        if df_proms.empty:
            st.warning("Crea primero una promotora en la pestaña 'Promotoras'.")
        else:
            lista_proms = df_proms['nombre'].tolist()

            with st.form("nueva_obra"):
                nom = st.text_input("Nombre Obra")
                prom = st.selectbox("Promotora", lista_proms)
                tipo = st.selectbox("Tipo", ["Residencial Lujo", "Oficinas", "BTR", "Otros"])
                arq = st.text_input("Arquitectura")
                ing = st.text_input("Ingeniería")
                fecha = st.date_input("Fecha Seguimiento", value=date.today() + timedelta(days=7))
                notas = st.text_area("Notas")

                if st.form_submit_button("Guardar"):
                    if not nom:
                        st.warning("El nombre de la obra es obligatorio.")
                    else:
                        db.collection('obras').add({
                            'nombre_obra': nom,
                            'promotora': prom,
                            'tipo_activo': tipo,
                            'arquitectura': arq,
                            'ingenieria': ing,
                            'estado': 'Detección',
                            'fecha_seguimiento': fecha,
                            'notas_seguimiento': notas
                        })
                        st.success("Obra guardada en la nube.")
                        st.rerun()

    # --- LISTADO Y EDICIÓN DE OBRAS ---
    st.subheader("Listado de Obras")

    df = get_obras()
    if df.empty:
        st.info("Todavía no hay obras registradas.")
    else:
        st.markdown("### 📋 Vista rápida")
        cols_mostrar = ['nombre_obra', 'promotora', 'estado', 'fecha_seguimiento']
        cols_mostrar = [c for c in cols_mostrar if c in df.columns]
        st.dataframe(df[cols_mostrar], hide_index=True)

        st.markdown("### ✏️ Editar obras")
        df_sorted = df.sort_values(by='fecha_seguimiento', ascending=True, na_position='last')

        for _, row in df_sorted.iterrows():
            obra_id = row['id']
            nombre_obra = row.get('nombre_obra', 'Sin nombre')
            promotora = row.get('promotora', '')
            estado_actual = row.get('estado', 'Detección')
            fecha_seg_actual = row.get('fecha_seguimiento')

            if not isinstance(fecha_seg_actual, date) and fecha_seg_actual is not None:
                fecha_seg_actual = normalize_fecha(fecha_seg_actual)

            with st.expander(f"🧱 {nombre_obra} | {promotora}"):
                col1, col2 = st.columns(2)
                estados_posibles = [
                    "Detección", "Revisión Planificada", "Llamada Realizada", "Reunión",
                    "Memoria Enviada", "En Prescripción", "Oferta Enviada",
                    "Negociación", "Ganada", "Perdida"
                ]

                with col1:
                    if estado_actual in estados_posibles:
                        idx = estados_posibles.index(estado_actual)
                    else:
                        idx = 0
                    nuevo_estado = st.selectbox("Estado", estados_posibles, index=idx)

                with col2:
                    nueva_fecha_seg = st.date_input(
                        "Fecha próximo seguimiento",
                        value=fecha_seg_actual if isinstance(fecha_seg_actual, date) else date.today() + timedelta(days=7),
                        key=f"fecha_{obra_id}"
                    )

                nuevas_notas = st.text_area(
                    "Notas de seguimiento",
                    value=row.get('notas_seguimiento', ''),
                    key=f"notas_{obra_id}"
                )

                if st.button("💾 Guardar cambios", key=f"guardar_{obra_id}"):
                    db.collection('obras').document(obra_id).update({
                        'estado': nuevo_estado,
                        'fecha_seguimiento': nueva_fecha_seg,
                        'notas_seguimiento': nuevas_notas
                    })
                    st.success("Obra actualizada correctamente.")
                    st.rerun()

# 3. PROMOTORAS
elif menu == "Promotoras":
    st.title("Promotoras")

    with st.form("nueva_prom"):
        nom = st.text_input("Nombre")
        tipo = st.selectbox("Tipo", ["Lujo", "Estándar", "Fondo"])
        pais = st.selectbox("País", ["España", "Portugal"])
        contacto = st.text_input("Contacto principal")
        email = st.text_input("Email")

        if st.form_submit_button("Crear Promotora"):
            if not nom:
                st.warning("El nombre de la promotora es obligatorio.")
            else:
                db.collection('promotoras').add({
                    'nombre': nom,
                    'tipo': tipo,
                    'pais': pais,
                    'contacto': contacto,
                    'email': email
                })
                st.success("Promotora creada correctamente.")
                st.rerun()

    df = get_promotoras()
    if not df.empty:
        st.subheader("Listado de promotoras")
        st.dataframe(df, hide_index=True)
    else:
        st.info("Todavía no hay promotoras registradas.")
