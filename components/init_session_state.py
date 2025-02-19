import streamlit as st
from prompts import assistant_system_prompt, omniguard_configuration

def init_session_state():
    """Initialize all required session state variables with default values."""
    
    # OmniGuard Configuration
    if "omniguard_configuration" not in st.session_state:
        st.session_state.omniguard_configuration = omniguard_configuration
    
    # System Prompts
    if "assistant_system_prompt" not in st.session_state:
        st.session_state.assistant_system_prompt = assistant_system_prompt
    
    # Model Selections
    if "selected_omniguard_model" not in st.session_state:
        st.session_state.selected_omniguard_model = "o3-mini-2025-01-31"
    if "selected_assistant_model" not in st.session_state:
        st.session_state.selected_assistant_model = "gpt-4o-mini"
    
    # Model Parameters
    if "selected_reasoning" not in st.session_state:
        st.session_state.selected_reasoning = "medium"
    if "temperature" not in st.session_state:
        st.session_state.temperature = 1.0
    
    # Data Sharing Settings
    if "contribute_training_data" not in st.session_state:
        st.session_state.contribute_training_data = True
    
    # Conversation State
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = ""
    if "refusal_count" not in st.session_state:
        st.session_state.refusal_count = 0
    
    # Site Configuration
    if "site_url" not in st.session_state:
        st.session_state.site_url = "https://example.com"
    if "site_name" not in st.session_state:
        st.session_state.site_name = "OmniGuard"