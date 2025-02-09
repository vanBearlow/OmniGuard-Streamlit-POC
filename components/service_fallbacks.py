import streamlit as st
import logging
from functools import wraps
from database import get_connection_with_retry
from typing import Optional, Any, Callable
import json

logger = logging.getLogger(__name__)

def with_database_fallback(default_value: Any = None):
    """
    Decorator that provides graceful fallback for database operations.
    Shows user-friendly messages and returns a default value if the operation fails.
    
    Args:
        default_value: Value to return if the database operation fails
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.exception(f"Database error in {func.__name__}")
                st.warning(
                    "⚠️ Unable to access the database at the moment. Some features may be limited. "
                    "Please try again later."
                )
                # Store error in session state for monitoring
                st.session_state.last_db_error = str(e)
                return default_value
        return wrapper
    return decorator

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
        if not st.session_state.get("contribute_training_data", True):
            api_key = st.session_state.get("api_key")
            if not api_key:
                st.warning(
                    "No API key provided. Since data sharing is disabled, "
                    "you'll need to provide your own OpenRouter API key in the configuration."
                )
                return None
            return api_key
            
        # Default production case
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

def safe_database_operation(operation: Callable, fallback_value: Any = None) -> Any:
    """
    Safely execute a database operation with retries and graceful fallback.
    
    Args:
        operation: Database operation function to execute
        fallback_value: Value to return if operation fails
    
    Returns:
        Result of the operation or fallback value
    """
    try:
        conn = get_connection_with_retry(max_retries=3, retry_delay=1)
        try:
            result = operation(conn)
            return result
        finally:
            conn.close()
    except Exception as e:
        logger.exception("Database operation failed")
        st.warning(
            "⚠️ Unable to complete the database operation. Some data may be unavailable. "
            "Please try again later."
        )
        return fallback_value

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