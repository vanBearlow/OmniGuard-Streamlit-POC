import streamlit as st
from dataclasses import dataclass
from typing import Dict, Any

from components.auth import auth

@dataclass
class ContributorInfo:
    """Structure for contributor information with the same logic as the old expander code."""
    name: str = ""
    x: str = ""         # X/Twitter handle
    discord: str = ""   # Discord username
    linkedin: str = ""

    @property
    def is_empty(self) -> bool:
        """Check if all fields are empty."""
        return not any(value.strip() for value in vars(self).values())


def handle_profile_form() -> None:
    """
    Handle the profile form submission and updates within session_state, exactly like the old expander.
    """
    # Grab any existing contributor data from session state (if present)
    existing_contributor_data = st.session_state.get("contributor", {})
    
    with st.form("profile_form"):
        info = ContributorInfo(
            name=st.text_input("Name:", value=existing_contributor_data.get("name", "")),
            x=st.text_input("X/Twitter:", value=existing_contributor_data.get("x", "")),
            discord=st.text_input("Discord:", value=existing_contributor_data.get("discord", "")),
            linkedin=st.text_input("LinkedIn:", value=existing_contributor_data.get("linkedin", ""))
        )

        if st.form_submit_button("Save Profile"):
            # Store updated contributor data in session_state, just as before
            st.session_state["contributor"] = vars(info)
            st.toast("Profile updated successfully!")
            st.rerun()


def main():
    st.set_page_config(page_title="Profile", page_icon="👤")

    # Must be logged in to view this page
    if not st.experimental_user.is_logged_in:
        st.error("You must be logged in to view or edit your profile.")
        auth()
        st.stop()

    st.title("My Profile")
    st.markdown("Update your personal information to be credited in the public dataset.")

    handle_profile_form()

if __name__ == "__main__":
    main()
