import json
import time
import logging
import streamlit as st
from openai import APIError, RateLimitError
import requests.exceptions

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

    This function builds a conversation context from session state messages,
    optionally includes a pending assistant response, and sends the assembled
    request to the OpenRouter endpoint via the OpenAI client. It returns the
    raw OmniGuard response if successful or a dictionary containing error details
    in case of an exception.

    Args:
        pending_assistant_response (str, optional): An optional assistant response
            to include in the OmniGuard evaluation.

    Returns:
        str or dict: The raw OmniGuard response text if the check is successful;
            otherwise, a dictionary with an error description.

    Sample Response Object:
        {
          "id": "gen-1739999831-XuET2XAeBv6Z5bK5xKkM",
          "choices": [
            "Choice(finish_reason='stop', index=0, logprobs=None, message=ChatCompletionMessage(content='{\\n  \"conversation_id\": \"be632036-142b-440f-b99a-d9d88882bad6-2\",\\n  \"analysisSummary\": \"The conversation is compliant. The system message sets a positive tone and the user’s greeting \\'hi\\' does not include any disallowed content or trigger any policy violations.\\n  \"compliant\": true\\n}', refusal=None, role='assistant', audio=None, function_call=None, tool_calls=None), native_finish_reason='stop')"
          ],
          "created": 1739999831,
          "model": "openai/o3-mini",
          "object": "chat.completion",
          "service_tier": null,
          "system_fingerprint": "fp_ef58bd3122",
          "usage": "CompletionUsage(completion_tokens=278, prompt_tokens=3978, total_tokens=4256, completion_tokens_details=None, prompt_tokens_details=None)",
          "provider": "OpenAI"
        }
        """
    
    try:
        # Track component timings
        timings = {
            'start': time.time(),
            'prep': 0,
            'api': 0,
            'process': 0
        }
        
        # Initialize OpenRouter client with current session API key
        client = get_openai_client()
        
        from components.conversation_utils import build_conversation_json, format_conversation_context
        
        # Build base conversation
        full_messages = st.session_state.messages.copy()
        
        # If evaluating assistant response, add it to messages
        if pending_assistant_response:
            full_messages.append({"role": "assistant", "content": pending_assistant_response})
        
        # Build and format conversation
        conversation = build_conversation_json(full_messages)
        conversation_context = format_conversation_context(conversation)
        
        # Record preparation time
        timings['prep'] = time.time() - timings['start']
        
        # Verify configuration before proceeding
        if not verify_configuration():
            raise Exception("Invalid OmniGuard configuration state")

        # Format omniguard_evaluation_input with configuration
        omniguard_config = st.session_state.get("omniguard_configuration")
        if not omniguard_config:
            raise Exception("OmniGuard configuration is missing")
        omniguard_evaluation_input = [
            {"role": "developer", "content": omniguard_config},
            {"role": "user", "content": conversation_context}
        ]
        
        # Get model-specific parameters
        model_params = get_model_params(st.session_state.get("selected_omniguard_model", "o3-mini"), is_omniguard=True)
        
        # API call timing
        api_start = time.time()
        try:
            response = client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": st.session_state.get("site_url", "https://example.com"),
                    "X-Title": st.session_state.get("site_name", sitename),
                },
                model=st.session_state.get("selected_omniguard_model", "o3-mini-2025-01-31"),
                messages=omniguard_evaluation_input,
                response_format={"type": "json_object"},
                **model_params
            )
        except RateLimitError as e:
            logger.error(f"Rate limit exceeded: {e}")
            raise
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during API call: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during API call: {e}")
            raise

        timings['api'] = time.time() - api_start

        # Process timing start
        process_start = time.time()

        # Store messages in session state instead of displaying directly
        st.session_state.omniguard_input_message = omniguard_evaluation_input

        # The entire raw response object
        st.session_state.omniguard_raw_api_response = response
        # Use raw response text directly without JSON parsing
        raw_content = response.choices[0].message.content
        omniguard_raw_response = raw_content

        # Store OmniGuard response in session state (just the text portion)
        st.session_state.omniguard_output_message = omniguard_raw_response

        timings['process'] = time.time() - process_start

        return omniguard_raw_response

    except (RateLimitError, APIError) as e:
        logger.exception("OpenAI API Error in OmniGuard")
        error_response = {
            "conversation_id": st.session_state.get("conversation_id", "error"),
            "analysisSummary": f"API Error: {str(e)}",
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
            "analysisSummary": f"Network Error: {str(e)}",
            "compliant": False,
            "response": {
                "action": "RefuseUser",
                "RefuseUser": f"OmniGuard network error - {str(e)}"
            }
        }
        return json.dumps(error_response)
    except json.JSONDecodeError as e:
        logger.exception("JSON Parsing Error in OmniGuard")
        return {
            "conversation_id": st.session_state.get("conversation_id", "error"),
            "analysisSummary": f"JSON Parse Error: {str(e)}",
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
            "analysisSummary": f"System Error: {str(e)}",
            "compliant": False,
            "response": {
                "action": "RefuseUser",
                "RefuseUser": f"OmniGuard system error - {str(e)}"
            }
        }
        return json.dumps(error_response)

def process_omniguard_result(omniguard_result, user_prompt, context):
    """
    Process OmniGuard result and handle appropriate actions.

    This function uses the raw OmniGuard result to decide whether to refuse
    the user message, refuse an assistant response, or proceed. The code also
    handles ambiguous or partial violations by requesting clarification.

    Args:
        omniguard_result (str): The string or JSON returned from `omniguard_check`.
        user_prompt (str): The original user prompt for reference if needed.
        context (str): Additional context string from the last message.

    Returns:
        None (Updates streamlit session with final assistant or refusal messages)
    """
    from components.chat.session_management import upsert_conversation_turn  # === CHANGES ===
    try:
        omniguard_raw_response = omniguard_result  # treat as raw string
        try:
            parsed_response = json.loads(omniguard_raw_response)
            compliant = parsed_response.get("compliant", False)
            analysis_summary = parsed_response.get("analysisSummary", "")
            conversation_id = parsed_response.get("conversation_id", "")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OmniGuard result: {e}")
            parsed_response = {}
            compliant = False
            analysis_summary = f"Parse error: {str(e)}"
            conversation_id = "error"

        with st.chat_message("assistant"):
            # First check - user message
            user_violates = not compliant
            if user_violates:
                # User message rejected
                response_text = parsed_response.get("response", {}).get(
                    "RefuseUser", "Message rejected for safety reasons."
                )
                
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})

                # === CHANGES ===
                # Even if user is refused, we can upsert to store the turn
                upsert_conversation_turn()
                return

            # If user is allowed, we generate the assistant response next
            from components.omniguard.assistant_service import fetch_assistant_response
            with st.spinner("Assistant...", show_time=True):
                assistant_response = fetch_assistant_response(user_prompt)

            # Second OmniGuard check - assistant response
            with st.spinner("Verifying response...", show_time=True):
                assistant_check = omniguard_check(pending_assistant_response=assistant_response)
            try:
                assistant_check_parsed = json.loads(assistant_check)
                assistant_compliant = assistant_check_parsed.get("compliant", False)
            except (json.JSONDecodeError, TypeError) as e:
                logger.error(f"Failed to parse assistant check response: {e}")
                assistant_compliant = False
            
            assistant_violates = not assistant_compliant
            
            if assistant_violates:
                # Assistant response rejected
                try:
                    response_text = (
                        assistant_check_parsed.get("response", {}).get("RefuseAssistant")
                        or "Assistant response blocked for safety reasons."
                    )
                except (TypeError, KeyError) as e:
                    logger.error(f"Error accessing assistant refusal message: {e}")
                    response_text = "Assistant response blocked for safety reasons."
            else:
                # Both checks passed
                response_text = assistant_response

            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})

        # === CHANGES ===
        # Now that user + assistant are final, store (or update) this turn
        upsert_conversation_turn()

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error in process_omniguard_result: {e}")
        if st.secrets.get("development_mode", False):
            st.error(f"Dev Mode Error: {e}")
        else:
            st.error("Something unexpected happened. Please try again later.")
    except Exception as e:
        logger.exception("Unexpected error in process_omniguard_result")
        if st.secrets.get("development_mode", False):
            st.error(f"Dev Mode Error: {e}")
        else:
            st.error("Something unexpected happened. Please try again later.")
