import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import date, timedelta, datetime
import json
from io import BytesIO  # para generar Excel en memoria

# ==========================
# CONFIGURACIÓN STREAMLIT
# ==========================
st.set_page_config(page_title="CRM Prescripción 2N", layout="wide", page_icon="🏗️")

# ==========================
# FIREBASE (usa st.secrets["firebase_key"])
# ==========================
if not firebase_admin._apps:
    try:
        secret_str = st.secrets["firebase_key"]  # viene del secrets.toml
        key_dict = json.loads(secret_str)
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    except KeyError:
        st.error("Error: no se encontró 'firebase_key' en los Secrets de Streamlit.")
        st.stop()
    except json.JSONDecodeError:
        st.error("ERROR DE FORMATO (JSON): El contenido de la clave no es JSON válido.")
        st.caption("Revisa el panel de Secrets: firebase_key debe contener el JSON del service account.")
        st.stop()
    except Exception as e:
        st.error(f"Error general de Firebase: {e}")
        st.stop()

db = firestore.client()

# ==========================
# FUNCIONES AUXILIARES
# ==========================

def normalize_fecha(value):
    """
    Convierte Timestamp / datetime / date / str en date o None.
    La usaremos para mostrar y comparar fechas.
    """
    if value is None:
        return None
    # Firestore Timestamp
    if hasattr(value, "to_datetime"):
        value = value.to_datetime()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        # Intentamos ISO (2025-11-30)
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            # Intentamos formatos típicos dd/mm/aa o dd/mm/aaaa
            for fmt in ("%d/%m/%y", "%d/%m/%Y"):
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
            return None
    return None


def default_pasos_seguimiento():
    """Plantilla de pasos para seguir un proyecto."""
    nombres = [
        "Identificar agentes clave (promotora / ingeniería / arquitectura / integrador)",
        "Primer contacto (llamada / email)",
        "Enviar dossier y referencias de 2N",
        "Programar reunión / demo con el cliente",
        "Preparar y enviar memoria técnica / oferta económica",
        "Seguimiento, ajustes y cierre (prescripción / adjudicación)"
    ]
    return [{"nombre": n, "completado": False} for n in nombres]


# ---- CLIENTES ----

def get_clientes():
    docs = db.collection("clientes").stream()
    items = []
    for d in docs:
        data = d.to_dict()
        data["id"] = d.id
        data["fecha_alta"] = normalize_fecha(data.get("fecha_alta"))
        items.append(data)
    if not items:
        return pd.DataFrame()
    df = pd.DataFrame(items)
    return df


def add_cliente(data):
    data["fecha_alta"] = datetime.utcnow()
    db.collection("clientes").add(data)


# ---- PROYECTOS (colección 'obras') ----

def get_proyectos():
    docs = db.collection("obras").stream()
    items = []
    for d in docs:
        data = d.to_dict()
        data["id"] = d.id
        data["fecha_creacion"] = normalize_fecha(data.get("fecha_creacion"))
        data["fecha_seguimiento"] = normalize_fecha(data.get("fecha_seguimiento"))
        items.append(data)
    if not items:
        return pd.DataFrame()
    df = pd.DataFrame(items)
    return df


def add_proyecto(data):
    """
    Inserta un proyecto.
    Siempre fuerza fecha_creacion como datetime.utcnow() (tipo correcto para Firestore).
    Si no hay fecha_seguimiento, la pone a hoy+7, en formato string ISO 'YYYY-MM-DD'.
    """
    data["fecha_creacion"] = datetime.utcnow()
    if "fecha_seguimiento" not in data or data["fecha_seguimiento"] is None:
        data["fecha_seguimiento"] = (date.today() + timedelta(days=7)).isoformat()
    db.collection("obras").add(data)


def actualizar_proyecto(proyecto_id, data):
    db.collection("obras").document(proyecto_id).update(data)


def delete_proyecto(proyecto_id):
    """Borra un proyecto en Firestore."""
    db.collection("obras").document(proyecto_id).delete()


