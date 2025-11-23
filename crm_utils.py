import json
import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
from datetime import datetime, date, timedelta
import pandas as pd
from io import BytesIO

# ================================
# 🔥 INICIALIZACIÓN CENTRALIZADA
# ================================
def _get_db():
    """Inicializa Firebase correctamente si no está inicializado."""
    if not firebase_admin._apps:
        try:
            key_str = st.secrets["firebase_key"]
            key_dict = json.loads(key_str)
            cred = credentials.Certificate(key_dict)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            raise RuntimeError(f"No se pudo inicializar Firebase: {e}")

    return firestore.client()


# ================================
# 📌 CLIENTES
# ================================
def get_clientes():
    db = _get_db()
    docs = db.collection("clientes").stream()
    items = []

    for d in docs:
        data = d.to_dict()
        data["id"] = d.id
        items.append(data)

    return pd.DataFrame(items) if items else pd.DataFrame()


def add_cliente(data):
    db = _get_db()
    data["fecha_alta"] = datetime.utcnow()
    db.collection("clientes").add(data)


# ================================
# 📌 PROYECTOS
# ================================
def get_proyectos():
    db = _get_db()
    docs = db.collection("obras").stream()
    items = []

    for d in docs:
        data = d.to_dict()
        data["id"] = d.id

        # Normalización básica de fechas
        if "fecha_creacion" in data and hasattr(data["fecha_creacion"], "to_datetime"):
            data["fecha_creacion"] = data["fecha_creacion"].to_datetime()

        if "fecha_seguimiento" in data:
            val = data["fecha_seguimiento"]
            if hasattr(val, "to_datetime"):
                data["fecha_seguimiento"] = val.to_datetime().date()
            elif isinstance(val, str):
                try:
                    data["fecha_seguimiento"] = datetime.fromisoformat(val).date()
                except:
                    data["fecha_seguimiento"] = None

        items.append(data)

    return pd.DataFrame(items) if items else pd.DataFrame()


def add_proyecto(data):
    db = _get_db()
    data["fecha_creacion"] = datetime.utcnow()
    db.collection("obras").add(data)


def actualizar_proyecto(pid, data):
    db = _get_db()
    db.collection("obras").document(pid).update(data)


def delete_proyecto(pid):
    db = _get_db()
    db.collection("obras").document(pid).delete()


# ================================
# 📌 FUNCIONES DE IMPORTACIÓN
# ================================
def filtrar_obras_importantes(df):
    if df.empty:
        return df

    df = df.copy()
    df["potencial_eur"] = df["potencial_eur"].fillna(0).astype(float)
    return df[(df["potencial_eur"] >= 50000) | (df["prioridad"] == "Alta")]


def generar_excel_obras_importantes(df):
    df = filtrar_obras_importantes(df)
    buffer = BytesIO()

    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Obras importantes")

    return buffer.getvalue()
