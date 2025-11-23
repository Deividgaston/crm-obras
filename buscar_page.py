
import streamlit as st

# ============================
# PROMPT PARA PROYECTOS
# ============================
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
        filtro_viv = f"\\n   - con un mínimo de {int(min_viv)} viviendas."

    extra_verticales = ""
    if incluir_hoteles_btr:
        extra_verticales = (
            "\\n   - prioriza hoteles 4/5* y BTR con potencial de control de accesos."
        )

    prompt = f"""
Quiero que actúes como mi agente de scouting de proyectos inmobiliarios para 2N.

PARÁMETROS ELEGIDOS:
- Zonas objetivo: {zonas_txt}
- Tipos de proyecto: {verticales_txt}
- Periodo: {rango_tiempo_txt}{filtro_viv}{extra_verticales}

TAREA:
1. Busca proyectos relevantes (fase proyecto, comercialización o construcción).
2. Devuelve tabla Markdown con columnas EXACTAS:

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

3. No inventes datos: deja vacío si no hay info.
4. Añade resumen final y Top 5 proyectos prioridad 2N.
"""
    return prompt.strip()

# ============================
# PROMPT PARA CLIENTES
# ============================
def _build_clientes_prompt(zonas, tipos_cliente, verticales, incluir_top10):
    zonas_txt = ", ".join(zonas) if zonas else "toda España"
    verticales_txt = ", ".join(verticales) if verticales else "residencial, BTR, oficinas, hoteles"
    tipos_txt = ", ".join(tipos_cliente) if tipos_cliente else "Arquitectura, Ingeniería, Integrators"

    extra_top = ""
    if incluir_top10:
        extra_top = "\\n5. Añade un ranking TOP 10 empresas prioridad 2N."

    prompt = f"""
Actúa como asistente de desarrollo de canal 2N.

PARÁMETROS:
- Zonas objetivo: {zonas_txt}
- Tipos de cliente buscados: {tipos_txt}
- Verticales: {verticales_txt}

TAREA:
1. Busca empresas relevantes asociadas a proyectos recientes.
2. Devuelve tabla Markdown con columnas exactas:

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
{extra_top}
"""
    return prompt.strip()

# ============================
# PÁGINA BUSCAR
# ============================
def render_buscar():
    st.title("🔎 Buscar proyectos y clientes (Generador de Prompts 2N)")

    tipo_busqueda = st.radio(
        "¿Qué quieres buscar?",
        ["Proyectos (obras)", "Clientes (promotoras, ingenierías, integrators)"],
        key="buscar_tipo",
    )

    st.markdown("---")
    st.subheader("🎯 Zonas objetivo")

    zonas_sel = st.multiselect(
        "Zonas",
        ["Comunidad de Madrid", "Madrid", "Barcelona", "Málaga", "Valencia", "Alicante",
         "Islas Baleares", "Costa del Sol", "España (otras zonas)"],
        default=["Comunidad de Madrid", "Málaga", "Barcelona"],
        key="buscar_zonas",
    )

    if tipo_busqueda.startswith("Proyectos"):
        st.subheader("🏗️ Parámetros de proyectos")

        verticales_sel = st.multiselect(
            "Verticales",
            ["Residencial lujo", "Residencial", "BTR", "Oficinas", "Hoteles 4/5*", 
             "Residencias estudiantes", "Residencias senior"],
            default=["Residencial lujo", "BTR", "Oficinas"],
            key="buscar_verticales_proy",
        )

        meses_sel = st.selectbox(
            "Periodo",
            [("6", "Últimos 6 meses"), ("12", "Últimos 12 meses"),
             ("18", "Últimos 18 meses"), ("24", "Últimos 24 meses")],
            index=1,
            format_func=lambda x: x[1],
            key="buscar_periodo",
        )
        meses_valor = meses_sel[0]

        min_viv = st.number_input(
            "Mínimo viviendas",
            min_value=0, value=0, step=10,
            key="buscar_min_viv",
        )

        incluir_hoteles_btr = st.checkbox(
            "Priorizar Hoteles/BTR",
            value=True,
            key="buscar_hoteles_btr",
        )

        prompt = _build_proyectos_prompt(
            zonas_sel, verticales_sel, meses_valor, min_viv, incluir_hoteles_btr
        )

    else:
        st.subheader("👤 Parámetros de clientes")

        tipos_cliente_sel = st.multiselect(
            "Tipos de cliente",
            ["Arquitectura", "Ingeniería", "Integrator Partner", "Promotora/Fondo"],
            default=["Arquitectura", "Ingeniería", "Integrator Partner"],
            key="buscar_tipos_cliente",
        )

        verticales_sel = st.multiselect(
            "Verticales asociadas",
            ["Residencial lujo", "Residencial", "BTR", "Oficinas", "Hoteles"],
            default=["Residencial lujo", "BTR", "Oficinas"],
            key="buscar_verticales_cli",
        )

        incluir_top10 = st.checkbox(
            "Incluir TOP-10 clientes recomendados",
            value=True,
            key="buscar_top10",
        )

        prompt = _build_clientes_prompt(
            zonas_sel, tipos_cliente_sel, verticales_sel, incluir_top10
        )

    st.markdown("---")
    st.subheader("🧾 Prompt generado")

    # BOTÓN PARA ACTUALIZAR
    if st.button("🔄 Actualizar prompt"):
        st.session_state["buscar_force_refresh"] = prompt

    if "buscar_force_refresh" not in st.session_state:
        st.session_state["buscar_force_refresh"] = prompt

    st.code(st.session_state["buscar_force_refresh"], language="text")
