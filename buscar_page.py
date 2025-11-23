import streamlit as st
from datetime import date


# ==========================
# UTILIDAD: CONSTRUIR PROMPT
# ==========================

def _build_prompt_from_filters(filtros: dict) -> str:
    tipo = filtros.get("tipo_busqueda", "Proyectos")

    zonas = filtros.get("zonas") or []
    zonas_txt = ", ".join(zonas) if zonas else "Comunidad de Madrid, Málaga, Valencia y Barcelona"

    verticales = filtros.get("verticales") or []
    verticales_txt = ", ".join(verticales) if verticales else "residencial de lujo, oficinas y hoteles"

    horizonte = filtros.get("horizonte", "próximos 24-36 meses")
    fuentes = filtros.get("fuentes") or []
    fuentes_txt = ", ".join(fuentes) if fuentes else "noticias, notas de prensa, portales inmobiliarios y LinkedIn"

    presupuesto_min = filtros.get("presupuesto_min")
    if presupuesto_min and presupuesto_min > 0:
        presupuesto_txt = f"con un presupuesto aproximado de construcción superior a {int(presupuesto_min):,} €".replace(
            ",", "."
        )
    else:
        presupuesto_txt = "sin filtrar por presupuesto mínimo concreto"

    extra = filtros.get("extra", "").strip()

    hoy = date.today().isoformat()

    # --- PROMPT PARA PROYECTOS ---
    if tipo == "Proyectos":
        prompt = f"""Quiero que actúes como un analista senior de mercado inmobiliario y construcción en España especializado en detectar nuevas obras relevantes para un fabricante de soluciones de videoportero IP y control de accesos (2N).

### OBJETIVO
Detectar **nuevos proyectos inmobiliarios y obras relevantes** en:
- **Zonas**: {zonas_txt}
- **Verticales**: {verticales_txt}
- **Horizonte temporal**: {horizonte}
- **Fuentes principales**: {fuentes_txt}
- **Presupuesto**: {presupuesto_txt}

Fecha de referencia del análisis: **{hoy}**.

### SALIDA OBLIGATORIA
Debes devolver **exclusivamente una tabla en formato tipo Excel** (sin texto alrededor) con **una fila por proyecto** y con estas columnas EXACTAS:

- Proyecto
- Ciudad
- Provincia
- Comunidad_Autonoma
- Pais
- Tipo_Proyecto        (por ejemplo: Residencial lujo, Residencial, Oficinas, Hotel, BTR…)
- Segmento             (por ejemplo: Lujo, Ultralujoso, Medio/alto…)
- Estado               (por ejemplo: En proyecto, En construcción, Comercialización, Entregado…)
- Promotora_Fondo      (promotor principal o fondo que impulsa la operación)
- Arquitectura         (estudio de arquitectura principal si lo hay)
- Ingenieria           (ingeniería de referencia si aparece)
- Fuente_URL           (enlace público donde se menciona el proyecto)
- Fecha_Inicio_Estimada
- Fecha_Entrega_Estimada
- Notas                (breve resumen del proyecto y cualquier detalle útil para la prescripción: nº de viviendas, tipología, etc.)

### INSTRUCCIONES
- Prioriza proyectos medianos y grandes donde tenga sentido un sistema de videoportero IP y control de accesos profesional.
- No inventes datos: si una columna no aparece en la fuente, déjala en blanco.
- Devuelve sólo la **tabla**, en formato para poder copiar y pegar a Excel o descargar como .xlsx.
"""
    # --- PROMPT PARA CLIENTES / CONTACTOS ---
    else:
        prompt = f"""Quiero que actúes como un analista de desarrollo de negocio especializado en detectar **potenciales clientes B2B** para soluciones de videoportero IP y control de accesos (2N) en España.

### OBJETIVO
Encontrar **empresas y contactos clave** relacionados con proyectos inmobiliarios en:
- **Zonas**: {zonas_txt}
- **Verticales**: {verticales_txt}
- **Horizonte temporal de proyectos**: {horizonte}
- **Fuentes principales**: {fuentes_txt}

Prioriza:
- Promotoras y fondos
- Estudios de arquitectura
- Ingenierías
- Integradores de sistemas / instaladores especializados

Fecha de referencia del análisis: **{hoy}**.

### SALIDA OBLIGATORIA
Devuelve **exclusivamente una tabla en formato tipo Excel** (sin texto alrededor) con **una fila por empresa/contacto** y con estas columnas EXACTAS:

- Empresa
- Tipo_Cliente          (Promotora, Fondo, Arquitectura, Ingeniería, Integrator Partner, Otro)
- Persona_Contacto
- Cargo
- Email
- Telefono
- Ciudad
- Provincia
- Pais
- Web
- LinkedIn
- Notas                 (relación con proyectos, especialización, tamaño aproximado…)
- Fuente_URL            (dónde has localizado la información)

### INSTRUCCIONES
- Prioriza empresas activas en proyectos de medio y gran tamaño en las zonas indicadas.
- No inventes datos: si un campo no está disponible, déjalo en blanco.
- Devuelve sólo la **tabla**, en formato para poder copiar y pegar a Excel o descargar como .xlsx.
"""

    # Extra manual del usuario
    if extra:
        prompt += f"\n\n### CONDICIONES ADICIONALES DEL USUARIO\n{extra}\n"

    return prompt


# ==========================
# PÁGINA BUSCAR
# ==========================

