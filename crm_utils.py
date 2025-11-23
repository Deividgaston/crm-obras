import json
from datetime import datetime, date, timedelta
from io import BytesIO

import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
import pandas as pd


# =========================================================
# 🔥 INICIALIZACIÓN PEREZOSA DE FIREBASE
# =========================================================
def _get_db():
    """
    Devuelve el cliente de Firestore.
    - Si Firebase no está inicializado, lo inicializa usando st.secrets["firebase_key"].
    - No hace ninguna llamada rara en import, solo cuando se usan las funciones.
    """
    if not firebase_admin._apps:
        try:
            key_str = st.secrets["firebase_key"]
            key_dict = json.loads(key_str)
            cred = credentials.Certificate(key_dict)
            firebase_admin.initialize_app(cred)
        except Exception as e:
            raise RuntimeError(
                f"Firebase no se pudo inicializar desde crm_utils. "
                f"Revisa st.secrets['firebase_key']. Detalle: {e}"
            )
    return firestore.client()


# =========================================================
# UTILIDADES DE FECHA
# =========================================================
def _normalize_fecha(value):
    if value is None:
        return None
    # Timestamp de Firestore
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


def default_pasos_seguimiento():
    nombres = [
        "Identificar agentes clave (promotora / ingeniería / arquitectura / integrador)",
        "Primer contacto (llamada / email)",
        "Enviar dossier y referencias de 2N",
        "Programar reunión / demo con el cliente",
        "Preparar y enviar memoria técnica / oferta económica",
        "Seguimiento, ajustes y cierre (prescripción / adjudicación)",
    ]
    return [{"nombre": n, "completado": False} for n in nombres]


# =========================================================
# CLIENTES
# =========================================================
def get_clientes():
    db = _get_db()
    docs = db.collection("clientes").stream()
    items = []
    for d in docs:
        data = d.to_dict()
        data["id"] = d.id
        if "fecha_alta" in data:
            data["fecha_alta"] = _normalize_fecha(data["fecha_alta"])
        items.append(data)
    return pd.DataFrame(items) if items else pd.DataFrame()


def add_cliente(data: dict):
    db = _get_db()
    data = dict(data)
    if "fecha_alta" not in data:
        data["fecha_alta"] = datetime.utcnow()
    db.collection("clientes").add(data)


def ensure_cliente_basico(nombre: str | None, tipo_cliente: str):
    """
    Si el nombre viene relleno, asegura que exista un cliente básico con ese nombre/empresa.
    No rompe nada si ya existe.
    """
    if not nombre:
        return
    df = get_clientes()
    if not df.empty and "empresa" in df.columns:
        mask = df["empresa"].fillna("") == nombre
        if mask.any():
            return
    add_cliente(
        {
            "nombre": "",
            "empresa": nombre,
            "tipo_cliente": tipo_cliente,
            "email": "",
            "telefono": "",
            "ciudad": "",
            "provincia": "",
            "notas": f"Creado automáticamente desde proyectos como {tipo_cliente}.",
        }
    )


# =========================================================
# PROYECTOS (colección 'obras')
# =========================================================
def get_proyectos():
    db = _get_db()
    docs = db.collection("obras").stream()
    items = []
    for d in docs:
        data = d.to_dict()
        data["id"] = d.id

        if "fecha_creacion" in data:
            fc = data["fecha_creacion"]
            if hasattr(fc, "to_datetime"):
                data["fecha_creacion"] = fc.to_datetime()
            elif isinstance(fc, str):
                try:
                    data["fecha_creacion"] = datetime.fromisoformat(fc)
                except Exception:
                    data["fecha_creacion"] = None

        if "fecha_seguimiento" in data:
            data["fecha_seguimiento"] = _normalize_fecha(data["fecha_seguimiento"])

        items.append(data)

    return pd.DataFrame(items) if items else pd.DataFrame()


def add_proyecto(data: dict):
    db = _get_db()
    data = dict(data)
    data.setdefault("fecha_creacion", datetime.utcnow())
    if "fecha_seguimiento" not in data or data["fecha_seguimiento"] is None:
        data["fecha_seguimiento"] = (date.today() + timedelta(days=7)).isoformat()
    db.collection("obras").add(data)


def actualizar_proyecto(proyecto_id: str, data: dict):
    db = _get_db()
    db.collection("obras").document(proyecto_id).update(data)


def delete_proyecto(proyecto_id: str):
    db = _get_db()
    db.collection("obras").document(proyecto_id).delete()


