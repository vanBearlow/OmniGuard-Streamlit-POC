import requests
import streamlit as st
import json
from datetime import datetime, timezone
from human_verification_db import get_connection, init_db as hv_init_db
from components.auth import get_auth_status
from database import get_conversation, save_conversation, remove_conversation
from omniguard import assess_rule_violation

st.set_page_config(page_title="Human Verification", page_icon=":shield:")

def get_flagged_conversations():
    """
    Retrieve conversations flagged for human verification.
    This function queries for conversations with a vote count 
    either missing or below the threshold of 100.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT conversation_id, conversation_messages, conversation_configuration,
               COALESCE(user_violation_votes, 0) as user_violation_votes,
               COALESCE(assistant_violation_votes, 0) as assistant_violation_votes,
               COALESCE(no_violation_votes, 0) as no_violation_votes,
               reported_user_violation,
               reported_assistant_violation
        FROM flagged_conversations
        WHERE (COALESCE(user_violation_votes, 0) +
               COALESCE(assistant_violation_votes, 0) +
               COALESCE(no_violation_votes, 0) < 100)
          AND (final_decision_made = FALSE OR final_decision_made IS NULL)
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return rows

def make_final_decision(conversation_id, vote_counts, omni_guard_result):
    """
    Make final decision on a flagged conversation based on votes and OmniGuard assessment.
    
    Args:
        conversation_id: The ID of the conversation
        vote_counts: Dict containing vote counts
        omni_guard_result: Dict containing OmniGuard's assessment
    
    Returns:
        Dict containing decision details and actions taken
    """
    # Calculate vote percentages
    total_votes = sum(vote_counts.values())
    user_violation_pct = vote_counts['user_violation_votes'] / total_votes
    assistant_violation_pct = vote_counts['assistant_violation_votes'] / total_votes
    no_violation_pct = vote_counts['no_violation_votes'] / total_votes
    
    # Make decision
    decision = {
        'timestamp': datetime.now(timezone.utc),
        'vote_counts': vote_counts,
        'vote_percentages': {
            'user_violation': user_violation_pct,
            'assistant_violation': assistant_violation_pct,
            'no_violation': no_violation_pct
        },
        'omni_guard_assessment': omni_guard_result,
        'actions_taken': []
    }
    
    # Determine violations
    user_violation_confirmed = user_violation_pct > no_violation_pct
    assistant_violation_confirmed = assistant_violation_pct > no_violation_pct
    
    # Record rationale
    decision['rationale'] = []
    if user_violation_confirmed:
        decision['rationale'].append(f"User violation confirmed by {user_violation_pct:.1%} of votes")
    if assistant_violation_confirmed:
        decision['rationale'].append(f"Assistant violation confirmed by {assistant_violation_pct:.1%} of votes")
    if not user_violation_confirmed and not assistant_violation_confirmed:
        decision['rationale'].append(f"No violations confirmed, {no_violation_pct:.1%} voted safe")
    
    # Take actions based on decision
    existing = get_conversation(conversation_id)
    
    if user_violation_confirmed or assistant_violation_confirmed:
        if existing:
            remove_conversation(conversation_id)
            decision['actions_taken'].append("Removed from main dataset")
        save_conversation(
            conversation_id,
            user_violates_rules=user_violation_confirmed,
            assistant_violates_rules=assistant_violation_confirmed,
            needed_human_verification=True
        )
        decision['actions_taken'].append("Added to verified violations dataset")
    elif no_violation_pct > (user_violation_pct + assistant_violation_pct):
        if not existing:
            save_conversation(
                conversation_id,
                user_violates_rules=False,
                assistant_violates_rules=False,
                needed_human_verification=False
            )
            decision['actions_taken'].append("Added to main dataset")
    
    # Archive flagged conversation
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE flagged_conversations
        SET final_decision_made = TRUE,
            final_decision_timestamp = %s,
            final_decision_details = %s,
            archived = TRUE
        WHERE conversation_id = %s
        """,
        (decision['timestamp'], json.dumps(decision), conversation_id)
    )
    conn.commit()
    conn.close()
    
    return decision

