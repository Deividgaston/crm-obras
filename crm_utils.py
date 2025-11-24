import json
from io import BytesIO
from datetime import datetime, date

import pandas as pd
import streamlit as st

import firebase_admin
from firebase_admin import credentials, firestore


# ============================================================
#  INICIALIZACIÓN ROBUSTA DE FIREBASE
# ============================================================

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


# ============================================================
#  PROYECTOS — CRUD BÁSICO
# ============================================================

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
    """
    Checklist base que se puede guardar dentro del proyecto
    en el campo 'pasos_seguimiento'.
    """
    return [
        {"nombre": "Detectado", "completado": False},
        {"nombre": "Primer contacto", "completado": False},
        {"nombre": "Visita / demo", "completado": False},
        {"nombre": "Oferta enviada", "completado": False},
        {"nombre": "Negociación", "completado": False},
        {"nombre": "Cerrado / Ganado", "completado": False},
    ]


# ============================================================
#  FUNCIONES DE APOYO PARA EXCEL / OBRAS IMPORTANTES
# ============================================================

def filtrar_obras_importantes(df_proy: pd.DataFrame) -> pd.DataFrame:
    """
    Devuelve sólo las obras "importantes":
    - prioridad = 'Alta' (case-insensitive) O
    - potencial_eur >= 50k
    Si el dataframe está vacío, devuelve DataFrame vacío.
    """
    if df_proy is None or df_proy.empty:
        return pd.DataFrame()

    df = df_proy.copy()

    if "prioridad" in df.columns:
        prio = df["prioridad"].fillna("").str.lower()
        mask_prio = prio.eq("alta")
    else:
        mask_prio = pd.Series(False, index=df.index)

    if "potencial_eur" in df.columns:
        pot = pd.to_numeric(df["potencial_eur"], errors="coerce").fillna(0.0)
        mask_pot = pot >= 50000
    else:
        mask_pot = pd.Series(False, index=df.index)

    mask = mask_prio | mask_pot
    return df[mask].copy()


def generar_excel_obras_importantes(df_proy: pd.DataFrame) -> bytes:
    """
    Genera un Excel en memoria (bytes) con la hoja 'Obras_importantes'.
    Se usa en la página de proyectos para el botón de descarga.
    """
    df_imp = filtrar_obras_importantes(df_proy)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_imp.to_excel(writer, index=False, sheet_name="Obras_importantes")
    output.seek(0)
    return output.getvalue()


# --------------------- IMPORTAR DESDE EXCEL ---------------------

def _parse_fecha_excel(valor):
    """
    Convierte valores de Excel a date o None.
    Admite datetime/date y strings tipo '30/11/25', '30/11/2025', ISO, etc.
    """
    if pd.isna(valor):
        return None

    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor

    if isinstance(valor, str):
        valor = valor.strip()
        if not valor:
            return None

        # Intentamos varios formatos comunes
        formatos = ["%d/%m/%y", "%d/%m/%Y", "%Y-%m-%d"]
        for fmt in formatos:
            try:
                return datetime.strptime(valor, fmt).date()
            except ValueError:
                continue

        # Último intento: fromisoformat
        try:
            return datetime.fromisoformat(valor).date()
        except Exception:
            return None

    return None


def importar_proyectos_desde_excel(uploaded_file) -> int:
    """
    Importa proyectos desde un Excel subido.

    Columnas recomendadas:
    - Nombre_obra / Proyecto
    - Ciudad
    - Provincia
    - Tipo_proyecto
    - Promotora_Fondo  (=> cliente_principal / promotora)
    - Arquitectura
    - Ingenieria
    - Prioridad
    - Potencial_2N
    - Fecha_creacion
    - Fecha_seguimiento
    - Notas
    """
    df = pd.read_excel(uploaded_file)
    if df.empty:
        return 0

    db = _get_db()
    creados = 0

    for _, row in df.iterrows():
        def get_col(*nombres, default=""):
            for n in nombres:
                if n in df.columns and not pd.isna(row.get(n)):
                    return row.get(n)
            return default

        nombre_obra = get_col("Nombre_obra", "nombre_obra", "Proyecto", default="Sin nombre")
        ciudad = get_col("Ciudad", "ciudad")
        provincia = get_col("Provincia", "provincia")
        tipo_proyecto = get_col("Tipo_proyecto", "tipo_proyecto", default="Residencial")
        promotora = get_col("Promotora_Fondo", "Promotora", "promotora", default=None)
        arquitectura = get_col("Arquitectura", "arquitectura", default=None)
        ingenieria = get_col("Ingenieria", "ingenieria", default=None)
        prioridad = str(get_col("Prioridad", "prioridad", default="Media") or "Media")
        potencial_raw = get_col("Potencial_2N", "potencial_eur", default=0)
        try:
            potencial_eur = float(potencial_raw or 0)
        except Exception:
            potencial_eur = 0.0

        fecha_creacion = _parse_fecha_excel(get_col("Fecha_creacion", "fecha_creacion", default=None))
        if fecha_creacion is None:
            fecha_creacion = datetime.utcnow().date()

        fecha_seguimiento = _parse_fecha_excel(get_col("Fecha_seguimiento", "fecha_seguimiento", default=None))
        if fecha_seguimiento is None:
            fecha_seguimiento = fecha_creacion

        notas = get_col("Notas", "notas", default="")

        data = {
            "nombre_obra": nombre_obra,
            "cliente_principal": promotora,
            "promotora": promotora,
            "tipo_proyecto": tipo_proyecto,
            "ciudad": ciudad,
            "provincia": provincia,
            "arquitectura": arquitectura,
            "ingenieria": ingenieria,
            "prioridad": prioridad,
            "potencial_eur": potencial_eur,
            "estado": "Detectado",
            "fecha_creacion": fecha_creacion.isoformat(),
            "fecha_seguimiento": fecha_seguimiento.isoformat(),
            "notas_seguimiento": notas,
            "notas_historial": [],
            "tareas": [],
            "pasos_seguimiento": default_pasos_seguimiento(),
        }

        db.collection("proyectos").add(data)
        creados += 1

    return creados


# ============================================================
#  CLIENTES — CRUD BÁSICO
# ============================================================

def add_cliente(data: dict):
    """
    Crea un nuevo cliente en Firestore.
    Se usa para arquitecturas, ingenierías, promotoras o integradores.
    """
    db = _get_db()
    data = dict(data) if data is not None else {}
    data.setdefault("fecha_alta", datetime.utcnow().isoformat())
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
