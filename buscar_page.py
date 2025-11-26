import streamlit as st
import pandas as pd
from io import BytesIO

# ==============================
# CARGA DE DATOS (OPTIMIZADA)
# ==============================

@st.cache_data(show_spinner=False)
def load_proyectos():
    from crm_utils import get_proyectos
    return get_proyectos()


@st.cache_data(show_spinner=False)
def load_clientes():
    from crm_utils import get_clientes
    return get_clientes()


# Forzar estilo Salesforce Lightning
try:
    from style_injector import inject_apple_style
except Exception:
    def inject_apple_style():
        pass


# ==============================
# HELPER PROMPT BUILDER
# ==============================

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


def _get_columns_for_tipo(tipo_busqueda: str):
    if tipo_busqueda == "Proyectos":
        return [
            "Proyecto",
            "Ciudad",
            "Provincia",
            "Tipo_Proyecto",
            "Segmento",
            "Nº_viviendas_aprox",
            "Promotora_Fondo",
            "Arquitectura",
            "Ingenieria",
            "Fase_proyecto",
            "Fecha_Inicio_Estimada",
            "Fecha_Entrega_Estimada",
            "Potencial_2N",
            "Fuente_URL",
            "Notas",
        ]
    else:
        return [
            "Empresa",
            "Tipo_Cliente",
            "Persona_contacto_principal",
            "Cargo",
            "Email",
            "Teléfono",
            "Ciudad",
            "Provincia",
            "Web",
            "LinkedIn",
            "Notas",
        ]


def _build_excel_template(tipo_busqueda: str) -> bytes:
    cols = _get_columns_for_tipo(tipo_busqueda)
    df = pd.DataFrame(columns=cols)
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    return buffer.getvalue()


# ==============================
# PLANTILLAS EN SESSION STATE
# ==============================

def _init_plantillas_state():
    if "buscar_plantillas" not in st.session_state:
        st.session_state["buscar_plantillas"] = []


def _guardar_plantilla(nombre: str, config: dict):
    _init_plantillas_state()
    plantillas = st.session_state["buscar_plantillas"]

    # Si ya existe una con ese nombre, la machacamos
    plantillas = [p for p in plantillas if p["nombre"] != nombre]
    plantillas.append({"nombre": nombre, "config": config})
    st.session_state["buscar_plantillas"] = plantillas


def _cargar_plantilla(nombre: str):
    _init_plantillas_state()
    for p in st.session_state["buscar_plantillas"]:
        if p["nombre"] == nombre:
            cfg = p["config"]
            # Volcamos la config a session_state
            st.session_state["tipo_busqueda_opt"] = cfg.get("tipo_busqueda", "Proyectos")
            st.session_state["zonas_select"] = cfg.get("zonas", [])
            st.session_state["verticales_select"] = cfg.get("verticales", [])
            st.session_state["estado_select"] = cfg.get("estado_objetivo", [])
            st.session_state["min_viv"] = cfg.get("min_viviendas", 0)
            st.session_state["min_pot"] = cfg.get("min_potencial", 0)
            st.session_state["tipo_cliente_select"] = cfg.get("tipo_cliente", [])
            st.session_state["foco_cliente_select"] = cfg.get("foco_negocio", [])
            st.session_state["horizonte_select"] = cfg.get("horizonte", "Proyectos en licitación ahora")
            st.session_state["detalle_txt"] = cfg.get("detalle", "")
            st.session_state["buscar_prompt_generado"] = cfg.get("ultimo_prompt", "")
            st.rerun()
    # Si no se encuentra, no hacemos nada


# ==============================
# PRESSETS RÁPIDOS
# ==============================

