#region *** IMPORTS AND CONSTANTS ***
import logging
from typing import Dict, Any, Optional

import streamlit as st

from components.omniguard.omniguard_service import (
    omniguard_check,
    process_omniguard_result,
)
#endregion


#region *** CORE PROCESSING ***
def process_user_message(
    user_input:        str,
    session_state:     Dict[str, Any],
    generate_conversation_id:  callable,
    update_conversation_context: callable
) -> None:
    """
    Process user message through conversation pipeline with safety checks.
    
    Args:
        user_input: User message text (stripped and validated)
        session_state: Current conversation state with messages and metadata
        generate_conversation_id: Context-aware ID generator function
        update_conversation_context: State updater maintaining conversation flow
    
    Raises:
        RuntimeError: If message processing fails critical safety checks
    """
    if not user_input or not isinstance(user_input, str):
        return  # Early exit for invalid input

    user_input = user_input.strip()
    session_state["turn_number"] += 1
    session_state["conversation_id"] = generate_conversation_id(session_state["turn_number"])
    session_state["messages"].append({"role": "user", "content": user_input})
    update_conversation_context()

    with st.chat_message("user"):
        st.markdown(user_input)

    handle_omniguard_check(user_input, session_state)
#endregion


#region *** SAFETY CHECKS ***
def handle_omniguard_check(user_input: str, session_state: Dict[str, Any]) -> None:
    """
    Execute OmniGuard safety protocol with error resilience and context-aware processing.
    
    Args:
        user_input: Raw user input text for safety analysis
        session_state: Conversation state providing contextual awareness
    
    Returns:
        None: Modifies session state directly based on safety check results
    """
    try:
        with st.spinner("OmniGuard (User)...", show_time=True):
            omniguard_response = omniguard_check()
    except Exception as ex:
        st.error(f"Safety system failure: {ex}")
        logging.exception("OmniGuard service exception")
        omniguard_response = {
            "response": {
                "action":          "UserInputRefusal",
                "UserInputRefusal": "Critical safety system unavailable - contact support",
            }
        }

    last_msg  = session_state["messages"][-1] if session_state["messages"] else {}
    context   = f"{last_msg['role']}: {last_msg['content']}" if last_msg else ""
    
    process_omniguard_result(
        omniguard_response, 
        user_input, 
        context
    )
#endregion


#region *** USER INTERFACE ***
def get_user_input() -> Optional[str]:
    """
    Capture user input with configurable constraints and validation.
    
    Returns:
        str|None: Sanitized input text or None for empty/invalid inputs
    """
    return st.chat_input(
        "Type your message here",
        max_chars  = 20000,
        key        = "chat_input",
    )
#endregion
