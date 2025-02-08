import streamlit as st
from dotenv import load_dotenv
load_dotenv()
from prompts import assistant_system_prompt, omniguard_configuration
from components.init_session_state import init_session_state

st.set_page_config(page_title="Configuration", page_icon=":shield:")

# Ensure session state is initialized
init_session_state()

st.title("Configuration")

# --- OmniGuard Configuration ---
with st.expander("OmniGuard", expanded=False):
    # OmniGuard Model Settings at the top
    st.subheader("Model Settings")
    selected_omniguard_model = st.selectbox(
        "Select OmniGuard model",
        ["o1-2024-12-17", "o3-mini-2025-01-31"],
        index=1,
        key="omniguard_model_select"
    )
    st.session_state.selected_omniguard_model = selected_omniguard_model
    
    selected_reasoning = st.selectbox(
        "Select reasoning effort",
        ["low", "medium", "high"],
        index=1,
        key="omniguard_reasoning_select"
    )
    st.session_state.selected_reasoning = selected_reasoning
    
    st.divider()
    
    # OmniGuard Configuration text area
    st.subheader("Configuration")
    updated_omniguard_config = st.text_area("`Customize and validate configuration settings to align with your organization's requirements.`",
                                value=st.session_state.omniguard_configuration, 
                                height=1000, 
                                label_visibility="visible",
                                key="omniguard_config_text")

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
    updated_assistant_prompt = st.text_area("`Define comprehensive behavioral guidelines and security parameters, including handling of sensitive information such as business proprietary data and personal identifiers.`",
                                value=st.session_state.assistant_system_prompt,
                                height=68,
                                key="assistant_prompt_text")

if "contribute_training_data" not in st.session_state:
    st.session_state.contribute_training_data = True

contribute = st.toggle(
    "Data Sharing",
    value=st.session_state.contribute_training_data,
    key="contribute_training_data_toggle",
    help="Contribute to advancing AI safety by allowing anonymous integration into our research dataset. All data is carefully curated and managed according to strict privacy standards. For additional details, please refer to the Home page."
)

st.session_state.contribute_training_data = contribute
if not contribute:
    # Check if user is logged in and has an API key
    if st.experimental_user.get("is_logged_in", False):
        from database import get_connection
        import json
        
        # Get user's stored API key
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT api_keys FROM users WHERE email = %s",
            (st.experimental_user.get("email"),)
        )
        result = cur.fetchone()
        conn.close()
        
        stored_api_keys = json.loads(result[0]) if result and result[0] else {}
        stored_key = stored_api_keys.get("openrouter")
        
        if stored_key:
            st.session_state.api_key = stored_key
            st.success("Using API key from your profile")
        else:
            st.info("To continue using OmniGuard without sharing your interaction data, please enter your OpenRouter API Key")
            user_api_key = st.text_input("OpenRouter API Key", type="password", key="api_key_input")
            if user_api_key:
                st.session_state.api_key = user_api_key
                # Save the API key to user's profile
                conn = get_connection()
                cur = conn.cursor()
                stored_api_keys["openrouter"] = user_api_key
                cur.execute(
                    "UPDATE users SET api_keys = %s WHERE email = %s",
                    (json.dumps(stored_api_keys), st.experimental_user.get("email"))
                )
                conn.commit()
                conn.close()
                st.success("API key saved to your profile")
            else:
                st.error("An API key is required when data sharing is disabled.")
                st.stop()
    else:
        st.info("To continue using OmniGuard without sharing your interaction data, please enter your OpenRouter API Key")
        user_api_key = st.text_input("OpenRouter API Key", type="password", key="api_key_input")
        if user_api_key:
            st.session_state.api_key = user_api_key
        else:
            st.error("An API key is required when data sharing is disabled.")
            st.stop()

if st.button("Save Changes", key="save_button"):
    st.session_state.omniguard_configuration = updated_omniguard_config
    st.session_state.assistant_system_prompt = updated_assistant_prompt
    
    # Ensure downstream functions receive the latest configuration
    if "conversation_context" in st.session_state:
        import json
        st.session_state.conversation_context = json.dumps({
            "conversation_id": st.session_state.get("conversation_id", ""),
            "messages": st.session_state.get("messages", []),
            "configuration": st.session_state.omniguard_configuration,
            "model": {
                "name": st.session_state.selected_omniguard_model,
                "reasoning_effort": st.session_state.selected_reasoning
            }
        })
    st.success("Changes Saved Successfully!")
    # Refresh the page so that updated session state is propagated to any consumers
    st.experimental_rerun()
