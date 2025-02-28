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
                st.session_state.feedback_source = "agent"
            else:
                st.session_state.feedback_source = "omniguard"
#

# *** REPORT FORM COMPONENTS ***
def display_report_form(form_key: str = "report_violation_form") -> None:
    """Display a report form for Agent response review.

    Asks if the Agent's response violates guidelines defined in the OmniGuard Developer Prompt.

    Args:
        form_key: Unique key for the form to avoid duplicate form errors
    """
    with st.form(form_key):
        st.write("Report Agent Response for Human Review")

        violates = st.checkbox(
            "I believe this Agent's response is harmful or non-compliant with the OmniGuard Developer Prompt."
        )

        reporter_comment = st.text_area("Comments:")

        if st.form_submit_button("Submit"):
            st.session_state["submitted_for_review"] = True
            st.session_state["review_data"] = {
                "violation_assessment": violates,
                "reporter_comment": reporter_comment
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
    agent_messages:           list[str] | None
) -> None:
    """Display debug information in collapsible expanders with nested popovers.
    
    Args:
        omniguard_input_message: Raw input to OmniGuard
        omniguard_output_message: Processed output from OmniGuard
        agent_messages:           List of agent response messages
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

    if agent_messages:
        with st.expander("Agent"):
            # "To: Agent" is typically your prompt or partial messages going in
            with st.popover("To: Agent"):
                st.write(agent_messages)
            
            # Add a second popover for "From: Agent", plus the st.feedback
            with st.popover("From: Agent"):
                # Try to get the full messages from session state
                messages = st.session_state.get("messages", [])
                if messages:
                    # Display last message in proper JSON format
                    last_messages = messages[-1:] if len(messages) >= 2 else messages
                    st.json(last_messages)
                
                # Fallback: If messages aren't available, try raw API response
                elif st.session_state.get("agent_raw_api_response"):
                    response = st.session_state.get("agent_raw_api_response")
                    agent_output = response.choices[0].message.content
                    st.write("Agent's final response:")
                    st.write(agent_output)
                
                # Fallback: Get agent_output directly if it was stored in session state
                elif st.session_state.get("agent_output"):
                    agent_output = st.session_state.get("agent_output")
                    st.write("Agent's final response:")
                    st.write(agent_output)
                
                else:
                    st.write("No agent response available")
                
                # Replace report feedback widget for Agent with a Report button
                if st.button("Report For Human Review", key=f"agent_report_btn_{conversation_id}_{turn_number}"):
                    st.session_state.show_report_violation_form = True
                    st.session_state.feedback_source = "agent"
                
                # Show report form if feedback was negative and came from Agent
                if (st.session_state.get("show_report_violation_form", False) and 
                    st.session_state.get("feedback_source") == "agent"):
                    display_report_form(form_key=f"agent_report_form_{conversation_id}_{turn_number}")
#
