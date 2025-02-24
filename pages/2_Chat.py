"""
Chat Interface Module

This module implements the main chat interface for OmniGuard, handling:
- User input processing and validation
- Message history display and management  
- OmniGuard security checks and verification
- Chat session state management
- Debug information display
"""

import streamlit as st
from components.conversation_utils       import  build_conversation_json, format_conversation_context
from components.chat.chat_history        import  display_messages, display_debug_expanders
from components.chat.chat_sidebar        import  setup_sidebar
from components.chat.user_input          import  process_user_message, get_user_input
from components.chat.session_management  import  init_chat_session_state,reset_chat_session_state,generate_conversation_id
from components.init_session_state       import  init_session_state

# Constants
PAGE_ICON = " :shield:"  # Shield emoji for visual appeal

#*** PAGE CONFIGURATION ***
st.set_page_config(
    page_title="OmniGuard Chat",
    page_icon=PAGE_ICON
)

def update_conversation_context():
    """
    Update the conversation context stored in session state.

    This function:
    1. Builds a JSON representation of the current conversation from message history
    2. Formats the conversation context for optimal processing
    3. Updates the session state with the new context

    The conversation context is used by OmniGuard to maintain conversation state
    and perform security checks based on the full chat history.
    """
    conversation = build_conversation_json(st.session_state.messages)
    st.session_state.conversation_context = format_conversation_context(conversation)

def main():
    """
    Main function for the OmniGuard Chat application.
    
    Handles the core chat interface functionality:
    - Initializes session state and chat-specific state
    - Sets up the sidebar with session management controls
    - Displays the message history
    - Processes user input and updates conversation context
    - Shows debug information when enabled
    """
    #*** SESSION STATE INITIALIZATION ***
    init_session_state()                                     # Initialize the base site-wide session state
    init_chat_session_state(update_conversation_context)     # Setup chat-specific session state
    
    #*** SIDEBAR SETUP (WITH SESSION MANAGEMENT) ***
    setup_sidebar(
        st.session_state,
        reset_callback=lambda: reset_chat_session_state(update_conversation_context)
    )
    
    #*** MAIN CHAT AREA: DISPLAY MESSAGES ***
    display_messages(st.session_state.messages)
    
    #*** HANDLE USER INPUT ***
    if (user_input := get_user_input()):
        process_user_message(
            user_input,
            st.session_state,
            generate_conversation_id,
            update_conversation_context
        )
    
    #*** DEBUG INFORMATION DISPLAY ***
    display_debug_expanders(
        st.session_state.omniguard_input_message,
        st.session_state.omniguard_output_message,
        st.session_state.assistant_messages
    )

if __name__ == "__main__":
    main()
