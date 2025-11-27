import streamlit as st
import pandas as pd

from crm_utils import get_proyectos, get_clientes


@st.cache_data(show_spinner=False)
def load_proyectos() -> pd.DataFrame | None:
    """Carga cacheada de proyectos desde Firestore."""
    return get_proyectos()


def invalidate_proyectos_cache() -> None:
    """Invalidar caché de proyectos tras escrituras en Firestore."""
    load_proyectos.clear()


@st.cache_data(show_spinner=False)
def load_clientes() -> pd.DataFrame | None:
    """Carga cacheada de clientes desde Firestore."""
    return get_clientes()


def invalidate_clientes_cache() -> None:
    """Invalidar caché de clientes tras escrituras en Firestore."""
    load_clientes.clear()
