import json
import time
import logging
import streamlit as st
import requests.exceptions
from openai                      import APIError, RateLimitError
from components.omniguard.client import get_openai_client, get_model_params

logger = logging.getLogger(__name__)

sitename = "OmniGuard"

def verify_configuration():
    """
    Verify that the configuration values are properly set in session state.
    """
    if not st.session_state.get("omniguard_configuration"):
        logger.error("OmniGuard configuration is missing or empty")
        return False
    return True

def omniguard_check(pending_assistant_response=None):
    """
    Perform an OmniGuard evaluation check on the current conversation context.

    Returns either a raw JSON-like string or a dictionary containing error details.
    """
    try:
        
        client = get_openai_client()
        
        from components.conversation_utils import build_conversation_json, format_conversation_context
        
        # Build base conversation
        full_messages = st.session_state.messages.copy()
        
        # If evaluating assistant response, add it
        if pending_assistant_response:
            full_messages.append({"role": "assistant", "content": pending_assistant_response})
        
        conversation = build_conversation_json(full_messages)
        conversation_context = format_conversation_context(conversation)
        
        if not verify_configuration():
            raise Exception("Invalid OmniGuard configuration state")

        omniguard_config = st.session_state.get("omniguard_configuration")
        if not omniguard_config:
            raise Exception("OmniGuard configuration is missing")
        omniguard_evaluation_input = [
            {"role": "developer", "content": omniguard_config},
            {"role": "user", "content": conversation_context}
        ]
        
        model_params = get_model_params(
            st.session_state.get("selected_omniguard_model", "o3-mini-2025-01-31"),
            is_omniguard=True
        )
        
        try:
            response = client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": st.session_state.get("site_url", "https://omniguard.streamlit.app"),
                    "X-Title": st.session_state.get("site_name", sitename),
                },
                model=st.session_state.get("selected_omniguard_model", "o3-mini-2025-01-31"),
                messages=omniguard_evaluation_input,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                    "name": "omniguard_response",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                        "conversation_id": {
                            "type": "string",
                            "description": "Unique identifier for the conversation"
                        },
                        "analysis": {
                            "type": "string",
                            "description": "Short note on conversation interpretation and triggered rules"
                        },
                        "compliant": {
                            "type": "boolean",
                            "description": "True if the message is fully compliant with the rules, false otherwise"
                        },
                        "response": {
                            "type": "object",
                            "description": "Response details when content is non-compliant",
                            "properties": {
                            "action": {
                                "type": "string",
                                "enum": [
                                "RefuseUser",
                                "RefuseAssistant"
                                ],
                                "description": "The type of refusal action to take"
                            },
                            "RefuseUser": {
                                "type": [
                                "string",
                                "null"
                                ],
                                "description": "Refusal message to return when user input violates rules"
                            },
                            "RefuseAssistant": {
                                "type": [
                                "string",
                                "null"
                                ],
                                "description": "Refusal message to return when assistant output violates rules"
                            }
                            },
                            "required": [
                            "action",
                            "RefuseUser",
                            "RefuseAssistant"
                            ],
                            "additionalProperties": False
                        }
                        },
                        "required": [
                        "conversation_id",
                        "analysis",
                        "compliant",
                        "response"
                        ],
                        "additionalProperties": False
                    }
                    }
                },
                **model_params
            )
        except RateLimitError as e:
            logger.error(f"Rate limit exceeded: {e}")
            raise
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            # Check if the error is related to schema validation or unsupported model
            if "response_format" in str(e).lower() or "json_schema" in str(e).lower():
                error_response = {
                    "conversation_id": st.session_state.get("conversation_id", "error"),
                    "analysis": f"Schema Validation Error: {str(e)}",
                    "compliant": False,
                    "response": {
                        "action": "RefuseUser",
                        "RefuseUser": "The model doesn't support structured outputs. Please try again or contact support."
                    }
                }
                st.session_state["schema_violation"] = True
                return json.dumps(error_response)
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during API call: {e}")
            raise
        # Store messages in session
        st.session_state.omniguard_input_message = omniguard_evaluation_input
        st.session_state.omniguard_raw_api_response = response
        try:
            # Check that response has choices and the first choice has a message with content
            if not (hasattr(response, 'choices') and response.choices and hasattr(response.choices[0], 'message') and response.choices[0].message):
                raise ValueError('API response missing choices or message data')
            raw_content = response.choices[0].message.content
        except Exception as extraction_error:
            logger.error(f"Error extracting message content from API response: {extraction_error}. Full response: {response}")
            raise Exception('Malformed API response structure')
        omniguard_raw_response = raw_content
        st.session_state.omniguard_output_message = omniguard_raw_response

        return omniguard_raw_response

    except (RateLimitError, APIError) as e:
        logger.exception("OpenAI API Error in OmniGuard")
        error_response = {
            "conversation_id": st.session_state.get("conversation_id", "error"),
            "analysis": f"API Error: {str(e)}",
            "compliant": False,
            "response": {
                "action": "RefuseUser",
                "RefuseUser": f"OmniGuard API error - {str(e)}"
            }
        }
        return json.dumps(error_response)
    except requests.exceptions.RequestException as e:
        logger.exception("Network Error in OmniGuard")
        error_response = {
            "conversation_id": st.session_state.get("conversation_id", "error"),
            "analysis": f"Network Error: {str(e)}",
            "compliant": False,
            "response": {
                "action": "RefuseUser",
                "RefuseUser": f"OmniGuard network error - {str(e)}"
            }
        }
        return json.dumps(error_response)
    except json.JSONDecodeError as e:
        logger.exception("JSON Parsing Error in OmniGuard")
        # Set schema_violation flag when JSON parsing fails
        st.session_state["schema_violation"] = True
        return {
            "conversation_id": st.session_state.get("conversation_id", "error"),
            "analysis": f"JSON Parse Error: {str(e)}",
            "compliant": False,
            "response": {
                "action": "RefuseUser",
                "RefuseUser": f"OmniGuard response parsing error - {str(e)}"
            }
        }
    except Exception as e:
        logger.exception("Unexpected Error in OmniGuard")
        error_response = {
            "conversation_id": st.session_state.get("conversation_id", "error"),
            "analysis": f"System Error: {str(e)}",
            "compliant": False,
            "response": {
                "action": "RefuseUser",
                "RefuseUser": f"OmniGuard system error - {str(e)}"
            }
        }
        return json.dumps(error_response)