def filtrar_obras_importantes(df_proy: pd.DataFrame) -> pd.DataFrame:
    """
    Define qué es una 'obra importante':
    - Estado en seguimiento (no perdido, no ganado), Y
    - Prioridad Alta, O
    - Potencial estimado >= 50.000 €
    """
    if df_proy.empty:
        return df_proy

    df = df_proy.copy()

    if "prioridad" not in df.columns:
        df["prioridad"] = "Media"
    if "potencial_eur" not in df.columns:
        df["potencial_eur"] = 0.0
    if "estado" not in df.columns:
        df["estado"] = "Detectado"

    estados_seguimiento = ["Seguimiento", "En Prescripción", "Oferta Enviada", "Negociación", "Detectado"]

    mask_estado = df["estado"].isin(estados_seguimiento)
    mask_prioridad = df["prioridad"] == "Alta"
    mask_potencial = df["potencial_eur"].fillna(0) >= 50000

    importantes = df[mask_estado & (mask_prioridad | mask_potencial)].copy()
    return importantes


# ==========================
# IMPORTAR PROYECTOS DESDE EXCEL
# ==========================

def importar_proyectos_desde_excel(file) -> int:
    """
    Importa proyectos desde un Excel generado por ChatGPT y los guarda en Firestore.
    Devuelve el número de proyectos creados.
    """
    try:
        df = pd.read_excel(file)
    except Exception as e:
        st.error(f"Error leyendo el Excel: {e}")
        return 0

    creados = 0
    hoy = date.today()

    # Función interna para convertir fechas a texto ISO o None
    def convertir_fecha(valor):
        if pd.isna(valor):
            return None
        # Si ya viene como date/datetime
        if isinstance(valor, (datetime, date)):
            return valor.isoformat()
        if isinstance(valor, str):
            valor = valor.strip()
            if not valor:
                return None
            # Intentamos dd/mm/aa o dd/mm/aaaa
            for fmt in ("%d/%m/%y", "%d/%m/%Y"):
                try:
                    d = datetime.strptime(valor, fmt).date()
                    return d.isoformat()
                except ValueError:
                    continue
            # Intentamos ISO directa
            try:
                d = datetime.fromisoformat(valor)
                if isinstance(d, datetime):
                    return d.date().isoformat()
            except Exception:
                pass
            # Como último recurso, lo guardamos tal cual en texto
            return valor
        # Cualquier otro tipo, lo convertimos a str
        try:
            return str(valor)
        except Exception:
            return None

    for _, row in df.iterrows():
        try:
            nombre_obra = str(row.get("Proyecto", "")).strip()
            if not nombre_obra:
                continue

            ciudad = str(row.get("Ciudad", "")).strip() or None
            provincia = str(row.get("Provincia", "")).strip() or None
            tipo_proyecto = str(row.get("Tipo_Proyecto", "")).strip() or None
            estado = str(row.get("Estado", "Detectado")).strip() or "Detectado"
            segmento = str(row.get("Segmento", "") or "").lower()

            # Promotor como cliente_principal
            promotor = str(row.get("Promotora_Fondo", "") or "").strip() or None

            # Arquitectura e ingeniería desde Excel
            arquitectura = str(row.get("Arquitectura", "") or "").strip() or None
            ingenieria = str(row.get("Ingenieria", "") or "").strip() or None

            # Prioridad simple basada en segmento
            if "ultra" in segmento or "lujo" in segmento:
                prioridad = "Alta"
            else:
                prioridad = "Media"

            potencial = 0.0  # si quieres luego lo afinamos

            # Fechas opcionales del Excel (dd/mm/aa, dd/mm/aaaa, ISO...)
            fecha_inicio = convertir_fecha(row.get("Fecha_Inicio_Estimada"))
            fecha_entrega = convertir_fecha(row.get("Fecha_Entrega_Estimada"))

            notas = str(row.get("Notas", "") or "").strip()
            url = str(row.get("Fuente_URL", "") or "").strip()
            notas_full = notas
            if url:
                if notas_full:
                    notas_full += f"\nFuente: {url}"
                else:
                    notas_full = f"Fuente: {url}"

            data = {
                "nombre_obra": nombre_obra,
                "cliente_principal": promotor,          # promotor como cliente principal
                "promotora": promotor,                  # también guardamos promotor explícito
                "arquitectura": arquitectura,
                "ingenieria": ingenieria,
                "tipo_proyecto": tipo_proyecto,
                "ciudad": ciudad,
                "provincia": provincia,
                "prioridad": prioridad,
                "potencial_eur": float(potencial),
                "estado": estado,
                # fecha_creacion la pone add_proyecto()
                "fecha_seguimiento": (hoy + timedelta(days=7)).isoformat(),  # SIEMPRE string
                "fecha_inicio": fecha_inicio,        # string o None
                "fecha_entrega": fecha_entrega,      # string o None
                "notas_seguimiento": notas_full,
            }

            add_proyecto(data)
            creados += 1

        except Exception as e:
            st.warning(f"No se pudo importar una fila: {e}")
            continue

    return creados


