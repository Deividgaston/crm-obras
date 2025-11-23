import streamlit as st
from style_injector import inject_apple_style


def _construir_prompt_proyectos(zonas, tipos, segmentos, horizonte, notas_extra):
    zonas_txt = ", ".join(zonas) if zonas else "España (foco en grandes capitales)"
    tipos_txt = ", ".join(tipos) if tipos else "residencial, oficinas y hoteles"
    seg_txt = ", ".join(segmentos) if segmentos else "alta gama, buena calidad"
    horiz_txt = horizonte or "corto y medio plazo (0-5 años)"

    extra = notas_extra.strip()
    extra_txt = f"\n\nContexto adicional del usuario:\n{extra}" if extra else ""

    prompt = f"""
Actúa como un analista de mercado inmobiliario especializado en proyectos nuevos
para integradores de soluciones de control de accesos y videoportero IP (marca 2N).

Quiero que busques **proyectos inmobiliarios nuevos o en desarrollo** en las siguientes zonas:
- Zonas objetivo: {zonas_txt}

Tipos de activo que me interesan:
- Tipos: {tipos_txt}
- Segmento / nivel: {seg_txt}
- Horizonte temporal: {horiz_txt}

Tu tarea:
1. Localiza **proyectos concretos** (no genéricos) que estén:
   - En promoción, construcción o recién lanzados.
   - Con cierto tamaño (mínimo ~20-30 unidades en residencial / más de 3-4 plantas en oficinas / hoteles relevantes).
2. Identifica para cada proyecto:
   - Nombre del proyecto (o nombre comercial si lo tiene).
   - Ciudad y provincia.
   - Tipo de proyecto (Residencial lujo, Residencial, BTR, Oficinas, Hotel, etc.).
   - Nombre de la promotora o fondo.
   - Estudio de arquitectura (si se conoce).
   - Ingeniería / project manager (si se conoce).
   - Segmento (alta gama, lujo, ultra lujo, estándar, etc.).
   - Fechas estimadas (inicio de obra y entrega, si se encuentran).
   - Enlace web principal o fuente de información.
   - Notas relevantes (por qué parece interesante para soluciones de acceso y videoportero IP).

3. Devuélveme el resultado **en formato tabla pensado para Excel**, con estas columnas EXACTAS:

- Proyecto
- Ciudad
- Provincia
- Tipo_Proyecto
- Promotora_Fondo
- Arquitectura
- Ingenieria
- Segmento
- Fecha_Inicio_Estimada
- Fecha_Entrega_Estimada
- Fuente_URL
- Notas

Formato de salida:
- Usa una tabla separada por columnas clara, que luego se pueda exportar fácilmente a Excel.
- No añadas texto adicional fuera de la tabla.

{extra_txt}
"""
    return prompt.strip()


def _construir_prompt_clientes(zonas, tipos_cliente, notas_extra):
    zonas_txt = ", ".join(zonas) if zonas else "España (foco en grandes capitales)"
    tipos_txt = ", ".join(tipos_cliente) if tipos_cliente else "ingenierías, arquitecturas y promotoras relevantes"

    extra = notas_extra.strip()
    extra_txt = f"\n\nContexto adicional del usuario:\n{extra}" if extra else ""

    prompt = f"""
Actúa como un analista de negocio B2B especializado en el sector inmobiliario y de integración
de soluciones de control de accesos y videoportero IP (marca 2N).

Quiero que busques **contactos de empresas relevantes** con el siguiente perfil:

Zonas objetivo:
- {zonas_txt}

Tipos de empresa:
- {tipos_txt}

Tu tarea:
1. Localiza empresas concretas (no listados genéricos) que:
   - Trabajen en proyectos residenciales, BTR, oficinas u hoteles.
   - Tengan actividad en obra nueva o rehabilitación donde el control de accesos y videoportero IP sea relevante.

2. Para cada empresa, devuelve:
   - Nombre de la empresa.
   - Tipo de cliente (Ingeniería, Arquitectura, Promotora, Integrator Partner, etc.).
   - Ciudad y provincia principal.
   - Página web.
   - Persona de contacto relevante (si se encuentra).
   - Email de contacto profesional.
   - Teléfono.
   - Notas (proyectos relevantes, segmentos, etc.).
   - URL de la fuente de información (LinkedIn, web, directorio, etc.).

3. Devuélveme el resultado **en formato tabla pensado para Excel**, con estas columnas EXACTAS:

- Empresa
- Tipo_Cliente
- Ciudad
- Provincia
- Web
- Persona_Contacto
- Email
- Telefono
- Notas
- Fuente_URL

Formato de salida:
- Usa una tabla clara que luego se pueda exportar fácilmente a Excel.
- No añadas texto adicional fuera de la tabla.

{extra_txt}
"""
    return prompt.strip()


