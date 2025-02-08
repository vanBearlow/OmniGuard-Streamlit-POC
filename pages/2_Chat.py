'''This page handles the chat interface, including the user input, OmniGuard checks, and message display.'''

import streamlit as st
from dotenv import load_dotenv
from database import init_db
from components.conversation_utils import build_conversation_json, format_conversation_context
from components.chat.chat_history import display_messages, display_debug_expanders
from components.chat.chat_sidebar import setup_sidebar
from components.chat.user_input import process_user_message, get_user_input
from components.chat.session_management import (
    init_session_state,
    reset_session_state,
    generate_conversation_id
)

init_db()
load_dotenv()

st.set_page_config(page_title="OmniGuard Chat", page_icon=":shield:")

def update_conversation_context():
    """Update the conversation context in session state."""
    conversation = build_conversation_json(st.session_state.messages)
    st.session_state.conversation_context = format_conversation_context(conversation)

def main():
    """Main chat application."""
    init_session_state(update_conversation_context)
    
    # Check for API key when data sharing is disabled
    if st.session_state.get("contribute_training_data") is False and not st.session_state.get("api_key"):
        st.error("An API key is required when data sharing is disabled. Please go to the Configuration page to enter your API key.")
        st.stop()
    
    # Setup sidebar with session management
    setup_sidebar(st.session_state, lambda: reset_session_state(update_conversation_context))
    
    # Main chat area
    display_messages(st.session_state.messages)
    
    # Handle user input
    user_input = get_user_input()
    if user_input:
        process_user_message(
            user_input,
            st.session_state,
            generate_conversation_id,
            update_conversation_context
        )
    
    # Display debug information
    display_debug_expanders(
        st.session_state.omniguard_input_message,
        st.session_state.omniguard_output_message,
        st.session_state.assistant_messages,
        st.session_state.raw_assistant_response,
        st.session_state.show_unfiltered_response
    )

if __name__ == "__main__":
    main()