# =========================================================
# OBRAS IMPORTANTES + EXPORTAR EXCEL
# =========================================================
def filtrar_obras_importantes(df_proy: pd.DataFrame) -> pd.DataFrame:
    if df_proy.empty:
        return df_proy

    df = df_proy.copy()
    if "prioridad" not in df.columns:
        df["prioridad"] = "Media"
    if "potencial_eur" not in df.columns:
        df["potencial_eur"] = 0.0

    df["potencial_eur"] = df["potencial_eur"].fillna(0).astype(float)

    estados_seguimiento = [
        "Detectado",
        "Seguimiento",
        "En Prescripción",
        "Oferta Enviada",
        "Negociación",
    ]

    mask_estado = df["estado"].isin(estados_seguimiento) if "estado" in df.columns else True
    mask_prioridad = df["prioridad"] == "Alta"
    mask_potencial = df["potencial_eur"] >= 50000

    importantes = df[mask_estado & (mask_prioridad | mask_potencial)].copy()
    return importantes


def generar_excel_obras_importantes(df_proy: pd.DataFrame) -> bytes:
    df_imp = filtrar_obras_importantes(df_proy)
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df_imp.to_excel(writer, index=False, sheet_name="Obras_importantes")
    return buffer.getvalue()


# =========================================================
# IMPORTAR PROYECTOS DESDE EXCEL (para pestaña Importar)
# =========================================================
def importar_proyectos_desde_excel(file) -> int:
    """
    Excel con columnas típicas:
    - Proyecto, Ciudad, Provincia, Tipo_Proyecto, Segmento, Estado,
      Promotora_Fondo, Arquitectura, Ingenieria,
      Fecha_Inicio_Estimada, Fecha_Entrega_Estimada,
      Notas, Fuente_URL
    """
    try:
        df = pd.read_excel(file)
    except Exception as e:
        st.error(f"Error leyendo el Excel: {e}")
        return 0

    creados = 0
    hoy = date.today()

    def _conv_fecha(valor):
        if pd.isna(valor):
            return None
        if isinstance(valor, (datetime, date)):
            return valor.isoformat()
        if isinstance(valor, str):
            valor = valor.strip()
            if not valor:
                return None
            # dd/mm/aa o dd/mm/aaaa
            for fmt in ("%d/%m/%y", "%d/%m/%Y"):
                try:
                    d = datetime.strptime(valor, fmt).date()
                    return d.isoformat()
                except ValueError:
                    continue
            # ISO
            try:
                d = datetime.fromisoformat(valor)
                if isinstance(d, datetime):
                    return d.date().isoformat()
            except Exception:
                pass
            return valor
        return str(valor)

    for _, row in df.iterrows():
        try:
            nombre_obra = str(row.get("Proyecto", "")).strip()
            if not nombre_obra:
                continue

            ciudad = str(row.get("Ciudad", "")).strip() or None
            provincia = str(row.get("Provincia", "")).strip() or None
            tipo_proyecto = str(row.get("Tipo_Proyecto", "")).strip() or None
            estado = str(row.get("Estado", "Detectado")).strip() or "Detectado"
            segmento = str(row.get("Segmento", "") or "").lower()

            promotor = str(row.get("Promotora_Fondo", "") or "").strip() or None
            arquitectura = str(row.get("Arquitectura", "") or "").strip() or None
            ingenieria = str(row.get("Ingenieria", "") or "").strip() or None

            # prioridad sencilla
            if "ultra" in segmento or "lujo" in segmento:
                prioridad = "Alta"
            else:
                prioridad = "Media"

            potencial = 0.0

            fecha_inicio = _conv_fecha(row.get("Fecha_Inicio_Estimada"))
            fecha_entrega = _conv_fecha(row.get("Fecha_Entrega_Estimada"))

            notas = str(row.get("Notas", "") or "").strip()
            url = str(row.get("Fuente_URL", "") or "").strip()
            notas_full = notas
            if url:
                if notas_full:
                    notas_full += f"\nFuente: {url}"
                else:
                    notas_full = f"Fuente: {url}"

            data = {
                "nombre_obra": nombre_obra,
                "cliente_principal": promotor,
                "promotora": promotor,
                "arquitectura": arquitectura,
                "ingenieria": ingenieria,
                "tipo_proyecto": tipo_proyecto,
                "ciudad": ciudad,
                "provincia": provincia,
                "prioridad": prioridad,
                "potencial_eur": float(potencial),
                "estado": estado,
                "fecha_seguimiento": (hoy + timedelta(days=7)).isoformat(),
                "fecha_inicio": fecha_inicio,
                "fecha_entrega": fecha_entrega,
                "notas_seguimiento": notas_full,
                "notas_historial": [],
                "tareas": [],
            }

            # crear clientes básicos si procede
            if promotor:
                ensure_cliente_basico(promotor, "Promotora")
            if arquitectura:
                ensure_cliente_basico(arquitectura, "Arquitectura")
            if ingenieria:
                ensure_cliente_basico(ingenieria, "Ingeniería")

            add_proyecto(data)
            creados += 1

        except Exception as e:
            st.warning(f"No se pudo importar una fila: {e}")
            continue

    return creados
