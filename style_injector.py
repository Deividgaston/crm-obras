import streamlit as st

def inject_apple_style():
    """Carga el CSS Apple desde apple_style.css."""
    try:
        with open("apple_style.css", "r") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"No se pudo cargar apple_style.css: {e}")
