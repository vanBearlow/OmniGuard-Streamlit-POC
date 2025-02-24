import streamlit as st

def auth():
    # If not logged in, show the login prompt
    if not st.experimental_user.is_logged_in:
        # (Optional) Clear any old user info from session state
        st.session_state.pop("user_name", None)
        # Display login button
        if st.button("Log in with Google"):
            st.login()  # triggers Google OAuth flow
    else:
        # User is logged in
        user_name = st.experimental_user.name or "User"
        # Store the user's name in session state for later use
        st.session_state["user_name"] = user_name
        st.markdown(f"`{user_name}`")
        # Display logout button
        if st.button("Log out"):
            st.logout()