from datetime import date, datetime, timedelta
from io import BytesIO
from typing import List, Dict, Any

import pandas as pd

from firebase_config import init_firebase


db = init_firebase()


def normalize_fecha(value):
    """Convierte Timestamp / datetime / date / str en date o None."""
    if value is None:
        return None
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
            for fmt in ("%d/%m/%y", "%d/%m/%Y"):
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
            return None
    return None


def default_pasos_seguimiento() -> List[Dict[str, Any]]:
    nombres = [
        "Identificar agentes clave (promotora / ingeniería / arquitectura / integrador)",
        "Primer contacto (llamada / email)",
        "Enviar dossier y referencias de 2N",
        "Programar reunión / demo con el cliente",
        "Preparar y enviar memoria técnica / oferta económica",
        "Seguimiento, ajustes y cierre (prescripción / adjudicación)",
    ]
    return [{"nombre": n, "completado": False} for n in nombres]


def get_clientes() -> pd.DataFrame:
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


def add_cliente(data: Dict[str, Any]) -> None:
    data["fecha_alta"] = datetime.utcnow()
    db.collection("clientes").add(data)


def ensure_cliente_basico(nombre: str | None, tipo: str) -> None:
    if not nombre:
        return
    col = db.collection("clientes")
    q = col.where("empresa", "==", nombre).where("tipo_cliente", "==", tipo).limit(1).stream()
    if any(True for _ in q):
        return
    col.add({
        "empresa": nombre,
        "tipo_cliente": tipo,
        "nombre": None,
        "email": None,
        "telefono": None,
        "ciudad": None,
        "provincia": None,
        "notas": "Creado automáticamente desde proyectos.",
        "fecha_alta": datetime.utcnow(),
    })


def get_proyectos() -> pd.DataFrame:
    docs = db.collection("obras").stream()
    items = []
    for d in docs:
        data = d.to_dict()
        data["id"] = d.id
        data["fecha_creacion"] = normalize_fecha(data.get("fecha_creacion"))
        data["fecha_seguimiento"] = normalize_fecha(data.get("fecha_seguimiento"))
        items.append(data)
    if not items:
        return pd.DataFrame()
    return pd.DataFrame(items)


def add_proyecto(data: Dict[str, Any]) -> None:
    data["fecha_creacion"] = datetime.utcnow()
    if "fecha_seguimiento" not in data or data["fecha_seguimiento"] is None:
        data["fecha_seguimiento"] = (date.today() + timedelta(days=7)).isoformat()
    db.collection("obras").add(data)


def actualizar_proyecto(proyecto_id: str, data: Dict[str, Any]) -> None:
    db.collection("obras").document(proyecto_id).update(data)


def delete_proyecto(proyecto_id: str) -> None:
    db.collection("obras").document(proyecto_id).delete()


def filtrar_obras_importantes(df_proy: pd.DataFrame) -> pd.DataFrame:
    if df_proy.empty:
        return df_proy.copy()

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


def generar_excel_obras_importantes(df_proy: pd.DataFrame) -> BytesIO:
    importantes = filtrar_obras_importantes(df_proy)
    output = BytesIO()
    importantes.to_excel(output, index=False, sheet_name="Obras importantes")
    output.seek(0)
    return output


def importar_proyectos_desde_excel(file) -> int:
    try:
        df = pd.read_excel(file)
    except Exception:
        return 0

    creados = 0
    hoy = date.today()

    def convertir_fecha(valor):
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

    for _, row in df.iterrows():
        try:
            nombre_obra = str(row.get("Proyecto", "")).strip()
            if not nombre_obra:
                continue

            ciudad = str(row.get("Ciudad", "") or "").strip() or None
            provincia = str(row.get("Provincia", "") or "").strip() or None
            tipo_proyecto = str(row.get("Tipo_Proyecto", "") or "").strip() or None
            estado = str(row.get("Estado", "Detectado") or "").strip() or "Detectado"
            segmento = str(row.get("Segmento", "") or "").lower()

            promotor = str(row.get("Promotora_Fondo", "") or "").strip() or None
            arquitectura = str(row.get("Arquitectura", "") or "").strip() or None
            ingenieria = str(row.get("Ingenieria", "") or "").strip() or None

            if "ultra" in segmento or "lujo" in segmento:
                prioridad = "Alta"
            else:
                prioridad = "Media"

            potencial = 0.0

            fecha_inicio = convertir_fecha(row.get("Fecha_Inicio_Estimada"))
            fecha_entrega = convertir_fecha(row.get("Fecha_Entrega_Estimada"))

            notas = str(row.get("Notas", "") or "").strip()
            url = str(row.get("Fuente_URL", "") or "").strip()
            notas_full = notas
            if url:
                notas_full = (notas_full + "\n" if notas_full else "") + f"Fuente: {url}"

            if promotor:
                ensure_cliente_basico(promotor, "Promotora")
            ensure_cliente_basico(arquitectura, "Arquitectura")
            ensure_cliente_basico(ingenieria, "Ingeniería")


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

            add_proyecto(data)
            creados += 1
        except Exception:
            continue

    return creados
