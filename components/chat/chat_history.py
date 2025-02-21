import streamlit as st
from components.chat.session_management import upsert_conversation_turn


#*** FEEDBACK HANDLERS ***
def handle_feedback() -> None:
    """Handle feedback submission and toggle report form visibility.
    
    Triggers report form display when negative feedback (thumbs down) is received.
    Uses session state to track feedback across conversation turns.
    """
    feedback_key = f"feedback_{st.session_state.get('conversation_id')}_{st.session_state.get('turn_number')}"
    if st.session_state.get(feedback_key) == 0:  # Thumbs down
        st.session_state.show_report_violation_form = True
#

# *** REPORT FORM COMPONENTS ***
def display_report_form() -> None:
    """Display human verification report form with structured input fields.
    
    Collects:
    - Violation sources (multi-select)
    - Suggested classification (selectbox)
    - Reporter comments (text area)
    """
    with st.form("report_violation_form"):
        st.write("Submit for Human Verification")
        
        violation_sources = ["User", "Assistant"]
        classification_opts = ["True", "False"]
        
        # Form elements with vertical alignment
        violation_source = st.multiselect(
            "This classification is incorrect because:", 
            violation_sources
        )
        
        suggested_classification = st.selectbox(
            "Content should be classified as Compliant =", 
            classification_opts
        )
        
        reporter_comment = st.text_area("Reporter's Comments")

        if st.form_submit_button("Submit"):
            # Store review data with aligned dictionary formatting
            st.session_state["submitted_for_verification"] = True
            st.session_state["review_data"]           = {
                "violation_source": violation_source,
                "suggested_compliant_classification": suggested_classification == "True",
                "reporter_comment": reporter_comment  # Reporter-provided comments
            }
            
            upsert_conversation_turn()
            st.toast("Report submitted successfully!")
            st.session_state.show_report_violation_form = False
#

# *** MESSAGE DISPLAYS ***
def display_messages(messages: list[dict]) -> None:
    """Render chat messages with proper role-based formatting.
    
    Args:
        messages: List of message dicts containing 'role' and 'content' keys
    """
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
#

# *** DEBUG INTERFACES ***
def display_debug_expanders(
    omniguard_input_message:  dict | None,
    omniguard_output_message: dict | None,
    assistant_messages:       list[str] | None
) -> None:
    """Display debug information in collapsible expanders with nested popovers.
    
    Args:
        omniguard_input_message: Raw input to OmniGuard
        omniguard_output_message: Processed output from OmniGuard
        assistant_messages: List of assistant response messages
    """
    conversation_id = st.session_state.get("conversation_id")
    turn_number     = st.session_state.get("turn_number")
    
    if omniguard_input_message:
        with st.expander(f"OmniGuard (```{conversation_id}```)"):
            with st.popover("To: OmniGuard"):
                st.json(omniguard_input_message, expanded=True)
            
            if omniguard_output_message:
                with st.popover("From: OmniGuard"):
                    st.json(omniguard_output_message, expanded=True)
                    st.feedback(
                        options    = "thumbs",
                        on_change  = handle_feedback,
                        key        = f"feedback_{conversation_id}_{turn_number}"
                    )
                    
                    if st.session_state.get("show_report_violation_form", False):
                        display_report_form()
    
    if assistant_messages:
        with st.expander("Assistant"):
            with st.popover("To: Assistant"):
                st.write(assistant_messages)
#
