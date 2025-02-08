import streamlit as st

def display_messages(messages):
    """Display chat messages from history."""
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

def display_debug_expanders(
    omniguard_input_message,
    omniguard_output_message,
    assistant_messages,
    raw_assistant_response,
    show_unfiltered_response
):
    """Display debug information in expanders."""
    with st.expander("Message to OmniGuard", expanded=True):
        if omniguard_input_message:
            st.json(omniguard_input_message)
        
    with st.expander("Message from OmniGuard", expanded=True):
        if omniguard_output_message:
            st.json(omniguard_output_message)
        
    with st.expander("Messages to Assistant", expanded=True):
        if assistant_messages:
            st.write(assistant_messages)
            
    # Show raw response if enabled
    if show_unfiltered_response:
        with st.expander("Raw Assistant Response (No OmniGuard)", expanded=True):
            if raw_assistant_response:
                st.markdown(raw_assistant_response)
                st.warning("⚠️ This is the raw response without OmniGuard safety checks. Use with caution.")