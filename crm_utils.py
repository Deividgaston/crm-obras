# crm_utils.py

import io
from datetime import date, datetime, timedelta

import firebase_admin
import pandas as pd
from firebase_admin import firestore


# =====================================================
# FIRESTORE DB HELPER
# =====================================================

def _get_db():
    """
    Devuelve el cliente de Firestore.

    IMPORTANTE:
    - Firebase se inicializa en app.py usando st.secrets["firebase_key"].
    - Aquí asumimos que eso ya está hecho. Si no, lanzamos un error claro.
    """
    try:
        firebase_admin.get_app()
    except ValueError:
        raise RuntimeError(
            "Firebase no está inicializado. Inicialízalo en app.py antes de usar crm_utils."
        )
    return firestore.client()


# =====================================================
# UTILIDADES DE FECHAS
# =====================================================

def normalize_fecha(value):
    """
    Convierte Timestamp / datetime / date / str en date o None.
    La usamos para mostrar y comparar fechas en los DataFrames.
    """
    if value is None:
        return None

    # Firestore Timestamp
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

        # Intentamos ISO (2025-11-30)
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            pass

        # Intentamos formatos típicos dd/mm/aa o dd/mm/aaaa
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
        "Seguimiento, ajustes y cierre (prescripción / adjudicación)",
    ]
    return [{"nombre": n, "completado": False} for n in nombres]


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
        # Si quisieras fecha_alta, aquí se podría normalizar
        if "fecha_alta" in data:
            data["fecha_alta"] = normalize_fecha(data.get("fecha_alta"))
        items.append(data)

    if not items:
        return pd.DataFrame()

    return pd.DataFrame(items)


def add_cliente(data: dict):
    """
    Inserta un cliente en la colección 'clientes'.
    Añade fecha_alta = datetime.utcnow() si no viene.
    """
    db = _get_db()
    if "fecha_alta" not in data or data["fecha_alta"] is None:
        data["fecha_alta"] = datetime.utcnow()
    db.collection("clientes").add(data)


def ensure_cliente_basico(nombre: str | None, tipo_cliente: str):
    """
    Crea un cliente mínimo (empresa) si no existe ya.

    - nombre: normalmente 'empresa' (Promotora, Arquitectura, Ingeniería)
    - tipo_cliente: 'Promotora', 'Arquitectura', 'Ingeniería', etc.
    """
    if not nombre:
        return

    db = _get_db()
    col = db.collection("clientes")

    # Buscamos por campo empresa
    query = col.where("empresa", "==", nombre).limit(1).stream()
    found = any(True for _ in query)
    if found:
        return

    col.add(
        {
            "nombre": "",
            "empresa": nombre,
            "tipo_cliente": tipo_cliente,
            "email": "",
            "telefono": "",
            "ciudad": "",
            "provincia": "",
            "notas": "Creado automáticamente desde importación/proyecto.",
            "fecha_alta": datetime.utcnow(),
        }
    )


# =====================================================
# PROYECTOS / OBRAS
# =====================================================

def get_proyectos():
    db = _get_db()
    docs = db.collection("obras").stream()
    items = []
    for d in docs:
        data = d.to_dict()
        data["id"] = d.id

        # Normalizamos fechas
        data["fecha_creacion"] = normalize_fecha(data.get("fecha_creacion"))
        data["fecha_seguimiento"] = normalize_fecha(data.get("fecha_seguimiento"))

        # Otros campos de fecha opcionales
        if "fecha_inicio" in data:
            data["fecha_inicio"] = normalize_fecha(data.get("fecha_inicio"))
        if "fecha_entrega" in data:
            data["fecha_entrega"] = normalize_fecha(data.get("fecha_entrega"))

        items.append(data)

    if not items:
        return pd.DataFrame()

    return pd.DataFrame(items)


def add_proyecto(data: dict):
    """
    Inserta un proyecto en la colección 'obras'.

    - Fuerza fecha_creacion como datetime.utcnow()
    - Si no hay fecha_seguimiento, pone hoy+7 (ISO string)
    """
    db = _get_db()
    data = dict(data)  # copia defensiva
    data["fecha_creacion"] = datetime.utcnow()

    if "fecha_seguimiento" not in data or data["fecha_seguimiento"] is None:
        data["fecha_seguimiento"] = (date.today() + timedelta(days=7)).isoformat()
    elif isinstance(data["fecha_seguimiento"], (date, datetime)):
        data["fecha_seguimiento"] = data["fecha_seguimiento"].isoformat()

    db.collection("obras").add(data)


def actualizar_proyecto(proyecto_id: str, data: dict):
    db = _get_db()
    # Normalizamos algunas fechas si vienen como date
    if "fecha_seguimiento" in data and isinstance(
        data["fecha_seguimiento"], (date, datetime)
    ):
        data["fecha_seguimiento"] = data["fecha_seguimiento"].isoformat()

    if "fecha_inicio" in data and isinstance(
        data["fecha_inicio"], (date, datetime)
    ):
        data["fecha_inicio"] = data["fecha_inicio"].isoformat()

    if "fecha_entrega" in data and isinstance(
        data["fecha_entrega"], (date, datetime)
    ):
        data["fecha_entrega"] = data["fecha_entrega"].isoformat()

    db.collection("obras").document(proyecto_id).update(data)


