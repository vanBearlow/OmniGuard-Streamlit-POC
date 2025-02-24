import uuid
import streamlit as st
from components.chat.session_management import get_supabase_client

def auth():
    """
    If not logged in, show the login prompt.
    If logged in, fetch or create a 'contributor_id' for the user and store it in session.
    """
    if not st.experimental_user.is_logged_in:
        # Clear old user info from session state
        st.session_state.pop("user_name", None)
        st.session_state.pop("contributor_id", None)
        
        if st.button("Log in with Google"):
            st.login()  # triggers Google OAuth flow
    else:
        # User is logged in
        user_name  = st.experimental_user.name or "User"
        user_email = st.experimental_user.email or "unknown@example.com"

        st.session_state["user_name"]  = user_name
        st.session_state["user_email"] = user_email
        
        supabase = get_supabase_client()
        try:
            res = (
                supabase.table("contributors")
                .select("*")
                .eq("email", user_email)
                .execute()
            )
            if not res.data:
                # No row yet: create one
                new_id = str(uuid.uuid4())
                supabase.table("contributors").insert({
                    "email":          user_email,
                    "contributor_id": new_id
                }).execute()
                st.session_state["contributor_id"] = new_id
            else:
                # Use existing row
                st.session_state["contributor_id"] = res.data[0]["contributor_id"]
        except Exception as e:
            st.error(f"Error retrieving contributor_id: {e}")

        st.markdown(f"`{user_name}`")

        if st.button("Log out"):
            st.logout()
