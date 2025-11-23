from style_injector import inject_apple_style
import streamlit as st

def render_buscar():
    inject_apple_style()
    st.title("Buscar (Apple-style placeholder)")
    st.write("This is a placeholder for the full buscar_page.py content.")
