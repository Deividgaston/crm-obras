import streamlit as st

def inject_global_styles():
    st.markdown("""
    <style>

    /* ------------------------------------------------------------------------------------
       TIPOGRAFÍA & BASE
    ------------------------------------------------------------------------------------ */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
        background: #0F172A !important;  /* Azul oscuro profesional */
        color: #E2E8F0 !important;      /* Texto gris-azulado suave */
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1250px;
    }

    /* ------------------------------------------------------------------------------------
       SIDEBAR (Cristal, estilo Apple)
    ------------------------------------------------------------------------------------ */
    [data-testid="stSidebar"] {
        background: rgba(30, 41, 59, 0.45) !important;
        backdrop-filter: blur(18px);
        border-right: 1px solid rgba(255,255,255,0.07);
    }

    [data-testid="stSidebar"] * {
        color: #E2E8F0 !important;
    }

    /* ------------------------------------------------------------------------------------
       TARJETAS TIPO APPLE
    ------------------------------------------------------------------------------------ */
    .apple-card {
        padding: 18px 22px;
        background: linear-gradient(145deg, #1E293B 0%, #0F172A 100%);
        border-radius: 18px;
        border: 1px solid rgba(148,163,184,0.18);
        box-shadow: 0 12px 28px rgba(0,0,0,0.45);
        margin-bottom: 18px;
    }

    .apple-card-light {
        padding: 16px 20px;
        background: rgba(30,41,59,0.65);
        border-radius: 16px;
        border: 1px solid rgba(148,163,184,0.25);
        box-shadow: 0 8px 20px rgba(0,0,0,0.35);
        margin-bottom: 18px;
    }

    /* ------------------------------------------------------------------------------------
       PESTAÑAS
    ------------------------------------------------------------------------------------ */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(30,41,59,0.6);
        border-radius: 16px;
        padding: 4px 6px;
    }

    .stTabs [data-baseweb="tab"] {
        color: #CBD5E1 !important;
        font-weight: 500;
    }

    .stTabs [aria-selected="true"] {
        background: #1E40AF !important;   /* Azul fuerte Apple */
        color: white !important;
        border-radius: 10px;
        font-weight: 600 !important;
    }

    /* ------------------------------------------------------------------------------------
       BADGES (SECCIÓN)
    ------------------------------------------------------------------------------------ */
    .section-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 999px;
        background: rgba(96,165,250,0.18);
        color: #60A5FA;
        font-size: 0.75rem;
        font-weight: 500;
        letter-spacing: 0.03em;
    }

    /* ------------------------------------------------------------------------------------
       FORMULARIOS & BOTONES
    ------------------------------------------------------------------------------------ */
    textarea, input, select {
        border-radius: 10px !important;
        background: rgba(255,255,255,0.04) !important;
        color: #F1F5F9 !important;
    }

    button[kind="primary"] {
        border-radius: 999px !important;
        background: #1E40AF !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
    }

    button {
        color: white !important;
    }

    /* ------------------------------------------------------------------------------------
       TABLAS
    ------------------------------------------------------------------------------------ */
    .data-editor-container {
        background-color: rgba(255,255,255,0.04) !important;
        border-radius: 12px !important;
    }

    /* ------------------------------------------------------------------------------------
       MODALES SIMULADOS
    ------------------------------------------------------------------------------------ */
    .modal-card {
        background: rgba(30,41,59,0.75);
        border: 1px solid rgba(148,163,184,0.25);
        border-radius: 18px;
        padding: 20px;
        box-shadow: 0 25px 60px rgba(0,0,0,0.6);
        margin-top: 20px;
        animation: fadeIn 0.18s ease-in-out;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(14px); }
        to { opacity: 1; transform: translateY(0); }
    }

    </style>
    """, unsafe_allow_html=True)

# Alias para compatibilidad con el resto de la app
def inject_apple_style():
    """
    Mantiene el nombre antiguo para no tocar el resto del código.
    Internamente solo llama a inject_global_styles().
    """
    inject_global_styles()

