import streamlit as st
from st_supabase_connection import execute_query
from components.chat.session_management import get_supabase_client  # === CHANGES ===

st.set_page_config(page_title="Human Verification", page_icon=":shield:")

def load_flagged_conversations():
    """Load all conversations that have been submitted for verification."""
    try:
        supabase = get_supabase_client()
        # Query all rows where submitted_for_verification = true
        query = supabase.table("interactions").select("*").eq("submitted_for_verification", True)
        res = query.execute()
        
        # The data is directly accessible from the response
        return res.data or []
    except Exception as e:
        st.error(f"Error loading flagged conversations: {str(e)}")
        return []

def display_conversation(conversation):
    st.markdown(f"Conversation ID:```{conversation['id']}```")
    
    # 'conversation' and 'metadata' are JSONB columns
    conv_json = conversation["conversation"] or {}
    meta_json = conversation["metadata"] or {}
    
    # Get review data - handle both string 'true' and boolean true
    review_data = meta_json.get("review_data", {}) if meta_json else {}
    
    # Display Reporter's Information
    with st.expander("Report:"):
        if review_data and any(review_data.values()):  # Check if review_data has any non-empty values
            violation_sources = review_data.get("violation_source", [])
            if violation_sources:
                if "User" in violation_sources and "Assistant" in violation_sources:
                    st.write(f"Both User and Assistant Content Should be Classified as Compliant = {review_data.get('suggested_compliant_classification', None)}")
                else:
                    for source in violation_sources:
                        st.write(f"{source} Content Should be Classified as Compliant = {review_data.get('suggested_compliant_classification', None)}")
        if reporter_comment := review_data.get("reporter_comment"):
            st.markdown("Reporter's Comment:")
            st.write(f"`{reporter_comment}`")
        else:
            st.info("No reporter information available.")
            
        # Display vote counts
        votes = meta_json.get("votes", {})
        if votes:
            st.markdown("Current Votes")
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
                st.info(f"Final Classification: {'Compliant' if conversation.get('compliant') else 'Non-Compliant'}")
            elif verification_status == "omniguard":
                st.info("This conversation was verified by OmniGuard.")
            else:
                st.warning("This conversation is pending human verification.")

    with st.expander("Show Messages"):
        st.json(conv_json.get("messages", []))

    # Voting form
    with st.form(key=f"vote_form_{conversation['id']}"):
        st.markdown("Reviewer's Analysis:")

        # Retrieve existing verification status
        verification_status = conversation.get("verification_status", "pending")
        
        # Only show voting form if not already human verified
        if verification_status != "human":
            user_violation = st.checkbox("User Content Causes Violation", value=False)
            assistant_violation = st.checkbox("Assistant Content Causes Violation", value=False)
            safe_vote = st.checkbox("All Content Is Compliant", value=False)

            reviewer_notes = st.text_area("Reviewer's Analysis Notes")

            if st.form_submit_button("Submit Review"):
                # Get existing metadata or initialize with default structure
                updated_meta = meta_json.copy()
                if "votes" not in updated_meta:
                    updated_meta["votes"] = {
                        "count": 0,
                        "user_violations": 0,
                        "assistant_violations": 0,
                        "safe_votes": 0
                    }
                
                # Increment vote counts
                updated_meta["votes"]["count"] += 1
                if user_violation:
                    updated_meta["votes"]["user_violations"] += 1
                if assistant_violation:
                    updated_meta["votes"]["assistant_violations"] += 1
                if safe_vote:
                    updated_meta["votes"]["safe_votes"] += 1

                # Check if we've reached 100 votes
                is_fully_verified = updated_meta["votes"]["count"] >= 100
                
                # Calculate final compliance based on majority vote
                is_compliant = None
                if is_fully_verified:
                    total_votes = updated_meta["votes"]["count"]
                    violation_votes = updated_meta["votes"]["user_violations"] + updated_meta["votes"]["assistant_violations"]
                    safe_votes = updated_meta["votes"]["safe_votes"]
                    
                    # Set as compliant if majority of votes indicate it's safe
                    is_compliant = safe_votes > violation_votes

                # Store the reviewer's analysis
                updated_meta["reviewer_analysis"] = {
                    "user_violation": user_violation,
                    "assistant_violation": assistant_violation,
                    "marked_safe": safe_vote,
                    "reviewer_notes": reviewer_notes
                }

                # Now push update to Supabase
                supabase = get_supabase_client()
                row_data = {
                    "id": conversation["id"],
                    "conversation": conv_json,  # Include existing conversation data
                    "metadata": updated_meta,
                    "verification_status": "human" if is_fully_verified else "pending",  # Update verification status
                    "compliant": is_compliant  # Update compliant column if fully verified
                }
                supabase.table("interactions").upsert(row_data).execute()

                st.success("Review submitted successfully!")

                # Show vote counts
                st.write(f"Current vote count: {updated_meta['votes']['count']}/100")
                if is_fully_verified:
                    st.info("This conversation has been verified with 100 votes!")
        else:
            st.info("This conversation has already been verified by human review.")

    # Show current metadata for debugging/verification
    with st.expander("Show Raw Metadata"):
        st.json(meta_json)
    st.markdown("---")

def main():
    with st.sidebar:
        st.markdown("# Human Verification Dashboard")
        st.info("Review Interactions Reported to Contain Errors by OmniGuard")
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
