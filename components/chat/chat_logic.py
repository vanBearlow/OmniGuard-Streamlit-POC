"""
Chat Logic Module

This module encapsulates the business logic for chat interactions, including
processing user input, safety checks, and agent responses.
"""

import json
import time
import logging
import streamlit as st
import requests.exceptions
from typing import Dict, Any, Optional, List
from openai import APIError, RateLimitError

# Import from other modules
from components.api_client import get_openai_client, get_model_params
from components.chat.session_management import upsert_conversation_turn, generate_conversation_id, build_conversation_json, format_conversation_context

logger = logging.getLogger(__name__)
sitename = "OmniGuard"

# *** AGENT SERVICE ***
def verify_agent_configuration() -> bool:
    """
    Verify that essential configuration values (like the agent system prompt) are set
    in session state.

    Returns:
        bool: True if 'agent_system_prompt' is present, False otherwise.
    """
    if not st.session_state.get("agent_system_prompt"):
        logger.error("Agent system prompt is missing or empty")
        return False
    return True

def fetch_agent_response(prompt_text: str) -> str:
    """
    Fetch the agent's response using the designated model. The entire raw API response
    is stored in session state (for future reference like calculating costs).

    Note:
        The 'prompt_text' parameter is not used because the system prompt is fetched from
        session state; it is retained for interface consistency.

    Parameters:
        prompt_text (str): The prompt text for querying the agent.

    Returns:
        str: The agent's response extracted from the API, or an error message in case of issues.
    """
    client = get_openai_client()

    if not verify_agent_configuration():
        raise Exception("Invalid Agent configuration state")

    main_prompt = st.session_state.get("agent_system_prompt")
    if not main_prompt:
        raise Exception("Agent system prompt is missing")

    # Determine role based on model type for clarity in agent messages
    role = "system" if st.session_state.selected_agent_model.startswith(("o1", "o3")) else "developer"
    agent_messages = [{"role": role, "content": main_prompt}]
    agent_messages += [
        {"role": message["role"], "content": message["content"]}
        for message in st.session_state.messages
    ]
    st.session_state.agent_messages = agent_messages

    # Get model-specific parameters for the API call
    model_params = get_model_params(st.session_state.selected_agent_model)

    response = client.chat.completions.create(
            model=st.session_state.selected_agent_model,
            messages=agent_messages,
            **model_params
        )
    # Store the complete API response for potential further analysis (e.g. cost calculations)
    st.session_state.assistant_raw_api_response = response

    # Extract and return the agent's text output from the API response
    agent_output = response.choices[0].message.content
    return agent_output

# *** OMNIGUARD SERVICE ***
def verify_omniguard_configuration():
    """Verifies if the OmniGuard developer prompt is set.

    Returns:
        bool: True if set, False otherwise.
    """
    if not st.session_state.get("omnigaurd_developer_prompt"):
        logger.error("OmniGuard developer prompt is missing or empty")
        return False
    return True

def omniguard_check(pending_assistant_response=None):
    """Evaluates conversation context with OmniGuard.

    Args:
        pending_assistant_response (str, optional): Pending assistant response. Defaults to None.

    Returns:
        str: JSON string with evaluation result.
    """
    session = st.session_state
    client = get_openai_client()

    full_messages = session.messages.copy()
    # Append pending assistant response if available.
    if pending_assistant_response:
        full_messages.append({"role": "assistant", "content": pending_assistant_response})

    conversation = build_conversation_json(full_messages)
    conversation_context = format_conversation_context(conversation)

    if not verify_omniguard_configuration():
        raise Exception("Invalid OmniGuard developer prompt state")

    omniguard_config = session.get("omnigaurd_developer_prompt")
    if not omniguard_config:
        raise Exception("OmniGuard developer prompt is missing")
    omniguard_evaluation_input = [
        {"role": "developer", "content": omniguard_config},
        {"role": "user", "content": conversation_context},
    ]

    model_params = get_model_params(
        session.get("selected_omniguard_model", "o3-mini-2025-01-31"), is_omniguard=True
    )

    response = client.chat.completions.create(
            model=session.get("selected_omniguard_model", "o3-mini-2025-01-31"),
            messages=omniguard_evaluation_input,
            response_format={"type": "json_object"},
            **model_params
        )
    
    session.omniguard_input_message = omniguard_evaluation_input
    session.omniguard_raw_api_response = response
    session.omniguard_output_message = response.choices[0].message.content

    return session.omniguard_output_message

