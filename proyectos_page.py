from style_injector import inject_apple_style
import streamlit as st

def render_proyectos():
    inject_apple_style()
    st.title("Proyectos (Apple-style placeholder)")
    st.write("This is a placeholder for the full proyectos_page.py content.")
