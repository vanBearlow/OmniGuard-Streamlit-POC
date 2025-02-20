import streamlit as st
from typing import Dict, Any

def setup_sidebar(session_state: Dict[str, Any], reset_callback) -> None:
    """Setup the chat sidebar with controls and statistics."""
    with st.sidebar:

        with st.expander("GETTING STARTED", expanded=False):
            st.markdown("""
            ### 1. Chat with OmniGuard
            Simply type your message and press Enter. Each response will include:
            - OmniGuard's classification
            - Assistant's response
            
            ### 2. Review & Feedback
            After each response, you can:
            - View the full details by clicking the expanders
            - Report incorrect classifications using 👎
            
            ### 3. Configuration
            Visit the Configuration tab to:
            - Adjust reasoning effort (low/medium/high)
            - Select assistant model
            - Customize Prompts/Rules
            """)
            st.markdown("---")
            st.markdown("## Configuration")
            st.markdown("""
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
            """)
        st.markdown("---")

        contributor = session_state.get("contributor", {})
        has_any_info = any(value.strip() for value in contributor.values()) if contributor else False
        expander_title = "Contributor Information (Empty)" if not has_any_info else "Contributor Information"
        with st.expander(expander_title, expanded=False):
            st.markdown("Add your name/socials to get credit in the dataset and appear on the Leaderboard. (Optional)")

            with st.form("contributor_form"):
              name = st.text_input("Name:")
              x = st.text_input("X:") #X/twitter handle
              discord = st.text_input("Discord:") #discord handle
              linkedin = st.text_input("LinkedIn:")
            
              submitted = st.form_submit_button("Save")
              if submitted:
                contributor_info = {
                    "name": name,
                    "x": x,
                    "discord": discord,
                    "linkedin": linkedin
                }
                session_state["contributor"] = contributor_info
                st.success("Saved Successfully")
                st.rerun()

        st.markdown("---")


        if st.button("Clear Conversation :broom:") and session_state.get("messages"):
            reset_callback()
            st.rerun()

        st.markdown("---")
        st.markdown("## Need Help? Leave Feedback?")
        st.markdown("Contact: [brianbellx](https://x.com/brianbellx)")