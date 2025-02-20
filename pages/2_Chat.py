'''This page handles the chat interface, including user input, OmniGuard checks, and message display.'''

import streamlit as st
from components.conversation_utils import build_conversation_json, format_conversation_context
from components.chat.chat_history       import display_messages, display_debug_expanders
from components.chat.chat_sidebar        import setup_sidebar
from components.chat.user_input          import process_user_message, get_user_input
from components.chat.session_management  import (
    init_session_state as init_chat_session_state,
    reset_session_state,
    generate_conversation_id
)
from components.init_session_state      import init_session_state

#*** PAGE CONFIGURATION ***
st.set_page_config(
    page_title="OmniGuard Chat",
    page_icon =" :shield:"  # using shield emoji for visual appeal
)

def update_conversation_context():
    """
    Update the conversation context stored in session state.

    This function builds the conversation JSON from the message history and 
    formats that context before storing it in the session state.
    """
    conversation = build_conversation_json(st.session_state.messages)
    st.session_state.conversation_context = format_conversation_context(conversation)

def main():
    """Main function for the OmniGuard Chat application."""
    #*** SESSION STATE INITIALIZATION ***
    init_session_state()                                     # Initialize the base session state.
    init_chat_session_state(update_conversation_context)     # Setup chat-specific session state.
    
    #*** SIDEBAR SETUP (WITH SESSION MANAGEMENT) ***
    setup_sidebar(
        st.session_state,
        lambda: reset_session_state(update_conversation_context)
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
