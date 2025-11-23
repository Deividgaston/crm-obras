import streamlit as st


def _build_proyectos_prompt(zonas, verticales, meses, min_viv, incluir_hoteles_btr):
    zonas_txt = ", ".join(zonas) if zonas else "toda España"
    verticales_txt = ", ".join(verticales) if verticales else "residencial, oficinas y hoteles"
    rango_tiempo_txt = {
        "6": "los últimos 6 meses",
        "12": "los últimos 12 meses",
        "18": "los últimos 18 meses",
        "24": "los últimos 24 meses",
    }.get(meses, "los últimos 12 meses")

    filtro_viv = ""
    if min_viv and min_viv > 0:
        filtro_viv = f" con un mínimo aproximado de {int(min_viv)} viviendas cuando aplique"

    extra_verticales = ""
    if incluir_hoteles_btr:
        extra_verticales = (
            " Presta especial atención a proyectos de hoteles de 4/5 estrellas y BTR "
            "(build-to-rent) donde tenga sentido un sistema de control de accesos avanzado."
        )

    prompt = f"""
Quiero que actúes como mi agente de scouting de proyectos inmobiliarios para 2N Telekomunikace.

Contexto:
- Trabajo como prescriptor técnico de soluciones de videoportero IP y control de accesos de 2N.
- Me interesan proyectos de: {verticales_txt}.
- Zonas objetivo: {zonas_txt}.
- Periodo a analizar: {rango_tiempo_txt}.{extra_verticales}

TAREA:
1. Busca en internet proyectos inmobiliarios relevantes que estén:
   - en fase de proyecto, comercialización o construcción (no solo entregados),
   - con un cierto volumen{filtro_viv},
   - en las zonas indicadas.

2. Para cada proyecto encontrado, rellena una tabla pensando en que luego la exportaré a Excel para mi CRM.
   Las columnas deben llamarse EXACTAMENTE así (respeta el nombre y el orden):

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

3. Devuélveme el resultado en forma de tabla en Markdown, con una fila por proyecto, listo para copiarlo a Excel.

4. No inventes datos: si algo no está claro, deja la celda vacía o pon "Desconocido".
5. Al final de la respuesta, añade un breve resumen con:
   - Nº total de proyectos.
   - Top 5 proyectos prioridad 2N para videoportero y control de accesos, con una frase de por qué.
"""
    return prompt.strip()


def _build_clientes_prompt(zonas, tipos_cliente, verticales, incluir_top10):
    zonas_txt = ", ".join(zonas) if zonas else "toda España"
    verticales_txt = ", ".join(verticales) if verticales else "residencial de lujo, BTR, oficinas y hoteles"
    tipos_txt = ", ".join(tipos_cliente) if tipos_cliente else "arquitecturas, ingenierías y system integrators"

    extra_top = ""
    if incluir_top10:
        extra_top = (
            "\n5. Al final, haz un breve ranking TOP 10 de empresas con mayor potencial para 2N "
            "(videoportero IP + control de accesos) y explica en una frase por qué."
        )

    prompt = f"""
Actúa como mi asistente de desarrollo de canal para 2N Telekomunikace.

Contexto:
- Busco estudios de arquitectura, ingenierías y system integrators que trabajen en proyectos de {verticales_txt}.
- Zonas objetivo: {zonas_txt}.

TAREA:
1. Identifica empresas del tipo: {tipos_txt}, que:
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

3. Devuélveme la tabla en formato Markdown, lista para copiar a Excel.

4. No inventes datos: si un campo no está claro, déjalo vacío o pon "Desconocido".
{extra_top}
"""
    return prompt.strip()


def render_buscar():
    st.title("🔎 Buscar proyectos y clientes")
    st.caption(
        "Esta sección te genera el *prompt perfecto* para pedirle a ChatGPT que busque "
        "proyectos o clientes y te devuelva un Excel compatible con tu CRM."
    )

    tipo_busqueda = st.radio(
        "¿Qué quieres buscar?",
        ["Proyectos (obras)", "Clientes (promotoras, ingenierías, integrators)"],
        horizontal=False,
        key="buscar_tipo_busqueda",
    )

    st.markdown("---")

    # Zonas comunes
    st.subheader("🎯 Filtros básicos")

    col_z1, col_z2 = st.columns([2, 1])
    with col_z1:
        zonas_sel = st.multiselect(
            "Zonas objetivo (ciudades / provincias)",
            options=[
                "Madrid",
                "Comunidad de Madrid",
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
        st.write("Selecciona las zonas donde quieres que busquemos proyectos o clientes.")

    st.markdown("")

    if tipo_busqueda.startswith("Proyectos"):
        # ============================
        # BUSCAR PROYECTOS
        # ============================
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

    else:
        # ============================
        # BUSCAR CLIENTES
        # ============================
        st.subheader("👤 Parámetros de búsqueda de clientes")

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            tipos_cliente_sel = st.multiselect(
                "Tipos de cliente",
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

    st.markdown(
        "### ✂️ Copia este prompt y pégalo en ChatGPT\n"
        "Te devolverá una tabla en Markdown que podrás pegar en Excel "
        "y guardar como `.xlsx` para importarla en la pestaña **Importar / Exportar**."
    )

    st.text_area(
        "Prompt listo para copiar (Cmd+C / Ctrl+C):",
        value=prompt,
        height=420,
        key="buscar_prompt_final",
    )
