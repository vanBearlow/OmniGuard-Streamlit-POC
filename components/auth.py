import streamlit as st
import logging
from typing import Optional, Tuple
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_auth_status() -> Tuple[bool, Optional[str]]:
    """
    Retrieve the current authentication status along with any authentication error message.

    This function checks if the user is logged in using Streamlit's experimental authentication user object.
    When the "development_mode" flag is enabled in Streamlit secrets, the function bypasses normal authentication
    and returns True.

    Returns:
        Tuple[bool, Optional[str]]:
            - is_authenticated (bool): True if the user is authenticated, otherwise False.
            - error_message (Optional[str]): An error message if any issues occur during authentication; otherwise, None.
    """
    try:
        dev_mode = bool(st.secrets.get("development_mode", False))
        if dev_mode:
            logger.info("Development mode is enabled. Bypassing authentication.")
            return True, None
        logger.info("Checking authentication status")
        try:
            is_logged_in = getattr(st.experimental_user, "is_logged_in", False)
            if is_logged_in:
                logger.info("User is authenticated")
                return True, None
            else:
                logger.info("User is not authenticated")
                return False, None
        except AttributeError:
            error_msg = "Authentication not available"
            logger.error(error_msg)
            return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected authentication error: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def render_auth_status():
    with st.sidebar:
        # This call will handle dev_mode logic
        is_authenticated, error = get_auth_status()
        if st.secrets.get("development_mode", False):
            st.info("Development Mode: No authentication required.")
            return
        elif error:
            st.error(f"Authentication error: {error}")
            return

        # If we reach here, dev_mode is off and we rely on real st.experimental_user
        if is_authenticated:
            col1, col2 = st.columns([2, 1])
            with col1:
                user_email = getattr(st.experimental_user, "email", None) or "Unknown"
                st.caption(f"👤 {user_email}")
            with col2:
                if st.button("🚪 Logout"):
                    try:
                        st.logout()
                    except Exception as e:
                        st.error(f"Logout failed: {str(e)}")
        else:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.caption("👤 Not logged in")
            with col2:
                if st.button("🔑 Login"):
                    try:
                        st.login()
                    except Exception as e:
                        st.error(f"Login failed: {str(e)}")