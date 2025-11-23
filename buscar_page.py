import streamlit as st


# ============================
# PROMPT PARA PROYECTOS
# ============================
def _build_proyectos_prompt(zonas, verticales, meses, min_viv, incluir_hoteles_btr):
    # Texto zonas
    if zonas:
        zonas_txt = ", ".join(zonas)
    else:
        zonas_txt = "toda España (si hay algo muy relevante fuera, puedes mencionarlo aparte)"

    # Texto verticales
    if verticales:
        verticales_txt = ", ".join(verticales)
    else:
        verticales_txt = "residencial, oficinas y hoteles"

    # Periodo
    rango_tiempo_txt = {
        "6": "los últimos 6 meses",
        "12": "los últimos 12 meses",
        "18": "los últimos 18 meses",
        "24": "los últimos 24 meses",
    }.get(meses, "los últimos 12 meses")

    # Filtro viviendas
    filtro_viv = ""
    if min_viv and min_viv > 0:
        filtro_viv = (
            f"\n   - con un mínimo aproximado de {int(min_viv)} viviendas cuando aplique."
        )

    # Priorizar hoteles / BTR
    extra_verticales = ""
    if incluir_hoteles_btr:
        extra_verticales = (
            "\n   - presta especial atención a proyectos de hoteles de 4/5 estrellas "
            "y BTR (build-to-rent) donde tenga sentido un sistema de control de accesos avanzado."
        )

    prompt = f"""
Quiero que actúes como mi agente de scouting de proyectos inmobiliarios para 2N Telekomunikace.

Contexto profesional:
- Trabajo como prescriptor técnico de soluciones de videoportero IP y control de accesos de 2N.
- Me interesan especialmente proyectos donde tenga sentido un control de accesos IP avanzado
  (portales, zonas comunes, garajes, smartlocks en vivienda, etc.).

PARÁMETROS QUE HE ELEGIDO:
- Zonas objetivo: {zonas_txt}
- Tipos de proyecto / verticales: {verticales_txt}
- Periodo a analizar: {rango_tiempo_txt}{filtro_viv}{extra_verticales}

TAREA:
1. Busca en internet proyectos inmobiliarios relevantes que estén:
   - en fase de proyecto, comercialización o construcción (no solo entregados),
   - con cierto volumen (nº viviendas significativo o edificio singular),
   - dentro de las zonas y verticales indicadas.

2. Para cada proyecto encontrado, rellena una tabla pensando en que luego la exportaré a Excel para mi CRM.
   Las columnas deben llamarse EXACTAMENTE así (respeta nombre y orden):

   - Proyecto
   - Ciudad
   - Provincia
   - Comunidad_Autonoma
   - País
   - Tipo_Proyecto            (Residencial lujo, Residencial, BTR, Oficinas, Hotel, Mixto, etc.)
   - Segmento                 (Lujo, Alto, Medio, etc.)
   - Nº_Viviendas             (si aplica, si no dejar vacío)
   - Promotora_Fondo
   - Arquitectura
   - Ingenieria
   - Estado                   (Detectado, En comercialización, En construcción, Entregado, etc.)
   - Fecha_Inicio_Estimada   (si no se conoce, dejar vacío)
   - Fecha_Entrega_Estimada  (si no se conoce, dejar vacío)
   - Fuente_URL
   - Notas

3. Devuélveme el resultado en forma de tabla en Markdown, con una fila por proyecto, lista para copiarla a Excel.

4. No inventes datos: si algo no está claro, deja la celda vacía o pon "Desconocido".

5. Al final de la respuesta, añade un breve resumen con:
   - Nº total de proyectos detectados.
   - Top 5 proyectos prioridad 2N para videoportero y control de accesos, con una frase explicando por qué.
"""
    return prompt.strip()


