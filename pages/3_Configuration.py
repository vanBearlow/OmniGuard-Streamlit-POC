import streamlit as st
from components.init_session_state import init_session_state
from prompts import assistant_system_prompt, omniguard_configuration

def reset_to_defaults():
    """Reset configuration values to defaults from prompts.py"""
    st.session_state.omniguard_configuration = omniguard_configuration
    st.session_state.assistant_system_prompt = assistant_system_prompt
    return True

def init_config_state():
    """Initialize configuration state in session."""
    if 'user_configs' not in st.session_state:
        st.session_state.user_configs = {}

def get_user_config(email):
    """Get user configuration from session state."""
    init_config_state()
    return st.session_state.user_configs.get(email, {
        'api_keys': {},
        'preferences': {}
    })

def save_user_config(email, config):
    """Save user configuration to session state."""
    init_config_state()
    st.session_state.user_configs[email] = config

def save_api_key(email, key_type, api_key):
    """Save API key to user configuration."""
    config = get_user_config(email)
    if 'api_keys' not in config:
        config['api_keys'] = {}
    config['api_keys'][key_type] = api_key
    save_user_config(email, config)
    st.success(f"{key_type} API key saved successfully")

def get_stored_api_key(email, key_type):
    """Get stored API key from user configuration."""
    config = get_user_config(email)
    return config.get('api_keys', {}).get(key_type)

def save_preference(email, pref_key, pref_value):
    """Save user preference to configuration."""
    config = get_user_config(email)
    if 'preferences' not in config:
        config['preferences'] = {}
    config['preferences'][pref_key] = pref_value
    save_user_config(email, config)

def get_preference(email, pref_key, default=None):
    """Get user preference from configuration."""
    config = get_user_config(email)
    return config.get('preferences', {}).get(pref_key, default)

st.set_page_config(page_title="Configuration", page_icon="⚙️")


init_session_state()

st.title("Configuration")

with st.form("configuration_form"):
    with st.expander("OmniGuard", expanded=False):
        st.subheader("Model Settings")
        st.write("`OmniGuard model is fixed to o3-mini-2025-01-31.`")
        selected_omniguard_model = "o3-mini-2025-01-31" #st.selectbox(
        #    "Select OmniGuard model",
        #    ["o1-2024-12-17", "o3-mini-2025-01-31"],
        #    index=1,
        #    key="omniguard_model_select"
        #)
        st.session_state.selected_omniguard_model = selected_omniguard_model

        selected_reasoning = st.selectbox(
            "Reasoning effort",
            ["low", "medium", "high"],
            index=1,
            key="omniguard_reasoning_select"
        )
        st.session_state.selected_reasoning = selected_reasoning

        st.divider()

        st.subheader("OmniGuard Configuration")
        st.markdown("`Customize and validate configuration settings to align with your organization's requirements.`")
        updated_omniguard_config = st.text_area(
            "Configuration",
            value=st.session_state.omniguard_configuration,
            height=400,
            key="omniguard_config_text",
            help="Enter your OmniGuard configuration settings."
        )
    with st.expander("Assistant", expanded=False):
        st.subheader("Model Settings")
        selected_assistant_model = st.selectbox(
            "Select Assistant model",
            ["gpt-4o-2024-05-13", "gpt-4o-mini-2024-07-18", "o1-2024-12-17", "o3-mini-2025-01-31"],
            index=1,
            key="assistant_model_select"
        )
        st.session_state.selected_assistant_model = selected_assistant_model

        if selected_assistant_model.startswith(("o1", "o3")):
            assistant_reasoning = st.selectbox(
                "Select reasoning effort",
                ["low", "medium", "high"],
                index=1,
                key="assistant_reasoning_select"
            )
            st.session_state.assistant_reasoning = assistant_reasoning
        else:
            temperature = st.number_input(
                "Temperature",
                min_value=0.0,
                max_value=2.0,
                value=st.session_state.get("temperature", 1.0),
                step=0.1,
                help="Higher values make output more random, lower values more deterministic",
                key="assistant_temperature_slider"
            )
            st.session_state.temperature = temperature

        #st.subheader("Assistant System Prompt")
        #st.markdown("`Define comprehensive behavioral guidelines and security parameters, including handling of sensitive information such as business proprietary data and personal identifiers.`")
        updated_assistant_prompt = st.text_area(
            "System Prompt",
            value=st.session_state.assistant_system_prompt,
            height=150,
            key="assistant_prompt_text"
        )

    # Buttons
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        submitted = st.form_submit_button("Save Changes")
    with col2:
        reset = st.form_submit_button("Reset")

    if reset:
        if reset_to_defaults():
            st.success("Configuration reset to defaults successfully!")
            st.rerun()  # Rerun to show updated values
    
    if submitted:
        # Update session state with new values
        st.session_state.omniguard_configuration = updated_omniguard_config
        st.session_state.assistant_system_prompt = updated_assistant_prompt
        
        # Verify the updates
        if (st.session_state.omniguard_configuration == updated_omniguard_config and 
            st.session_state.assistant_system_prompt == updated_assistant_prompt):
            st.success("Configuration saved successfully!")
        else:
            st.error("Failed to save configuration. Please try again.")
