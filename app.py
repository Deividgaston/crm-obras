import streamlit as st
from datetime import date, datetime, timedelta

# Funciones de acceso a datos (Firestore) y utilidades
from crm_utils import (
    get_clientes,
    get_proyectos,
    add_cliente,
    actualizar_proyecto,
)

# Páginas específicas
from proyectos_page import render_proyectos
from buscar_page import render_buscar
from clientes_page import render_clientes_page  # tu página de clientes


# ==========================
# CONFIGURACIÓN GENERAL
# ==========================
st.set_page_config(
    page_title="CRM Prescripción",
    layout="wide",
    page_icon="🏗️",
)

# ==========================
# ESTILO APPLE-LIKE
# ==========================
st.markdown(
    """
<style>
/* Fuente tipo SF / Inter */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
    background: #020617 !important;  /* fondo dark azul marino */
}

/* Contenedor principal */
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2.4rem;
    max-width: 1200px;
}

/* Sidebar Apple style */
[data-testid="stSidebar"] {
    background: rgba(15,23,42,0.96) !important; /* slate-900 */
    backdrop-filter: blur(16px);
    border-right: 1px solid rgba(15,23,42,0.85);
}

[data-testid="stSidebar"] h1, 
[data-testid="stSidebar"] h2, 
[data-testid="stSidebar"] h3 {
    font-weight: 600 !important;
    color: #E5E7EB !important;
}

/* Títulos globales */
h1 {
    font-weight: 640 !important;
    letter-spacing: -0.03em;
    font-size: 1.7rem !important;
    color: #E5E7EB !important;
}

h2 {
    font-weight: 600 !important;
    letter-spacing: -0.02em;
    font-size: 1.25rem !important;
    color: #E5E7EB !important;
}

/* Tarjetas principales */
.apple-card {
    padding: 16px 20px;
    background: radial-gradient(circle at top left, #0F172A 0%, #020617 70%);
    border-radius: 18px;
    border: 1px solid rgba(148,163,184,0.28);
    box-shadow: 0 24px 60px rgba(15,23,42,0.85);
    margin-bottom: 18px;
}

/* Tarjeta ligera (listas, tablas) */
.apple-card-light {
    padding: 14px 18px;
    background: #020617;
    border-radius: 16px;
    border: 1px solid rgba(51,65,85,0.9);
    box-shadow: 0 18px 40px rgba(15,23,42,0.9);
    margin-bottom: 16px;
}

/* Métricas de cabecera tipo Apple dashboard */
.metric-row {
    display: flex;
    gap: 14px;
    margin-top: 6px;
    margin-bottom: 8px;
}

.metric-box {
    flex: 1;
    padding: 12px 14px;
    background: radial-gradient(circle at top left, #0B1120 0%, #020617 70%);
    border-radius: 14px;
    border: 1px solid rgba(51,65,85,0.9);
    box-shadow: 0 18px 40px rgba(15,23,42,0.9);
}

.metric-title {
    font-size: 0.78rem;
    color: #9CA3AF;
    letter-spacing: 0.09em;
    text-transform: uppercase;
}

.metric-value {
    font-size: 1.5rem;
    font-weight: 640;
    margin-top: 2px;
    color: #E5E7EB;
}

.metric-sub {
    font-size: 0.76rem;
    color: #6B7280;
    margin-top: 2px;
}

/* Botones más suaves