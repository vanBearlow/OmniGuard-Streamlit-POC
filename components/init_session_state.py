import streamlit as st
from components.prompts import assistant_system_prompt, omniguard_configuration

def ensure_config_initialized():
    """Ensure configuration values are properly initialized."""
    # Always ensure these exist with proper values
    if "omniguard_configuration" not in st.session_state:
        st.session_state.omniguard_configuration = omniguard_configuration
    if "assistant_system_prompt" not in st.session_state:
        st.session_state.assistant_system_prompt = assistant_system_prompt

def init_session_state():
    """Initialize all required session state variables with default values."""
    
    # Initialize configurations
    ensure_config_initialized()
    
    # Model Selections (only set if not already set)
    if "selected_omniguard_model" not in st.session_state:
        st.session_state.selected_omniguard_model = "o3-mini-2025-01-31"
    if "selected_assistant_model" not in st.session_state:
        st.session_state.selected_assistant_model = "gpt-4o-mini-2024-07-18"
    
    # Model Parameters (only set if not already set)
    if "selected_reasoning" not in st.session_state:
        st.session_state.selected_reasoning = "low"
    if "temperature" not in st.session_state:
        st.session_state.temperature = 1.0
    
    # Site Configuration
    if "site_url" not in st.session_state:
        st.session_state.site_url = "https://omniguard.streamlit.app"
    if "site_name" not in st.session_state:
        st.session_state.site_name = "OmniGuard"
