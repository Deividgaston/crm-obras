import firebase_admin
from firebase_admin import firestore
from datetime import datetime, date, timedelta
import pandas as pd
from io import BytesIO


# =====================================================
# HELPER: OBTENER DB (ESPERA QUE app.py YA HAYA HECHO initialize_app)
# =====================================================

def _get_db():
    """
    Devuelve el cliente de Firestore.
    IMPORTANTE: Firebase debe estar inicializado en app.py con firebase_admin.initialize_app(...)
    usando st.secrets["firebase_key"].
    """
    if not firebase_admin._apps:
        raise RuntimeError(
            "Firebase no está inicializado. Inicialízalo en app.py antes de usar crm_utils."
        )
    return firestore.client()


# =====================================================
# NORMALIZACIÓN DE FECHAS
# =====================================================

def normalize_fecha(value):
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

        # ISO
        try:
            return datetime.fromisoformat(value).date()
        except Exception:
            pass

        # dd/mm/yy y dd/mm/yyyy
        for fmt in ("%d/%m/%y", "%d/%m/%Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except Exception:
                pass

        return None

    return None


# =====================================================
# CLIENTES
# =====================================================

def get_clientes():
    db = _get_db()
    docs = db.collection("clientes").stream()
    items = []

    for d in docs:
        data = d.to_dict()
        data["id"] = d.id
        items.append(data)

    return pd.DataFrame(items) if items else pd.DataFrame()


def add_cliente(data: dict):
    db = _get_db()
    data["fecha_alta"] = datetime.utcnow()
    db.collection("clientes").add(data)


def ensure_cliente_basico(nombre_empresa: str, tipo: str):
    """
    Crea automáticamente un cliente si no existe.
    Útil para arquitecturas, ingenierías o promotoras detectadas al importar proyectos.
    """
    if not nombre_empresa:
        return

    db = _get_db()
    col = db.collection("clientes")
    query = col.where("empresa", "==", nombre_empresa).stream()

    exists = False
    for _ in query:
        exists = True
        break

    if not exists:
        col.add(
            {
                "empresa": nombre_empresa,
                "tipo_cliente": tipo,
                "fecha_alta": datetime.utcnow(),
            }
        )


# =====================================================
# PROYECTOS
# =====================================================

def get_proyectos():
    db = _get_db()
    docs = db.collection("obras").stream()
    items = []

    for d in docs:
        data = d.to_dict()
        data["id"] = d.id
        data["fecha_creacion"] = normalize_fecha(data.get("fecha_creacion"))
        data["fecha_seguimiento"] = normalize_fecha(data.get("fecha_seguimiento"))
        items.append(data)

    return pd.DataFrame(items) if items else pd.DataFrame()


def add_proyecto(data: dict):
    db = _get_db()
    data["fecha_creacion"] = datetime.utcnow()
    if "fecha_seguimiento" not in data or not data["fecha_seguimiento"]:
        data["fecha_seguimiento"] = (date.today() + timedelta(days=7)).isoformat()
    db.collection("obras").add(data)


def actualizar_proyecto(proyecto_id: str, data: dict):
    db = _get_db()
    db.collection("obras").document(proyecto_id).update(data)


def delete_proyecto(proyecto_id: str):
    db = _get_db()
    db.collection("obras").document(proyecto_id).delete()


def default_pasos_seguimiento():
    """
    Checklist base de pasos de seguimiento de un proyecto.
    """
    nombres = [
        "Identificar agentes clave (promotora / ingeniería / arquitectura / integrador)",
        "Primer contacto (llamada / email)",
        "Enviar dossier y referencias de 2N",
        "Programar reunión / demo con el cliente",
        "Preparar y enviar memoria técnica / oferta económica",
        "Seguimiento, ajustes y cierre (prescripción / adjudicación)",
    ]
    return [{"nombre": n, "completado": False} for n in nombres]


# =====================================================
# OBRAS IMPORTANTES
# =====================================================

def filtrar_obras_importantes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Obras importantes = prioridad Alta o potencial >= 50k,
    y en estados de seguimiento (no Ganado/Perdido).
    """
    if df is None or df.empty:
        return df

    df = df.copy()
    if "prioridad" not in df.columns:
        df["prioridad"] = "Media"

    if "potencial_eur" not in df.columns:
        df["potencial_eur"] = 0.0

    estados_ok = [
        "Detectado",
        "Seguimiento",
        "En Prescripción",
        "Oferta Enviada",
        "Negociación",
    ]

    mask_estado = df["estado"].fillna("").isin(estados_ok)
    mask_prioridad = df["prioridad"].fillna("") == "Alta"
    mask_potencial = df["potencial_eur"].fillna(0) >= 50000

    return df[mask_estado & (mask_prioridad | mask_potencial)].copy()


# =====================================================
# EXPORTAR EXCEL OBRAS IMPORTANTES
# =====================================================

def generar_excel_obras_importantes(df_proy: pd.DataFrame) -> BytesIO:
    importantes = filtrar_obras_importantes(df_proy)
    output = BytesIO()
    importantes.to_excel(output, index=False)
    output.seek(0)
    return output


# =====================================================
# IMPORTAR PROYECTOS DESDE EXCEL (PLANTILLA CHATGPT)
# =====================================================

def importar_proyectos_desde_excel(file) -> int:
    """
    Importa proyectos desde un Excel con columnas como:
    Proyecto, Ciudad, Provincia, Tipo_Proyecto, Segmento, Estado,
    Fuente_URL, Notas, Promotora_Fondo, Arquitectura, Ingenieria,
    Fecha_Inicio_Estimada, Fecha_Entrega_Estimada
    """
    try:
        df = pd.read_excel(file)
    except Exception:
        return 0

    db = _get_db()
    creados = 0
    hoy = date.today()

    for _, row in df.iterrows():
        nombre_obra = str(row.get("Proyecto", "")).strip()
        if not nombre_obra:
            continue

        promotor = (row.get("Promotora_Fondo") or None) and str(row.get("Promotora_Fondo")).strip()
        arquitectura = (row.get("Arquitectura") or None) and str(row.get("Arquitectura")).strip()
        ingenieria = (row.get("Ingenieria") or None) and str(row.get("Ingenieria")).strip()

        if promotor:
            ensure_cliente_basico(promotor, "Promotora")
        if arquitectura:
            ensure_cliente_basico(arquitectura, "Arquitectura")
        if ingenieria:
            ensure_cliente_basico(ingenieria, "Ingeniería")

        segmento = str(row.get("Segmento", "") or "").lower()
        prioridad = "Alta" if ("lujo" in segmento or "ultra" in segmento or "luxury" in segmento) else "Media"

        fecha_inicio = normalize_fecha(row.get("Fecha_Inicio_Estimada"))
        fecha_entrega = normalize_fecha(row.get("Fecha_Entrega_Estimada"))

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
            "tipo_proyecto": row.get("Tipo_Proyecto", None),
            "ciudad": row.get("Ciudad", None),
            "provincia": row.get("Provincia", None),
            "prioridad": prioridad,
            "potencial_eur": float(row.get("Potencial_Estimado", 0) or 0),
            "estado": row.get("Estado", "Detectado") or "Detectado",
            "fecha_seguimiento": (hoy + timedelta(days=7)).isoformat(),
            "fecha_inicio": fecha_inicio.isoformat() if isinstance(fecha_inicio, date) else fecha_inicio,
            "fecha_entrega": fecha_entrega.isoformat() if isinstance(fecha_entrega, date) else fecha_entrega,
            "notas_seguimiento": notas_full,
            "notas_historial": [],
            "tareas": [],
            "pasos_seguimiento": default_pasos_seguimiento(),
        }

        db.collection("obras").add(data)
        creados += 1

    return creados
