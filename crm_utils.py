import streamlit as st
from datetime import datetime
from typing import List, Dict, Any

import firebase_admin
from firebase_admin import credentials, firestore


# ============================================================
# INICIALIZACIÓN FIRESTORE (UNA SOLA VEZ)
# ============================================================
@st.cache_resource(show_spinner=False)
def _get_db():
    """
    Devuelve el cliente de Firestore.
    - Se inicializa solo una vez por sesión Streamlit.
    - Intenta usar credenciales de st.secrets si existen.
    """
    if not firebase_admin._apps:
        try:
            # Si tienes las credenciales en st.secrets["firebase"], úsalo aquí
            # Ejemplo:
            # cred = credentials.Certificate(st.secrets["firebase"])
            # firebase_admin.initialize_app(cred)
            #
            # Si lo tienes con Application Default Credentials (Streamlit Cloud),
            # basta con inicializar sin parámetros:
            firebase_admin.initialize_app()
        except Exception:
            # Si ya está inicializado o hay algún problema, dejamos que siga.
            pass

    return firestore.client()


# ============================================================
# HELPERS DE CACHÉ
# ============================================================
def _clear_proyectos_cache():
    try:
        get_proyectos.clear()
    except Exception:
        pass


def _clear_clientes_cache():
    try:
        get_clientes.clear()
    except Exception:
        pass


# ============================================================
# PROYECTOS
# ============================================================
@st.cache_data(ttl=60, show_spinner=False)
def get_proyectos() -> List[Dict[str, Any]]:
    """
    Devuelve la lista de proyectos desde Firestore.
    Usa caché 60s para no hacer lecturas constantes.
    """
    db = _get_db()
    docs = db.collection("proyectos").stream()

    proyectos: List[Dict[str, Any]] = []
    for doc in docs:
        d = doc.to_dict() or {}
        d["id"] = doc.id
        proyectos.append(d)

    return proyectos


def add_proyecto(data: Dict[str, Any]) -> str:
    """
    Crea un nuevo proyecto en la colección 'proyectos'.
    Devuelve el id del documento creado.
    """
    db = _get_db()

    # Añadimos fecha_creacion si no viene en data
    if "fecha_creacion" not in data:
        data["fecha_creacion"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    doc_ref = db.collection("proyectos").document()
    doc_ref.set(data)

    _clear_proyectos_cache()
    return doc_ref.id


def actualizar_proyecto(proyecto_id: str, data: Dict[str, Any]) -> None:
    """
    Actualiza un proyecto existente.
    """
    db = _get_db()
    db.collection("proyectos").document(proyecto_id).update(data)
    _clear_proyectos_cache()


def delete_proyecto(proyecto_id: str) -> None:
    """
    Elimina un proyecto por ID.
    """
    db = _get_db()
    db.collection("proyectos").document(proyecto_id).delete()
    _clear_proyectos_cache()


# ============================================================
# CLIENTES
# ============================================================
@st.cache_data(ttl=60, show_spinner=False)
def get_clientes() -> List[Dict[str, Any]]:
    """
    Devuelve la lista de clientes desde Firestore.
    Usa caché 60s para no hacer lecturas constantes.
    """
    db = _get_db()
    docs = db.collection("clientes").stream()

    clientes: List[Dict[str, Any]] = []
    for doc in docs:
        d = doc.to_dict() or {}
        d["id"] = doc.id
        clientes.append(d)

    return clientes


def add_cliente(data: Dict[str, Any]) -> str:
    """
    Crea un nuevo cliente en la colección 'clientes'.
    Devuelve el id del documento creado.
    """
    db = _get_db()

    if "fecha_creacion" not in data:
        data["fecha_creacion"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    doc_ref = db.collection("clientes").document()
    doc_ref.set(data)

    _clear_clientes_cache()
    return doc_ref.id


def actualizar_cliente(cliente_id: str, data: Dict[str, Any]) -> None:
    """
    Actualiza un cliente existente.
    """
    db = _get_db()
    db.collection("clientes").document(cliente_id).update(data)
    _clear_clientes_cache()


def delete_cliente(cliente_id: str) -> None:
    """
    Elimina un cliente por ID.
    """
    db = _get_db()
    db.collection("clientes").document(cliente_id).delete()
    _clear_clientes_cache()