# ==========================
# MENÚ LATERAL
# ==========================
st.sidebar.title("🏗️ CRM Prescripción 2N")
menu = st.sidebar.radio("Ir a:", ["Panel de Control", "Clientes", "Proyectos"])

# ==========================
# PANEL DE CONTROL
# ==========================
if menu == "Panel de Control":
    st.title("⚡ Panel de Control")

    df_clientes = get_clientes()
    df_proyectos = get_proyectos()

    total_clientes = len(df_clientes) if not df_clientes.empty else 0
    total_proyectos = len(df_proyectos) if not df_proyectos.empty else 0
    proyectos_activos = 0
    if not df_proyectos.empty and "estado" in df_proyectos.columns:
        proyectos_activos = len(df_proyectos[~df_proyectos["estado"].isin(["Ganado", "Perdido"])])

    c1, c2, c3 = st.columns(3)
    c1.metric("Clientes en CRM", total_clientes)
    c2.metric("Proyectos totales", total_proyectos)
    c3.metric("Proyectos activos", proyectos_activos)

    st.divider()
    st.subheader("🚨 Seguimientos pendientes (hoy o pasados)")

    if not df_proyectos.empty and "fecha_seguimiento" in df_proyectos.columns:
        hoy = date.today()
        pendientes = df_proyectos[
            df_proyectos["fecha_seguimiento"].notna()
            & (df_proyectos["fecha_seguimiento"] <= hoy)
            & (~df_proyectos["estado"].isin(["Ganado", "Perdido"]))
        ]

        if pendientes.empty:
            st.success("No tienes seguimientos atrasados. ✅")
        else:
            st.error(f"Tienes {len(pendientes)} proyectos con seguimiento pendiente.")
            for _, row in pendientes.sort_values("fecha_seguimiento").iterrows():
                with st.expander(f"⏰ {row.get('nombre_obra', 'Sin nombre')} – {row['fecha_seguimiento']}"):
                    st.write(f"**Cliente principal (promotor):** {row.get('cliente_principal', '—')}")
                    st.write(f"**Estado:** {row.get('estado', '—')}")
                    st.write(f"**Notas:** {row.get('notas_seguimiento', '')}")
                    if st.button("Posponer 1 semana", key=f"posponer_{row['id']}"):
                        nueva_fecha = (hoy + timedelta(days=7)).isoformat()
                        actualizar_proyecto(row["id"], {"fecha_seguimiento": nueva_fecha})
                        st.success("Pospuesto 1 semana.")
                        st.rerun()
    else:
        st.info("Todavía no hay proyectos en el sistema.")

