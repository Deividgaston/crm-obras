import streamlit as st


def _modo_compacto() -> bool:
    return bool(st.session_state.get("modo_compacto", False))


def render_buscar():
    compacto = _modo_compacto()

    st.markdown(
        """
        <div class="crm-card">
            <div class="section-badge">Motor de scouting</div>
            <h1 style="margin-top:4px; margin-bottom:4px;">Buscador asistido</h1>
            <p class="text-muted" style="margin-bottom:0;">
                Genera prompts para que yo (ChatGPT) te ayude a localizar
                nuevos proyectos o clientes en función de tu estrategia.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="crm-card-light">
            <h3>1. Tipo de búsqueda</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        tipo_objeto = st.selectbox(
            "Quiero buscar…",
            ["Proyectos / obras", "Clientes (promotoras, ingenierías, etc.)"],
        )
    with col2:
        zona = st.multiselect(
            "Zonas geográficas",
            ["Madrid", "Málaga", "Valencia", "Alicante", "Barcelona", "Mallorca", "Portugal"],
        )

    col3, col4 = st.columns(2)
    with col3:
        vertical = st.multiselect(
            "Vertical",
            ["Residencial lujo", "BTR", "Oficinas", "Hotel", "Educativo", "Sanitario", "Otro"],
        )
    with col4:
        estado = st.multiselect(
            "Estado del proyecto",
            ["Planeado", "En comercialización", "En construcción", "Entregado"],
        )

    st.markdown(
        """
        <div class="crm-card-light">
            <h3>2. Filtro de tamaño e inversión</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col5, col6 = st.columns(2)
    with col5:
        min_viviendas = st.number_input(
            "Mínimo nº de viviendas (si aplica)",
            min_value=0,
            step=10,
            value=50,
        )
    with col6:
        min_inversion = st.number_input(
            "Inversión mínima estimada (M€)",
            min_value=0.0,
            step=1.0,
            value=5.0,
        )

    st.markdown(
        """
        <div class="crm-card-light">
            <h3>3. Criterios de prioridad</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col7, col8 = st.columns(2)
    with col7:
        prioridad = st.selectbox(
            "Qué priorizas",
            [
                "Volumen de obra (nº viviendas / m²)",
                "Ticket económico (inversión total)",
                "Reconocimiento de marca / arquitecto",
                "Velocidad de salida a obra",
            ],
        )
    with col8:
        ventana_tiempo = st.selectbox(
            "Horizonte temporal",
            ["Corto plazo (0-12 meses)", "Medio plazo (1-3 años)", "Largo plazo (3-5 años)"],
        )

    notas_extra = st.text_area(
        "Notas específicas (opcional)",
        placeholder="Ejemplo: priorizar BTR en zona norte de Madrid con promotoras internacionales...",
    )

    # --------- Generación de prompt ----------
    if st.button("🧠 Generar prompt para ChatGPT"):
        tipo_txt = "proyectos inmobiliarios" if "Proyectos" in tipo_objeto else "clientes / contactos profesionales"

        zonas_txt = ", ".join(zona) if zona else "España (con foco en zonas de alto valor inmobiliario)"
        vertical_txt = ", ".join(vertical) if vertical else "cualquier vertical relevante"
        estado_txt = ", ".join(estado) if estado else "cualquier estado donde todavía tenga sentido entrar con prescripción"

        prompt = f"""
Eres mi asistente de scouting para el mercado inmobiliario de alto valor.

Quiero que busques **{tipo_txt}** alineados con el portfolio de soluciones de 2N (videoportero IP y control de accesos) según estos criterios:

- **Zonas**: {zonas_txt}
- **Vertical**: {vertical_txt}
- **Estado del proyecto**: {estado_txt}
- **Mínimo nº de viviendas** (si aplica): {min_viviendas}
- **Inversión mínima estimada**: aproximadamente {min_inversion} M€
- **Prioridad**: {prioridad}
- **Horizonte temporal**: {ventana_tiempo}

Devuélveme la información en una tabla con estas columnas, preparada para importar luego a mi CRM:

- Nombre del proyecto o cliente
- Nº de viviendas / m² (si aplica)
- Ciudad / localidad
- Provincia / región
- Promotora / fondo
- Arquitectura
- Ingeniería
- Tipo de activo (residencial lujo, BTR, oficinas, hotel, educativo…)
- Estado del proyecto
- Fecha estimada de inicio / hito relevante
- Web o fuente de donde lo has obtenido
- Notas relevantes (por qué puede encajar con 2N, complejidad, etc.)

{f"Notas adicionales a tener en cuenta: {notas_extra}" if notas_extra.strip() else ""}

Cuando tengas la tabla, dime también de forma breve:
- cuáles serían las **3 oportunidades más interesantes**,
- y qué estrategia de entrada propones (a quién contactar primero y con qué mensaje).
        """.strip()

        st.markdown("#### Prompt generado")
        st.code(prompt, language="markdown")
        st.success("Copia el prompt y pégalo en una nueva conversación de ChatGPT para lanzar la búsqueda.")

    if compacto:
        st.caption("💡 En móvil verás menos controles de golpe, pero el prompt generado incluye todos los filtros.")
