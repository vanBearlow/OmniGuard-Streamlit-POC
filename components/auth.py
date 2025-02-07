import streamlit as st
from typing import Optional

def get_auth_status() -> tuple[bool, Optional[str]]:
    """
    Get the current authentication status and any error message.
    Returns (is_authenticated, error_message)
    """
    try:
        return st.experimental_user.is_logged_in, None
    except (AttributeError, Exception) as e:
        return False, str(e)

def render_auth_status():
    """Renders a consistent authentication status and login/logout UI in the sidebar."""
    with st.sidebar:
        is_authenticated, error = get_auth_status()
        
        if error:
            st.error(f"Authentication error: {error}")
            st.info("Please check authentication configuration")
            return
        
        if is_authenticated:
            try:
                user_email = getattr(st.experimental_user, 'email', 'User')
                st.write(f"👤 Logged in as: {user_email}")
                if st.button("🚪 Logout", use_container_width=True):
                    st.logout()
            except Exception as e:
                st.error(f"Error displaying user info: {str(e)}")
        else:
            st.write("👤 Not logged in")
            if st.button("🔑 Login with Google", use_container_width=True):
                st.login()