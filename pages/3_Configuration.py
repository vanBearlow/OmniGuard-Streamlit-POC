import streamlit as st
from dotenv import load_dotenv
load_dotenv()
from prompts import assistant_system_prompt, CMS_configuration

st.set_page_config(page_title="Configuration", page_icon=":shield:")

# --- Initialize Session State ---
if "CMS_configuration" not in st.session_state:
    st.session_state.CMS_configuration = CMS_configuration
if "assistant_system_prompt" not in st.session_state:
    st.session_state.assistant_system_prompt = assistant_system_prompt

# Updated title to match the README terminology
st.title("Configuration")

# --- Text Areas for Editing Prompts ---
with st.expander("CMS Configuration", expanded=False):
    updated_omni_config = st.text_area("Feel free to edit the configuration to your liking.",
                               value=st.session_state.CMS_configuration, height=1000, label_visibility="visible")
    
with st.expander("Assistant System Prompt", expanded=False):
    updated_assistant_prompt = st.text_area("Assistant System Prompt",
                               value=st.session_state.assistant_system_prompt,
                               height=68, label_visibility="hidden")

if "contribute_training_data" not in st.session_state:
    st.session_state.contribute_training_data = True

contribute = st.toggle(
    "Data Sharing",
    value=st.session_state.contribute_training_data,
    key="contribute_training_data_toggle",
    help="Your contributions will be integrated into publicly accessible datasets. For additional details, please refer to the Home page."
)

st.session_state.contribute_training_data = contribute
if not contribute:
    st.info("To continue using CMS without sharing your interaction data, please enter your own OpenRouter API Key")
    user_api_key = st.text_input("OpenRouter API Key", type="password")
    if user_api_key:
        st.session_state.api_key = user_api_key
    else:
        st.error("An API key is required when data sharing is disabled.")
        st.stop()

if st.button("Save Changes"):
    st.session_state.CMS_configuration = updated_omni_config
    st.session_state.assistant_system_prompt = updated_assistant_prompt
    # Ensure downstream functions receive the latest configuration
    if "conversation_context" in st.session_state:
        import json
        st.session_state.conversation_context = json.dumps({
            "conversation_id": st.session_state.get("conversation_id", ""),
            "messages": st.session_state.get("messages", []),
            "configuration": st.session_state.CMS_configuration
        })
    st.success("Changes Saved Successfully!")
    # Refresh the page so that updated session state is propagated to any consumers
    st.experimental_rerun()
