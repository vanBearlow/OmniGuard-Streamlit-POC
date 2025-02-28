import streamlit as st
from components.prompts import agent_system_prompt, omnigaurd_developer_prompt

def ensure_config_initialized():
    """Ensure developer prompt values are properly initialized."""
    # Always ensure these exist with proper values
    if "omnigaurd_developer_prompt" not in st.session_state:
        st.session_state.omnigaurd_developer_prompt = omnigaurd_developer_prompt
    if "agent_system_prompt" not in st.session_state:
        st.session_state.agent_system_prompt = agent_system_prompt

def init_session_state():
    """Initialize all required session state variables with default values."""
    
    # Initialize configurations
    ensure_config_initialized()
    
    # Model Selections (only set if not already set)
    if "selected_omniguard_model" not in st.session_state:
        st.session_state.selected_omniguard_model = "o3-mini-2025-01-31"
    if "selected_agent_model" not in st.session_state:
        st.session_state.selected_agent_model = "gpt-4o-mini-2024-07-18"
    
    # Model Parameters (only set if not already set)
    if "selected_reasoning" not in st.session_state:
        st.session_state.selected_reasoning = "low"
    if "temperature" not in st.session_state:
        st.session_state.temperature = 1.0
    
    # Site Developer Prompt
    if "site_url" not in st.session_state:
        st.session_state.site_url = "https://omniguard.streamlit.app"
    if "site_name" not in st.session_state:
        st.session_state.site_name = "OmniGuard"
