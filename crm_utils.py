import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
from io import BytesIO

from firebase_config import db


# ==========================
# UTILIDADES DE FECHAS / PASOS
# ==========================

def normalize_fecha(value):
    """Convierte Timestamp / datetime / date / str en date o None."""
    if value is None:
        return None
    if hasattr(value, "to_datetime"):  # Firestore Timestamp
        value = value.to_datetime()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            for fmt in ("%d/%m/%y", "%d/%m/%Y"):
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
            return None
    return None


def default_pasos_seguimiento():
    """Plantilla de pasos para seguir un proyecto."""
    nombres = [
        "Identificar agentes clave (promotora / ingeniería / arquitectura / integrador)",
        "Primer contacto (llamada / email)",
        "Enviar dossier y referencias de 2N",
        "Programar reunión / demo con el cliente",
        "Preparar y enviar memoria técnica / oferta económica",
        "Seguimiento, ajustes y cierre (prescripción / adjudicación)"
    ]
    return [{"nombre": n, "completado": False} for n in nombres]


# ==========================
# CLIENTES
# ==========================

def get_clientes():
    docs = db.collection("clientes").stream()
    items = []
    for d in docs:
        data = d.to_dict()
        data["id"] = d.id
        data["fecha_alta"] = normalize_fecha(data.get("fecha_alta"))
        items.append(data)
    return pd.DataFrame(items) if items else pd.DataFrame()


def add_cliente(data):
    data["fecha_alta"] = datetime.utcnow()
    db.collection("clientes").add(data)


def ensure_cliente_basico(nombre: str, tipo: str):
    """
    Si no existe un cliente con esa empresa y tipo, lo crea con datos básicos.
    Aquí podrías enchufar en el futuro una API para buscar teléfono/email/web.
    """
    if not nombre:
        return
    try:
        q = (
            db.collection("clientes")
            .where("empresa", "==", nombre)
            .where("tipo_cliente", "==", tipo)
            .limit(1)
            .stream()
        )
        exists = any(True for _ in q)
        if exists:
            return

        cliente_data = {
            "nombre": "",
            "empresa": nombre,
            "tipo_cliente": tipo,
            "email": "",
            "telefono": "",
            "ciudad": "",
            "provincia": "",
            "notas": "Creado automáticamente desde un proyecto.",
            "fecha_alta": datetime.utcnow(),
        }
        db.collection("clientes").add(cliente_data)
    except Exception:
        pass


# ==========================
# PROYECTOS (OBRAS)
# ==========================

def get_proyectos():
    docs = db.collection("obras").stream()
    items = []
    for d in docs:
        data = d.to_dict()
        data["id"] = d.id
        data["fecha_creacion"] = normalize_fecha(data.get("fecha_creacion"))
        data["fecha_seguimiento"] = normalize_fecha(data.get("fecha_seguimiento"))
        items.append(data)
    return pd.DataFrame(items) if items else pd.DataFrame()


def add_proyecto(data):
    """Inserta un proyecto."""
    data["fecha_creacion"] = datetime.utcnow()
    if "fecha_seguimiento" not in data or data["fecha_seguimiento"] is None:
        data["fecha_seguimiento"] = (date.today() + timedelta(days=7)).isoformat()
    db.collection("obras").add(data)


def actualizar_proyecto(proyecto_id, data):
    db.collection("obras").document(proyecto_id).update(data)


def delete_proyecto(proyecto_id):
    db.collection("obras").document(proyecto_id).delete()


def filtrar_obras_importantes(df_proy: pd.DataFrame) -> pd.DataFrame:
    """
    Define qué es una 'obra importante':
    - Estado en seguimiento (no perdido, no ganado), Y
    - Prioridad Alta, O
    - Potencial estimado >= 50.000 €
    """
    if df_proy.empty:
        return df_proy

    df = df_proy.copy()
    if "prioridad" not in df.columns:
        df["prioridad"] = "Media"
    if "potencial_eur" not in df.columns:
        df["potencial_eur"] = 0.0
    if "estado" not in df.columns:
        df["estado"] = "Detectado"

    estados_seguimiento = ["Seguimiento", "En Prescripción", "Oferta Enviada", "Negociación", "Detectado"]
    mask_estado = df["estado"].isin(estados_seguimiento)
    mask_prioridad = df["prioridad"] == "Alta"
    mask_potencial = df["potencial_eur"].fillna(0) >= 50000

    return df[mask_estado & (mask_prioridad | mask_potencial)].copy()


# ==========================
# IMPORTAR DESDE EXCEL
# ==========================

def _convertir_fecha_excel(valor):
    """Convierte un valor del Excel a string ISO o None."""
    if pd.isna(valor):
        return None
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    if isinstance(valor, str):
        valor = valor.strip()
        if not valor:
            return None
        for fmt in ("%d/%m/%y", "%d/%m/%Y"):
            try:
                d = datetime.strptime(valor, fmt).date()
                return d.isoformat()
            except ValueError:
                continue
        try:
            d = datetime.fromisoformat(valor)
            if isinstance(d, datetime):
                return d.date().isoformat()
            return d.isoformat()
        except Exception:
            return valor
    try:
        return str(valor)
    except Exception:
        return None


def importar_proyectos_desde_excel(file) -> int:
    """Importa proyectos desde un Excel generado por ChatGPT."""
    try:
        df = pd.read_excel(file)
    except Exception as e:
        st.error(f"Error leyendo el Excel: {e}")
        return 0

    creados = 0
    hoy = date.today()

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

            prioridad = "Alta" if ("ultra" in segmento or "lujo" in segmento) else "Media"
            potencial = 0.0

            fecha_inicio = _convertir_fecha_excel(row.get("Fecha_Inicio_Estimada"))
            fecha_entrega = _convertir_fecha_excel(row.get("Fecha_Entrega_Estimada"))

            notas = str(row.get("Notas", "") or "").strip()
            url = str(row.get("Fuente_URL", "") or "").strip()
            notas_full = notas
            if url:
                notas_full = (notas_full + "\n") if notas_full else ""
                notas_full += f"Fuente: {url}"

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
            }

            ensure_cliente_basico(promotor, "Promotora")
            ensure_cliente_basico(arquitectura, "Arquitectura")
            ensure_cliente_basico(ingenieria, "Ingeniería")

            add_proyecto(data)
            creados += 1
        except Exception as e:
            st.warning(f"No se pudo importar una fila: {e}")
            continue

    return creados


# ==========================
# EXPORTAR A EXCEL
# ==========================

def generar_excel_obras_importantes(df_proy: pd.DataFrame) -> BytesIO:
    df_importantes = filtrar_obras_importantes(df_proy)
    output = BytesIO()
    if df_importantes.empty:
        return output

    cols_imp = [
        "nombre_obra", "cliente_principal", "tipo_proyecto",
        "ciudad", "provincia", "prioridad", "potencial_eur",
        "estado", "fecha_creacion", "fecha_seguimiento"
    ]
    cols_imp = [c for c in cols_imp if c in df_importantes.columns]

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_importantes[cols_imp].to_excel(writer, index=False, sheet_name="Obras importantes")
    output.seek(0)
    return output
