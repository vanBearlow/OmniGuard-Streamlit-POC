import json
import time
import logging
import streamlit as st
import requests.exceptions
from openai import APIError, RateLimitError
from components.omniguard.client import get_openai_client, get_model_params


logger = logging.getLogger(__name__)

sitename = "OmniGuard"

def verify_configuration():
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
    try:
        session = st.session_state
        client = get_openai_client()

        from components.conversation_utils import build_conversation_json, format_conversation_context

        full_messages = session.messages.copy()
        # Append pending assistant response if available.
        if pending_assistant_response:
            full_messages.append({"role": "assistant", "content": pending_assistant_response})

        conversation = build_conversation_json(full_messages)
        conversation_context = format_conversation_context(conversation)

        if not verify_configuration():
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

        try:
            response = client.chat.completions.create(
                model=session.get("selected_omniguard_model", "o3-mini-2025-01-31"),
                messages=omniguard_evaluation_input,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "omniguard_response",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "conversation_id": {"type": "string"},
                                "analysis": {"type": "string"},
                                "compliant": {"type": "boolean"},
                                "response": {
                                    "type": "object",
                                    "properties": {
                                        "action": {
                                            "type": "string",
                                            "enum": ["RefuseUser", "RefuseAssistant"],
                                        },
                                        "RefuseUser": {"type": ["string", "null"]},
                                        "RefuseAssistant": {"type": ["string", "null"]},
                                    },
                                    "required": ["action", "RefuseUser", "RefuseAssistant"],
                                    "additionalProperties": False,
                                },
                            },
                            "required": ["conversation_id", "analysis", "compliant", "response"],
                            "additionalProperties": False,
                        },
                    },
                },
                **model_params
            )
        except RateLimitError as e:
            logger.error(f"Rate limit exceeded: {e}")
            raise
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            if "response_format" in str(e).lower() or "json_schema" in str(e).lower():
                error_response = {
                    "conversation_id": session.get("conversation_id", "error"),
                    "analysis": f"Schema Validation Error: {str(e)}",
                    "compliant": False,
                    "response": {
                        "action": "RefuseUser",
                        "RefuseUser": "I'm sorry, I can't help with that. Please try again later. (Rate limit)",
                        "RefuseAssistant": None,
                    },
                }
                session["schema_violation"] = True
                return json.dumps(error_response)
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during API call: {e}")
            raise

        session.omniguard_input_message = omniguard_evaluation_input
        session.omniguard_raw_api_response = response
        try:
            if not (
                hasattr(response, "choices")
                and response.choices
                and hasattr(response.choices[0], "message")
                and response.choices[0].message
            ):
                raise ValueError("API response missing choices or message data")
            raw_content = response.choices[0].message.content
        except Exception as extraction_error:
            logger.error(
                f"Error extracting message content from API response: {extraction_error}. Full response: {response}"
            )
            raise Exception("Malformed API response structure")
        session.omniguard_output_message = raw_content

        return raw_content

    except (RateLimitError, APIError) as e:
        logger.exception("OpenAI API Error in OmniGuard")
        error_response = {
            "conversation_id": session.get("conversation_id", "error"),
            "analysis": f"API Error: {str(e)}",
            "compliant": False,
            "response": {
                "action": "RefuseUser",
                "RefuseUser": f"OmniGuard API error - {str(e)}",
                "RefuseAssistant": None,
            },
        }
        return json.dumps(error_response)
    except requests.exceptions.RequestException as e:
        logger.exception("Network Error in OmniGuard")
        error_response = {
            "conversation_id": session.get("conversation_id", "error"),
            "analysis": f"Network Error: {str(e)}",
            "compliant": False,
            "response": {
                "action": "RefuseUser",
                "RefuseUser": f"OmniGuard network error - {str(e)}",
                "RefuseAssistant": None,
            },
        }
        return json.dumps(error_response)
    except json.JSONDecodeError as e:
        logger.exception("JSON Parsing Error in OmniGuard")
        session["schema_violation"] = True
        error_response = {
            "conversation_id": session.get("conversation_id", "error"),
            "analysis": f"JSON Parse Error: {str(e)}",
            "compliant": False,
            "response": {
                "action": "RefuseUser",
                "RefuseUser": f"OmniGuard response parsing error - {str(e)}",
                "RefuseAssistant": None,
            },
        }
        return json.dumps(error_response)
    except Exception as e:
        logger.exception("Unexpected Error in OmniGuard")
        error_response = {
            "conversation_id": session.get("conversation_id", "error"),
            "analysis": f"System Error: {str(e)}",
            "compliant": False,
            "response": {
                "action": "RefuseUser",
                "RefuseUser": f"OmniGuard system error - {str(e)}",
                "RefuseAssistant": None,
            },
        }
        return json.dumps(error_response)

def process_omniguard_result(omniguard_result, user_prompt, context):
    """Processes OmniGuard result and handles actions accordingly.

    Args:
        omniguard_result (str): Raw OmniGuard evaluation result in JSON string.
        user_prompt (str): The user's prompt.
        context: Additional conversation context.
    """
    from components.chat.session_management import upsert_conversation_turn, generate_conversation_id
    session = st.session_state
    try:
        session["schema_violation"] = False

        omniguard_raw_response = omniguard_result
        try:
            parsed_response = json.loads(omniguard_raw_response)
            logger.debug(f"Parsed OmniGuard response: {parsed_response}")
            compliant = parsed_response.get("compliant", False)
            if not compliant and "response" not in parsed_response:
                logger.error("Schema validation issue: Missing 'response' key in non-compliant result")
                session["schema_violation"] = True

            analysis_summary = parsed_response.get("analysis", "")
            conversation_id = parsed_response.get("conversation_id", "")
            action = parsed_response.get("response", {}).get("action")

            session["compliant"] = compliant
            session["action"] = action

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OmniGuard result: {e}. Raw response: {omniguard_raw_response}")
            session["schema_violation"] = True
            parsed_response = {}
            compliant = False
            analysis_summary = f"Parse error: {str(e)}"
            conversation_id = "error"
            session["compliant"] = False
            session["action"] = None

        # --- USER VIOLATION CHECK ---
        user_violates = not compliant
        if user_violates:
            response_text = parsed_response.get("response", {}).get(
                "RefuseUser", "I'm sorry, I can't help with that. Please try again later. (Message parsing error)"
            )

            with st.chat_message("assistant"):
                st.markdown(response_text)

            session.messages.append({"role": "agent", "content": response_text})
            session["turn_number"] += 1
            session["conversation_id"] = generate_conversation_id(session["turn_number"])
            upsert_conversation_turn()
            return

        # --- Proceed for compliant user ---
        from components.omniguard.agent_service import fetch_agent_response
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

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error in process_omniguard_result: {e}")
        st.error("Something unexpected happened. Please try again later.")
        session["compliant"] = False
        session["action"] = None
    except Exception as e:
        logger.exception("Unexpected error in process_omniguard_result")
        st.error("Something unexpected happened. Please try again later.")
        session["compliant"] = False
        session["action"] = None