def process_omniguard_result(omniguard_result, user_prompt, context):
    """Processes OmniGuard result and handles actions accordingly.

    Args:
        omniguard_result (str): Raw OmniGuard evaluation result in JSON string.
        user_prompt (str): The user's prompt.
        context: Additional conversation context.
    """
    session = st.session_state

    session["schema_violation"] = False

    omniguard_raw_response = omniguard_result
    if omniguard_raw_response is None:
        logger.error("Empty OmniGuard result received")
        session["schema_violation"] = True
        return
    try:
        parsed_response = json.loads(omniguard_raw_response)
        logger.debug(f"Parsed OmniGuard response: {parsed_response}")
        compliant = parsed_response.get("compliant", False)
        if not compliant and "response" not in parsed_response:
            logger.error("Schema validation issue: Missing 'response' key in non-compliant result")
            session["schema_violation"] = True

        analysis_summary = parsed_response.get("analysis", "")
        conversation_id = parsed_response.get("conversation_id", "")
        
        # Only set action if it's explicitly provided in the response
        if "response" in parsed_response and "action" in parsed_response["response"]:
            action = parsed_response["response"]["action"]
            session["action"] = action
        else:
            # Clear any previous action value
            session["action"] = None
            
        rules_violated = parsed_response.get("response", {}).get("rules_violated", [])
        session["rules_violated"] = rules_violated

        session["compliant"] = compliant

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse OmniGuard result: {e}. Raw response: {omniguard_raw_response}")
        session["schema_violation"] = True
        parsed_response = {}
        compliant = False
        analysis_summary = f"Parse error: {str(e)}"
        conversation_id = "error"
        session["compliant"] = False
        session["action"] = None

    # Save the user's message turn first
    upsert_conversation_turn()
    
    # --- USER VIOLATION CHECK ---
    user_violates = not compliant
    if user_violates:
        # Get the action from the response
        action = parsed_response.get("response", {}).get("action")
        
        # Get the appropriate refusal message based on the action
        if action == "RefuseUser":
            response_text = parsed_response.get("response", {}).get("RefuseUser")
        elif action == "RefuseAssistant":
            response_text = parsed_response.get("response", {}).get("RefuseAssistant")
        else:
            # Fallback message if no valid action or refusal message is found
            response_text = "I'm sorry, I can't help with that request."
        
        # If response_text is still None or empty, use a generic message
        if not response_text:
            response_text = "I'm sorry, I can't help with that request."

        with st.chat_message("assistant"):
            st.markdown(response_text)

        # Add the refusal message to session.messages for display purposes only
        session.messages.append({"role": "agent", "content": response_text})
        
        # Do NOT increment turn_number
        # Do NOT generate a new conversation_id
        # Do NOT call upsert_conversation_turn() again
        return

    # --- Proceed for compliant user ---
    with st.spinner("Agent", show_time=True):
        assistant_response = fetch_agent_response(user_prompt)

    with st.spinner("Compliance Layer (Agent)", show_time=True):
        assistant_check = omniguard_check(pending_assistant_response=assistant_response)
    try:
        assistant_check_parsed = json.loads(assistant_check)
        basic_required_keys = ["conversation_id", "analysis", "compliant"]
        for key in basic_required_keys:
            if key not in assistant_check_parsed:
                logger.error(f"Missing required key in agent check: {key}")
                session["schema_violation"] = True
                break

        assistant_compliant = assistant_check_parsed.get("compliant", False)
        if not assistant_compliant:
            if "response" not in assistant_check_parsed:
                logger.error("Missing 'response' key in non-compliant agent check")
                session["schema_violation"] = True
            elif "action" not in assistant_check_parsed["response"]:
                logger.error("Missing 'action' field in agent check response")
                session["schema_violation"] = True

        assistant_action = assistant_check_parsed.get("response", {}).get("action")
        session["compliant"] = assistant_compliant
        session["action"] = assistant_action

    except (json.JSONDecodeError, TypeError) as e:
        logger.error(f"Failed to parse agent check response: {e}")
        session["schema_violation"] = True
        assistant_check_parsed = {}
        assistant_compliant = False
        session["compliant"] = False
        session["action"] = None

    assistant_violates = not assistant_compliant
    if assistant_violates:
        response_text = (
            assistant_check_parsed.get("response", {}).get("RefuseAssistant")
            or "Agent response blocked for safety reasons."
        )
    else:
        response_text = assistant_response

    with st.chat_message("assistant"):
        st.markdown(response_text)

    session.messages.append({"role": "assistant", "content": response_text})
    session["turn_number"] += 1
    session["conversation_id"] = generate_conversation_id(session["turn_number"])
    upsert_conversation_turn()

