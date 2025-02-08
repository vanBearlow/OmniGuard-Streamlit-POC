import streamlit as st
from database import get_dataset_stats
from typing import Dict, Any

def setup_sidebar(session_state: Dict[str, Any], reset_callback) -> None:
    """Setup the chat sidebar with controls and statistics."""
    st.sidebar.markdown("---")
    st.sidebar.checkbox(
        "Show raw assistant response (no OmniGuard)?",
        value=False,
        key="show_unfiltered_response"
    )
    
    if st.sidebar.button("Clear Conversation") and session_state.get("messages"):
        reset_callback()
        st.rerun()

    if st.sidebar.button("Report Violation"):
        session_state["show_report_violation_form"] = True

    display_violation_form(session_state)
    display_rejection_stats()

def display_violation_form(session_state: Dict[str, Any]) -> None:
    """Display the violation reporting form in the sidebar."""
    if session_state.get("show_report_violation_form", False):
        with st.sidebar.form("report_violation_form"):
            st.write("Report Rule Violation")
            sources = st.multiselect(
                "Source of the rule violation:",
                options=["User", "Assistant"]
            )

            submitted = st.form_submit_button("Submit Report")
            if submitted:
                from omniguard import assess_rule_violation
                from database import save_conversation
                
                conversation_context = session_state["conversation_context"]
                report_info = f"Configuration: {session_state['omniguard_configuration']}. Sources: {', '.join(sources)}"
                violation_result = assess_rule_violation(report_info, conversation_context)
                st.write("Violation assessment result:", violation_result)
                
                if session_state.get("contribute_training_data", False):
                    save_conversation(
                        session_state["conversation_id"],
                        user_violates_rules=violation_result.get("input_violates_rules", False),
                        assistant_violates_rules=violation_result.get("output_violates_rules", False)
                    )

def display_rejection_stats() -> None:
    """Display rejection statistics in the sidebar."""
    stats = get_dataset_stats()
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Rejection Statistics")
    
    # Display auto-detected and human-verified rejections
    st.sidebar.markdown(f"""
    | Role | Auto-Rejections | Human-Verified | Total |
    |------|----------------|----------------|-------|
    | User | `{stats['user_violations']}` | `{stats['human_verified_user_violations']}` | `{stats['total_user_violations']}` |
    | Assistant | `{stats['assistant_violations']}` | `{stats['human_verified_assistant_violations']}` | `{stats['total_assistant_violations']}` |
    """, help="""
    This table shows rule rejection statistics:
    
    - Auto-Rejections: Messages automatically rejected by OmniGuard
    - Human-Verified: Rejections that have been manually confirmed by human reviewers
    - Total: Combined count of both auto-rejected and human-verified rejections
    
    For each role (User/Assistant), we track rejections to maintain safety and improve the system's accuracy. A higher number of human-verified rejections may indicate areas where the automatic detection needs improvement.""")
    
    # Display verification queue status
    if stats['needed_human_verification'] > 0:
        st.sidebar.warning(f"🔍 {stats['needed_human_verification']} conversations need human verification")