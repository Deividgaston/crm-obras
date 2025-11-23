import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json

# Inicializa Firebase una sola vez y expone `db`
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