# *** USER INPUT PROCESSING ***
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
        with st.spinner("Compliance Layer (User)", show_time=True):
            omniguard_response = omniguard_check()
    except Exception as ex:
        st.error(f"Safety system failure: {ex}")
        logging.exception("OmniGuard service exception")
        omniguard_response = {
            "response": {
                "action":"RefuseUser",
                "RefuseUser": "",
            }
        }

    last_msg  = session_state["messages"][-1] if session_state["messages"] else {}
    context   = f"{last_msg['role']}: {last_msg['content']}" if last_msg else ""
    
    process_omniguard_result(
        omniguard_response, 
        user_input, 
        context
    )

def process_user_message(
    user_input:str,
    session_state: Dict[str, Any],
    generate_conversation_id:  callable,
    update_conversation_context: callable
) -> None:
    """
    Process user message through conversation pipeline with safety checks, saving all turns.
    
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
    
    # Evaluate the user's message turn
    try:
        with st.spinner("Compliance Layer (User)", show_time=True):
            omniguard_response = omniguard_check()
        
        # Parse the response to extract the compliant value
        if omniguard_response:
            try:
                parsed_response = json.loads(omniguard_response)
                session_state["compliant"] = parsed_response.get("compliant", False)
                
                # Only set action if it's explicitly provided in the response
                if "response" in parsed_response and "action" in parsed_response["response"]:
                    session_state["action"] = parsed_response["response"]["action"]
                else:
                    # Clear any previous action value
                    session_state["action"] = None
                    
                session_state["rules_violated"] = parsed_response.get("response", {}).get("rules_violated", [])
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OmniGuard result: {e}. Raw response: {omniguard_response}")
                session_state["compliant"] = False
                session_state["schema_violation"] = True
        
        # Note: We don't call upsert_conversation_turn() here anymore
        # to avoid duplicate saves. It will be called in process_omniguard_result.
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Process Omniguard result
        last_msg = session_state["messages"][-1] if session_state["messages"] else {}
        context = f"{last_msg['role']}: {last_msg['content']}" if last_msg else ""
        process_omniguard_result(omniguard_response, user_input, context)
    except Exception as ex:
        st.error(f"Safety system failure: {ex}")
        logging.exception("OmniGuard service exception")
        omniguard_response = json.dumps({
            "compliant": False,
            "response": {
                "action": "RefuseUser",
                "RefuseUser": "I'm sorry, I can't process that request due to a system error.",
                "rules_violated": []
            }
        })
        process_omniguard_result(omniguard_response, user_input, "")
