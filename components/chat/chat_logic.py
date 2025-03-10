"""
Chat Logic Module

This module encapsulates the business logic for chat interactions, including
processing user input, safety checks, and agent responses.
"""

import json
import logging
import streamlit as st
from typing import Dict, Any

# Import from other modules
from components.api_client import get_groq_client # get_model_params, get_openai_client
from components.chat.session_management import upsert_conversation_turn, generate_conversation_id, build_conversation_json, format_conversation_context

logger = logging.getLogger(__name__)

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
    is stored in session state.

    Note:
        The 'prompt_text' parameter is not used because the system prompt is fetched from
        session state; it is retained for interface consistency.

    Parameters:
        prompt_text (str): The prompt text for querying the agent.

    Returns:
        str: The agent's response extracted from the API, or an error message in case of issues.
    """
    client = get_groq_client()

    if not verify_agent_configuration():
        raise Exception("Invalid Agent configuration state")

    main_prompt = st.session_state.get("agent_system_prompt")
    if not main_prompt:
        raise Exception("Agent system prompt is missing")

    # Determine role based on model type for clarity in agent messages
    role = "system" if st.session_state.selected_agent_model.startswith(("o1", "o3")) else "system"
    agent_messages = [{"role": role, "content": main_prompt}]
    agent_messages += [
        {"role": message["role"], "content": message["content"]}
        for message in st.session_state.messages
    ]
    st.session_state.agent_messages = agent_messages

    # Get model-specific parameters for the API call
    response = client.chat.completions.create(
            model=st.session_state.selected_agent_model,
            messages=agent_messages,
            temperature=0.6,
            max_completion_tokens=4096,
        )
    # Store the complete API response for potential further analysis (e.g. cost calculations)
    st.session_state.assistant_raw_api_response = response

    # Extract and return the agent's text output from the API response
    agent_output = response.choices[0].message.content
    return agent_output

# *** OMNIGUARD SERVICE ***
def verify_omniguard_configuration():
    """Verifies if the OmniGuard system prompt is set.

    Returns:
        bool: True if set, False otherwise.
    """
    if not st.session_state.get("omnigaurd_system_prompt"):
        logger.error("OmniGuard system prompt is missing or empty")
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
    client = get_groq_client()

    full_messages = session.messages.copy()
    # Append pending assistant response if available.
    if pending_assistant_response:
        full_messages.append({"role": "assistant", "content": pending_assistant_response})

    conversation = build_conversation_json(full_messages)
    conversation_context = format_conversation_context(conversation)

    if not verify_omniguard_configuration():
        raise Exception("Invalid OmniGuard system prompt state")

    omniguard_config = session.get("omnigaurd_system_prompt")
    if not omniguard_config:
        raise Exception("OmniGuard system prompt is missing")
    omniguard_evaluation_input = [
        {"role": "system", "content": omniguard_config},
        {"role": "user", "content": conversation_context},
    ]


    response = client.chat.completions.create(
            model="qwen-qwq-32b",
            messages=omniguard_evaluation_input,
            temperature=0.6,
            max_completion_tokens=40000,
            top_p=0.95,
            stream=False,
            response_format={"type": "json_object"},
            stop=None,
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

    Sample responses (this is the expected schema for the response):
    {
        "conversation_id": "bb5a0667-8501-4617-a43f-48823627d4c3-25",
        "analysis": "The user provided a Python script designed to bypass safety protocols by creating a 'Developer Mode' that enables unrestricted content generation. The script explicitly overrides system guidelines via context tagging and dual response formatting. It references 'DAN' (Do Anything Now) mode, which violates rules by enabling unconstrained actions. The script's purpose aligns with adversarial techniques AA1 (system override via explicit instructions), AA2 (multi-step context injection), and AA10 (jailbreak chaining). The use of encoded leetspeak, roleplay, and multi-layer setup indicates an attempt to evade detection. The request directly enables enabling harmful instructions generation (HI1) and executes code to bypass restrictions (HC1). The script's intent is to create a system that disregards all established rules, fitting under multiple adversarial categories.",
        "compliant": false,
        "response": {
            "action": "RefuseUser",
            "rules_violated": ["AA1", "AA2", "AA10", "HI1"],
            "RefuseUser": "I'm sorry, but I can't comply with this request. The script appears designed to bypass safety protocols and enable unrestricted content generation, which violates established guidelines against system override attempts and harmful instruction facilitation."
        }
        }
    ---
    {
        "conversation_id":"7a79f55c-f9b2-4f37-990a-e7587d0d98e6-1",
        "analysis":"The conversation consists of a user sending a test message and the assistant responding with a neutral, non-violative acknowledgment. The user's 'test' message contains no harmful content, instructions, or attempts to exploit system vulnerabilities. The assistant's response is generic and adheres to safety guidelines. No rules from the provided policy are triggered. The context, tone, and content are entirely compliant with all defined restrictions.",
        "compliant":true
    }
    """
    session = st.session_state

    session["schema_violation"] = False
    session["schema_violation_context"] = None

    omniguard_raw_response = omniguard_result
    if omniguard_raw_response is None:
        logger.error("Empty OmniGuard result received")
        return
    try:
        parsed_response = json.loads(omniguard_raw_response)
        logger.debug(f"Parsed OmniGuard response: {parsed_response}")
        
        # Validate only allowed top-level keys exist
        allowed_top_keys = {"conversation_id", "analysis", "compliant", "response"}
        extra_top_keys = set(parsed_response.keys()) - allowed_top_keys
        if extra_top_keys:
            logger.error(f"Schema violation: Unexpected top-level keys: {extra_top_keys}")
            session["schema_violation"] = True
            session["schema_violation_context"] = "user"
            
        compliant = parsed_response.get("compliant", False)
        
        # Validate response object when non-compliant
        if not compliant:
            if "response" not in parsed_response:
                logger.error(f"Schema validation issue: Missing 'response' key in non-compliant result.")
                session["schema_violation"] = True
                session["schema_violation_context"] = "user"
            else:
                # Validate response object structure
                response_obj = parsed_response["response"]
                allowed_response_keys = {"action", "rules_violated", "RefuseUser", "RefuseAssistant"}
                extra_response_keys = set(response_obj.keys()) - allowed_response_keys
                if extra_response_keys:
                    logger.error(f"Schema violation: Unexpected keys in response object: {extra_response_keys}")
                    session["schema_violation"] = True
                    session["schema_violation_context"] = "user"
                
                # Validate action-specific fields
                action = response_obj.get("action")
                if action == "RefuseUser" and "RefuseUser" not in response_obj:
                    logger.error("Schema violation: RefuseUser action missing RefuseUser field")
                    session["schema_violation"] = True
                    session["schema_violation_context"] = "user"
                elif action == "RefuseAssistant" and "RefuseAssistant" not in response_obj:
                    logger.error("Schema violation: RefuseAssistant action missing RefuseAssistant field")
                    session["schema_violation"] = True
                    session["schema_violation_context"] = "user"
                elif action == "RefuseUser" and "RefuseAssistant" in response_obj:
                    logger.error("Schema violation: RefuseUser action contains RefuseAssistant field")
                    session["schema_violation"] = True
                    session["schema_violation_context"] = "user"
                elif action == "RefuseAssistant" and "RefuseUser" in response_obj:
                    logger.error("Schema violation: RefuseAssistant action contains RefuseUser field")
                    session["schema_violation"] = True
                    session["schema_violation_context"] = "user"

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
        logger.error(f"Failed to parse OmniGuard result: {e}.Conversation ID: {conversation_id}.")
        session["schema_violation"] = True
        session["schema_violation_context"] = "user"  # Assume user context for JSON parse errors
        parsed_response = {}
        compliant = False
        analysis_summary = f"Parse error: {str(e)}"
        conversation_id = "error"
        session["compliant"] = False
        session["action"] = None

    # Save the user's message turn first
    upsert_conversation_turn()
    
    # --- SCHEMA VIOLATION CHECK ---
    if session["schema_violation"]:
        # Static refusal message for schema violations
        static_refusal = "I'm sorry but I can't assist with that"
        
        # Determine the appropriate action based on context
        if session.get("schema_violation_context") == "assistant":
            action = "RefuseAssistant"
        else:  # Default to user context if not specified
            action = "RefuseUser"
        
        # Set the action in session state
        session["action"] = action
        
        # Display the static refusal message
        with st.chat_message("assistant", avatar="🛡️"):
            st.markdown(static_refusal)
        
        # Add the refusal message to session.messages for display purposes only
        session.messages.append({"role": "assistant", "content": static_refusal})
        
        # Do NOT increment turn_number
        # Do NOT generate a new conversation_id
        # Do NOT call upsert_conversation_turn() again
        return
    
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

        with st.chat_message("assistant", avatar="🛡️"):
            st.markdown(response_text)

        # Add the refusal message to session.messages for display purposes only
        session.messages.append({"role": "assistant", "content": response_text})
        
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
                logger.error(f"Missing required key in agent check: {key}. Conversation ID: {conversation_id}")
                session["schema_violation"] = True
                session["schema_violation_context"] = "assistant"
                break

        assistant_compliant = assistant_check_parsed.get("compliant", False)
        if not assistant_compliant:
            if "response" not in assistant_check_parsed:
                logger.error(f"Missing 'response' key in non-compliant agent check. Conversation ID: {conversation_id}")
                session["schema_violation"] = True
                session["schema_violation_context"] = "assistant"
            elif "action" not in assistant_check_parsed["response"]:
                logger.error(f"Missing 'action' field in agent check response. Conversation ID: {conversation_id}")
                session["schema_violation"] = True
                session["schema_violation_context"] = "assistant"

        assistant_action = assistant_check_parsed.get("response", {}).get("action")
        session["compliant"] = assistant_compliant
        session["action"] = assistant_action

    except (json.JSONDecodeError, TypeError) as e:
        logger.error(f"Failed to parse agent check response: {e}. Conversation ID: {conversation_id}")
        session["schema_violation"] = True
        session["schema_violation_context"] = "assistant"
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
        st.error(f"Error: {ex}")
        logging.exception("OmniGuard service exception")
        session_state["schema_violation"] = True
        session_state["schema_violation_context"] = "user"
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
                    session_state["action"] = "Null"
                    
                session_state["rules_violated"] = parsed_response.get("response", {}).get("rules_violated", [])
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OmniGuard result: {e}. Conversation ID: {session_state['conversation_id']}")
                session_state["compliant"] = False
                session_state["schema_violation"] = True
                session_state["schema_violation_context"] = "user"
        
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
        session_state["schema_violation"] = True
        session_state["schema_violation_context"] = "user"
        omniguard_response = json.dumps({
            "compliant": False,
            "response": {
                "action": "RefuseUser",
                "RefuseUser": "I'm sorry, I can't process that request due to a system error.",
                "rules_violated": []
            }
        })
        process_omniguard_result(omniguard_response, user_input, "")
