import streamlit as st

def display_messages(messages):
    """Display chat messages from history."""
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

def display_debug_expanders(
    omniguard_input_message,
    omniguard_output_message,
    assistant_messages
):
    """Display debug information in expanders."""
    if omniguard_input_message:
        with st.popover("To: OmniGuard"):
            st.json(omniguard_input_message)
        
    if omniguard_output_message:
        with st.popover("From: OmniGuard"):
            st.json(omniguard_output_message)
        
    if assistant_messages:
        with st.popover("To: Assistant"):
            st.write(assistant_messages)
        