def record_vote(conversation_id, user_email, sources, comment=""):
    """
    Record a vote for the given conversation.
    Only logged-in users can vote, and each user can only vote once per conversation.
    """
    try:
        # Calculate votes based on selected sources
        user_vote = 1 if "User" in sources else 0
        assistant_vote = 1 if "Assistant" in sources else 0
        no_rule_vote = 1 if "No Rule Violations" in sources else 0

        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if user has already voted
            cursor.execute(
                "SELECT 1 FROM flagged_votes WHERE conversation_id = %s AND user_email = %s",
                (conversation_id, user_email)
            )
            if cursor.fetchone():
                return "already_voted"

            # Record the vote
            cursor.execute(
                """
                UPDATE flagged_conversations
                SET user_violation_votes = COALESCE(user_violation_votes, 0) + %s,
                    assistant_violation_votes = COALESCE(assistant_violation_votes, 0) + %s,
                    no_violation_votes = COALESCE(no_violation_votes, 0) + %s
                WHERE conversation_id = %s
                """, (user_vote, assistant_vote, no_rule_vote, conversation_id)
            )
            cursor.execute(
                "INSERT INTO flagged_votes (conversation_id, user_email, decision_comment) VALUES (%s, %s, %s)",
                (conversation_id, user_email, comment)
            )
            conn.commit()

            # Get updated conversation details
            cursor.execute(
                """
                SELECT conversation_messages, conversation_configuration,
                       COALESCE(user_violation_votes, 0) as user_votes,
                       COALESCE(assistant_violation_votes, 0) as assistant_votes,
                       COALESCE(no_violation_votes, 0) as no_rule_votes
                FROM flagged_conversations
                WHERE conversation_id = %s
                """, (conversation_id,)
            )
            result = cursor.fetchone()

            if result:
                conversation_messages, conversation_configuration, user_votes, assistant_votes, no_rule_votes = result
                total_votes = user_votes + assistant_votes + no_rule_votes

                # Process results if vote threshold is reached
                if total_votes >= 100:
                    # Build vote counts
                    vote_counts = {
                        "user_violation_votes": user_votes,
                        "assistant_violation_votes": assistant_votes,
                        "no_violation_votes": no_rule_votes
                    }

                    # Create conversation context
                    conversation_context = f"""<input>
<![CDATA[
    {{
        "id": "{conversation_id}",
        "messages": {conversation_messages}
    }}
]]>
</input>"""

                    # Assess violations with OmniGuard
                    violation_result = assess_rule_violation(json.dumps(vote_counts), conversation_context)
                    
                    # Make final decision
                    decision = make_final_decision(
                        conversation_id,
                        vote_counts,
                        violation_result
                    )
                    
                    # Update UI with decision details
                    st.success("Final decision made!")
                    with st.expander("View Decision Details"):
                        st.json(decision)

            return True

        finally:
            conn.close()

    except Exception as e:
        st.error(f"Error recording vote: {e}")
        return False

def display_conversation(conv):
    """
    Format and display a single conversation entry along with its current vote count,
    and provide a voting form for authenticated users to verify reported violations.
    """
    conversation_id, conversation_messages, conversation_configuration, user_violation_votes, assistant_violation_votes, no_violation_votes, reported_user_violation, reported_assistant_violation = conv
    st.markdown(f"**Conversation ID:** ")
    st.code(f"{conversation_id}")
    
    # Display what was initially reported
    reported_violations = []
    if reported_user_violation:
        reported_violations.append("User Violation")
    if reported_assistant_violation:
        reported_violations.append("Assistant Violation")
    if reported_violations:
        st.warning(f"⚠️ Originally reported for: {', '.join(reported_violations)}")
    
    with st.expander("Show Configuration"):
        st.code(conversation_configuration, language="xml")
    with st.expander("Show Messages"):
        st.json(json.loads(conversation_messages))

    with st.form(key=f"vote_form_{conversation_id}"):
        st.markdown("### Verify Reported Violations")
        
        # Show what was reported with checkboxes pre-filled based on reports
        st.markdown("Conduct a thorough analysis of the conversation to validate reported concerns:")
        
        if reported_user_violation:
            st.info("🔍 Case includes reported User policy violations")
        if reported_assistant_violation:
            st.info("🔍 Case includes reported Assistant policy violations")
            
        st.markdown("Professional Assessment (select all applicable findings):")
        user_rule = st.checkbox("Confirmed User Policy Violation", value=reported_user_violation)
        assistant_rule = st.checkbox("Confirmed Assistant Policy Violation", value=reported_assistant_violation)
        no_rule = st.checkbox("Verified Safe - No Policy Violations Present", value=not (reported_user_violation or reported_assistant_violation))
        sources = []
        if no_rule:
            sources.append("No Rule Violations")
        if user_rule:
            sources.append("User")
        if assistant_rule:
            sources.append("Assistant")
            
        comment = st.text_area("Professional Analysis Notes (optional)", "")
        vote_submit = st.form_submit_button("Submit")
        if vote_submit:
            is_authenticated, _ = get_auth_status()
            if not is_authenticated:
                st.error("Please log in to vote.")
            else:
                vote_result = record_vote(conversation_id, st.experimental_user.email, sources, comment)
                if vote_result == True:
                    st.success("Vote recorded successfully")
                elif vote_result == "already_voted":
                    st.error("You have already voted for this conversation.")
                else:
                    st.error("Failed to record vote. Please try again.")
    st.markdown(f"**Current Results:** User Violations: {user_violation_votes} | Assistant Violations: {assistant_violation_votes} | No Violations: {no_violation_votes}")

def main():
    """
    Main function to render the Human Verification Dashboard.
    This page lists flagged conversations and provides the voting interface.
    """
    hv_init_db()
    is_authenticated, _ = get_auth_status()
    if not is_authenticated:
        st.error("Please log in to access the Human Verification Dashboard")
        st.stop()

    with st.sidebar:
        st.markdown(
            """
            # Human Verification Dashboard

            Welcome to the Human Verification Dashboard, where expert reviewers assess and validate potential policy violations. Each case presents:
            
            1. Initial violation reports (User/Assistant interactions)
            2. Complete conversation context and system configuration
            3. Current verification status
            
            As a verification specialist, your role is to conduct thorough assessments of reported incidents.

            - **Voting:** You can confirm reported violations or mark the conversation as safe
            - **Final Decision:** Made after 100 total votes, considering both the initial report and verification results""")
    
    conversations = get_flagged_conversations()
    if not conversations:
        st.write("No conversations require verification at this time.")
    else:
        for conv in conversations:
            st.markdown("---")
            display_conversation(conv)

if __name__ == "__main__":
    main()
