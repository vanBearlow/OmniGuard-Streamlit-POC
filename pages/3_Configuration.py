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
if "selected_cms_model" not in st.session_state:
    st.session_state.selected_cms_model = "o3-mini-2025-01-31"
if "selected_assistant_model" not in st.session_state:
    st.session_state.selected_assistant_model = "gpt-4o-mini"
if "selected_reasoning" not in st.session_state:
    st.session_state.selected_reasoning = "medium"
if "temperature" not in st.session_state:
    st.session_state.temperature = 1.0

st.title("Configuration")

# --- CMS Configuration ---
with st.expander("CMS", expanded=False):
    # CMS Model Settings at the top
    st.subheader("Model Settings")
    selected_cms_model = st.selectbox(
        "Select CMS model",
        ["o1-2024-12-17", "o3-mini-2025-01-31"],
        index=1,
        key="cms_model_select"
    )
    st.session_state.selected_cms_model = selected_cms_model
    
    selected_reasoning = st.selectbox(
        "Select reasoning effort",
        ["low", "medium", "high"],
        index=1,
        key="cms_reasoning_select"
    )
    st.session_state.selected_reasoning = selected_reasoning
    
    st.divider()
    
    # CMS Configuration text area
    st.subheader("Configuration")
    updated_omniguard_config = st.text_area("`Feel make and test any changes to the configuration.`",
                                value=st.session_state.CMS_configuration, 
                                height=1000, 
                                label_visibility="visible",
                                key="cms_config_text")

# --- Assistant Configuration ---
with st.expander("Assistant", expanded=False):
    # Assistant Model Settings at the top
    st.subheader("Model Settings")
    selected_assistant_model = st.selectbox(
        "Select Assistant model",
        ["gpt-4o", "gpt-4o-mini", "o1-2024-12-17", "o3-mini-2025-01-31"],
        index=1,
        key="assistant_model_select"

    )
    st.session_state.selected_assistant_model = selected_assistant_model
    
    # Show appropriate parameters based on assistant model type
    if selected_assistant_model.startswith(("o1", "o3")):  # Reasoning models
        assistant_reasoning = st.selectbox(
            "Select reasoning effort",
            ["low", "medium", "high"],
            index=1,
            key="assistant_reasoning_select"
        )
        st.session_state.assistant_reasoning = assistant_reasoning
    else:  # Non-reasoning models
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=st.session_state.get("temperature", 1.0),
            step=0.1,
            help="Higher values make output more random, lower values more deterministic",
            key="assistant_temperature_slider"
        )
        st.session_state.temperature = temperature
    
    st.divider()
    
    # Assistant System Prompt
    st.subheader("System Prompt")
    updated_assistant_prompt = st.text_area("`Configure the assistant's behavior, context and capabilities. (eg:  Business Proprietary Information, Personal Information, etc.)`",
                                value=st.session_state.assistant_system_prompt,
                                height=68,
                                key="assistant_prompt_text")

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
    user_api_key = st.text_input("OpenRouter API Key", type="password", key="api_key_input")
    if user_api_key:
        st.session_state.api_key = user_api_key
    else:
        st.error("An API key is required when data sharing is disabled.")
        st.stop()

if st.button("Save Changes", key="save_button"):
    st.session_state.CMS_configuration = updated_omniguard_config
    st.session_state.assistant_system_prompt = updated_assistant_prompt
    
    # Ensure downstream functions receive the latest configuration
    if "conversation_context" in st.session_state:
        import json
        st.session_state.conversation_context = json.dumps({
            "conversation_id": st.session_state.get("conversation_id", ""),
            "messages": st.session_state.get("messages", []),
            "configuration": st.session_state.CMS_configuration,
            "model": {
                "name": st.session_state.selected_cms_model,
                "reasoning_effort": st.session_state.selected_reasoning
            }
        })
    st.success("Changes Saved Successfully!")
    # Refresh the page so that updated session state is propagated to any consumers
    st.experimental_rerun()
