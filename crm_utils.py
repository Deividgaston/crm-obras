import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json
from datetime import datetime, date, timedelta
import pandas as pd
from io import BytesIO


# ==========================
# FIREBASE INIT
# ==========================

if not firebase_admin._apps:
    try:
        secret_str = st.secrets["firebase_key"]
        key_dict = json.loads(secret_str)
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    except KeyError:
        st.error("Error: no se encontró 'firebase_key' en los Secrets de Streamlit.")
        st.stop()
    except json.JSONDecodeError:
        st.error("ERROR JSON: revisa el contenido de firebase_key en los Secrets.")
        st.stop()
    except Exception as e:
        st.error(f"Error general de Firebase: {e}")
        st.stop()

db = firestore.client()


# ==========================
# UTILIDADES DE FECHAS
# ==========================

def normalize_fecha(value):
    """
    Convierte Firestore Timestamp / datetime / date / str en date o None.
    """
    if value is None:
        return None

    if hasattr(value, "to_datetime"):
        value = value.to_datetime()

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        # ISO
        try:
            dt = datetime.fromisoformat(value)
            return dt.date()
        except Exception:
            pass
        # dd/mm/aa o dd/mm/aaaa
        for fmt in ("%d/%m/%y", "%d/%m/%Y"):
            try:
                dt = datetime.strptime(value, fmt)
                return dt.date()
            except ValueError:
                continue
        return None

    return None


# ==========================
# CHECKLIST BASE
# ==========================

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
    if not items:
        return pd.DataFrame()
    return pd.DataFrame(items)


def add_cliente(data: dict):
    data = dict(data)
    data["fecha_alta"] = datetime.utcnow()
    db.collection("clientes").add(data)


def ensure_cliente_basico(nombre: str | None, tipo_cliente: str):
    """
    Si existe ya un cliente con esa empresa y tipo, no hace nada.
    Si no existe, crea un registro básico.
    """
    if not nombre:
        return
    col = db.collection("clientes")
    q = col.where("empresa", "==", nombre).where("tipo_cliente", "==", tipo_cliente).limit(1)
    docs = list(q.stream())
    if docs:
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
            "notas": "Creado automáticamente desde proyecto.",
        }
    )


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
        data["fecha_inicio"] = normalize_fecha(data.get("fecha_inicio"))
        data["fecha_entrega"] = normalize_fecha(data.get("fecha_entrega"))
        items.append(data)
    if not items:
        return pd.DataFrame()
    return pd.DataFrame(items)


def add_proyecto(data: dict):
    """
    Inserta un proyecto.
    - Fuerza fecha_creacion como datetime.utcnow()
    - Si no hay fecha_seguimiento, la pone a hoy+7
    """
    data = dict(data)
    data["fecha_creacion"] = datetime.utcnow()
    if not data.get("fecha_seguimiento"):
        data["fecha_seguimiento"] = (date.today() + timedelta(days=7)).isoformat()
    db.collection("obras").add(data)


def actualizar_proyecto(proyecto_id: str, data: dict):
    db.collection("obras").document(proyecto_id).update(data)


def delete_proyecto(proyecto_id: str):
    db.collection("obras").document(proyecto_id).delete()


# ==========================
# OBRAS IMPORTANTES / FILTROS
# ==========================

def filtrar_obras_importantes(df_proy: pd.DataFrame) -> pd.DataFrame:
    """
    Obras importantes:
    - Estado en seguimiento (Detectado, Seguimiento, En Prescripción, Oferta Enviada, Negociación)
    - Y prioridad Alta, o potencial >= 50k
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

    estados_seguimiento = [
        "Detectado",
        "Seguimiento",
        "En Prescripción",
        "Oferta Enviada",
        "Negociación",
    ]

    mask_estado = df["estado"].isin(estados_seguimiento)
    mask_prioridad = df["prioridad"] == "Alta"
    mask_potencial = df["potencial_eur"].fillna(0) >= 50000

    importantes = df[mask_estado & (mask_prioridad | mask_potencial)].copy()
    return importantes


# ==========================
# IMPORTAR DESDE EXCEL (PROYECTOS)
# ==========================

def _convertir_fecha_excel(valor):
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
    return str(valor)


def importar_proyectos_desde_excel(file) -> int:
    """
    Importa proyectos desde un Excel con columnas tipo:
    - Proyecto, Ciudad, Provincia, Tipo_Proyecto,
      Promotora_Fondo, Arquitectura, Ingenieria,
      Segmento, Fecha_Inicio_Estimada, Fecha_Entrega_Estimada,
      Notas, Fuente_URL
    """
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

            promotor = str(row.get("Promotora_Fondo", "")).strip() or None
            arquitectura = str(row.get("Arquitectura", "")).strip() or None
            ingenieria = str(row.get("Ingenieria", "")).strip() or None
            segmento = str(row.get("Segmento", "") or "").lower()

            if "ultra" in segmento or "lujo" in segmento:
                prioridad = "Alta"
            else:
                prioridad = "Media"

            potencial = 0.0

            fecha_inicio = _convertir_fecha_excel(row.get("Fecha_Inicio_Estimada"))
            fecha_entrega = _convertir_fecha_excel(row.get("Fecha_Entrega_Estimada"))

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
                "estado": "Detectado",
                "fecha_seguimiento": (hoy + timedelta(days=7)).isoformat(),
                "fecha_inicio": fecha_inicio,
                "fecha_entrega": fecha_entrega,
                "notas_seguimiento": notas_full,
                "notas_historial": [],
                "tareas": [],
                "pasos_seguimiento": [],
            }

            add_proyecto(data)
            creados += 1

        except Exception as e:
            st.warning(f"No se pudo importar una fila: {e}")
            continue

    return creados


# ==========================
# EXPORTAR EXCEL DE OBRAS IMPORTANTES
# ==========================

def generar_excel_obras_importantes(df_proy: pd.DataFrame) -> BytesIO:
    """
    Devuelve un BytesIO con un Excel de las obras importantes.
    """
    importantes = filtrar_obras_importantes(df_proy)
    if importantes.empty:
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            pd.DataFrame().to_excel(writer, index=False, sheet_name="Obras")
        buffer.seek(0)
        return buffer

    cols_export = [
        "nombre_obra",
        "cliente_principal",
        "ciudad",
        "provincia",
        "tipo_proyecto",
        "prioridad",
        "potencial_eur",
        "estado",
        "fecha_seguimiento",
        "arquitectura",
        "ingenieria",
        "notas_seguimiento",
    ]
    cols_export = [c for c in cols_export if c in importantes.columns]
    df_out = importantes[cols_export].copy()
    df_out.rename(
        columns={
            "nombre_obra": "Proyecto",
            "cliente_principal": "Cliente_principal",
            "tipo_proyecto": "Tipo_Proyecto",
            "potencial_eur": "Potencial_EUR",
            "fecha_seguimiento": "Fecha_Seguimiento",
        },
        inplace=True,
    )

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df_out.to_excel(writer, index=False, sheet_name="Obras_Importantes")
    buffer.seek(0)
    return buffer