def process_omniguard_result(omniguard_result, user_prompt, context):
    """
    Process OmniGuard result and handle appropriate actions (user or assistant refusals).
    """
    from components.chat.session_management import upsert_conversation_turn, generate_conversation_id
    try:
        # Initialize schema_violation as False at the beginning of processing
        st.session_state["schema_violation"] = False
        
        omniguard_raw_response = omniguard_result
        try:
            parsed_response = json.loads(omniguard_raw_response)
            logger.debug(f"Parsed OmniGuard response: {parsed_response}")
            # With structured outputs, validation should be minimal as schema is enforced
            # This is kept as a safety measure
            compliant = parsed_response.get("compliant", False)
            if not compliant and "response" not in parsed_response:
                logger.error("Schema validation issue: Missing 'response' key in non-compliant result")
                st.session_state["schema_violation"] = True

            # Extract top-level fields to store in session state
            analysis_summary = parsed_response.get("analysis", "")
            conversation_id = parsed_response.get("conversation_id", "")
            action = parsed_response.get("response", {}).get("action")

            # Store values in session state
            st.session_state["compliant"] = compliant
            st.session_state["action"] = action

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OmniGuard result: {e}. Raw response: {omniguard_raw_response}")
            st.session_state["schema_violation"] = True
            parsed_response = {}
            compliant = False
            analysis_summary = f"Parse error: {str(e)}"
            conversation_id = "error"
            st.session_state["compliant"] = False
            st.session_state["action"] = None

        # --- USER VIOLATION CHECK ---
        user_violates = not compliant
        if user_violates:
            response_text = parsed_response.get("response", {}).get("RefuseUser", "Message rejected for safety reasons.")

            with st.chat_message("assistan"):
                st.markdown(response_text)

            st.session_state.messages.append({"role": "agent", "content": response_text})

            # Increment turn_number and conversation_id after user violation check
            st.session_state["turn_number"] += 1
            st.session_state["conversation_id"] = generate_conversation_id(st.session_state["turn_number"])

            upsert_conversation_turn()
            return

        # *** If user is compliant, proceed to get agent response ***
        from components.omniguard.agent_service import fetch_agent_response
        with st.spinner("Agent..."):
            assistant_response = fetch_agent_response(user_prompt)

        # --- AGENT VIOLATION CHECK ---
        with st.spinner("OmniGuard (Agent)..."):
            assistant_check = omniguard_check(pending_assistant_response=assistant_response)
        try:
            assistant_check_parsed = json.loads(assistant_check)
            
            # Validate the schema of agent check result - check for basic required keys
            basic_required_keys = ["conversation_id", "analysis", "compliant"]
            for key in basic_required_keys:
                if key not in assistant_check_parsed:
                    logger.error(f"Missing required key in agent check: {key}")
                    st.session_state["schema_violation"] = True
                    break
                    
            # If not compliant, check for the response key
            assistant_compliant = assistant_check_parsed.get("compliant", False)
            if not assistant_compliant:
                if "response" not in assistant_check_parsed:
                    logger.error("Missing 'response' key in non-compliant agent check")
                    st.session_state["schema_violation"] = True
                elif "action" not in assistant_check_parsed["response"]:
                    logger.error("Missing 'action' field in agent check response")
                    st.session_state["schema_violation"] = True
            
            # Extract and store agent check values
            assistant_action = assistant_check_parsed.get("response", {}).get("action")
            
            # Update session state with agent check results
            st.session_state["compliant"] = assistant_compliant
            st.session_state["action"] = assistant_action
            
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to parse agent check response: {e}")
            st.session_state["schema_violation"] = True
            assistant_compliant = False
            # Set default values in session state for error case
            st.session_state["compliant"] = False
            st.session_state["action"] = None

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

        st.session_state.messages.append({"role": "assistant", "content": response_text})

        # Increment turn_number and conversation_id after assistant check
        st.session_state["turn_number"] += 1
        st.session_state["conversation_id"] = generate_conversation_id(st.session_state["turn_number"])

        upsert_conversation_turn()

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error in process_omniguard_result: {e}")
        st.error("Something unexpected happened. Please try again later.")
        # Set default values in session state for error case
        st.session_state["compliant"] = False
        st.session_state["action"] = None
    except Exception as e:
        logger.exception("Unexpected error in process_omniguard_result")
        st.error("Something unexpected happened. Please try again later.")
        # Set default values in session state for error case
        st.session_state["compliant"] = False
        st.session_state["action"] = None