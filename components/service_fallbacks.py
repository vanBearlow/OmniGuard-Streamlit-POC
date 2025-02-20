"""
Module: service_fallbacks.py
Description:
    Provides utility functions for handling API key retrieval.
    Includes graceful error handling with user feedback via Streamlit.
"""

import streamlit as st
import logging
from typing import Optional

logger = logging.getLogger(__name__)


#*** API KEY CHECK FUNCTION REGION ***
def check_api_key() -> Optional[str]:
    """
    Retrieve OpenRouter API key from secrets and provide user feedback.

    Returns:
        Optional[str]: The API key if available; otherwise, None.
    """
    try:
        api_key = st.secrets.get("OPENROUTER_API_KEY")
        
        if not api_key:
            st.error(
                "OpenRouter API key not configured. The application may have limited functionality. "
                "Please try again later or contact support."
            )
            return None
        
        return api_key

    except Exception as err:
        logger.exception("Error checking API key")
        st.error(
            "Unable to verify API key configuration. Some features may be unavailable. "
            "Please try again later."
        )
        return None