import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, date, timedelta
import pandas as pd
from io import BytesIO

# =====================================================
# INICIALIZACIÓN FIREBASE
# =====================================================

if not firebase_admin._apps:
    cred = credentials.Certificate(
        # Se rellena desde streamlit con st.secrets["firebase_key"]
        # El archivo principal app.py ya lo carga correctamente.
        {}
    )
    firebase_admin.initialize_app(cred)

db = firestore.client()


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
            except:
                pass

        return None

    return None


# =====================================================
# CLIENTES
# =====================================================

def get_clientes():
    docs = db.collection("clientes").stream()
    items = []

    for d in docs:
        data = d.to_dict()
        data["id"] = d.id
        items.append(data)

    return pd.DataFrame(items) if items else pd.DataFrame()


def add_cliente(data):
    data["fecha_alta"] = datetime.utcnow()
    db.collection("clientes").add(data)


def ensure_cliente_basico(nombre_empresa: str, tipo: str):
    """
    Crea automáticamente un cliente si no existe.
    útil para Arquitectura, Ingeniería o Promotora detectadas en proyectos importados.
    """
    if not nombre_empresa:
        return

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
    data["fecha_creacion"] = datetime.utcnow()
    if "fecha_seguimiento" not in data or not data["fecha_seguimiento"]:
        data["fecha_seguimiento"] = (date.today() + timedelta(days=7)).isoformat()

    db.collection("obras").add(data)


def actualizar_proyecto(proyecto_id, data):
    db.collection("obras").document(proyecto_id).update(data)


def delete_proyecto(proyecto_id):
    db.collection("obras").document(proyecto_id).delete()


# =====================================================
# OBRAS IMPORTANTES
# =====================================================

def filtrar_obras_importantes(df: pd.DataFrame) -> pd.DataFrame:
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
# EXPORTAR EXCEL
# =====================================================

def generar_excel_obras_importantes(df_proy: pd.DataFrame):
    importantes = filtrar_obras_importantes(df_proy)

    output = BytesIO()
    importantes.to_excel(output, index=False)
    output.seek(0)
    return output


# =====================================================
# IMPORTAR PROYECTOS DESDE EXCEL CHATGPT
# =====================================================

def importar_proyectos_desde_excel(file) -> int:
    try:
        df = pd.read_excel(file)
    except Exception:
        return 0

    creados = 0
    hoy = date.today()

    for _, row in df.iterrows():
        nombre_obra = str(row.get("Proyecto", "")).strip()
        if not nombre_obra:
            continue

        promotor = row.get("Promotora_Fondo", None)
        arquitectura = row.get("Arquitectura", None)
        ingenieria = row.get("Ingenieria", None)

        if promotor:
            ensure_cliente_basico(promotor, "Promotora")
        if arquitectura:
            ensure_cliente_basico(arquitectura, "Arquitectura")
        if ingenieria:
            ensure_cliente_basico(ingenieria, "Ingeniería")

        fecha_inicio = normalize_fecha(row.get("Fecha_Inicio_Estimada"))
        fecha_entrega = normalize_fecha(row.get("Fecha_Entrega_Estimada"))

        data = {
            "nombre_obra": nombre_obra,
            "cliente_principal": promotor,
            "promotora": promotor,
            "arquitectura": arquitectura,
            "ingenieria": ingenieria,
            "tipo_proyecto": row.get("Tipo_Proyecto", None),
            "ciudad": row.get("Ciudad", None),
            "provincia": row.get("Provincia", None),
            "prioridad": "Alta" if str(row.get("Segmento", "")).lower() in ["lujo", "ultra", "luxury"] else "Media",
            "potencial_eur": 0.0,
            "estado": row.get("Estado", "Detectado"),
            "fecha_seguimiento": (hoy + timedelta(days=7)).isoformat(),
            "fecha_inicio": fecha_inicio,
            "fecha_entrega": fecha_entrega,
            "notas_seguimiento": str(row.get("Notas", "")).strip(),
        }

        add_proyecto(data)
        creados += 1

    return creados