def _aplicar_preset(nombre: str):
    """
    Rellena los filtros con presets típicos de David.
    """
    if nombre == "BTR Madrid Málaga":
        st.session_state["tipo_busqueda_opt"] = "Proyectos"
        st.session_state["zonas_select"] = ["Madrid", "Málaga"]
        st.session_state["verticales_select"] = ["BTR"]
        st.session_state["estado_select"] = ["Proyecto básico", "Proyecto ejecutivo"]
        st.session_state["min_viv"] = 80
        st.session_state["min_pot"] = 200000
        st.session_state["horizonte_select"] = "Entrega 12-24 meses"
        st.session_state["detalle_txt"] = "Prioriza BTR institucional con operador profesional."

    elif nombre == "Residencial lujo Marbella":
        st.session_state["tipo_busqueda_opt"] = "Proyectos"
        st.session_state["zonas_select"] = ["Málaga"]
        st.session_state["verticales_select"] = ["Residencial lujo"]
        st.session_state["estado_select"] = ["Proyecto ejecutivo", "Obra en curso"]
        st.session_state["min_viv"] = 20
        st.session_state["min_pot"] = 150000
        st.session_state["horizonte_select"] = "Entrega 12-24 meses"
        st.session_state["detalle_txt"] = "Costa del Sol, promociones de lujo con alta expectativa de valor añadido en accesos."

    elif nombre == "Promotoras lujo Costa del Sol":
        st.session_state["tipo_busqueda_opt"] = "Clientes"
        st.session_state["zonas_select"] = ["Málaga", "Otras"]
        st.session_state["tipo_cliente_select"] = ["Promotora", "Fondo"]
        st.session_state["foco_cliente_select"] = ["Residencial lujo", "BTR"]
        st.session_state["horizonte_select"] = "Proyectos en licitación ahora"
        st.session_state["detalle_txt"] = "Empresas muy activas en la Costa del Sol con cartera de proyectos de lujo."

    elif nombre == "Oficinas prime Madrid":
        st.session_state["tipo_busqueda_opt"] = "Proyectos"
        st.session_state["zonas_select"] = ["Madrid"]
        st.session_state["verticales_select"] = ["Oficinas"]
        st.session_state["estado_select"] = ["Proyecto básico", "Proyecto ejecutivo"]
        st.session_state["min_viv"] = 0
        st.session_state["min_pot"] = 250000
        st.session_state["horizonte_select"] = "Entrega 12-24 meses"
        st.session_state["detalle_txt"] = "Edificios de oficinas prime con alto volumen de usuarios y rotación."

    st.rerun()


# ==============================
# RENDER PRINCIPAL
# ==============================