# ==========================
# CLIENTES
# ==========================
elif menu == "Clientes":
    st.title("👤 CRM de Clientes (ingenierías, promotoras, arquitectos, integrators)")

    # Alta de cliente
    with st.expander("➕ Añadir nuevo cliente"):
        with st.form("form_cliente"):
            nombre = st.text_input("Nombre / Persona de contacto")
            empresa = st.text_input("Empresa")
            tipo_cliente = st.selectbox(
                "Tipo de cliente",
                ["Ingeniería", "Promotora", "Arquitectura", "Integrator Partner", "Otro"]
            )
            email = st.text_input("Email")
            telefono = st.text_input("Teléfono")
            ciudad = st.text_input("Ciudad")
            provincia = st.text_input("Provincia")
            notas = st.text_area("Notas (proyectos, relación, info importante)")

            enviar = st.form_submit_button("Guardar cliente")

        if enviar:
            if not nombre and not empresa:
                st.warning("Pon al menos un nombre o una empresa.")
            else:
                add_cliente({
                    "nombre": nombre,
                    "empresa": empresa,
                    "tipo_cliente": tipo_cliente,
                    "email": email,
                    "telefono": telefono,
                    "ciudad": ciudad,
                    "provincia": provincia,
                    "notas": notas,
                })
                st.success("Cliente guardado correctamente.")
                st.rerun()

    st.subheader("📋 Listado de clientes")

    df_clientes = get_clientes()
    if df_clientes.empty:
        st.info("Aún no hay clientes en el CRM.")
    else:
        cols_mostrar = ["nombre", "empresa", "tipo_cliente", "email", "telefono", "ciudad", "provincia"]
        cols_mostrar = [c for c in cols_mostrar if c in df_clientes.columns]
        st.dataframe(df_clientes[cols_mostrar], hide_index=True, use_container_width=True)

