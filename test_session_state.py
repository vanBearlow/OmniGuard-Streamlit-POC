"""
Session State Test Script

This script tests the initialization of session state variables for the OmniGuard chat application.
It can be used to diagnose issues with session state initialization and verify that all required
variables are properly set.

Usage:
    streamlit run test_session_state.py
"""

import streamlit as st
import logging
import sys
from components.chat.session_management import init_session_state, ensure_config_initialized
from components.chat.session_management import init_chat_session_state, reset_chat_session_state
from components.chat.session_management import StateManager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Define a simple update_conversation_context function for testing
def update_conversation_context():
    """Simple implementation for testing"""
    try:
        messages = StateManager.get("messages", [])
        system_prompt = StateManager.get("assistant_system_prompt", "")
        
        # Create a simple conversation context
        conversation = {
            "id": StateManager.get("conversation_id", "test-id"),
            "messages": [{"role": "system", "content": system_prompt}] + messages
        }
        
        # Format as XML-like structure
        import json
        formatted = f"<input>\n{json.dumps(conversation, indent=2)}\n</input>"
        
        # Store in session state
        StateManager.set("conversation_context", formatted)
        logger.debug("Test conversation context updated successfully")
        
    except Exception as e:
        logger.error(f"Error in test update_conversation_context: {e}")
        st.error(f"Error updating conversation context: {e}")

# Page configuration
st.set_page_config(
    page_title="OmniGuard Session State Test",
    page_icon="🧪"
)

st.title("OmniGuard Session State Test")
st.write("This tool tests the initialization of session state variables for the OmniGuard chat application.")

# Initialize session state
with st.spinner("Initializing session state..."):
    try:
        # Initialize base session state
        init_session_state()
        st.success("✅ Base session state initialized")
        
        # Initialize chat-specific session state
        init_chat_session_state(update_conversation_context)
        st.success("✅ Chat session state initialized")
    except Exception as e:
        st.error(f"❌ Error initializing session state: {e}")
        logger.error(f"Error initializing session state: {e}", exc_info=True)

# Display session state variables
st.header("Session State Variables")

# Check critical variables
critical_vars = [
    "messages", 
    "conversation_id", 
    "turn_number", 
    "assistant_system_prompt", 
    "omniguard_configuration",
    "conversation_context"
]

for var in critical_vars:
    col1, col2 = st.columns([1, 3])
    with col1:
        if StateManager.exists(var):
            st.success(f"✅ {var}")
        else:
            st.error(f"❌ {var}")
    with col2:
        if StateManager.exists(var):
            value = StateManager.get(var)
            if var in ["assistant_system_prompt", "omniguard_configuration", "conversation_context"]:
                # For long text, show a truncated version
                if isinstance(value, str):
                    st.text_area(f"{var} (truncated)", value[:100] + "..." if len(value) > 100 else value, height=50)
                else:
                    st.write(f"Type: {type(value)}")
            elif var == "messages":
                st.write(f"Messages: {len(value)} items")
            else:
                st.write(value)
        else:
            st.write("Not set")

# Add a reset button
if st.button("Reset Session State"):
    try:
        reset_chat_session_state(update_conversation_context)
        st.success("Session state reset successfully")
        st.rerun()
    except Exception as e:
        st.error(f"Error resetting session state: {e}")
        logger.error(f"Error resetting session state: {e}", exc_info=True)

# Add a debug expander with all session state
with st.expander("Full Session State Debug"):
    st.json(StateManager.get_dict())
