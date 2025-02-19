import streamlit as st
from typing import Dict, Any

def setup_sidebar(session_state: Dict[str, Any], reset_callback) -> None:
    """Setup the chat sidebar with controls and statistics."""
    with st.sidebar:

        with st.expander("README", expanded=False):
            st.markdown("## Review OmniGuard's response")
            st.markdown(""" Inside of the chat, you can review the response and submit a report for human verification. Using the thumbs down feedback.
                """)
            st.markdown("---")
            st.markdown("## Configuration")
            st.markdown("You can configure the model, reasoning effort, and temperature, rules, and other parameters in the Configuration tab.")
        st.markdown("---")

        if st.button("Clear Conversation :broom:") and session_state.get("messages"):
            reset_callback()
            st.rerun()
        st.markdown("---")