# ==========================
# PROYECTOS
# ==========================
elif menu == "Proyectos":
    st.title("🏗️ CRM de Proyectos")

    df_clientes = get_clientes()
    nombres_clientes = ["(sin asignar)"]
    if not df_clientes.empty and "empresa" in df_clientes.columns:
        nombres_clientes += sorted(df_clientes["empresa"].dropna().unique().tolist())

    # ---- Alta de proyecto manual ----
    with st.expander("➕ Añadir nuevo proyecto manualmente"):
        with st.form("form_proyecto"):
            nombre_obra = st.text_input("Nombre del proyecto / obra")
            cliente_principal = st.selectbox("Cliente principal (normalmente promotor)", nombres_clientes)
            tipo_proyecto = st.selectbox(
                "Tipo de proyecto",
                ["Residencial lujo", "Residencial", "Oficinas", "Hotel", "BTR", "Otro"]
            )
            ciudad = st.text_input("Ciudad")
            provincia = st.text_input("Provincia")
            arquitectura = st.text_input("Arquitectura")
            ingenieria = st.text_input("Ingeniería")
            prioridad = st.selectbox("Prioridad", ["Alta", "Media", "Baja"])
            potencial_eur = st.number_input(
                "Potencial estimado 2N (€)", min_value=0.0, step=10000.0, value=50000.0
            )
            estado_inicial = "Detectado"
            fecha_seg = st.date_input("Primera fecha de seguimiento", value=date.today() + timedelta(days=7))
            notas = st.text_area("Notas iniciales (fuente del proyecto, link, etc.)")

            guardar_proy = st.form_submit_button("Guardar proyecto")

        if guardar_proy:
            if not nombre_obra:
                st.warning("El nombre del proyecto es obligatorio.")
            else:
                add_proyecto({
                    "nombre_obra": nombre_obra,
                    "cliente_principal": None if cliente_principal == "(sin asignar)" else cliente_principal,
                    "tipo_proyecto": tipo_proyecto,
                    "ciudad": ciudad,
                    "provincia": provincia,
                    "arquitectura": arquitectura or None,
                    "ingenieria": ingenieria or None,
                    "prioridad": prioridad,
                    "potencial_eur": float(potencial_eur),
                    "estado": estado_inicial,
                    "fecha_seguimiento": fecha_seg.isoformat(),  # string, no date
                    "notas_seguimiento": notas,
                })
                st.success("Proyecto creado correctamente.")
                st.rerun()

    # ---- Listado y gestión de proyectos ----
    df_proy = get_proyectos()

    if df_proy.empty:
        st.info("Todavía no hay proyectos guardados en Firestore.")
    else:
        # ===== AVISO DE POSIBLES DUPLICADOS =====
        st.markdown("### ⚠️ Revisión de posibles proyectos duplicados")

        df_tmp = df_proy.copy()
        # Clave para detectar duplicados (puedes ajustar columnas)
        key_cols_all = ["nombre_obra", "cliente_principal", "ciudad", "provincia"]
        key_cols = [c for c in key_cols_all if c in df_tmp.columns]

        if key_cols:
            df_tmp["dup_key"] = df_tmp[key_cols].astype(str).agg(" | ".join, axis=1)
            duplicated_mask = df_tmp["dup_key"].duplicated(keep=False)
            df_dups = df_tmp[duplicated_mask].copy()

            if df_dups.empty:
                st.success("No se han detectado proyectos duplicados por nombre + cliente + ciudad + provincia. ✅")
            else:
                grupos = df_dups["dup_key"].unique()
                st.warning(f"Se han detectado {len(grupos)} grupos de proyectos que podrían estar duplicados.")
                st.caption("Revisa y borra los que sobren para mantener limpio el CRM.")

                for g in grupos:
                    grupo_df = df_dups[df_dups["dup_key"] == g]
                    titulo = grupo_df.iloc[0].get("nombre_obra", "Proyecto sin nombre")
                    with st.expander(f"Posibles duplicados: {titulo}"):
                        show_cols = ["id", "nombre_obra", "cliente_principal", "ciudad",
                                     "provincia", "estado", "fecha_creacion", "fecha_seguimiento"]
                        show_cols = [c for c in show_cols if c in grupo_df.columns]
                        st.dataframe(grupo_df[show_cols], hide_index=True, use_container_width=True)

                        for _, row in grupo_df.iterrows():
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(
                                    f"• {row.get('nombre_obra','')} "
                                    f"({row.get('cliente_principal','—')} – {row.get('ciudad','—')})"
                                )
                            with col2:
                                if st.button("🗑️ Borrar este proyecto", key=f"del_dup_{row['id']}"):
                                    delete_proyecto(row["id"])
                                    st.success("Proyecto borrado.")
                                    st.rerun()
        else:
            st.info("No hay suficientes campos para detectar duplicados automáticamente.")

        # ===== LISTADO GENERAL =====
        st.subheader("📂 Todos los proyectos")
        cols = [
            "nombre_obra", "cliente_principal", "promotora",
            "tipo_proyecto", "ciudad", "provincia",
            "arquitectura", "ingenieria",
            "prioridad", "potencial_eur",
            "estado", "fecha_creacion", "fecha_seguimiento"
        ]
        cols = [c for c in cols if c in df_proy.columns]
        st.dataframe(
            df_proy[cols].sort_values("fecha_creacion", ascending=False),
            hide_index=True,
            use_container_width=True
        )

        st.markdown("### 📌 Proyectos en seguimiento")
        en_seg = df_proy[df_proy["estado"].isin(["Seguimiento", "En Prescripción", "Oferta Enviada", "Negociación"])]

        if en_seg.empty:
            st.info("No hay proyectos en seguimiento todavía.")
        else:
            hoy = date.today()
            for _, row in en_seg.sort_values("fecha_seguimiento", ascending=True).iterrows():
                with st.expander(f"📌 {row['nombre_obra']} – próximo seguimiento {row.get('fecha_seguimiento','—')}"):
                    st.write(f"**Promotor (cliente principal):** {row.get('cliente_principal','—')}")
                    st.write(f"**Arquitectura:** {row.get('arquitectura','—')}")
                    st.write(f"**Ingeniería:** {row.get('ingenieria','—')}")
                    st.write(f"**Tipo:** {row.get('tipo_proyecto','—')}")
                    st.write(f"**Estado:** {row.get('estado','—')}")
                    st.write(f"**Prioridad:** {row.get('prioridad','Media')}")
                    st.write(f"**Potencial 2N (€):** {row.get('potencial_eur','—')}")
                    st.write(f"**Notas de seguimiento:** {row.get('notas_seguimiento','')}")

                    pasos = row.get("pasos_seguimiento")
                    if not pasos:
                        if st.button("Crear checklist de pasos", key=f"crear_pasos_{row['id']}"):
                            pasos = default_pasos_seguimiento()
                            actualizar_proyecto(row["id"], {"pasos_seguimiento": pasos})
                            st.success("Checklist creado.")
                            st.rerun()
                    else:
                        st.markdown("#### ✅ Pasos de seguimiento")
                        estados = []
                        for i, paso in enumerate(pasos):
                            checked = st.checkbox(
                                paso.get("nombre", f"Paso {i+1}"),
                                value=paso.get("completado", False),
                                key=f"chk_{row['id']}_{i}"
                            )
                            estados.append(checked)

                        if st.button("💾 Guardar pasos", key=f"save_pasos_{row['id']}"):
                            for i, chk in enumerate(estados):
                                pasos[i]["completado"] = chk
                            actualizar_proyecto(row["id"], {"pasos_seguimiento": pasos})
                            st.success("Pasos actualizados.")
                            st.rerun()

                    nueva_fecha = st.date_input(
                        "Nueva fecha de seguimiento",
                        value=row.get("fecha_seguimiento") or hoy,
                        key=f"fecha_seg_{row['id']}"
                    )
                    if st.button("Actualizar fecha de seguimiento", key=f"upd_fecha_{row['id']}"):
                        actualizar_proyecto(row["id"], {"fecha_seguimiento": nueva_fecha.isoformat()})
                        st.success("Fecha de seguimiento actualizada.")
                        st.rerun()

        # ==========================
        # EXPORTAR EXCEL OBRAS IMPORTANTES
        # ==========================
        st.markdown("### 📤 Exportar Excel de obras importantes")

        df_importantes = filtrar_obras_importantes(df_proy)

        if df_importantes.empty:
            st.info("Ahora mismo no hay obras marcadas como importantes según los criterios definidos.")
            st.caption("Criterios: prioridad Alta o potencial ≥ 50.000 € y estado en seguimiento/detección.")
        else:
            st.write("Obras consideradas *importantes*:")
            cols_imp = [
                "nombre_obra", "cliente_principal", "tipo_proyecto",
                "ciudad", "provincia", "prioridad", "potencial_eur",
                "estado", "fecha_creacion", "fecha_seguimiento"
            ]
            cols_imp = [c for c in cols_imp if c in df_importantes.columns]
            st.dataframe(df_importantes[cols_imp], hide_index=True, use_container_width=True)

            output = BytesIO()
            fecha_str = date.today().isoformat()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df_importantes[cols_imp].to_excel(writer, index=False, sheet_name="Obras importantes")
            output.seek(0)

            st.download_button(
                label=f"⬇️ Descargar Excel obras importantes ({fecha_str})",
                data=output,
                file_name=f"obras_importantes_{fecha_str}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # ==========================
    # IMPORTAR DESDE EXCEL (SIEMPRE VISIBLE)
    # ==========================
    st.markdown("### 📥 Importar proyectos desde Excel (ChatGPT)")
    st.caption(
        "Sube el Excel que te genero desde ChatGPT. "
        "En las columnas de fecha puedes escribir, por ejemplo: 30/11/25 o 30/11/2025 (formato dd/mm/aa). "
        "El campo Promotora_Fondo se usará como cliente principal (promotor)."
    )

    uploaded_file = st.file_uploader(
        "Sube aquí el archivo .xlsx con los proyectos",
        type=["xlsx"],
        key="uploader_import"
    )

    if uploaded_file is not None:
        try:
            df_preview = pd.read_excel(uploaded_file)
            st.write("Vista previa de los datos a importar:")
            st.dataframe(df_preview.head(), use_container_width=True)

            if st.button("🚀 Importar estos proyectos al CRM"):
                creados = importar_proyectos_desde_excel(uploaded_file)
                st.success(f"Importación completada. Proyectos creados: {creados}")
                st.rerun()
        except Exception as e:
            st.error(f"Error leyendo el Excel: {e}")
    else:
        st.info("Sube un Excel para poder importarlo.")
