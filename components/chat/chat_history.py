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
    conversation_id = st.session_state.get("conversation_id")
    turn_number = st.session_state.get("turn_number")
    
    if omniguard_input_message:
        with st.expander(f"OmniGuard (```{conversation_id}```)"):
            with st.popover("To: OmniGuard"):
                st.json(omniguard_input_message, expanded=True)
            if omniguard_output_message:
                with st.popover("From: OmniGuard"):
                    st.json(omniguard_output_message, expanded=True)
                    #TODO: add on_change function that opens a dialog to allow the user to submit a report for human verification. should only be shown if its thumbs down.
                    st.feedback(options="thumbs", on_change=None, args=None, kwargs=None)
            
    if assistant_messages:
        with st.expander(f"Assistant"):
            with st.popover("To: Assistant"):
                st.write(assistant_messages)
        