import streamlit as st
from typing import Dict, Any, Protocol

#  *** Documentation Content ***
GETTING_STARTED_DOC = """
### 1. Chat with OmniGuard
Simply type your message and press Enter. Each response will include:
- OmniGuard's classification
- Assistant's response

### 2. Review & Feedback
After each response, you can:
- View the full details by clicking the expanders
- Report incorrect classifications using 👎

### 3. Configuration 
In the Configuration tab, you can customize:

### OmniGuard Settings
- **Model**: Fixed to `o3-mini-2025-01-31`
- **Reasoning Effort**: Choose between low, medium, or high
- **Configuration Settings**: Customize organization requirements

### Assistant Settings
- **Model Selection**: Choose from:
  - gpt-4o-2024-05-13
  - gpt-4o-mini-2024-07-18
  - o1-2024-12-17
  - o3-mini-2025-01-31
- **Model Parameters**: 
  - For O1/O3 models: Reasoning effort (low/medium/high)
  - For GPT models: Temperature (0.0 - 2.0)

### 4. Profile (Optional)
Sign in and visit the **Profile** page to add your information (name, socials) and receive credit for your contributions in the public dataset.
"""

def render_documentation() -> None:
    """Render the documentation section in an expander."""
    with st.expander("GETTING STARTED", expanded=False):
        st.markdown(GETTING_STARTED_DOC)

class ResetCallback(Protocol):
    """Type protocol for reset callback function."""
    def __call__(self) -> None: ...

def setup_sidebar(session_state: Dict[str, Any], reset_callback: ResetCallback) -> None:
    """
    Setup the chat sidebar with controls and statistics.
    
    Args:
        session_state: Streamlit session state dictionary
        reset_callback: Callback function to reset the conversation
    """
    from components.auth import auth  # Moved inside to avoid import issues
    with st.sidebar:
        auth()
        st.markdown("---")
        # Render main documentation
        render_documentation()
        st.markdown("---")
        
        # Clear conversation button
        if st.button("Clear Conversation :broom:") and session_state.get("messages"):
            reset_callback()
            st.rerun()
        
        # Help section
        st.markdown("---")
        st.markdown("## Need Help? Leave Feedback?")
        st.markdown("Contact: [brianbellx](https://x.com/brianbellx)")
