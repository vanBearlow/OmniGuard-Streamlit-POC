import streamlit as st

def show_alpha_banner():
    """Display an alpha version banner across the application."""
    st.info(
        "This is an alpha version. Expect bugs and rapid changes... even possibly the name."
    ) 