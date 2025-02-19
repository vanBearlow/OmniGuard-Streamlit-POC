import streamlit as st
from typing import Dict, Any

def setup_sidebar(session_state: Dict[str, Any], reset_callback) -> None:
    """Setup the chat sidebar with controls and statistics."""
    
    if st.sidebar.button("Clear Conversation :broom:") and session_state.get("messages"):
        reset_callback()
        st.rerun()
    st.sidebar.markdown("---")
                