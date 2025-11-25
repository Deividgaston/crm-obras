import streamlit as st

# Inyectar estilo Apple para mantener coherencia visual
try:
    from style_injector import inject_apple_style
except Exception:
    def inject_apple_style():
        pass


# ============================================================
#  Página principal BUSCAR
# ============================================================

def render_buscar():

    inject_apple_style()

    # ⚠️ MARCA DE VERSIÓN PARA COMPROBAR QUE ESTE ARCHIVO SE ESTÁ EJECUTANDO
    st.markdown("🟢 <b>VERSIÓN NUEVA DE BUSCAR_PAGE.PY CARGADA</b>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="apple-card">
            <div class="section-badge">Scouting</div>
            <h1 style="margin-top:4px; margin-bottom:4px;">Buscar proyectos y clientes</h1>
            <p style="color:#9CA3AF; margin-bottom:0; font-size:0.9rem;">
                Diseña búsquedas inteligentes para que ChatGPT te prepare Excels de proyectos
                o clientes en función de zona, tipo de activo y segmento.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- Contenedor principal ---
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.markdown("#### 🎯 Configurar búsqueda", unsafe_allow_html=True)

    tipo_busqueda = st.radio(
        "¿Qué quieres buscar?",
        ["Proyectos", "Clientes"],
        horizontal=True,
    )

    zonas = st.multiselect(
        "Zonas / provincias a buscar",
        ["Madrid", "Málaga", "Barcelona", "Valencia", "Alicante", "Mallorca", "Otras"],
        default=["Madrid", "Málaga"],
    )

    # --------- Si la búsqueda es de proyectos ----------
    if tipo_busqueda == "Proyectos":

        verticales = st.multiselect(
            "Verticales de proyecto",
            ["Residencial lujo", "Residencial", "Oficinas", "Hotel", "BTR", "Otros"],
            default=["Residencial lujo", "Oficinas", "Hotel"],
        )

        estado_objetivo = st.multiselect(
            "Momento del proyecto",
            ["Solar", "Proyecto básico", "Proyecto ejecutivo", "Obra en curso"],
            default=["Proyecto básico", "Proyecto ejecutivo"],
        )

        min_viviendas = st.number_input(
            "Mínimo nº de viviendas (si aplica)",
            min_value=0,
            step=10,
            value=0,
        )

        min_potencial = st.number_input(
            "Potencial mínimo estimado para 2N (€)",
            min_value=0,
            step=50000,
            value=0,
        )

    # --------- Si la búsqueda es de clientes ----------
    else:
        tipo_cliente = st.multiselect(
            "Tipo de cliente",
            ["Promotora", "Ingeniería", "Arquitectura", "Integrator Partner", "Fondo"],
            default=["Promotora", "Ingeniería", "Arquitectura"],
        )

        foco_negocio = st.multiselect(
            "Foco principal",
            ["Residencial lujo", "BTR", "Oficinas", "Hoteles", "Mixto"],
            default=["Residencial lujo", "BTR"],
        )

    horizonte = st.selectbox(
        "Horizonte temporal",
        ["Proyectos en licitación ahora", "Entrega 12-24 meses", "Entrega +24 meses"],
        index=0,
    )

    detalle = st.text_area(
        "Detalles extra que quieres que tenga en cuenta ChatGPT (opcional)",
        placeholder="Ejemplo: proyectos donde la domótica no sea el foco principal y el acceso IP sí.",
    )

    # ----------------------------------------------------------------------
    # BOTÓN GENERAR PROMPT (no hace nada salvo refrescar la interfaz)
    # ----------------------------------------------------------------------
    if st.button("🔄 Generar prompt"):
        pass

    # ----------------------------------------------------------------------
    # MOSTRAR PROMPT GENERADO
    # ----------------------------------------------------------------------

    st.markdown("#### 🧠 Prompt generado para ChatGPT")

    prompt = _construir_prompt(
        tipo_busqueda=tipo_busqueda,
        zonas=zonas,
        verticales=verticales if tipo_busqueda == "Proyectos" else None,
        estado_objetivo=estado_objetivo if tipo_busqueda == "Proyectos" else None,
        min_viviendas=min_viviendas if tipo_busqueda == "Proyectos" else None,
        min_potencial=min_potencial if tipo_busqueda == "Proyectos" else None,
        tipo_cliente=tipo_cliente if tipo_busqueda == "Clientes" else None,
        foco_negocio=foco_negocio if tipo_busqueda == "Clientes" else None,
        horizonte=horizonte,
        detalle=detalle,
    )

    st.code(prompt, language="markdown")
    st.caption("Copia este prompt y pégalo en ChatGPT. Pídele siempre que te devuelva un Excel con las columnas que ya usamos en tu CRM.")

    st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
#  FUNCIÓN INTERNA PARA MAQUETAR EL PROMPT
# ============================================================

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

    # ----------------------------------------------------------------------
    # SI ES BÚSQUEDA DE PROYECTOS
    # ----------------------------------------------------------------------
    if tipo_busqueda == "Proyectos":

        verticales_txt = ", ".join(verticales) if verticales else "cualquier tipología"
        estado_txt = ", ".join(estado_objetivo) if estado_objetivo else "cualquier fase"
        extra = f"\n\nDetalles adicionales: {detalle}" if detalle else ""

        return f"""
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

    # ----------------------------------------------------------------------
    # SI ES BÚSQUEDA DE CLIENTES
    # ----------------------------------------------------------------------
    else:

        tipos_txt = ", ".join(tipo_cliente) if tipo_cliente else "cualquier tipo"
        foco_txt = ", ".join(foco_negocio) if foco_negocio else "cualquier segmento"
        extra = f"\n\nDetalles adicionales: {detalle}" if detalle else ""

        return f"""
Eres un analista de negocio especializado en identificar **clientes potenciales para soluciones 2N** (control de accesos y videoportero IP).

Quiero que busques **empresas** (no proyectos) en las zonas: {zonas_txt}.
Tipo de empresa objetivo: {tipos_txt}.
Foco principal de negocio: {foco_txt}.
Horizonte temporal: {horizonte}.

Devuélveme la información en formato tabla pensando en un Excel con estas columnas:

- Empresa
- Tipo_Cliente (Promotora, Ingeniería, Arquitectura, Integrator, Fondo)
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
