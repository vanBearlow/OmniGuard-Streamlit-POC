import streamlit as st
from st_supabase_connection import execute_query
from components.chat.session_management import get_supabase_client
from typing import List, Dict, Any

st.set_page_config(page_title="Human Verification", page_icon=":shield:")


def load_flagged_conversations() -> List[Dict[str, Any]]:
    """
    Load all flagged conversations that have been submitted for verification.

    Returns:
        List[Dict[str, Any]]: List of conversation records or an empty list on error.
    """
    try:
        supabase = get_supabase_client()
        # Query interactions where submitted_for_verification is True
        query = (
            supabase.table("interactions")
            .select("*")
            .eq("submitted_for_verification", True)
        )
        res = query.execute()
        return res.data or []
    except Exception as e:
        st.error(f"Error loading flagged conversations: {e}")
        return []


def display_conversation(conversation: Dict[str, Any]) -> None:
    """
    Display a single flagged conversation and allow for human vote-based review.

    Args:
        conversation (Dict[str, Any]): The conversation record from the database.
    """
    st.markdown(f"**Conversation ID:** `{conversation['id']}`")

    # Extract JSON data (or default to an empty dict)
    conv_json: Dict[str, Any] = conversation.get("conversation") or {}
    meta_json: Dict[str, Any] = conversation.get("metadata") or {}

    # Retrieve review data; handle both string 'true' and boolean True.
    review_data: Dict[str, Any] = meta_json.get("review_data", {}) or {}

    # --- REPORT SECTION ---
    with st.expander("Report:"):
        if review_data and any(review_data.values()):
            violation_sources = review_data.get("violation_source", [])
            suggested_compliant = review_data.get("suggested_compliant_classification", None)
            if violation_sources:
                # Use a combined message if both User and Assistant content are flagged
                if "User" in violation_sources and "Assistant" in violation_sources:
                    st.write(
                        f"Both User and Assistant Content should be classified as Compliant = {suggested_compliant}"
                    )
                else:
                    for source in violation_sources:
                        st.write(
                            f"{source} Content should be classified as Compliant = {suggested_compliant}"
                        )
        if reporter_comment := review_data.get("reporter_comment"):
            st.markdown("**Reporter's Comment:**")
            st.write(f"`{reporter_comment}`")
        else:
            st.info("No reporter information available.")

        # Display vote counts if available
        votes: Dict[str, Any] = meta_json.get("votes", {})
        if votes:
            st.markdown("**Current Votes:**")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Votes", f"{votes.get('count', 0)}/100")
            with col2:
                st.metric("User Violations", votes.get("user_violations", 0))
            with col3:
                st.metric("Assistant Violations", votes.get("assistant_violations", 0))
            with col4:
                st.metric("Safe Votes", votes.get("safe_votes", 0))

            verification_status = conversation.get("verification_status", "pending")
            if verification_status == "human":
                st.success("This conversation has been verified by human review!")
                compliant_status = "Compliant" if conversation.get("compliant") else "Non-Compliant"
                st.info(f"Final Classification: {compliant_status}")
            elif verification_status == "omniguard":
                st.info("This conversation was verified by OmniGuard.")
            else:
                st.warning("This conversation is pending human verification.")
    # --- END REPORT SECTION ---

    # --- MESSAGES SECTION ---
    with st.expander("Show Messages"):
        st.json(conv_json.get("messages", []))
    # --- END MESSAGES SECTION ---

    # --- VOTING FORM SECTION ---
    with st.form(key=f"vote_form_{conversation['id']}"):
        st.markdown("**Reviewer's Analysis:**")

        # Retrieve current verification status
        verification_status = conversation.get("verification_status", "pending")

        # Only show the voting inputs if not already human verified
        if verification_status != "human":
            user_violation: bool     = st.checkbox("User Content Causes Violation", value=False)
            assistant_violation: bool = st.checkbox("Assistant Content Causes Violation", value=False)
            safe_vote: bool          = st.checkbox("All Content Is Compliant", value=False)
            reviewer_notes: str      = st.text_area("Reviewer's Analysis Notes")

            if st.form_submit_button("Submit Review"):
                # Get or initialize the votes dictionary
                updated_meta = meta_json.copy()
                if "votes" not in updated_meta:
                    updated_meta["votes"] = {
                        "count":                0,
                        "user_violations":      0,
                        "assistant_violations": 0,
                        "safe_votes":           0,
                    }

                # Increment vote counts
                updated_meta["votes"]["count"]                += 1
                if user_violation:
                    updated_meta["votes"]["user_violations"]  += 1
                if assistant_violation:
                    updated_meta["votes"]["assistant_violations"]  += 1
                if safe_vote:
                    updated_meta["votes"]["safe_votes"]       += 1

                # Check if the conversation has reached the threshold of 100 votes
                is_fully_verified = updated_meta["votes"]["count"] >= 100

                # Calculate final compliance based on majority if fully verified
                is_compliant = None
                if is_fully_verified:
                    violation_votes = (
                        updated_meta["votes"]["user_violations"]
                        + updated_meta["votes"]["assistant_violations"]
                    )
                    safe_votes = updated_meta["votes"]["safe_votes"]
                    is_compliant = safe_votes > violation_votes

                # Store the reviewer's analysis
                updated_meta["reviewer_analysis"] = {
                    "user_violation":      user_violation,
                    "assistant_violation": assistant_violation,
                    "marked_safe":         safe_vote,
                    "reviewer_notes":      reviewer_notes,
                }

                # Prepare the updated row to push to Supabase
                row_data = {
                    "id":                  conversation["id"],
                    "conversation":        conv_json,  # Preserve existing conversation data
                    "metadata":            updated_meta,
                    "verification_status": "human" if is_fully_verified else "pending",
                    "compliant":           is_compliant,
                }

                supabase = get_supabase_client()
                supabase.table("interactions").upsert(row_data).execute()

                st.success("Review submitted successfully!")
                st.write(f"Current vote count: {updated_meta['votes']['count']}/100")
                if is_fully_verified:
                    st.info("This conversation has been verified with 100 votes!")
        else:
            st.info("This conversation has already been verified by human review.")
    # --- END VOTING FORM SECTION ---

    # --- RAW METADATA SECTION ---
    with st.expander("Show Raw Metadata"):
        st.json(meta_json)
    # --- END RAW METADATA SECTION ---

    st.markdown("---")


def main() -> None:
    """
    Main function to render the Human Verification Dashboard.
    """
    # --- SIDEBAR CONFIGURATION ---
    with st.sidebar:
        st.markdown("# Human Verification Dashboard")
        st.info("Review Interactions Reported to Contain Errors by OmniGuard")
        if st.button("Refresh Dashboard"):
            st.rerun()
    # --- END SIDEBAR CONFIGURATION ---

    conversations = load_flagged_conversations()
    if not conversations:
        st.info("No conversations require verification at this time.")
    else:
        for conv in conversations:
            display_conversation(conv)


if __name__ == "__main__":
    main()
