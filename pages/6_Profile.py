import streamlit as st
from dataclasses import dataclass
from typing import Dict, Any

from components.auth import auth
from components.chat.session_management import get_supabase_client

@dataclass
class ContributorInfo:
    """Used to capture user input in the profile form."""
    name: str = ""
    x: str = ""
    discord: str = ""
    linkedin: str = ""

    @property
    def is_empty(self) -> bool:
        return not any(getattr(self, field).strip() for field in vars(self))

def handle_profile_form():
    """
    Display a form that updates the user’s profile info in the 'contributors' table.
    """
    user_email = st.session_state.get("user_email")
    contributor_id = st.session_state.get("contributor_id")
    if not user_email or not contributor_id:
        st.warning("Please log in first to edit your profile.")
        return


    supabase = get_supabase_client()

    # Attempt to fetch existing data from 'contributors'
    existing_data = {}
    try:
        res = (
            supabase.table("contributors")
            .select("*")
            .eq("contributor_id", contributor_id)
            .single()
            .execute()
        )
        if res.data:
            existing_data = res.data
    except Exception as ex:
        st.error(f"Error loading profile info: {ex}")

    # Build defaults for the form
    default_info = ContributorInfo(
        name= existing_data.get("name", ""),
        x= existing_data.get("x", ""),
        discord= existing_data.get("discord", ""),
        linkedin= existing_data.get("linkedin", "")
    )

    st.subheader("Your Profile")
    with st.form("profile_form"):
        # Show contributor_id
        
        name_input    = st.text_input("Name:", value=default_info.name)
        x_input       = st.text_input("X/Twitter:", value=default_info.x)
        discord_input = st.text_input("Discord:", value=default_info.discord)
        linkedin_input= st.text_input("LinkedIn:", value=default_info.linkedin)
        st.caption(f"**Your Contributor ID:** `{contributor_id}`")

        if st.form_submit_button("Save Profile"):
            # Update 'contributors' row
            try:
                supabase.table("contributors").update({
                    "name":     name_input.strip(),
                    "x":        x_input.strip(),
                    "discord":  discord_input.strip(),
                    "linkedin": linkedin_input.strip()
                }).eq("contributor_id", contributor_id).execute()

                # Optionally store these in session for quick reference
                st.session_state["contributor"] = {
                    "name":     name_input,
                    "x":        x_input,
                    "discord":  discord_input,
                    "linkedin": linkedin_input,
                }
                st.toast("Profile updated successfully!")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Error saving profile data: {e}")

def main():
    st.set_page_config(page_title="Profile", page_icon="👤")

    if not st.experimental_user.is_logged_in:
        st.error("You must be logged in to view or edit your profile.")
        auth()
        return

    handle_profile_form()

if __name__ == "__main__":
    main()