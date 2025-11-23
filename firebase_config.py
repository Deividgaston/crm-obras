import json
import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st


_DB = None


def init_firebase():
    """Inicializa Firebase usando st.secrets['firebase_key'] y devuelve el cliente de Firestore."""
    global _DB

    if _DB is not None:
        return _DB

    if firebase_admin._apps:
        _DB = firestore.client()
        return _DB

    try:
        secret_str = st.secrets["firebase_key"]
    except KeyError:
        st.error("No se encontró 'firebase_key' en los Secrets de Streamlit.")
        st.stop()

    try:
        key_dict = json.loads(secret_str)
    except json.JSONDecodeError:
        st.error("El contenido de 'firebase_key' no es un JSON válido. Revisa los Secrets.")
        st.stop()

    try:
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
        _DB = firestore.client()
        return _DB
    except Exception as e:
        st.error(f"Error inicializando Firebase: {e}")
        st.stop()
