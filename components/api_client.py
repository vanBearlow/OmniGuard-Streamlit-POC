"""
Module: api_client.py
Description:
    Provides utility functions for OpenAI client interactions, including API key retrieval and model parameter configuration.
"""

import streamlit as st
import logging
from groq import Groq
from openai import OpenAI
from typing import Optional

logger = logging.getLogger(__name__)

def get_api_key() -> str:
    """
    Retrieve the API key from Streamlit secrets.

    Raises:
        ValueError: If the API key is not available.
    Returns:
        str: The retrieved API key.
    """
    api_key = st.secrets.get("API_KEY")
    if not api_key:
        st.error("API key not configured. Notify Brian")
        raise ValueError("API key not available")
    return api_key

def get_openai_client() -> OpenAI: # Not Used
    """Initialize and return an OpenAI client with the configured API key."""
    return OpenAI(api_key=get_api_key())

def get_groq_client() -> Groq:
    """Initialize and return a Groq client with the configured API key."""
    return Groq(api_key=get_api_key())


# def get_model_params(model_name: str, is_omniguard: bool = False) -> dict:
#     """
#     Get appropriate parameters based on model type.

#     Args:
#         model_name (str): The model name (e.g., 'o3-mini-2025-01-31').
#         is_omniguard (bool): Whether this is for an OmniGuard call.

#     Returns:
#         dict: A dictionary of parameters (e.g., 'reasoning_effort' or 'temperature').
#     """
#     params = {}
#     if is_omniguard:
#         params["reasoning_effort"] = st.session_state.get("selected_reasoning", "low")
#     else:
#         if model_name.startswith(("o1", "o3")):
#             params["reasoning_effort"] = st.session_state.get("agent_reasoning", "low")
#         else:
#             params["temperature"] = st.session_state.get("temperature", 1.0)
#     return params