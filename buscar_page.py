import streamlit as st
from style_injector import inject_apple_style

# ==========================================
# HELPERS PARA GENERAR PROMPTS
# ==========================================

def _build_proyectos_prompt(zonas, verticales, meses, min_viv, incluir_hoteles_btr):
    if zonas:
        zonas_txt = ", ".join(zonas)
    else:
        zonas_txt = "toda España"

    if verticales:
        verticales_txt = ", ".join(verticales)
    else:
        verticales_txt = "residencial, oficinas y hoteles"

    rango_tiempo_txt = {
        "6": "los últimos 6 meses",
        "12": "los últimos 12 meses",
        "18": "los últimos 18 meses",
        "24": "los últimos 24 meses",
    }.get(meses, "los últimos 12 meses")

    filtro_viv = ""
    if min_viv and min_viv > 0:
        filtro_viv = f"\n- Mínimo {int(min_viv)} viviendas"

    extra_verticales = ""
    if incluir_hoteles_btr:
        extra_verticales = (
            "\n- Priorizar hoteles 4/5* y proyectos BTR por su alto potencial de control de accesos."
        )

    prompt = f"""
Quiero que actúes como mi agente profesional de scouting inmobiliario.

🎯 **Objetivo:** Encontrar proyectos relevantes donde aplicar videoportero IP + control de accesos.

📍 **Zonas objetivo:** {zonas_txt}
🏗️ **Verticales:** {verticales_txt}
🕒 **Periodo:** {rango_tiempo_txt}
{filtro_viv}
{extra_verticales}

---

## 📌 Qué debes buscar
- Proyectos en fase de proyecto, construcción o comercialización.
- Obras de tamaño relevante o de promotoras/arquitecturas importantes.
- Que tengan sentido técnico para control de accesos avanzado.

---

## 📊 Entrega la información en una **tabla Markdown** con EXACTAMENTE estas columnas:

- Proyecto  
- Ciudad  
- Provincia  
- Comunidad_Autonoma  
- País  
- Tipo_Proyecto  
- Segmento  
- Nº_Viviendas  
- Promotora_Fondo  
- Arquitectura  
- Ingenieria  
- Estado  
- Fecha_Inicio_Estimada  
- Fecha_Entrega_Estimada  
- Fuente_URL  
- Notas  

⚠️ **No inventes datos**: deja vacío si no hay información verificable.
"""
    return prompt.strip()



def _build_clientes_prompt(zonas, tipos_cliente, verticales, incluir_top10):
    if zonas:
        zonas_txt = ", ".join(zonas)
    else:
        zonas_txt = "toda España"

    if tipos_cliente:
        tipos_txt = ", ".join(tipos_cliente)
    else:
        tipos_txt = "Arquitectura, Ingeniería e Integrators"

    if verticales:
        verticales_txt = ", ".join(verticales)
    else:
        verticales_txt = "residencial, oficinas y hoteles"

    extra_top = ""
    if incluir_top10:
        extra_top = "\nIncluye al final un TOP 10 de empresas con más potencial."

    prompt = f"""
Quiero que actúes como mi analista profesional de desarrollo de canal.

🎯 **Objetivo:** Encontrar arquitecturas, ingenierías, integrators y promotoras potentes.

📍 **Zonas objetivo:** {zonas_txt}  
🏢 **Tipos de cliente prioritarios:** {tipos_txt}  
🏗️ **Verticales relevantes:** {verticales_txt}  
{extra_top}

---

## 📊 Devuelve una **tabla Markdown** con EXACTAMENTE estas columnas:

- Empresa  
- Tipo_Cliente  
- Ciudad  
- Provincia  
- País  
- Web  
- Email_Contacto  
- Teléfono  
- Persona_Contacto  
- Cargo  
- Segmento_Objetivo  
- Fuente_URL  
- Notas  

⚠️ No inventes datos. Si algo no está disponible, déjalo en blanco.
"""
    return prompt.strip()
# ==========================================
# PÁGINA PRINCIPAL DE BÚSQUEDA APPLE PREMIUM
# ==========================================

def render_buscar():
    inject_apple_style()

    st.markdown("""
        <div class="apple-card">
            <div class="section-badge">Scouting & Canal</div>
            <h1 style="margin-top: 6px;">Buscar proyectos y clientes</h1>
            <p style="color:#6B7280; margin-bottom: 0;">
                Genera un prompt profesional para detectar nuevas obras o clientes estratégicos.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Tipo de búsqueda
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    tipo = st.radio(
        "¿Qué quieres buscar?",
        ["Proyectos (obras)", "Clientes (promotoras, ingenierías, integrators)"],
        key="buscar_tipo",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # Zonas
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.subheader("🎯 Zonas objetivo")
    zonas = st.multiselect(
        "Selecciona las zonas",
        [
            "Madrid", "Comunidad de Madrid",
            "Málaga", "Costa del Sol",
            "Barcelona", "Provincia de Barcelona",
            "Valencia", "Alicante",
            "Islas Baleares",
            "España"
        ],
        default=["Madrid", "Málaga", "Barcelona"]
    )
    st.markdown("</div>", unsafe_allow_html=True)
    # Parámetros según tipo
    if tipo.startswith("Proyectos"):
        st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
        st.subheader("🏗️ Filtros de obra")

        verticales = st.multiselect(
            "Verticales",
            ["Residencial lujo", "Residencial", "BTR", "Oficinas", "Hoteles 4/5*", "Otros"],
            default=["Residencial lujo", "BTR", "Hoteles 4/5*"]
        )

        meses = st.selectbox(
            "Periodo a analizar",
            [("6", "Últimos 6 meses"),
             ("12", "Últimos 12 meses"),
             ("18", "Últimos 18 meses"),
             ("24", "Últimos 24 meses")],
            index=1,
            format_func=lambda x: x[1]
        )[0]

        min_viv = st.number_input("Mínimo de viviendas", min_value=0, step=10, value=0)
        incluir_hoteles_btr = st.checkbox("Priorizar hoteles y BTR", value=True)

        prompt = _build_proyectos_prompt(
            zonas, verticales, meses, min_viv, incluir_hoteles_btr
        )
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
        st.subheader("👤 Filtros de cliente")

        tipos_cliente = st.multiselect(
            "Tipo de cliente",
            ["Arquitectura", "Ingeniería", "Integrator Partner", "Promotora/Fondo"],
            default=["Arquitectura", "Ingeniería", "Integrator Partner"]
        )

        verticales = st.multiselect(
            "Verticales del cliente",
            ["Residencial lujo", "Residencial", "BTR", "Oficinas", "Hoteles"],
            default=["Residencial lujo", "Oficinas"]
        )

        incluir_top10 = st.checkbox("Incluir ranking TOP 10", value=True)

        prompt = _build_clientes_prompt(
            zonas, tipos_cliente, verticales, incluir_top10
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # Prompt final
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.subheader("🧾 Prompt final (listo para copiar)")

    if st.button("🔄 Actualizar prompt"):
        st.session_state["prompt_busqueda"] = prompt

    if "prompt_busqueda" not in st.session_state:
        st.session_state["prompt_busqueda"] = prompt

    st.code(st.session_state["prompt_busqueda"], language="text")
    st.markdown("</div>", unsafe_allow_html=True)
