import streamlit as st
from st_supabase_connection import execute_query
from components.chat.session_management import get_supabase_client  # === CHANGES ===

st.set_page_config(page_title="Human Verification", page_icon=":shield:")

def load_flagged_conversations():
    # === CHANGES START ===
    supabase = get_supabase_client()
    # Query all rows that have metadata->>'submittedForReview' = 'true'
    query = supabase.table("conversation_turns").select("*").eq("metadata->>submittedForReview", "true")
    res = query.execute()
    if res.error:
        st.error(f"Error loading flagged conversations: {res.error}")
        return []
    if not res.data:
        return []
    return res.data
    # === CHANGES END ===

def display_conversation(conversation):
    st.subheader(f"Conversation ID: {conversation['id']}")
    
    # 'conversation' and 'metadata' are JSONB columns
    conv_json = conversation["conversation"] or {}
    meta_json = conversation["metadata"] or {}

    with st.expander("Show Configuration"):
        # Possibly show the OmniGuard configuration from conv_json
        st.json(conv_json.get("omniguardConfiguration", "<no config>"))

    with st.expander("Show Messages"):
        st.json(conv_json.get("messages", []))

    # Voting form
    with st.form(key=f"vote_form_{conversation['id']}"):
        st.markdown("### Verify Reported Violations")

        # Retrieve existing final verdict from metadata
        existing_verified = bool(meta_json.get("verified", False))

        user_violation = st.checkbox("Confirm User Policy Violation", value=False)
        assistant_violation = st.checkbox("Confirm Assistant Policy Violation", value=False)
        safe_vote = st.checkbox("Mark as Safe", value=False)

        analysis_notes = st.text_area("Professional Analysis Notes (optional)")

        if st.form_submit_button("Submit Vote"):
            # For a real multi-vote approach, you'd parse the existing votes, add a new one, etc.
            # Simplified here: let's just set a final verified + compliance
            updated_meta = meta_json.copy()
            updated_meta["verified"] = True
            # finalCompliant = false if user or assistant violation is checked
            updated_meta["finalCompliant"] = not (user_violation or assistant_violation)

            # Possibly store the analysis notes or any other data
            updated_meta["analysisNotes"] = analysis_notes

            # Now push update to Supabase
            supabase = get_supabase_client()
            row_data = {
                "id": conversation["id"],
                "metadata": updated_meta
            }
            supabase.table("conversation_turns").upsert(row_data).execute()

            st.success("Vote recorded & conversation updated successfully!")

    # Show placeholders for vote counts, etc. if you track them in detail
    st.markdown("**Current Metadata:**")
    st.json(meta_json)
    st.markdown("---")

def main():
    with st.sidebar:
        st.markdown("# Human Verification Dashboard")
        st.info("Review flagged conversations and cast your vote on reported policy violations.")
        if st.button("Refresh Dashboard"):
            st.experimental_rerun()
    
    conversations = load_flagged_conversations()
    if not conversations:
        st.info("No conversations require verification at this time.")
    else:
        for conv in conversations:
            display_conversation(conv)

if __name__ == "__main__":
    main()
