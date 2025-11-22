import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import date, timedelta
import json
import os 

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="CRM Prescripción 2n", layout="wide", page_icon="🏗️")

# --- CONEXIÓN A FIREBASE (¡ATENCIÓN! USAMOS LA NUEVA CLAVE 'firebase_key') ---
if not firebase_admin._apps:
    try:
        # Leemos el secreto de Streamlit Cloud. ¡El nombre AHORA es 'firebase_key'!
        secret_str = st.secrets["firebase_key"]
        
        # Convertimos el texto JSON a diccionario
        key_dict = json.loads(secret_str)
        
        # Inicializamos Firebase con el diccionario
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
        
    except KeyError:
        st.error("Error: La llave 'firebase_key' no se encontró en Streamlit Secrets.")
        st.caption("Asegúrate de que la clave en el panel de secretos de Streamlit Cloud se llama 'firebase_key'.")
        st.stop()
    except json.JSONDecodeError as e:
        st.error("ERROR DE FORMATO (JSON): El contenido de la clave no es JSON válido.")
        st.caption("Esto es el famoso error de carácter oculto. Por favor, usa el bloque de clave final que te proporciono en la Sección 3 y pégalo sin espacios extras.")
        st.stop()
    except Exception as e:
        st.error(f"Error general de Firebase: {e}")
        st.stop()

db = firestore.client()

# --- FUNCIONES AUXILIARES ---
def get_promotoras():
    docs = db.collection('promotoras').stream()
    items = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        items.append(data)
    return pd.DataFrame(items)

def get_obras():
    docs = db.collection('obras').stream()
    items = []
    for doc in docs:
        data = doc.to_dict()
        data['id'] = doc.id
        # Convertir timestamp de firebase a fecha legible si es necesario
        items.append(data)
    return pd.DataFrame(items)

# --- INTERFAZ PRINCIPAL ---

st.sidebar.title("🏗️ Prescripción 2n (Cloud)")
menu = st.sidebar.radio("Ir a:", ["Panel de Control", "Mis Obras", "Promotoras"])

# 1. PANEL DE CONTROL
if menu == "Panel de Control":
    st.title("⚡ Panel de Control y Alertas")
    
    df_obras = get_obras()
    
    if not df_obras.empty:
        total = len(df_obras[~df_obras['estado'].isin(['Ganada', 'Perdida'])])
        revision = len(df_obras[df_obras['estado'] == 'Revisión Planificada'])
    else:
        total, revision = 0, 0
        
    col1, col2 = st.columns(2)
    col1.metric("Obras Activas", total)
    col2.metric("En Revisión", revision)
    
    st.divider()
    st.subheader("🚨 Alertas de Seguimiento")
    
    if not df_obras.empty:
        # Filtramos las que toca llamar hoy o antes
        today_str = str(date.today())
        alerta_df = df_obras[
            (df_obras['fecha_seguimiento'] <= today_str) & 
            (~df_obras['estado'].isin(['Ganada', 'Perdida']))
        ]
        
        if not alerta_df.empty:
            st.error(f"Tienes {len(alerta_df)} seguimientos pendientes.")
            for index, row in alerta_df.iterrows():
                with st.expander(f"⏰ {row['nombre_obra']} - {row['fecha_seguimiento']}"):
                    st.write(f"**Estado:** {row['estado']}")
                    st.write(f"**Nota:** {row.get('notas_seguimiento','')}")
                    
                    if st.button(f"✅ Posponer 1 semana", key=row['id']):
                        next_week = str(date.today() + timedelta(days=7))
                        db.collection('obras').document(row['id']).update({
                            'fecha_seguimiento': next_week
                        })
                        st.rerun()
        else:
            st.success("Todo al día.")

# 2. MIS OBRAS
elif menu == "Mis Obras":
    st.title("Gestión de Obras")
    
    with st.expander("➕ Añadir Nueva Obra"):
        df_proms = get_promotoras()
        if df_proms.empty:
            st.warning("Crea primero una promotora.")
        else:
            # Crear diccionario para el selectbox
            lista_proms = df_proms['nombre'].tolist()
            
            with st.form("nueva_obra"):
                nom = st.text_input("Nombre Obra")
                prom = st.selectbox("Promotora", lista_proms)
                tipo = st.selectbox("Tipo", ["Residencial Lujo", "Oficinas", "BTR", "Otros"])
                arq = st.text_input("Arquitectura")
                ing = st.text_input("Ingeniería")
                fecha = st.date_input("Fecha Seguimiento")
                notas = st.text_area("Notas")
                
                if st.form_submit_button("Guardar"):
                    db.collection('obras').add({
                        'nombre_obra': nom,
                        'promotora': prom,
                        'tipo_activo': tipo,
                        'arquitectura': arq,
                        'ingenieria': ing,
                        'estado': 'Detección',
                        'fecha_seguimiento': str(fecha),
                        'notas_seguimiento': notas
                    })
                    st.success("Guardada en la nube!")
                    st.rerun()
    
    st.subheader("Listado")
    df = get_obras()
    if not df.empty:
        st.dataframe(df[['nombre_obra', 'promotora', 'estado', 'fecha_seguimiento']])

# 3. PROMOTORAS
elif menu == "Promotoras":
    st.title("Promotoras")
    with st.form("nueva_prom"):
        nom = st.text_input("Nombre")
        tipo = st.selectbox("Tipo", ["Lujo", "Estándar", "Fondo"])
        pais = st.selectbox("País", ["España", "Portugal"])
        contacto = st.text_input("Contacto")
        email = st.text_input("Email")
        
        if st.form_submit_button("Crear Promotora"):
            db.collection('promotoras').add({
                'nombre': nom,
                'tipo': tipo,
                'pais': pais,
                'contacto': contacto,
                'email': email
            })
            st.success("Creada!")
            st.rerun()
            
    df = get_promotoras()
    if not df.empty:
        st.dataframe(df)
