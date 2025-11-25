import pandas as pd
from datetime import datetime
from typing import Dict, Any

from crm_utils import get_proyectos


def load_dashboard_data() -> pd.DataFrame:
    """
    Carga y normaliza los datos de proyectos para el dashboard.
    Usa get_proyectos() que ya está cacheado en crm_utils, así que
    no machaca Firestore en cada rerun.
    """
    proyectos = get_proyectos()

    # Acepta lista de dicts, DataFrame o None
    if proyectos is None:
        df = pd.DataFrame()
    elif isinstance(proyectos, pd.DataFrame):
        df = proyectos.copy()
    else:
        df = pd.DataFrame(proyectos)

    if df.empty:
        return df

    # --- Normalización de columnas clave ---
    # Potencial económico
    if "potencial_eur" not in df.columns:
        df["potencial_eur"] = 0.0
    df["potencial_eur"] = pd.to_numeric(
        df["potencial_eur"], errors="coerce"
    ).fillna(0.0)

    # Estado del proyecto
    if "estado" not in df.columns:
        df["estado"] = "Detectado"
    df["estado"] = df["estado"].fillna("Detectado")

    # Prioridad
    if "prioridad" not in df.columns:
        df["prioridad"] = "Media"
    df["prioridad"] = df["prioridad"].fillna("Media")

    # Fecha creación
    if "fecha_creacion" in df.columns:
        df["fecha_creacion"] = pd.to_datetime(
            df["fecha_creacion"], errors="coerce"
        )
    else:
        df["fecha_creacion"] = pd.NaT

    # Año-mes para series temporales
    df["anio_mes"] = df["fecha_creacion"].dt.to_period("M").astype(str)

    # Provincia
    if "provincia" not in df.columns:
        df["provincia"] = ""
    df["provincia"] = df["provincia"].fillna("")

    # Promotora / cliente principal unificado
    if "cliente_principal" in df.columns:
        base = df["cliente_principal"]
    else:
        base = None

    if base is not None:
        df["promotora_display"] = base.fillna("").astype(str)
    else:
        df["promotora_display"] = ""

    return df


def compute_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcula KPIs globales a partir del dataframe normalizado.
    """
    if df.empty:
        return {
            "total_proyectos": 0,
            "total_potencial": 0.0,
            "ticket_medio": 0.0,
            "proyectos_activos": 0,
            "ratio_ganados": 0.0,
        }

    total_proyectos = len(df)
    total_potencial = float(df["potencial_eur"].sum())
    ticket_medio = float(
        df["potencial_eur"].mean() if total_proyectos > 0 else 0.0
    )

    # Proyectos activos (todo menos Perdido / Paralizado)
    activos = df[
        ~df["estado"].isin(["Perdido", "Paralizado"])
    ]
    proyectos_activos = len(activos)

    # Ratio ganados
    ganados = (df["estado"] == "Ganado").sum()
    ratio_ganados = (
        (ganados / total_proyectos) * 100 if total_proyectos > 0 else 0.0
    )

    return {
        "total_proyectos": total_proyectos,
        "total_potencial": total_potencial,
        "ticket_medio": ticket_medio,
        "proyectos_activos": proyectos_activos,
        "ratio_ganados": ratio_ganados,
    }


def compute_funnel_estado(df: pd.DataFrame) -> pd.DataFrame:
    """
    Genera un dataframe para un funnel simple basado en 'estado'.
    Orden típico de tu pipeline.
    """
    if df.empty:
        return pd.DataFrame(columns=["estado", "proyectos"])

    orden = [
        "Detectado",
        "Seguimiento",
        "En Prescripción",
        "Oferta Enviada",
        "Negociación",
        "Ganado",
        "Perdido",
        "Paralizado",
    ]

    conteo = df["estado"].value_counts().to_dict()
    data = []

    for estado in orden:
        data.append(
            {
                "estado": estado,
                "proyectos": int(conteo.get(estado, 0)),
            }
        )

    return pd.DataFrame(data)


def compute_proyectos_por_mes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Número de proyectos creados por mes (anio_mes).
    """
    if df.empty or "anio_mes" not in df.columns:
        return pd.DataFrame(columns=["anio_mes", "proyectos"])

    g = df.groupby("anio_mes")["id"].count().reset_index()
    g = g.rename(columns={"id": "proyectos"})
    # Orden cronológico
    try:
        g["anio_mes_dt"] = pd.to_datetime(g["anio_mes"], format="%Y-%m")
        g = g.sort_values("anio_mes_dt")
    except Exception:
        pass
    return g[["anio_mes", "proyectos"]]


def compute_potencial_por_provincia(df: pd.DataFrame) -> pd.DataFrame:
    """
    Potencial total y número de obras por provincia.
    """
    if df.empty:
        return pd.DataFrame(columns=["provincia", "proyectos", "potencial"])

    g = df.groupby("provincia").agg(
        proyectos=("id", "count"),
        potencial=("potencial_eur", "sum"),
    ).reset_index()
    g = g[g["provincia"].str.strip() != ""]
    g = g.sort_values("potencial", ascending=False)
    return g


def compute_ranking_promotoras(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """
    Ranking de promotoras/cliente principal por potencial total.
    """
    if df.empty:
        return pd.DataFrame(columns=["promotora_display", "proyectos", "potencial"])

    g = df.groupby("promotora_display").agg(
        proyectos=("id", "count"),
        potencial=("potencial_eur", "sum"),
    ).reset_index()
    g = g[g["promotora_display"].str.strip() != ""]
    g = g.sort_values("potencial", ascending=False).head(top_n)
    return g


def compute_prioridades(df: pd.DataFrame) -> pd.DataFrame:
    """
    Conteo de proyectos por prioridad.
    """
    if df.empty:
        return pd.DataFrame(columns=["prioridad", "proyectos"])

    g = df.groupby("prioridad")["id"].count().reset_index()
    g = g.rename(columns={"id": "proyectos"})
    return g


def compute_histograma_potencial(df: pd.DataFrame) -> pd.Series:
    """
    Devuelve la serie de potencial para histogramas/análisis.
    """
    if df.empty:
        return pd.Series([], dtype=float)
    return df["potencial_eur"]
