import json
from io import BytesIO

import pandas as pd
import streamlit as st

import firebase_admin
from firebase_admin import credentials, firestore


# ----------- INICIALIZACIÓN ROBUSTA DE FIREBASE -----------

def _init_firebase():
    """
    Inicializa Firebase si aún no está inicializado.
    Lee el service account de st.secrets["firebase_key"].
    Admite tanto dict como cadena JSON.
    """
    if firebase_admin._apps:
        return  # ya está inicializado

    if "firebase_key" not in st.secrets:
        raise RuntimeError(
            "No se ha encontrado 'firebase_key' en st.secrets. "
            "Configúralo en la sección 'Secrets' de Streamlit."
        )

    key_data = st.secrets["firebase_key"]

    # Puede venir como string JSON o como dict
    if isinstance(key_data, str):
        try:
            key_data = json.loads(key_data)
        except Exception as e:
            raise ValueError(f"'firebase_key' debe ser un JSON válido: {e}")

    cred = credentials.Certificate(key_data)
    firebase_admin.initialize_app(cred)


def _get_db():
    """Devuelve el cliente de Firestore asegurando que Firebase está inicializado."""
    _init_firebase()
    return firestore.client()


# A partir de aquí tus funciones pueden usar _get_db()
# Ejemplos:

def get_clientes():
    db = _get_db()
    docs = db.collection("clientes").stream()
    data = []
    for d in docs:
        row = d.to_dict()
        row["id"] = d.id
        data.append(row)
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


def get_proyectos():
    db = _get_db()
    docs = db.collection("proyectos").stream()
    data = []
    for d in docs:
        row = d.to_dict()
        row["id"] = d.id
        data.append(row)
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


def add_proyecto(data: dict):
    db = _get_db()
    db.collection("proyectos").add(data)


def actualizar_proyecto(doc_id: str, data: dict):
    db = _get_db()
    db.collection("proyectos").document(doc_id).update(data)


def delete_proyecto(doc_id: str):
    db = _get_db()
    db.collection("proyectos").document(doc_id).delete()


def default_pasos_seguimiento():
    return [
        {"nombre": "Detectado", "completado": False},
        {"nombre": "Primer contacto", "completado": False},
        {"nombre": "Visita / demo", "completado": False},
        {"nombre": "Oferta enviada", "completado": False},
        {"nombre": "Negociación", "completado": False},
        {"nombre": "Cerrado / Ganado", "completado": False},
    ]


# ... y aquí debajo dejas/añades el resto:
# - filtrar_obras_importantes(df)
# - importar_proyectos_desde_excel(file)
# - generar_excel_obras_importantes(df)
# etc.
# ============================================================
#  CLIENTES — CRUD básico
# ============================================================

def add_cliente(data: dict):
    """
    Crea un nuevo cliente en Firestore.
    Se usa para arquitecturas, ingenierías, promotoras o integradores.
    """
    db = _get_db()
    data["fecha_alta"] = datetime.utcnow().isoformat()
    db.collection("clientes").add(data)


def actualizar_cliente(cliente_id: str, data: dict):
    """
    Actualiza los datos de un cliente existente.
    """
    db = _get_db()
    db.collection("clientes").document(cliente_id).update(data)


def delete_cliente(cliente_id: str):
    """
    Elimina un cliente de Firestore.
    """
    db = _get_db()
    db.collection("clientes").document(cliente_id).delete()
