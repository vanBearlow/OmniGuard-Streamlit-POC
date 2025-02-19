import streamlit as st
import logging
from typing import Optional, Any, Callable

logger = logging.getLogger(__name__)


def check_api_key() -> Optional[str]:
    """
    Check for OpenRouter API key availability and provide clear user feedback.
    
    Returns:
        str: API key if available, None otherwise
    """
    try:
        dev_mode = bool(st.secrets.get("development_mode", False))
        
        # Development mode check
        if dev_mode:
            api_key = st.secrets.get("OPENROUTER_API_KEY")
            if not api_key:
                st.error(
                    "OpenRouter API key not configured in development mode. "
                    "Please add it to your secrets.toml file."
                )
                return None
            return api_key
            
        # Production mode check
        api_key = st.secrets.get("OPENROUTER_API_KEY")
        if not api_key:
            st.error(
                "OpenRouter API key not configured. The application may have limited functionality. "
                "Please try again later or contact support."
            )
            return None
        return api_key
            
    except Exception as e:
        logger.exception("Error checking API key")
        st.error(
            "Unable to verify API key configuration. Some features may be unavailable. "
            "Please try again later."
        )
        return None


def safe_api_operation(operation: Callable, error_message: str = None) -> Any:
    """
    Safely execute an API operation with graceful error handling.
    
    Args:
        operation: API operation function to execute
        error_message: Custom error message to display on failure
    
    Returns:
        Result of the operation or None on failure
    """
    try:
        api_key = check_api_key()
        if not api_key:
            return None
            
        return operation(api_key)
    except Exception as e:
        logger.exception("API operation failed")
        if error_message:
            st.error(error_message)
        else:
            st.error(
                "Unable to complete the requested operation. "
                "The service may be temporarily unavailable. Please try again later."
            )
        return None