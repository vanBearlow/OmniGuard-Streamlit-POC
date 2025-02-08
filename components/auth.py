import streamlit as st
import logging
from typing import Optional, Tuple
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_auth_status() -> Tuple[bool, Optional[str]]:
    """
    Get the current authentication status and any error message.
    Returns (is_authenticated, error_message)
    """
    try:
        # Check for development mode first
        if st.secrets.get("development_mode", False):
            logger.info("Development mode is enabled, bypassing authentication")
            return True, None
            
        logger.info("Checking authentication status")
        is_logged_in = st.experimental_user.is_logged_in
        if is_logged_in:
            logger.info("User is authenticated")
        else:
            logger.info("User is not authenticated")
        return is_logged_in, None
    except AttributeError as e:
        error_msg = "Streamlit experimental_user not available. Check if authentication is enabled."
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Authentication error: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return False, error_msg

def render_auth_status():
    """Renders a consistent authentication status and login/logout UI in the sidebar."""
    with st.sidebar:
        try:
            logger.info("Rendering authentication status")
            
            # Check for development mode first
            if st.secrets.get("development_mode", False):
                logger.info("Development mode is enabled")
                st.info("Running in development mode")
                return
                
            is_authenticated, error = get_auth_status()
            
            if error:
                logger.error(f"Authentication status error: {error}")
                st.error(f"Authentication error: {error}")
                st.info("Please check authentication configuration in .streamlit/secrets.toml")
                return
            
            if is_authenticated:
                try:
                    user_email = getattr(st.experimental_user, 'email', 'User')
                    logger.info(f"Displaying info for authenticated user: {user_email}")
                    st.write(f"👤 Logged in as: {user_email}")
                    
                    if st.button("🚪 Logout", use_container_width=True):
                        logger.info("Logout button clicked")
                        try:
                            st.logout()
                            logger.info("Logout successful")
                        except Exception as e:
                            error_msg = f"Logout failed: {str(e)}"
                            logger.error(f"{error_msg}\n{traceback.format_exc()}")
                            st.error(error_msg)
                            
                except Exception as e:
                    error_msg = f"Error displaying user info: {str(e)}"
                    logger.error(f"{error_msg}\n{traceback.format_exc()}")
                    st.error(error_msg)
            else:
                logger.info("User not logged in, displaying login button")
                st.write("👤 Not logged in")
                
                if st.button("🔑 Login with Google", use_container_width=True):
                    logger.info("Login button clicked")
                    try:
                        # Check for required OAuth configuration
                        if not st.secrets.get("oauth"):
                            error_msg = "OAuth configuration missing in .streamlit/secrets.toml"
                            logger.error(error_msg)
                            st.error(error_msg)
                            return
                            
                        st.login()
                        logger.info("Login flow initiated")
                    except Exception as e:
                        error_msg = f"Login failed: {str(e)}"
                        logger.error(f"{error_msg}\n{traceback.format_exc()}")
                        st.error(error_msg)
                        
        except Exception as e:
            error_msg = f"Error in auth status UI: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            st.error(error_msg)