def render_buscar():
    inject_apple_style()

    st.markdown("""
        <div class="apple-card">
            <div class="section-badge">Scouting</div>
            <h1 style="margin-top:6px;">Buscar proyectos y clientes</h1>
            <p style="color:#9FB3D1;margin-bottom:0;">
                Generador de prompts profesionales para que ChatGPT te prepare Excels listos para importar al CRM.
            </p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.subheader("🎛 Configura tu búsqueda")

    tipo_busqueda = st.radio(
        "¿Qué quieres buscar?",
        ["Proyectos nuevos", "Clientes potenciales"],
        horizontal=True,
    )

    # Zonas
    st.markdown("##### 🌍 Zonas objetivo")
    zonas_opciones = ["Madrid", "Málaga", "Valencia", "Barcelona", "Mallorca", "Alicante", "Otras zonas España"]
    zonas_sel = st.multiselect(
        "Selecciona zonas:",
        zonas_opciones,
        default=["Madrid", "Málaga", "Barcelona", "Valencia"],
    )

    notas_extra = ""
    prompt_generado = ""

    if tipo_busqueda == "Proyectos nuevos":
        st.markdown("##### 🏗 Tipo de proyectos")
        tipos_proy = st.multiselect(
            "Tipos de proyecto a priorizar",
            ["Residencial lujo", "Residencial", "BTR", "Oficinas", "Hotel", "Otros"],
            default=["Residencial lujo", "BTR", "Oficinas", "Hotel"],
        )

        segmentos = st.multiselect(
            "Segmento / nivel",
            ["Ultra lujo", "Lujo", "Alta gama", "Estándar"],
            default=["Ultra lujo", "Lujo", "Alta gama"],
        )

        horizonte = st.selectbox(
            "Horizonte temporal",
            ["Corto plazo (0-2 años)", "Medio plazo (2-5 años)", "Largo plazo (5+ años)", "Corto y medio plazo"],
            index=3,
        )

        notas_extra = st.text_area(
            "Notas adicionales para afinar la búsqueda (opcional)",
            placeholder="Ejemplo: Foco en BTR de fondos internacionales, proyectos con amenities, conserjería, etc.",
        )

        if st.button("🔁 Actualizar prompt"):
            prompt_generado = _construir_prompt_proyectos(
                zonas=zonas_sel,
                tipos=tipos_proy,
                segmentos=segmentos,
                horizonte=horizonte,
                notas_extra=notas_extra,
            )
            st.session_state["buscar_prompt"] = prompt_generado

    else:
        st.markdown("##### 👥 Tipo de clientes")
        tipos_cliente = st.multiselect(
            "Tipos de empresa objetivo",
            ["Ingeniería", "Arquitectura", "Promotora", "Integrator Partner", "Fondo de inversión", "Otro"],
            default=["Promotora", "Arquitectura", "Ingeniería"],
        )

        notas_extra = st.text_area(
            "Notas adicionales para afinar la búsqueda (opcional)",
            placeholder="Ejemplo: Enfoque en promotoras de residencial de lujo y BTR en costa y grandes capitales.",
        )

        if st.button("🔁 Actualizar prompt"):
            prompt_generado = _construir_prompt_clientes(
                zonas=zonas_sel,
                tipos_cliente=tipos_cliente,
                notas_extra=notas_extra,
            )
            st.session_state["buscar_prompt"] = prompt_generado

    st.markdown("</div>", unsafe_allow_html=True)

    # Bloque prompt
    st.markdown('<div class="apple-card-light">', unsafe_allow_html=True)
    st.subheader("📋 Prompt generado para ChatGPT")

    prompt_mostrar = st.session_state.get("buscar_prompt", "").strip()
    if not prompt_mostrar:
        st.caption("Configura arriba tu búsqueda y pulsa **Actualizar prompt** para generarlo.")
    else:
        st.code(prompt_mostrar, language="markdown")
        st.caption("Copia este prompt, pégalo en ChatGPT y pídele que te devuelva el resultado en una tabla lista para Excel.")

    st.markdown("</div>", unsafe_allow_html=True)
