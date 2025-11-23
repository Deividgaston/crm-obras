import streamlit as st

from firebase_config import init_firebase
from panel_page import render_panel
from clientes_page import render_clientes
from proyectos_page import render_proyectos


st.set_page_config(page_title="CRM Prescripción 2N", layout="wide", page_icon="🏗️")


init_firebase()


st.sidebar.title("🏗️ CRM Prescripción 2N")
menu = st.sidebar.radio("Ir a:", ["Panel de Control", "Clientes", "Proyectos"])


if menu == "Panel de Control":
    render_panel()
elif menu == "Clientes":
    render_clientes()
else:
    render_proyectos()