def render_buscar():
    # Cabecera compacta, coherente con el resto
    st.markdown(
        """
        <div class="apple-card">
            <div class="section-badge">Scouting & research</div>
            <h3 style="margin-top: 6px; font-size:1.25rem;">Buscador asistido para proyectos y clientes</h3>
            <p style="color:#9FB3D1; margin-bottom: 0; font-size:0.85rem;">
                Define filtros, genera un prompt profesional y úsalo en ChatGPT para encontrar nuevas obras
                o clientes. Después, importa el Excel al CRM desde la pestaña <strong>Proyectos → Importar / Exportar</strong>.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_izq, col_der = st.columns([1.15, 0.85])

    # ==========================
    # COLUMNA IZQUIERDA: FILTROS
    # ==========================
    with col_izq:
        st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
        st.markdown(
            "#### 🎯 Definir búsqueda",
            unsafe_allow_html=True,
        )

        with st.form("form_buscar"):
            tipo_busqueda = st.radio(
                "¿Qué quieres buscar?",
                ["Proyectos", "Clientes"],
                horizontal=True,
            )

            c1, c2 = st.columns(2)
            with c1:
                zonas = st.multiselect(
                    "Zonas / provincias objetivo",
                    [
                        "Madrid",
                        "Málaga",
                        "Barcelona",
                        "Valencia",
                        "Alicante",
                        "Islas Baleares",
                        "Lisboa",
                        "Oporto",
                    ],
                    default=["Madrid", "Málaga", "Barcelona", "Valencia"],
                )
            with c2:
                verticales = st.multiselect(
                    "Verticales / tipo de activo",
                    [
                        "Residencial lujo",
                        "Residencial medio / alto",
                        "Oficinas",
                        "Hoteles",
                        "BTR",
                        "CoLiving",
                        "Residencias estudiantes",
                    ],
                    default=["Residencial lujo", "Oficinas", "Hoteles"],
                )

            horizonte = st.selectbox(
                "Horizonte de los proyectos",
                [
                    "Obras ya en marcha",
                    "Obras en proyecto / planificación",
                    "Entrega prevista 0-24 meses",
                    "Entrega prevista 24-48 meses",
                    "Sin filtro / mixto",
                ],
                index=2,
            )

            fuentes = st.multiselect(
                "Fuentes a priorizar en la búsqueda",
                [
                    "Noticias",
                    "Notas de prensa",
                    "Portales inmobiliarios",
                    "Boletines urbanísticos",
                    "Concursos públicos",
                    "LinkedIn",
                    "Webs corporativas",
                ],
                default=["Noticias", "Portales inmobiliarios", "LinkedIn"],
            )

            presupuesto_min = st.number_input(
                "Ticket mínimo aprox. del proyecto (obra) en €",
                min_value=0,
                step=500000,
                value=0,
                help="Opcional. Sólo se usa en el prompt si es mayor que 0.",
            )

            extra = st.text_area(
                "Condiciones adicionales (opcional)",
                placeholder=(
                    "Ejemplos:\n"
                    "- Proyectos con más de 80 viviendas\n"
                    "- Foco en promotoras de alto standing\n"
                    "- Excluir vivienda protegida, etc."
                ),
            )

            actualizar = st.form_submit_button("🔁 Actualizar prompt")

        st.markdown("</div>", unsafe_allow_html=True)

    # ==========================
    # COLUMNA DERECHA: PROMPT RESULTANTE
    # ==========================
    with col_der:
        st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
        st.markdown(
            "#### 🧠 Prompt generado",
            unsafe_allow_html=True,
        )

        if "buscar_prompt" not in st.session_state:
            # Prompt inicial por defecto
            st.session_state["buscar_prompt"] = _build_prompt_from_filters(
                {
                    "tipo_busqueda": "Proyectos",
                    "zonas": ["Madrid", "Málaga", "Barcelona", "Valencia"],
                    "verticales": ["Residencial lujo", "Oficinas", "Hoteles"],
                    "horizonte": "próximos 24-36 meses",
                    "fuentes": ["Noticias", "Portales inmobiliarios", "LinkedIn"],
                    "presupuesto_min": 0,
                    "extra": "",
                }
            )

        if actualizar:
            filtros = {
                "tipo_busqueda": tipo_busqueda,
                "zonas": zonas,
                "verticales": verticales,
                "horizonte": horizonte,
                "fuentes": fuentes,
                "presupuesto_min": presupuesto_min,
                "extra": extra,
            }
            st.session_state["buscar_prompt"] = _build_prompt_from_filters(filtros)

        prompt_text = st.session_state.get("buscar_prompt", "")

        st.caption("Copia este prompt y pégalo en ChatGPT para obtener los proyectos o clientes en formato tabla/Excel:")
        st.code(prompt_text, language="markdown")

        st.markdown("---")
        st.markdown(
            """
            **Cómo usarlo en tu flujo de trabajo:**
            1. Copia el prompt completo.
            2. Pégalo en ChatGPT (modelo con navegación).
            3. Pídele que te entregue el resultado como **archivo Excel (.xlsx)** o tabla copiable.
            4. Guarda ese Excel localmente.
            5. Ve a **Proyectos → Importar / Exportar** y sube el fichero para incorporarlo al CRM.
            """,
            unsafe_allow_html=True,
        )

        st.markdown("</div>", unsafe_allow_html=True)