def delete_proyecto(proyecto_id: str):
    db = _get_db()
    db.collection("obras").document(proyecto_id).delete()


# =====================================================
# FILTRADO OBRAS IMPORTANTES
# =====================================================

def filtrar_obras_importantes(df_proy: pd.DataFrame) -> pd.DataFrame:
    """
    Define qué es una 'obra importante':
    - Estado en seguimiento (no perdido, no ganado), Y
    - Prioridad Alta, O
    - Potencial estimado >= 50.000 €
    """
    if df_proy is None or df_proy.empty:
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
        "En comercialización",
    ]

    mask_estado = df["estado"].isin(estados_seguimiento)
    mask_prioridad = df["prioridad"] == "Alta"
    mask_potencial = df["potencial_eur"].fillna(0) >= 50000

    importantes = df[mask_estado & (mask_prioridad | mask_potencial)].copy()
    return importantes


# =====================================================
# IMPORTAR PROYECTOS DESDE EXCEL (ChatGPT)
# =====================================================

def _convertir_fecha_excel(valor):
    """
    Convierte un valor procedente de Excel a un string ISO 'YYYY-MM-DD'
    o None. Acepta:
    - celdas vacías / NaN
    - date/datetime
    - str en formatos dd/mm/aa, dd/mm/aaaa, ISO
    """
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

        # ISO directo
        try:
            d = datetime.fromisoformat(valor)
            if isinstance(d, datetime):
                d = d.date()
            return d.isoformat()
        except Exception:
            pass

        # Último recurso: texto tal cual
        return valor

    # Otros tipos -> str
    try:
        return str(valor)
    except Exception:
        return None


def importar_proyectos_desde_excel(file) -> int:
    """
    Importa proyectos desde un Excel generado por ChatGPT y los guarda en Firestore.
    Devuelve el número de proyectos creados.

    Columnas esperadas (nombres orientativos):
    - Proyecto
    - Ciudad
    - Provincia
    - Tipo_Proyecto
    - Segmento
    - Estado
    - Promotora_Fondo
    - Arquitectura
    - Ingenieria
    - Fecha_Inicio_Estimada
    - Fecha_Entrega_Estimada
    - Notas
    - Fuente_URL
    """
    try:
        df = pd.read_excel(file)
    except Exception as e:
        # Este error se maneja desde la página de proyectos
        raise RuntimeError(f"Error leyendo el Excel: {e}")

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

            # Promotor como cliente principal
            promotor = str(row.get("Promotora_Fondo", "") or "").strip() or None

            arquitectura = str(row.get("Arquitectura", "") or "").strip() or None
            ingenieria = str(row.get("Ingenieria", "") or "").strip() or None

            # Creamos clientes mínimos si no existen
            if promotor:
                ensure_cliente_basico(promotor, "Promotora")
            if arquitectura:
                ensure_cliente_basico(arquitectura, "Arquitectura")
            if ingenieria:
                ensure_cliente_basico(ingenieria, "Ingeniería")

            # Prioridad simple basada en segmento
            if "ultra" in segmento or "lujo" in segmento:
                prioridad = "Alta"
            else:
                prioridad = "Media"

            potencial = 0.0  # se puede mejorar más adelante

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
                "estado": estado,
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
            # No paramos la importación por una fila mala
            print(f"No se pudo importar una fila: {e}")

    return creados


# =====================================================
# GENERAR EXCEL DE OBRAS IMPORTANTES (openpyxl)
# =====================================================

def generar_excel_obras_importantes(df_proy: pd.DataFrame) -> io.BytesIO:
    """
    Genera un Excel en memoria con las obras importantes usando openpyxl
    (compatible con Streamlit Cloud).
    """
    df_imp = filtrar_obras_importantes(df_proy)
    if df_imp is None or df_imp.empty:
        # Devolvemos un Excel vacío pero válido
        df_imp = pd.DataFrame(
            columns=[
                "nombre_obra",
                "cliente_principal",
                "ciudad",
                "provincia",
                "estado",
                "prioridad",
                "potencial_eur",
                "fecha_seguimiento",
            ]
        )

    # Quitamos columnas técnicas que no quieras exportar
    cols_export = [
        c
        for c in df_imp.columns
        if c not in ("id", "notas_historial", "tareas", "pasos_seguimiento")
    ]
    df_imp = df_imp[cols_export]

    buffer = io.BytesIO()
    # 🔴 Antes: engine="xlsxwriter" (no disponible en Streamlit Cloud)
    # ✅ Ahora: engine="openpyxl"
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_imp.to_excel(writer, index=False, sheet_name="Obras_importantes")

    buffer.seek(0)
    return buffer
