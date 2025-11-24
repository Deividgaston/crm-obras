import json
from io import BytesIO
from datetime import datetime, date

import pandas as pd
import streamlit as st

import firebase_admin
from firebase_admin import credentials, firestore


# ============================================================
#  INICIALIZACIÓN FIREBASE
# ============================================================

def _init_firebase():
    """
    Inicializa Firebase si aún no está inicializado.
    Lee el service account de st.secrets["firebase_key"].
    Admite tanto dict como cadena JSON.
    """
    if firebase_admin._apps:
        return  # ya está iniciado

    firebase_key = st.secrets.get("firebase_key", None)
    if not firebase_key:
        raise RuntimeError("No se encontró 'firebase_key' en st.secrets.")

    if isinstance(firebase_key, str):
        firebase_key = json.loads(firebase_key)

    cred = credentials.Certificate(firebase_key)
    firebase_admin.initialize_app(cred)


def _get_db():
    """
    Retorna el cliente Firestore, inicializando Firebase si es necesario.
    """
    _init_firebase()
    return firestore.client()


# ============================================================
#  CRUD PROYECTOS (OPTIMIZADO)
# ============================================================

@st.cache_data(ttl=60)
def get_proyectos():
    """
    Lee todos los proyectos de Firestore (colección 'proyectos').
    Cacheado 60s para no agotar la cuota por muchos reruns.
    """
    db = _get_db()
    docs = db.collection("proyectos").stream()
    proyectos = []
    for doc in docs:
        d = doc.to_dict()
        d["id"] = doc.id
        proyectos.append(d)
    return proyectos


def add_proyecto(data: dict):
    db = _get_db()
    db.collection("proyectos").add(data)


def actualizar_proyecto(proyecto_id: str, data: dict):
    db = _get_db()
    db.collection("proyectos").document(proyecto_id).update(data)


def delete_proyecto(proyecto_id: str):
    db = _get_db()
    db.collection("proyectos").document(proyecto_id).delete()


def delete_all_proyectos():
    """
    Elimina TODOS los documentos de la colección 'proyectos' usando batches
    para reducir el número de peticiones y no fundir la cuota.
    """
    db = _get_db()
    docs = list(db.collection("proyectos").stream())

    if not docs:
        return 0

    batch = db.batch()
    count_in_batch = 0
    total = 0

    for doc in docs:
        ref = db.collection("proyectos").document(doc.id)
        batch.delete(ref)
        count_in_batch += 1
        total += 1

        # Firestore recomienda máx. 500 operaciones por batch
        if count_in_batch >= 450:
            batch.commit()
            batch = db.batch()
            count_in_batch = 0

    # Commit final si queda algo pendiente
    if count_in_batch > 0:
        batch.commit()

    # Limpiamos la caché para que la app no muestre datos antiguos
    st.cache_data.clear()

    return total


# ============================================================
#  CRUD CLIENTES (OPTIMIZADO)
# ============================================================

@st.cache_data(ttl=60)
def get_clientes():
    """
    Lee todos los clientes de Firestore (colección 'clientes').
    Cacheado 60s para no agotar la cuota.
    """
    db = _get_db()
    docs = db.collection("clientes").stream()
    clientes = []
    for doc in docs:
        d = doc.to_dict()
        d["id"] = doc.id
        clientes.append(d)
    return clientes


def add_cliente(data: dict):
    db = _get_db()
    db.collection("clientes").add(data)


def actualizar_cliente(cliente_id: str, data: dict):
    db = _get_db()
    db.collection("clientes").document(cliente_id).update(data)


def delete_cliente(cliente_id: str):
    db = _get_db()
    db.collection("clientes").document(cliente_id).delete()
