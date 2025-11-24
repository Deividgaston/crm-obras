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
#  UTILIDADES GENERALES
# ============================================================

def _parse_fecha_excel(valor):
    """
    Intenta parsear un valor de fecha proveniente de Excel.
    Acepta:
      - datetime / date directamente
      - cadenas con formato 'YYYY-MM-DD' o similares
      - números (fechas seriales de Excel)
    Devuelve un objeto date o None si no se puede parsear.
    """
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    if isinstance(valor, (int, float)):
        # Interpretar como fecha serial de Excel
        try:
            # Excel base 1899-12-30
            base = datetime(1899, 12, 30)
            return (base + pd.to_timedelta(valor, unit="D")).date()
        except Exception:
            return None
    if isinstance(valor, str):
        valor = valor.strip()
        if not valor:
            return None
        # Intentar varios formatos
        formatos = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y/%m/%d",
            "%d.%m.%Y",
        ]
        for fmt in formatos:
            try:
                return datetime.strptime(valor, fmt).date()
            except ValueError:
                continue
    return None


# ============================================================
#  CRUD PROYECTOS
# ============================================================

def get_proyectos():
    """
    Lee todos los proyectos de Firestore (colección 'proyectos').
    Devuelve una lista de diccionarios con id incluido.
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
    """
    Crea un nuevo proyecto en Firestore.
    """
    db = _get_db()
    db.collection("proyectos").add(data)


def actualizar_proyecto(proyecto_id: str, data: dict):
    """
    Actualiza los datos de un proyecto.
    """
    db = _get_db()
    db.collection("proyectos").document(proyecto_id).update(data)


def delete_proyecto(proyecto_id: str):
    """
    Elimina un proyecto de la colección 'proyectos'.
    """
    db = _get_db()
    db.collection("proyectos").document(proyecto_id).delete()


# ============================================================
#  CRUD CLIENTES
# ============================================================

def get_clientes():
    """
    Lee todos los clientes de Firestore (colección 'clientes').
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
    """
    Crea un nuevo cliente en Firestore.
    """
    db = _get_db()
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


# ============================================================
#  PASOS SEGUIMIENTO / PLANTILLA
# ============================================================

def default_pasos_seguimiento():
    """
    Devuelve la lista de pasos por defecto para el seguimiento de una obra.
    """
    return [
        {"nombre": "Contacto inicial", "completado": False},
        {"nombre": "Reunión técnica", "completado": False},
        {"nombre": "Envío de documentación", "completado": False},
        {"nombre": "Oferta enviada", "completado": False},
        {"nombre": "Negociación", "completado": False},
        {"nombre": "Cierre / Decisión", "completado": False},
    ]


# ============================================================
#  IMPORTAR PROYECTOS DESDE EXCEL
# ============================================================

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
            "cliente": promotora,                 # 🔴 NUEVO: también rellenamos 'cliente'
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
#  EXPORT / FILTROS (resumen de obras importantes)
# ============================================================

def filtrar_obras_importantes(df_proyectos: pd.DataFrame) -> pd.DataFrame:
    """
    Dado un DataFrame de proyectos, filtra aquellos considerados
    "importantes" según prioridad o potencial_2N.
    """
    if df_proyectos.empty:
        return df_proyectos

    df = df_proyectos.copy()

    if "prioridad" in df.columns:
        mask_prio = df["prioridad"].isin(["Alta", "Muy alta"])
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
    Genera un Excel con las obras importantes filtradas.
    """
    buffer = BytesIO()
    df_proy.to_excel(buffer, index=False)
    buffer.seek(0)
    return buffer.getvalue()
def delete_all_proyectos():
    """
    Elimina TODOS los documentos de la colección 'proyectos'.
    """
    db = _get_db()
    docs = db.collection("proyectos").stream()

    borrados = 0
    for doc in docs:
        db.collection("proyectos").document(doc.id).delete()
        borrados += 1

    return borrados
