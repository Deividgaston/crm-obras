import streamlit as st
import pandas as pd

# Cachea llamadas a Firebase para no repetir cargas
@st.cache_data(show_spinner=False)
def load_proyectos():
    from crm_utils import get_proyectos
    return get_proyectos()

@st.cache_data(show_spinner=False)
def load_clientes():
    from crm_utils import get_clientes
    return get_clientes()

# Forzar estilo Salesforce
try:
    from style_injector import inject_apple_style
except Exception:
    def inject_apple_style():
        pass


# =========================================================
# GENERADOR DE PROMPT (LO MISMO QUE TU ARCHIVO ORIGINAL)
# =========================================================
def _construir_prompt(
    tipo_busqueda,
    zonas,
    verticales=None,
    estado_objetivo=None,
    min_viviendas=None,
    min_potencial=None,
    tipo_cliente=None,
    foco_negocio=None,
    horizonte=None,
    detalle=None,
):
    zonas_txt = ", ".join(zonas) if zonas else "toda España"

    if tipo_busqueda == "Proyectos":
        verticales_txt = ", ".join(verticales) if verticales else "cualquier tipología"
        estado_txt = ", ".join(estado_objetivo) if estado_objetivo else "cualquier fase"
        extra = f"\n\nDetalles adicionales: {detalle}" if detalle else ""

        prompt = f"""
Eres un analista de mercado inmobiliario especializado en prescripción de soluciones de control de accesos y videoportero IP (2N).

Quiero que busques **proyectos inmobiliarios** en las zonas: {zonas_txt}.
Tipos de proyecto objetivo: {verticales_txt}.
Fase del proyecto: {estado_txt}.
Horizonte temporal: {horizonte}.

Si hay dato disponible, prioriza proyectos:
- con un volumen relevante de viviendas (mínimo {min_viviendas} si aplica),
- y un potencial de inversión en control de accesos / videoportero IP superior a {min_potencial} €.

Devuélveme la información en formato tabla pensando en un Excel con estas columnas:

- Proyecto
- Ciudad
- Provincia
- Tipo_Proyecto
- Segmento (lujo, estándar, BTR, etc.)
- Nº_viviendas_aprox
- Promotora_Fondo
- Arquitectura
- Ingenieria
- Fase_proyecto
- Fecha_Inicio_Estimada
- Fecha_Entrega_Estimada
- Potencial_2N (estimación en € si puedes)
- Fuente_URL
- Notas

Quiero como salida SOLO la tabla, sin explicaciones alrededor.

{extra}
        """.strip()
        return prompt

    else:
        tipos_txt = ", ".join(tipo_cliente) if tipo_cliente else "cualquier tipo"
        foco_txt = ", ".join(foco_negocio) if foco_negocio else "cualquier segmento"
        extra = f"\n\nDetalles adicionales: {detalle}" if detalle else ""

        prompt = f"""
Eres un analista de negocio especializado en identificar **clientes potenciales para soluciones 2N** (control de accesos y videoportero IP).

Quiero que busques **empresas** (no proyectos) en las zonas: {zonas_txt}.
Tipo de empresa objetivo: {tipos_txt}.
Foco principal de negocio: {foco_txt}.
Horizonte temporal: {horizonte}.

Devuélveme la información en formato tabla pensando en un Excel con estas columnas:

- Empresa
- Tipo_Cliente
- Persona_contacto_principal
- Cargo
- Email
- Teléfono
- Ciudad
- Provincia
- Web
- LinkedIn
- Notas

Quiero como salida SOLO la tabla, sin explicaciones alrededor.

{extra}
        """.strip()
        return prompt


