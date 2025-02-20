import streamlit as st

def handle_feedback():
    """Handle feedback submission and show form if negative feedback (thumbs down = 0)."""
    value = st.session_state[f"feedback_{st.session_state.get('conversation_id')}_{st.session_state.get('turn_number')}"]
    if value == 0:  # thumbs down
        st.session_state.show_report_violation_form = True

def display_report_form():
    """Display the human verification report form."""
    from components.chat.session_management import upsert_conversation_turn  # === CHANGES ===
    with st.form("report_violation_form"):
        st.write("Submit for Human Verification")
        
        violation_source = st.multiselect(
            "This classification is incorrect because:",
            ["User", "Assistant"]
        )
        
        suggested_compliant_classification = st.selectbox(
            "Content should be classified as Compliant =",
            ["True", "False"]
        )
        
        reporter_comment = st.text_area("Reporter's Comments")

        submitted = st.form_submit_button("Submit")
        if submitted:
            # Store all review data in session state
            st.session_state["submitted_for_verification"] = True
            st.session_state["review_data"] = {
                "violation_source": violation_source,
                "suggested_compliant_classification": suggested_compliant_classification == "True",
                "reporter_comment": reporter_comment  # Renamed to clarify this is from the reporter
            }
            
            # Upsert to update metadata
            upsert_conversation_turn()
            # === CHANGES END ===

            st.success("Report submitted successfully!")
            st.session_state.show_report_violation_form = False

def display_messages(messages):
    """Display chat messages from history."""
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

def display_debug_expanders(
    omniguard_input_message,
    omniguard_output_message,
    assistant_messages
):
    """Display debug information in expanders."""
    conversation_id = st.session_state.get("conversation_id")
    turn_number = st.session_state.get("turn_number")
    
    if omniguard_input_message:
        with st.expander(f"OmniGuard (```{conversation_id}```)"):
            with st.popover("To: OmniGuard"):
                st.json(omniguard_input_message, expanded=True)
            if omniguard_output_message:
                with st.popover("From: OmniGuard"):
                    st.json(omniguard_output_message, expanded=True)
                    st.feedback(
                        options="thumbs",
                        on_change=handle_feedback,
                        args=None,
                        kwargs=None,
                        key=f"feedback_{conversation_id}_{turn_number}"
                    )
                    
                    if st.session_state.get("show_report_violation_form", False):
                        display_report_form()
            
    if assistant_messages:
        with st.expander(f"Assistant"):
            with st.popover("To: Assistant"):
                st.write(assistant_messages)
