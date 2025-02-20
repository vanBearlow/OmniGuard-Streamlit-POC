"""
Module: service_fallbacks.py
Description:
    Provides utility functions for handling API key retrieval and safely executing API operations.
    Includes graceful error handling with user feedback via Streamlit.
"""

import streamlit as st
import logging
from typing import Optional, Any, Callable

logger = logging.getLogger(__name__)


#*** API KEY CHECK FUNCTION REGION ***
def check_api_key() -> Optional[str]:
    """
    Retrieve OpenRouter API key from secrets and provide user feedback.

    Returns:
        Optional[str]: The API key if available; otherwise, None.
    """
    try:
        # Determine if we're in development mode
        dev_mode = bool(st.secrets.get("development_mode", False))
        api_key  = st.secrets.get("OPENROUTER_API_KEY")
        
        if not api_key:
            # Construct error message based on the mode
            msg = (
                "OpenRouter API key not configured in development mode. "
                "Please add it to your secrets.toml file."
                if dev_mode else
                "OpenRouter API key not configured. The application may have limited functionality. "
                "Please try again later or contact support."
            )
            st.error(msg)
            return None
        
        return api_key

    except Exception as err:
        logger.exception("Error checking API key")
        st.error(
            "Unable to verify API key configuration. Some features may be unavailable. "
            "Please try again later."
        )
        return None


#*** SAFE API OPERATION WRAPPER REGION ***
def safe_api_operation(operation: Callable, error_message: Optional[str] = None) -> Any:
    """
    Execute an API operation safely using the available API key.

    Args:
        operation (Callable): A callable that receives the API key and performs the operation.
        error_message (Optional[str]): Custom error message to display upon failure.

    Returns:
        Any: Result of the operation if successful; otherwise, None.
    """
    try:
        api_key = check_api_key()
        if not api_key:
            return None
        return operation(api_key)
    
    except Exception as err:
        logger.exception("API operation failed")
        st.error(
            error_message or
            "Unable to complete the requested operation. The service may be temporarily unavailable. "
            "Please try again later."
        )
        return None