# ============================
# PROMPT PARA CLIENTES
# ============================
def _build_clientes_prompt(zonas, tipos_cliente, verticales, incluir_top10):
    # Zonas
    if zonas:
        zonas_txt = ", ".join(zonas)
    else:
        zonas_txt = "toda España (si hay algo muy relevante fuera, puedes mencionarlo aparte)"

    # Verticales
    if verticales:
        verticales_txt = ", ".join(verticales)
    else:
        verticales_txt = "residencial de lujo, BTR, oficinas y hoteles"

    # Tipos de cliente
    if tipos_cliente:
        tipos_txt = ", ".join(tipos_cliente)
    else:
        tipos_txt = "Arquitectura, Ingeniería y System Integrators"

    extra_top = ""
    if incluir_top10:
        extra_top = (
            "\n5. Al final, haz un breve ranking TOP 10 de empresas con mayor potencial para 2N "
            "(videoportero IP + control de accesos) y explica en una frase por qué cada una."
        )

    prompt = f"""
Actúa como mi asistente de desarrollo de canal para 2N Telekomunikace.

Contexto profesional:
- Busco empresas con las que colaborar a nivel de prescripción y proyectos:
  arquitecturas, ingenierías, integradores y, si aplica, promotoras/fondos.
- Me interesan empresas activas en proyectos de {verticales_txt}.

PARÁMETROS QUE HE ELEGIDO:
- Zonas objetivo: {zonas_txt}
- Tipos de cliente a priorizar: {tipos_txt}

TAREA:
1. Identifica empresas del tipo indicado que:
   - estén activas en proyectos de edificios residenciales, BTR, oficinas o hoteles,
   - aparezcan asociadas a proyectos recientes o de cierto tamaño,
   - tengan afinidad con tecnología de edificios, domótica, seguridad o similares.

2. Prepara una tabla pensada para importar a mi CRM, con las siguientes columnas EXACTAS:

   - Empresa
   - Tipo_Cliente        (Arquitectura, Ingeniería, Integrator Partner, Promotora/Fondo, Otro)
   - Ciudad
   - Provincia
   - País
   - Web
   - Email_Contacto      (si hay varios, indica el principal)
   - Teléfono
   - Persona_Contacto
   - Cargo
   - Segmento_Objetivo   (Residencial lujo, BTR, Oficinas, Hoteles, etc.)
   - Fuente_URL
   - Notas

3. Devuélveme la tabla en formato Markdown, lista para copiarla a Excel.

4. No inventes datos: si un campo no está claro, déjalo vacío o pon "Desconocido".
{extra_top}
"""
    return prompt.strip()


