"""
Chat Interface Module

This module implements the main chat interface for OmniGuard, handling user interactions
with the AI assistant. It manages the chat session, processes user inputs, displays message
history, and integrates security checks.

Features:
- User input processing and validation
- Message history display and management
- OmniGuard security checks and review
- Chat session state management
- Debug information display
"""

import streamlit as st
from components.chat.chat_ui import display_messages, display_debug_expanders, setup_sidebar, get_user_input
from components.chat.chat_logic import process_user_message, build_conversation_json, format_conversation_context
from components.chat.session_management import init_chat_session_state, reset_chat_session_state, generate_conversation_id
from components.init_session_state import init_session_state

# Constants
PAGE_ICON = " :shield:"

# Page system prompt
st.set_page_config(page_title="OmniGuard Chat", page_icon=PAGE_ICON)

def update_conversation_context():
    """
    Updates the conversation context stored in session state.
    
    Builds a JSON representation of the current conversation from message history,
    formats it for optimal processing, and updates the session state.
    """
    conversation = build_conversation_json(st.session_state.messages)
    st.session_state.conversation_context = format_conversation_context(conversation)

def main():
    """
    Main function for the OmniGuard Chat application.
    
    Initializes session state, sets up the UI components, displays message history,
    processes user input, and shows debug information when enabled.
    """
    # Initialize session states
    init_session_state()
    init_chat_session_state(update_conversation_context)
    
    # Setup sidebar with session management
    setup_sidebar(
        st.session_state,
        reset_callback=lambda: reset_chat_session_state(update_conversation_context)
    )
    
    # Display chat message history
    display_messages(st.session_state.messages)
    
    # Handle user input
    if (user_input := get_user_input()):
        process_user_message(
            user_input,
            st.session_state,
            generate_conversation_id,
            update_conversation_context
        )
        # Rerun to refresh UI and sync with session state before next interaction
        #st.rerun()
    
    # Display debug information when enabled
    display_debug_expanders(
        st.session_state.omniguard_input_message,
        st.session_state.omniguard_output_message,
        st.session_state.agent_messages
    )

if __name__ == "__main__":
    main()
