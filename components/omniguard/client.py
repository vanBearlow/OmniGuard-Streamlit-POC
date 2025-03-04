import logging
import streamlit as st
from openai                       import OpenAI
from components.service_fallbacks import check_api_key

logger = logging.getLogger(__name__)

def get_api_key():
    """
    Retrieve the API key based on configuration.

    This function checks for an API key in Streamlit secrets or other
    fallback mechanisms. Raises ValueError if not available.
    """
    api_key = check_api_key()
    if not api_key:
        raise ValueError("OpenRouter API key not available")
    return api_key

def get_openai_client():
    return OpenAI(api_key=get_api_key())

def get_model_params(model_name, is_omniguard=False):
    """
    Get appropriate parameters based on model type.

    For OmniGuard, references a `selected_reasoning` from session state.
    For the agent, references either `agent_reasoning` or `temperature`,
    depending on the model type.

    Args:
        model_name (str): The model name (e.g., 'o3-mini-2025-01-31').
        is_omniguard (bool): Whether this is for an OmniGuard call.

    Returns:
        dict: A dictionary of parameters (e.g., 'reasoning_effort' or 'temperature').
    """
    params = {}
    
    # For OmniGuard, both o1 and o3 are reasoning models
    if is_omniguard:
        params["reasoning_effort"] = st.session_state.get("selected_reasoning", "low")
    else:
        # For agent, check model type
        if model_name.startswith(("o1", "o3")):
            params["reasoning_effort"] = st.session_state.get("agent_reasoning", "low")
        else:
            params["temperature"] = st.session_state.get("temperature", 1.0)
    
    return params