def render_buscar():
    inject_apple_style()
    _init_plantillas_state()

    # CABECERA
    st.markdown(
        """
        <div class="apple-card">
            <div class="badge">Scouting</div>
            <h3 style="margin-top:4px; margin-bottom:4px;">Buscar proyectos y clientes objetivo</h3>
            <p style="color:#5A6872; margin-bottom:0; font-size:0.85rem;">
                Configura filtros para que ChatGPT te genere tablas de proyectos o clientes
                listas para Excel y para importar al CRM de prescripción.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.markdown("#### 🎛 Configuración de la búsqueda", unsafe_allow_html=True)

    # Tipo principal
    tipo_busqueda = st.radio(
        "¿Qué quieres buscar?",
        ["Proyectos", "Clientes"],
        horizontal=True,
        key="tipo_busqueda_opt",
    )

    # Zonas
    zonas = st.multiselect(
        "Zonas / provincias objetivo",
        ["Madrid", "Málaga", "Barcelona", "Valencia", "Alicante", "Mallorca", "Otras"],
        default=st.session_state.get("zonas_select", ["Madrid", "Málaga"]),
        key="zonas_select",
    )

    # Filtros específicos
    verticales = estado_objetivo = min_viviendas = min_potencial = None
    tipo_cliente = foco_negocio = None

    if tipo_busqueda == "Proyectos":
        verticales = st.multiselect(
            "Verticales de proyecto",
            ["Residencial lujo", "Residencial", "Oficinas", "Hotel", "BTR", "Otros"],
            default=st.session_state.get(
                "verticales_select",
                ["Residencial lujo", "Oficinas", "Hotel"],
            ),
            key="verticales_select",
        )

        estado_objetivo = st.multiselect(
            "Momento del proyecto",
            ["Solar", "Proyecto básico", "Proyecto ejecutivo", "Obra en curso"],
            default=st.session_state.get(
                "estado_select",
                ["Proyecto básico", "Proyecto ejecutivo"],
            ),
            key="estado_select",
        )

        col1, col2 = st.columns(2)
        with col1:
            min_viviendas = st.number_input(
                "Mínimo nº de viviendas (si aplica)",
                min_value=0,
                step=10,
                value=st.session_state.get("min_viv", 0),
                key="min_viv",
            )
        with col2:
            min_potencial = st.number_input(
                "Potencial mínimo 2N (€)",
                min_value=0,
                step=50000,
                value=st.session_state.get("min_pot", 0),
                key="min_pot",
            )

    else:
        tipo_cliente = st.multiselect(
            "Tipo de cliente",
            ["Promotora", "Ingeniería", "Arquitectura", "Integrator Partner", "Fondo"],
            default=st.session_state.get(
                "tipo_cliente_select",
                ["Promotora", "Ingeniería", "Arquitectura"],
            ),
            key="tipo_cliente_select",
        )

        foco_negocio = st.multiselect(
            "Foco principal de negocio",
            ["Residencial lujo", "BTR", "Oficinas", "Hoteles", "Mixto"],
            default=st.session_state.get(
                "foco_cliente_select",
                ["Residencial lujo", "BTR"],
            ),
            key="foco_cliente_select",
        )

    horizonte = st.selectbox(
        "Horizonte temporal",
        ["Proyectos en licitación ahora", "Entrega 12-24 meses", "Entrega +24 meses"],
        index=["Proyectos en licitación ahora", "Entrega 12-24 meses", "Entrega +24 meses"].index(
            st.session_state.get("horizonte_select", "Proyectos en licitación ahora")
        ),
        key="horizonte_select",
    )

    detalle = st.text_area(
        "Detalles extra para afinar la búsqueda (opcional)",
        value=st.session_state.get("detalle_txt", ""),
        placeholder="Ejemplo: proyectos donde la domótica no sea el foco principal y el acceso IP sí.",
        key="detalle_txt",
    )

    # =========================
    # PRESETS RÁPIDOS
    # =========================
    st.markdown("---")
    st.markdown(
        """
        <div style="font-size:13px; font-weight:600; color:#032D60; margin-bottom:4px;">
            ⚡ Presets rápidos
        </div>
        """,
        unsafe_allow_html=True,
    )

    c_p1, c_p2, c_p3, c_p4 = st.columns(4)
    with c_p1:
        if st.button("BTR Madrid / Málaga"):
            _aplicar_preset("BTR Madrid Málaga")
    with c_p2:
        if st.button("Residencial lujo Marbella"):
            _aplicar_preset("Residencial lujo Marbella")
    with c_p3:
        if st.button("Promotoras lujo Costa del Sol"):
            _aplicar_preset("Promotoras lujo Costa del Sol")
    with c_p4:
        if st.button("Oficinas prime Madrid"):
            _aplicar_preset("Oficinas prime Madrid")

    # =========================
    # PLANTILLAS GUARDADAS
    # =========================
    st.markdown("---")
    st.markdown("#### 📁 Plantillas de búsqueda", unsafe_allow_html=True)

    col_save, col_load = st.columns([2, 2])

    with col_save:
        nombre_plantilla = st.text_input(
            "Nombre de la plantilla",
            placeholder="Ej: BTR institucional Madrid/Málaga",
            key="nombre_plantilla_input",
        )
        if st.button("💾 Guardar plantilla"):
            if not nombre_plantilla.strip():
                st.warning("Pon un nombre a la plantilla.")
            else:
                cfg = {
                    "tipo_busqueda": tipo_busqueda,
                    "zonas": zonas,
                    "verticales": verticales,
                    "estado_objetivo": estado_objetivo,
                    "min_viviendas": min_viviendas,
                    "min_potencial": min_potencial,
                    "tipo_cliente": tipo_cliente,
                    "foco_negocio": foco_negocio,
                    "horizonte": horizonte,
                    "detalle": detalle,
                    "ultimo_prompt": st.session_state.get("buscar_prompt_generado", ""),
                }
                _guardar_plantilla(nombre_plantilla.strip(), cfg)
                st.success("Plantilla guardada.")

    with col_load:
        plantillas = st.session_state.get("buscar_plantillas", [])
        nombres = ["(ninguna)"] + [p["nombre"] for p in plantillas]
        sel = st.selectbox(
            "Cargar plantilla",
            nombres,
            key="plantilla_sel",
        )
        if st.button("📂 Cargar"):
            if sel != "(ninguna)":
                _cargar_plantilla(sel)

    # =========================
    # GENERAR PROMPT
    # =========================
    st.markdown("---")
    st.markdown("#### 🧠 Prompt generado para ChatGPT", unsafe_allow_html=True)

    if st.button("🔄 Generar prompt"):
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
        st.session_state["buscar_prompt_generado"] = prompt

    prompt_actual = st.session_state.get("buscar_prompt_generado", "")
    if prompt_actual:
        st.code(prompt_actual, language="markdown")
    else:
        st.info("Configura tu búsqueda y pulsa *Generar prompt*.")

    # =========================
    # GENERAR EXCEL BASE
    # =========================
    st.markdown("---")
    st.markdown("#### 📊 Generar Excel base para esta búsqueda", unsafe_allow_html=True)

    excel_bytes = _build_excel_template(tipo_busqueda)
    nombre_excel = (
        f"plantilla_proyectos_{horizonte.replace(' ', '_')}.xlsx"
        if tipo_busqueda == "Proyectos"
        else f"plantilla_clientes_{horizonte.replace(' ', '_')}.xlsx"
    )

    st.download_button(
        "⬇️ Descargar Excel base",
        data=excel_bytes,
        file_name=nombre_excel,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.caption("Rellena este Excel con los datos que te devuelva ChatGPT y ya lo tendrás listo para importar al CRM.")
    st.markdown("</div>", unsafe_allow_html=True)