# =========================================================
# PÁGINA PRINCIPAL — RENDER BUSCAR
# =========================================================
def render_buscar():
    inject_apple_style()

    # ------------------------------
    # CABECERA SALESFORCE
    # ------------------------------
    st.markdown(
        """
        <div class="apple-card">
            <div class="section-badge">Scouting</div>
            <h3 style="margin-top:4px; margin-bottom:4px;">Buscar proyectos y clientes</h3>
            <p style="color:#5A6872; margin-bottom:0; font-size:0.85rem;">
                Diseña búsquedas inteligentes para que ChatGPT te prepare Excels de proyectos
                o clientes según zona, segmento y vertical.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.markdown("#### 🎯 Configurar búsqueda", unsafe_allow_html=True)

    # ------------------------------
    # OPCIÓN PRINCIPAL
    # ------------------------------
    tipo_busqueda = st.radio(
        "¿Qué quieres buscar?",
        ["Proyectos", "Clientes"],
        horizontal=True,
        key="tipo_busqueda_opt",
    )

    # ------------------------------
    # ZONAS
    # ------------------------------
    zonas = st.multiselect(
        "Zonas / provincias a buscar",
        ["Madrid", "Málaga", "Barcelona", "Valencia", "Alicante", "Mallorca", "Otras"],
        default=["Madrid", "Málaga"],
        key="zonas_select",
    )

    # ------------------------------
    # OPCIONES SI BUSCO PROYECTOS
    # ------------------------------
    verticales = estado_objetivo = min_viviendas = min_potencial = None
    tipo_cliente = foco_negocio = None

    if tipo_busqueda == "Proyectos":

        verticales = st.multiselect(
            "Verticales de proyecto",
            ["Residencial lujo", "Residencial", "Oficinas", "Hotel", "BTR", "Otros"],
            default=["Residencial lujo", "Oficinas", "Hotel"],
            key="verticales_select",
        )

        estado_objetivo = st.multiselect(
            "Momento del proyecto",
            ["Solar", "Proyecto básico", "Proyecto ejecutivo", "Obra en curso"],
            default=["Proyecto básico", "Proyecto ejecutivo"],
            key="estado_select",
        )

        col1, col2 = st.columns(2)
        with col1:
            min_viviendas = st.number_input(
                "Mínimo nº de viviendas (si aplica)",
                min_value=0,
                step=10,
                value=0,
                key="min_viv",
            )

        with col2:
            min_potencial = st.number_input(
                "Potencial mínimo 2N (€)",
                min_value=0,
                step=50000,
                value=0,
                key="min_pot",
            )

    # ------------------------------
    # OPCIONES SI BUSCO CLIENTES
    # ------------------------------
    else:
        tipo_cliente = st.multiselect(
            "Tipo de cliente",
            ["Promotora", "Ingeniería", "Arquitectura", "Integrator Partner", "Fondo"],
            default=["Promotora", "Ingeniería", "Arquitectura"],
            key="tipo_cliente_select",
        )

        foco_negocio = st.multiselect(
            "Foco principal",
            ["Residencial lujo", "BTR", "Oficinas", "Hoteles", "Mixto"],
            default=["Residencial lujo", "BTR"],
            key="foco_cliente_select",
        )

    # ------------------------------
    # HORIZONTE
    # ------------------------------
    horizonte = st.selectbox(
        "Horizonte temporal",
        ["Proyectos en licitación ahora", "Entrega 12-24 meses", "Entrega +24 meses"],
        index=0,
        key="horizonte_select",
    )

    detalle = st.text_area(
        "Detalles extra que quieres que tenga en cuenta ChatGPT (opcional)",
        placeholder="Ejemplo: proyectos donde la domótica no sea el foco principal y el acceso IP sí.",
        key="detalle_txt",
    )

    # ==================================================
    # BOTÓN GENERAR PROMPT
    # ==================================================
    genera = st.button("🔄 Generar prompt", key="gen_prompt_btn")

    # ==================================================
    # PROMPT RESULTADO
    # ==================================================
    st.markdown("#### 🧠 Prompt generado para ChatGPT")

    if genera:
        prompt = _construir_prompt(
            tipo_busqueda=tipo_busqueda,
            zonas=zonas,
            verticales=verticales,
            estado_objetivo=estado_objetivo,
            min_viviendas=min_viviendas,
            min_potencial=min_potencial,
            tipo_cliente=tipo_cliente,
            foco_negocio=foco_negocio,
            horizonte=horizonte,
            detalle=detalle,
        )
        st.code(prompt, language="markdown")
    else:
        st.info("Configura parámetros y pulsa *Generar prompt*.")

    st.caption("Copia este prompt y úsalo en ChatGPT para obtener un Excel listo para importar al CRM.")
    st.markdown("</div>", unsafe_allow_html=True)
