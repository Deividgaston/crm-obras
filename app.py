import streamlit as st

# Importa las “páginas”
from panel_page import render_panel_control
from clientes_page import render_clientes
from proyectos_page import render_proyectos

st.set_page_config(page_title="CRM Prescripción 2N", layout="wide", page_icon="🏗️")

st.sidebar.title("🏗️ CRM Prescripción 2N")
menu = st.sidebar.radio("Ir a:", ["Panel de Control", "Clientes", "Proyectos"])

if menu == "Panel de Control":
    render_panel_control()
elif menu == "Clientes":
    render_clientes()
elif menu == "Proyectos":
    render_proyectos()
