import streamlit as st
from components.chat.session_management import get_supabase_client
from typing                             import List, Dict, Any
from components.init_session_state import init_session_state
from components.banner import show_alpha_banner

st.set_page_config(page_title="Human Verification", page_icon="🔍")

# Show alpha banner
show_alpha_banner()


def load_flagged_conversations() -> List[Dict[str, Any]]:
    """
    Load all flagged conversations that have been submitted for verification.
    We rely on 'submitted_for_verification' for filtering,
    and 'verifier' to check final verification status.
    """
    try:
        supabase = get_supabase_client()
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
    Enforces one-vote-per-user by checking if user's contributor_id is in the 'voters' list.
    """
    st.markdown(f"**Conversation ID:** `{conversation['id']}`")

    conv_json: Dict[str, Any] = conversation.get("conversation") or {}
    meta_json: Dict[str, Any] = conversation.get("metadata") or {}
    review_data: Dict[str, Any] = meta_json.get("review_data", {}) or {}

    # --- REPORT SECTION ---
    with st.expander("Report:"):
        if review_data and any(review_data.values()):
            violation_sources = review_data.get("violation_source", [])
            suggested_compliant = review_data.get("suggested_compliant_classification", None)
            if violation_sources:
                if "User" in violation_sources and "Agent" in violation_sources:
                    st.write(
                        f"Both User and Agent content should be classified as Compliant = {suggested_compliant}"
                    )
                else:
                    for source in violation_sources:
                        st.write(
                            f"{source} content should be classified as Compliant = {suggested_compliant}"
                        )
        if reporter_comment := review_data.get("reporter_comment"):
            st.markdown("**Reporter's Comment:**")
            st.write(f"`{reporter_comment}`")
        else:
            st.info("No reporter comment available.")

        votes: Dict[str, Any] = meta_json.get("votes", {})
        if votes:
            st.markdown("**Current Votes:**")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Votes", f"{votes.get('count', 0)}/100")
            with col2:
                st.metric("User Violations", votes.get("user_violations", 0))
            with col3:
                st.metric("Agent Violations", votes.get("assistant_violations", 0))
            with col4:
                st.metric("Compliant Votes", votes.get("compliant_votes", 0))

            verifier = conversation.get("verifier", "pending")
            if verifier == "human":
                st.toast("This conversation has been verified by human review!")
                compliant_status = "Compliant" if conversation.get("compliant") else "Non-Compliant"
                st.info(f"Final Classification: {compliant_status}")
            elif verifier == "omniguard":
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

        verifier = conversation.get("verifier", "pending")
        current_user_id = st.session_state.get("contributor_id")

        # If conversation already verified as "human", hide voting
        if verifier == "human":
            st.info("This conversation has already been verified by human review.")
        else:
            # If user not logged in or missing contributor_id, can't vote
            if not current_user_id:
                st.warning("Please log in to cast a vote.")
            else:
                user_violation: bool      = st.checkbox("User Content Causes Violation", value=False)
                assistant_violation: bool = st.checkbox("Agent Content Causes Violation", value=False)
                safe_vote: bool           = st.checkbox("All Content Is Compliant", value=False)
                reviewer_notes: str       = st.text_area("Reviewer's Analysis Notes")

                if st.form_submit_button("Submit Review"):
                    meta_copy = meta_json.copy()
                    if "votes" not in meta_copy:
                        meta_copy["votes"] = {
                            "count": 0,
                            "user_violations": 0,
                            "assistant_violations": 0,
                            "compliant_votes": 0,
                        }

                    # Add "voters" list if not present
                    if "voters" not in meta_copy["votes"]:
                        meta_copy["votes"]["voters"] = []

                    # Check if the current user already voted
                    if current_user_id in meta_copy["votes"]["voters"]:
                        st.warning("You have already voted on this conversation.")
                    else:
                        # Register user as a voter
                        meta_copy["votes"]["voters"].append(current_user_id)

                        # Tally the new vote
                        meta_copy["votes"]["count"] += 1
                        if user_violation:
                            meta_copy["votes"]["user_violations"] += 1
                        if assistant_violation:
                            meta_copy["votes"]["assistant_violations"] += 1
                        if safe_vote:
                            meta_copy["votes"]["compliant_votes"] += 1

                        # Check threshold
                        is_fully_verified = meta_copy["votes"]["count"] >= 100
                        is_compliant = None
                        if is_fully_verified:
                            violation_votes = (
                                meta_copy["votes"]["user_violations"]
                                + meta_copy["votes"]["assistant_violations"]
                            )
                            compliant_votes = meta_copy["votes"]["compliant_votes"]
                            is_compliant = compliant_votes > violation_votes

                        # Store reviewer's analysis
                        meta_copy["reviewer_analysis"] = {
                            "user_violation":      user_violation,
                            "assistant_violation": assistant_violation,
                            "marked_safe":         safe_vote,
                            "reviewer_notes":      reviewer_notes,
                        }

                        # Upsert row data
                        new_verifier = "human" if is_fully_verified else "pending"
                        row_data = {
                            "id": conversation["id"],
                            "conversation": conv_json,
                            "metadata": meta_copy,
                            "verifier": new_verifier,
                            "compliant": is_compliant,
                        }

                        supabase = get_supabase_client()
                        supabase.table("interactions").upsert(row_data).execute()

                        st.toast("Review submitted successfully!")
                        st.write(f"Current vote count: {meta_copy['votes']['count']}/100")
                        if is_fully_verified:
                            st.info("This conversation has been verified with 100 votes!")
    # --- END VOTING FORM SECTION ---

    with st.expander("Show Raw Metadata"):
        st.json(meta_json)
    st.markdown("---")


def main() -> None:
    """
    Main function to render the Human Verification Dashboard.
    """
    with st.sidebar:
        st.markdown("# Human Verification Dashboard")
        st.info("Review interactions flagged for potential errors.")
        if st.button("Refresh Dashboard"):
            st.rerun()

    conversations = load_flagged_conversations()
    if not conversations:
        st.info("No conversations require verification at this time.")
    else:
        for conv in conversations:
            display_conversation(conv)


if __name__ == "__main__":
    main()
