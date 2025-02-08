import uuid
import streamlit as st
from typing import Callable
from prompts import omniguard_configuration, assistant_system_prompt

def generate_conversation_id(turn_number: int = 1) -> str:
    """Generate a unique conversation ID combining base ID and turn number."""
    if "base_conversation_id" not in st.session_state:
        st.session_state.base_conversation_id = str(uuid.uuid4())
        st.session_state.turn_number = 1
    return f"{st.session_state.base_conversation_id}-{turn_number}"

def reset_session_state(update_conversation_context: Callable) -> None:
    """
    Reset session state variables to their initial values.
    
    Args:
        update_conversation_context: Function to update the conversation context
    """
    st.session_state.messages = []
    st.session_state.base_conversation_id = str(uuid.uuid4())
    st.session_state.turn_number = 1
    st.session_state.conversation_id = generate_conversation_id(st.session_state.turn_number)
    st.session_state.rejection_count = 0
    st.session_state.omniguard_input_message = None
    st.session_state.omniguard_output_message = None
    st.session_state.assistant_messages = None
    st.session_state.raw_assistant_response = None
    update_conversation_context()

def init_session_state(update_conversation_context: Callable) -> None:
    """
    Initialize all session state variables if they don't exist.
    
    Args:
        update_conversation_context: Function to update the conversation context
    """
    # Message Management
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Conversation Management
    if "base_conversation_id" not in st.session_state:
        st.session_state.base_conversation_id = str(uuid.uuid4())
    if "turn_number" not in st.session_state:
        st.session_state.turn_number = 1
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = generate_conversation_id(st.session_state.turn_number)
    
    # Configuration
    if "omniguard_configuration" not in st.session_state:
        st.session_state.omniguard_configuration = omniguard_configuration
    if "assistant_system_prompt" not in st.session_state:
        st.session_state.assistant_system_prompt = assistant_system_prompt
    
    # UI State
    if "show_report_violation_form" not in st.session_state:
        st.session_state.show_report_violation_form = False
    
    # Metrics & Counters
    if "rejection_count" not in st.session_state:
        st.session_state.rejection_count = 0
    
    # Context Management
    if "conversation_context" not in st.session_state:
        update_conversation_context()
    
    # Message Display State
    if "omniguard_input_message" not in st.session_state:
        st.session_state.omniguard_input_message = None
    if "omniguard_output_message" not in st.session_state:
        st.session_state.omniguard_output_message = None
    if "assistant_messages" not in st.session_state:
        st.session_state.assistant_messages = None
    if "raw_assistant_response" not in st.session_state:
        st.session_state.raw_assistant_response = None
    if "show_unfiltered_response" not in st.session_state:
        st.session_state.show_unfiltered_response = False