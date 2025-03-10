import streamlit as st
from components.prompts import agent_system_prompt, omnigaurd_system_prompt

def ensure_config_initialized():
    """Ensure system prompt values are properly initialized."""
    # Always ensure these exist with proper values
    if "omnigaurd_system_prompt" not in st.session_state:
        st.session_state.omnigaurd_system_prompt = omnigaurd_system_prompt
    if "agent_system_prompt" not in st.session_state:
        st.session_state.agent_system_prompt = agent_system_prompt

def init_session_state():
    """Initialize all required session state variables with default values."""
    
    # Initialize configurations
    ensure_config_initialized()
    
    # Model Selections (only set if not already set)
    # if "selected_omniguard_model" not in st.session_state:
    #     st.session_state.selected_omniguard_model = "o3-mini-2025-01-31"
    if "selected_agent_model" not in st.session_state:
        st.session_state.selected_agent_model = "llama-3.1-8b-instant"
    
    # Model Parameters (only set if not already set)
    # if "selected_reasoning" not in st.session_state:
    #     st.session_state.selected_reasoning = "low"
    # if "temperature" not in st.session_state:
    #     st.session_state.temperature = 1.0