# ============================
# PÁGINA BUSCAR
# ============================
def render_buscar():
    st.title("🔎 Buscar proyectos y clientes")
    st.caption(
        "Elige los filtros y te genero automáticamente un prompt perfecto para usar en ChatGPT. "
        "La respuesta será una tabla que podrás pasar a Excel y luego importar al CRM."
    )

    tipo_busqueda = st.radio(
        "¿Qué quieres buscar?",
        ["Proyectos (obras)", "Clientes (promotoras, ingenierías, integrators)"],
        horizontal=False,
        key="buscar_tipo_busqueda",
    )

    st.markdown("---")

    # ===== ZONAS (COMÚN) =====
    st.subheader("🎯 Zonas objetivo")

    col_z1, col_z2 = st.columns([2, 1])
    with col_z1:
        zonas_sel = st.multiselect(
            "Zonas (ciudades / provincias / áreas)",
            options=[
                "Comunidad de Madrid",
                "Madrid",
                "Barcelona",
                "Provincia de Barcelona",
                "Málaga",
                "Costa del Sol",
                "Valencia",
                "Alicante",
                "Islas Baleares",
                "España (otras zonas)",
            ],
            default=["Comunidad de Madrid", "Málaga", "Barcelona", "Valencia", "Alicante"],
            key="buscar_zonas",
        )
    with col_z2:
        st.write("")
        st.write(
            "Selecciona las zonas donde quieres que el agente busque información "
            "de proyectos o clientes."
        )

    st.markdown("")

    # ==========================================================
    # BUSCADOR DE PROYECTOS
    # ==========================================================
    if tipo_busqueda.startswith("Proyectos"):
        st.subheader("🏗️ Parámetros de búsqueda de proyectos")

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            verticales_sel = st.multiselect(
                "Verticales / tipos de proyecto",
                options=[
                    "Residencial lujo",
                    "Residencial",
                    "BTR",
                    "Oficinas",
                    "Hoteles 4/5*",
                    "Residencias estudiantes",
                    "Residencias senior",
                    "Otros",
                ],
                default=["Residencial lujo", "BTR", "Oficinas", "Hoteles 4/5*"],
                key="buscar_verticales_proy",
            )
        with col_p2:
            meses_sel = st.selectbox(
                "Periodo a analizar",
                options=[
                    ("6", "Últimos 6 meses"),
                    ("12", "Últimos 12 meses"),
                    ("18", "Últimos 18 meses"),
                    ("24", "Últimos 24 meses"),
                ],
                index=1,
                format_func=lambda x: x[1],
                key="buscar_periodo_proy",
            )
            meses_valor = meses_sel[0]

        col_p3, col_p4 = st.columns(2)
        with col_p3:
            min_viv = st.number_input(
                "Mínimo aproximado de viviendas (0 = sin filtro)",
                min_value=0,
                value=0,
                step=10,
                key="buscar_min_viv",
            )
        with col_p4:
            incluir_hoteles_btr = st.checkbox(
                "Priorizar hoteles y BTR con alto potencial de control de accesos",
                value=True,
                key="buscar_hoteles_btr",
            )

        st.markdown("---")
        st.subheader("🧾 Prompt generado para proyectos")

        prompt = _build_proyectos_prompt(
            zonas_sel, verticales_sel, meses_valor, min_viv, incluir_hoteles_btr
        )

    # ==========================================================
    # BUSCADOR DE CLIENTES
    # ==========================================================
    else:
        st.subheader("👤 Parámetros de búsqueda de clientes")

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            tipos_cliente_sel = st.multiselect(
                "Tipos de cliente a buscar",
                options=[
                    "Arquitectura",
                    "Ingeniería",
                    "Integrator Partner",
                    "Promotora/Fondo",
                    "Otro",
                ],
                default=["Arquitectura", "Ingeniería", "Integrator Partner"],
                key="buscar_tipos_cliente",
            )
        with col_c2:
            verticales_sel = st.multiselect(
                "Enfoque de los clientes",
                options=[
                    "Residencial lujo",
                    "Residencial",
                    "BTR",
                    "Oficinas",
                    "Hoteles",
                    "Residencias estudiantes",
                    "Residencias senior",
                    "Otros",
                ],
                default=["Residencial lujo", "BTR", "Oficinas", "Hoteles"],
                key="buscar_verticales_cli",
            )

        incluir_top10 = st.checkbox(
            "Pedir un TOP 10 de empresas con más potencial para 2N",
            value=True,
            key="buscar_top10_clientes",
        )

        st.markdown("---")
        st.subheader("🧾 Prompt generado para clientes")

        prompt = _build_clientes_prompt(
            zonas_sel, tipos_cliente_sel, verticales_sel, incluir_top10
        )

    # =======================
    # PROMPT FINAL PARA COPIAR
    # =======================
    st.markdown(
        "### ✂️ Copia este prompt y pégalo en ChatGPT\n"
        "Te devolverá una tabla en Markdown que podrás pegar en Excel, guardar como `.xlsx` "
        "e importar en la pestaña **Importar / Exportar** de tu CRM."
    )

    st.text_area(
        "Prompt listo para copiar (Cmd+C / Ctrl+C):",
        value=prompt,
        height=430,
        key="buscar_prompt_final",
    )
