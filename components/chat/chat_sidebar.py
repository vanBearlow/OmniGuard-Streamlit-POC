import streamlit as st
from typing      import Dict, Any, Protocol
from dataclasses import dataclass
from functools   import partial

@dataclass
class ContributorInfo:
    """Structure for contributor information with validation."""
    name: str = ""
    x: str = ""      # X/Twitter handle
    discord: str = "" # Discord username
    linkedin: str = ""
    
    @property
    def is_empty(self) -> bool:
        """Check if all fields are empty."""
        return not any(value.strip() for value in vars(self).values())

class ResetCallback(Protocol):
    """Type protocol for reset callback function."""
    def __call__(self) -> None: ...

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
- **System Prompt**: Customize assistant behavior
"""
# 

def render_documentation() -> None:
    """Render the documentation section in an expander."""
    with st.expander("GETTING STARTED", expanded=False):
        st.markdown(GETTING_STARTED_DOC)

def handle_contributor_form(session_state: Dict[str, Any]) -> None:
    """Handle the contributor form submission and updates."""
    with st.form("contributor_form"):
        info = ContributorInfo(
            name=st.text_input("Name:"),
            x=st.text_input("X:"),
            discord=st.text_input("Discord:"),
            linkedin=st.text_input("LinkedIn:")
        )
        
        if st.form_submit_button("Save"):
            session_state["contributor"] = vars(info)
            st.toast("Saved Successfully")
            st.rerun()

def render_contributor_section(session_state: Dict[str, Any]) -> None:
    """Render the contributor information section."""
    contributor = ContributorInfo(**session_state.get("contributor", {}))
    title = "Contributor Information (Empty)" if contributor.is_empty else "Contributor Information"
    
    with st.expander(title, expanded=False):
        st.markdown(
            "Add your name/socials to get credit in the dataset and appear on the Leaderboard. (Optional)"
        )
        handle_contributor_form(session_state)

def setup_sidebar(session_state: Dict[str, Any], reset_callback: ResetCallback) -> None:
    """
    Setup the chat sidebar with controls and statistics.
    
    Args:
        session_state: Streamlit session state dictionary
        reset_callback: Callback function to reset the conversation
    """
    with st.sidebar:
        # Render main documentation
        render_documentation()
        st.markdown("---")
        
        # Render contributor section
        render_contributor_section(session_state)
        st.markdown("---")
        
        # Clear conversation button
        if st.button("Clear Conversation :broom:") and session_state.get("messages"):
            reset_callback()
            st.rerun()
        
        # Help section
        st.markdown("---")
        st.markdown("## Need Help? Leave Feedback?")
        st.markdown("Contact: [brianbellx](https://x.com/brianbellx)")