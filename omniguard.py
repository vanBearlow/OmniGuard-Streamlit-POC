import json
import os
import time
import streamlit as st
from openai import OpenAI
from openai import APIError, RateLimitError
import requests.exceptions
import logging
from components.cost_utils import calculate_costs

logger = logging.getLogger(__name__)

sitename = "OmniGuard"

# --- Helper functions for API key and client initialization ---
def get_api_key():
    """Retrieve the API key based on configuration."""
    from components.service_fallbacks import check_api_key
    
    api_key = check_api_key()
    if not api_key:
        raise ValueError("OpenRouter API key not available")
    return api_key

def get_openai_client():
    """Initialize and return the OpenAI client."""
    try:
        # Creates an OpenAI client from openrouter.ai
        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=get_api_key()
        )
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
        raise

def get_model_params(model_name, is_omniguard=False):
    """
    Get appropriate parameters based on model type.
    
    For OmniGuard:
      - Both o1 and o3 are reasoning models, so we store
        the selected reasoning effort (low, medium, or high).
    For the assistant:
      - If the model is o1/o3, we also store a reasoning effort.
      - Otherwise (e.g., GPT-like model), we store temperature.
    """
    params = {}
    
    # For OmniGuard, both o1 and o3 are reasoning models
    if is_omniguard:
        params["reasoning_effort"] = st.session_state.get("selected_reasoning", "medium")
    else:
        # For assistant, check model type
        if model_name.startswith(("o1", "o3")):
            params["reasoning_effort"] = st.session_state.get("assistant_reasoning", "medium")
        else:
            params["temperature"] = st.session_state.get("temperature", 1.0)
    
    return params

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
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "gpt-4o-mini",
        "system_fingerprint": "fp_44709d6fcb",
        "choices": [{
            "index": 0,
            "message": {
            "role": "assistant",
            "content": "    {
                "conversation_id": "string",
                "analysisSummary": "string",
                "compliant": boolean,
                "response": {
                    "action": "RefuseUser | RefuseAssistant",
                    "RefuseUser | RefuseAssistant": "string"
                }
            }",
            },
            "logprobs": null,
            "finish_reason": "stop"
        }],
        "service_tier": "default",
        "usage": {
            "prompt_tokens": 9,
            "completion_tokens": 12,
            "total_tokens": 21,
            "completion_tokens_details": {
                "reasoning_tokens": 0,
                "accepted_prediction_tokens": 0,
                "rejected_prediction_tokens": 0
            }
        }
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
        
        # Initialize OpenRouter client with current session API key using the helper
        client = get_openai_client()
        
        from components.conversation_utils import build_conversation_json, format_conversation_context
        
        # Build base conversation from session state
        full_messages = st.session_state.messages.copy()
        
        # If evaluating assistant response, add it to messages
        if pending_assistant_response:
            full_messages.append({"role": "assistant", "content": pending_assistant_response})
        
        # Build and format conversation
        conversation = build_conversation_json(full_messages)
        conversation_context = format_conversation_context(conversation)
        
        # Record preparation time
        timings['prep'] = time.time() - timings['start']
        
        # Format OmniGuard evaluation input with configuration
        omniguard_config = st.session_state.omniguard_configuration
        omniguard_evaluation_input = [
            {"role": "developer", "content": omniguard_config},
            {"role": "user", "content": conversation_context}
        ]
        
        # Get model-specific parameters for OmniGuard
        model_params = get_model_params(st.session_state.selected_omniguard_model, is_omniguard=True)
        
        # API call timing
        api_start = time.time()
        try:
            response = client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": st.session_state.get("site_url", "https://example.com"),
                    "X-Title": st.session_state.get("site_name", sitename),
                },
                model=st.session_state.get("selected_omniguard_model", "o3-mini"),
                messages=omniguard_evaluation_input,
                response_format={"type": "json_object"},  # We want JSON content from OmniGuard
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

        logger.debug("OmniGuard raw response: %s", response.choices[0].message.content)

        # Safely capture usage data
        usage_data = {}
        if hasattr(response, 'usage') and response.usage:
            # Use getattr to avoid errors if a field isn't present
            usage_data = {
                'prompt_tokens': getattr(response.usage, 'prompt_tokens', 0),
                'completion_tokens': getattr(response.usage, 'completion_tokens', 0),
                'total_tokens': getattr(response.usage, 'total_tokens', 0)
            }
            # If there's some extra detail about tokens, parse it safely
            if hasattr(response.usage, 'completion_tokens_details') and response.usage.completion_tokens_details:
                # For example, reasoning tokens
                usage_data['completion_tokens_details'] = {
                    'reasoning_tokens': getattr(response.usage.completion_tokens_details, 'reasoning_tokens', 0)
                }
        
        # Extract raw content from the first choice
        raw_content = response.choices[0].message.content or ""
        
        # Use raw response text directly without JSON parsing
        omniguard_raw_response = raw_content

        # Store OmniGuard response in session state
        st.session_state.omniguard_output_message = omniguard_raw_response

        timings['process'] = time.time() - process_start
        # Optionally, you can store the timings and usage_data somewhere if needed

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

    This function interprets the OmniGuard response (raw JSON or string) to see if
    the user or the assistant message should be refused. If the user request is not
    compliant, it returns a refusal message. If user request is allowed, it attempts
    to fetch the assistant's response, checks it again with OmniGuard, and if that
    fails, refuses the assistant response.
    
    Args:
        omniguard_result (str): The raw OmniGuard result (possibly JSON).
        user_prompt (str): The original user prompt text.
        context (str): Additional context from the last user message.
    """
    try:
        # Because the result may be JSON or a string containing JSON, parse carefully
        omniguard_raw_response = omniguard_result
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
            # First check - user message compliance
            user_violates = not compliant
            
            if user_violates:
                # User message rejected
                response_text = parsed_response.get("response", {}).get("RefuseUser", 
                    "Message rejected for safety reasons.")
                
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
                return

            # If user message is allowed, proceed to fetch the assistant's response
            with st.spinner("Assistant...", show_time=True):
                assistant_response = fetch_assistant_response(user_prompt)
            
            # Second check - assistant response compliance
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

            # Show the final outcome in chat and store it
            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            
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

def fetch_assistant_response(prompt_text):
    """
    When OmniGuard returns compliant=True for the user,
    this queries the Assistant to get a response, which
    will then be re-checked by OmniGuard.

    The function also tracks usage data from the assistant
    response call (if available), and calculates cost.
    """
    try:
        # Track component timings
        timings = {
            'start': time.time(),
            'prep': 0,
            'api': 0,
            'process': 0
        }
        
        # Create new OpenRouter client using the helper function
        client = get_openai_client()

        main_prompt = st.session_state.assistant_system_prompt
        
        # Use appropriate role based on model type
        role = "system" if st.session_state.selected_assistant_model.startswith(("o1", "o3")) else "developer"
        assistant_messages = [{"role": role, "content": main_prompt}]
        assistant_messages += [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]

        # Store assistant messages in session state for debugging
        st.session_state.assistant_messages = assistant_messages

        # Get model-specific parameters
        model_params = get_model_params(st.session_state.selected_assistant_model)
        
        # Record preparation time
        timings['prep'] = time.time() - timings['start']
        
        # API call timing
        api_start = time.time()
        try:
            response = client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": st.session_state.get("site_url", "https://example.com"),
                    "X-Title": st.session_state.get("site_name", sitename),
                },
                model=st.session_state.selected_assistant_model,
                messages=assistant_messages,
                **model_params
            )
        except RateLimitError as e:
            logger.error(f"Rate limit exceeded in fetch_assistant_response: {e}")
            raise
        except APIError as e:
            logger.error(f"OpenAI API error in fetch_assistant_response: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error in fetch_assistant_response: {e}")
            raise
        
        timings['api'] = time.time() - api_start
        
        # Process timing start
        process_start = time.time()
        
        # Capture usage data if present
        usage_data = {}
        if hasattr(response, 'usage') and response.usage:
            usage_data = {
                'prompt_tokens': getattr(response.usage, 'prompt_tokens', 0),
                'completion_tokens': getattr(response.usage, 'completion_tokens', 0),
                'total_tokens': getattr(response.usage, 'total_tokens', 0)
            }
            if hasattr(response.usage, 'completion_tokens_details') and response.usage.completion_tokens_details:
                usage_data['completion_tokens_details'] = {
                    'reasoning_tokens': getattr(response.usage.completion_tokens_details, 'reasoning_tokens', 0)
                }
        
        # Calculate costs with error handling
        model_name = st.session_state.selected_assistant_model
        is_cached = st.session_state.get("use_cached_input", False)
        try:
            input_cost, output_cost, total_cost = calculate_costs(
                model_name,
                usage_data.get('prompt_tokens', 0),
                usage_data.get('completion_tokens', 0),
                is_cached
            )
        except Exception as e:
            logger.error(f"Cost calculation error in fetch_assistant_response: {e}")
            input_cost = output_cost = total_cost = 0
        
        # Record process timing
        timings['process'] = time.time() - process_start
        
        # Calculate total latency
        latency = int((time.time() - timings['start']) * 1000)
        
        # Extract the assistant's content from the response
        assistant_output = response.choices[0].message.content
        
        return assistant_output

    except RateLimitError as e:
        logger.exception("Rate limit exceeded")
        return "Assistant temporarily unavailable due to rate limiting. Please try again in a moment."
    except APIError as e:
        logger.exception("OpenAI API Error")
        return "Assistant temporarily unavailable. Please try again."
    except requests.exceptions.RequestException as e:
        logger.exception("Network Error")
        return "Unable to reach assistant due to network issues. Please check your connection."
    except Exception as e:
        logger.exception("Unexpected Error")
        return "An unexpected error occurred. Please try again."
