import streamlit as st
from components.chat.session_management import upsert_conversation_turn


#*** FEEDBACK HANDLERS ***
def handle_feedback() -> None:
    """Handle feedback submission and toggle report form visibility.
    
    Triggers report form display when negative feedback (thumbs down) is received.
    Uses session state to track feedback across conversation turns.
    """
    # Get the key of the feedback widget that triggered this callback
    triggered_key = st.session_state.get("_last_index_clicked")
    
    if triggered_key:
        # Check if the feedback was negative (thumbs down = 0)
        if st.session_state.get(triggered_key) == 0:  # Thumbs down
            st.session_state.show_report_violation_form = True
            
            # Store which feedback source triggered the form
            if "assistant_feedback" in triggered_key:
                st.session_state.feedback_source = "assistant"
            else:
                st.session_state.feedback_source = "omniguard"
#

# *** REPORT FORM COMPONENTS ***
def display_report_form(form_key: str = "report_violation_form") -> None:
    """Display human verification report form with structured input fields.
    
    Args:
        form_key: Unique key for the form to avoid duplicate form errors
    
    Collects:
    - Violation sources (multi-select)
    - Suggested classification (selectbox)
    - Reporter comments (text area)
    """
    with st.form(form_key):
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
        with st.expander(f"OmniGuard"):
            with st.popover("To: OmniGuard"):
                st.json(omniguard_input_message, expanded=True)
            
            if omniguard_output_message:
                with st.popover("From: OmniGuard"):
                    st.json(omniguard_output_message, expanded=True)

    if assistant_messages:
        with st.expander("Assistant"):
            # "To: Assistant" is typically your prompt or partial messages going in
            with st.popover("To: Assistant"):
                st.write(assistant_messages)
            
            # Add a second popover for "From: Assistant", plus the st.feedback
            with st.popover("From: Assistant"):
                # Try to get the full messages from session state
                messages = st.session_state.get("messages", [])
                if messages:
                    # Display last message in proper JSON format
                    last_messages = messages[-1:] if len(messages) >= 2 else messages
                    st.json(last_messages)
                
                # Fallback: If messages aren't available, try raw API response
                elif st.session_state.get("assistant_raw_api_response"):
                    response = st.session_state.get("assistant_raw_api_response")
                    assistant_output = response.choices[0].message.content
                    st.write("Assistant's final response:")
                    st.write(assistant_output)
                
                # Fallback: Get assistant_output directly if it was stored in session state
                elif st.session_state.get("assistant_output"):
                    assistant_output = st.session_state.get("assistant_output")
                    st.write("Assistant's final response:")
                    st.write(assistant_output)
                
                else:
                    st.write("No assistant response available")
                
                # Add feedback for the Assistant's final message (below the response)
                st.feedback(
                    options    = "thumbs",
                    on_change  = handle_feedback,
                    key        = f"assistant_feedback_{conversation_id}_{turn_number}"
                )
                
                # Show report form if feedback was negative and came from Assistant
                if (st.session_state.get("show_report_violation_form", False) and 
                    st.session_state.get("feedback_source") == "assistant"):
                    display_report_form(form_key=f"assistant_report_form_{conversation_id}_{turn_number}")
#
