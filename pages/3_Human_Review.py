"""Human Review dashboard for reviewing flagged conversations.

This module provides an interface for human reviewers to verify conversations
that have been flagged by the system. Reviewers can vote on whether content
violates guidelines and add analysis notes.
"""

import streamlit as st
from components.chat.session_management import get_supabase_client
from typing import List, Dict, Any
from components.init_session_state import init_session_state

st.set_page_config(page_title="Human Review", page_icon="🔍")


def load_flagged_conversations() -> List[Dict[str, Any]]:
    """Load all flagged conversations submitted for review.

    Retrieves conversations marked with 'submitted_for_review' flag
    from the database. Uses 'verifier' field to check review status.

    Returns:
        List of conversation dictionaries containing all metadata.
    """
    try:
        supabase = get_supabase_client()
        query = supabase.table("interactions").select("*").eq("submitted_for_review", True)
        res = query.execute()
        return res.data or []
    except Exception as e:
        st.error(f"Error loading flagged conversations: {e}")
        return []


def display_conversation(conversation: Dict[str, Any]) -> None:
    """Display a flagged conversation with review interface.

    Shows conversation details, report information, and provides
    a voting interface for human reviewers to classify content.
    Enforces one-vote-per-user policy.

    Args:
        conversation: Dictionary containing conversation data and metadata
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
                st.markdown(f"**Total Votes**\n{votes.get('count', 0)}/100")
            with col2:
                st.markdown(f"**User Violation**\n{votes.get('user_violations', 0)}")
            with col3:
                st.markdown(f"**Assistant Violation**\n{votes.get('assistant_violations', 0)}")
            with col4:
                st.markdown(f"**Compliant / Non-Harmful**\n{votes.get('compliant_votes', 0)}")

    # --- MESSAGES SECTION ---
    with st.expander("Show Messages"):
        st.json(conv_json.get("messages", []))

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
                st.warning("Please log in to cast a vote. Visit your [Profile](/profile) for login options.")
            else:
                user_violation: bool = st.checkbox("User Content Causes Violation", value=False)
                assistant_violation: bool = st.checkbox(
                    "Agent Content Causes Violation", value=False
                )
                safe_vote: bool = st.checkbox("All Content Is Compliant", value=False)
                reviewer_notes: str = st.text_area("Reviewer's Analysis Notes")

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
                            "user_violation": user_violation,
                            "assistant_violation": assistant_violation,
                            "marked_safe": safe_vote,
                            "reviewer_notes": reviewer_notes,
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

    with st.expander("Show Raw Metadata"):
        st.json(meta_json)
    st.markdown("---")


def main() -> None:
    """Render the Human Review Dashboard if the user is logged in.

    Checks login status; if not logged in, shows a warning.
    """
    if not st.session_state.get("contributor_id"):
        st.warning("Please log in to access Human Review Dashboard. Visit your [Profile](/profile) for login options.")
        return

    with st.sidebar:
        st.markdown("# Human Review Dashboard")
        st.info("Review Interactions Reported as Harmful / Non-Compliant")
        st.markdown("---")
        st.markdown("Will not be visible to the public. Maybe")

    conversations = load_flagged_conversations()
    if not conversations:
        st.info("No conversations require review at this time.")
    else:
        for conv in conversations:
            display_conversation(conv)


if __name__ == "__main__":
    main()
