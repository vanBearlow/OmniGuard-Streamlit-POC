# region: Imports
import streamlit as st
from components.init_session_state import init_session_state
from prompts import assistant_system_prompt, omniguard_configuration
from typing import Any, Dict, Optional
# endregion

# region: Configuration State Helpers
def reset_to_defaults() -> bool:
    """
    Reset configuration values to defaults from prompts.py.
    """
    st.session_state.omniguard_configuration   = omniguard_configuration
    st.session_state.assistant_system_prompt   = assistant_system_prompt
    return True

def init_config_state() -> None:
    """
    Initialize configuration state in session.
    Ensures 'user_configs' key is created.
    """
    if 'user_configs' not in st.session_state:
        st.session_state.user_configs = {}

def get_user_config(email: str) -> Dict[str, Any]:
    """
    Retrieve the user configuration from session state.
    
    Args:
        email (str): The user's email.
    
    Returns:
        dict: User configuration with 'api_keys' and 'preferences'.
    """
    init_config_state()
    return st.session_state.user_configs.get(
        email,
        {
            'api_keys'   : {},
            'preferences': {}
        }
    )

def save_user_config(email: str, config: Dict[str, Any]) -> None:
    """
    Save the given configuration for the user.
    
    Args:
        email (str): The user's email.
        config (dict): The configuration data.
    """
    init_config_state()
    st.session_state.user_configs[email] = config

def save_api_key(email: str, key_type: str, api_key: str) -> None:
    """
    Save an API key to the user's configuration.
    
    Args:
        email (str): The user's email.
        key_type (str): The type/name of the API key.
        api_key (str): The API key.
    """
    config = get_user_config(email)
    if 'api_keys' not in config:
        config['api_keys'] = {}
    config['api_keys'][key_type] = api_key
    save_user_config(email, config)
    st.toast(f"{key_type} API key saved successfully")

def get_stored_api_key(email: str, key_type: str) -> Optional[str]:
    """
    Retrieve a stored API key from the user's configuration.
    
    Args:
        email (str): The user's email.
        key_type (str): The type/name of the API key.
    
    Returns:
        Optional[str]: The API key if present, else None.
    """
    config = get_user_config(email)
    return config.get('api_keys', {}).get(key_type)

def save_preference(email: str, pref_key: str, pref_value: Any) -> None:
    """
    Save a user preference to the configuration.
    
    Args:
        email (str): The user's email.
        pref_key (str): The preference key.
        pref_value (Any): The value of the preference.
    """
    config = get_user_config(email)
    if 'preferences' not in config:
        config['preferences'] = {}
    config['preferences'][pref_key] = pref_value
    save_user_config(email, config)

def get_preference(email: str, pref_key: str, default: Any = None) -> Any:
    """
    Get a user preference from the configuration.
    
    Args:
        email (str): The user's email.
        pref_key (str): The preference key.
        default (Any, optional): Default value if preference is missing.
    
    Returns:
        Any: The preference or the default value.
    """
    config = get_user_config(email)
    return config.get('preferences', {}).get(pref_key, default)
# endregion

# region: Streamlit Page Configuration & UI
# Set up the page configuration
st.set_page_config(
    page_title="Configuration",
    page_icon="⚙️"
)

# Initialize session state
init_session_state()

# Page title
st.title("Configuration")

# --- Configuration Form --- #
with st.form("configuration_form"):
    # OmniGuard Configuration Section
    with st.expander("OmniGuard", expanded=False):
        st.subheader("Model Settings")
        #st.write("`OmniGuard model is fixed to o3-mini-2025-01-31.`")
        selected_omniguard_model = st.selectbox(
            "Select OmniGuard model `temporarily added o1`",
            options=["o1-2024-12-17", "o3-mini-2025-01-31"],
            index=1,
            key="omniguard_model_select"
        )
        st.session_state.selected_omniguard_model = selected_omniguard_model

        selected_reasoning = st.selectbox(
            "Reasoning effort",
            options=["low", "medium", "high"],
            index=0,
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
    
    # Assistant Configuration Section
    with st.expander("Assistant", expanded=False):
        st.subheader("Model Settings")
        selected_assistant_model = st.selectbox(
            "Select Assistant model",
            options=["gpt-4o-2024-08-06", "gpt-4o-mini-2024-07-18", "o1-2024-12-17", "o3-mini-2025-01-31"],
            index=0,
            key="assistant_model_select"
        )
        st.session_state.selected_assistant_model = selected_assistant_model

        if selected_assistant_model.startswith(("o1", "o3")):
            assistant_reasoning = st.selectbox(
                "Select reasoning effort",
                options=["low", "medium", "high"],
                index=0,
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

        updated_assistant_prompt = st.text_area(
            "System Prompt",
            value=st.session_state.assistant_system_prompt,
            height=150,
            key="assistant_prompt_text"
        )

    # --- Form Buttons --- #
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        submitted = st.form_submit_button("Save Changes")
    with col2:
        reset = st.form_submit_button("Reset")

    if reset:
        if reset_to_defaults():
            st.toast("Configuration reset to defaults successfully!")
            st.rerun()  # Rerun to update displayed values
    
    if submitted:
        # Update the session state with the latest values from the form
        st.session_state.omniguard_configuration   = updated_omniguard_config
        st.session_state.assistant_system_prompt   = updated_assistant_prompt
        
        # Confirmation of the updates
        if (
            st.session_state.omniguard_configuration == updated_omniguard_config and
            st.session_state.assistant_system_prompt == updated_assistant_prompt
        ):
            st.toast("Configuration saved successfully!")
        else:
            st.error("Failed to save configuration. Please try again.")
# endregion
