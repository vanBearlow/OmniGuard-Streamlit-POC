import json
import os
import time
import streamlit as st
from openai import OpenAI
from database import save_conversation
import logging
from components.init_session_state import init_session_state

# Ensure session state is initialized
init_session_state()

# Cost per token in USD based on model
MODEL_COSTS = {
    # GPT-4o versions
    "gpt-4o-2024-08-06": {"input": 2.50, "cached_input": 1.25, "output": 10.00},
    "gpt-4o-2024-11-20": {"input": 2.50, "cached_input": 1.25, "output": 10.00},
    "gpt-4o-2024-05-13": {"input": 5.00, "output": 15.00},
    
    # GPT-4o-audio-preview versions
    "gpt-4o-audio-preview-2024-12-17": {"input": 2.50, "output": 10.00},
    "gpt-4o-audio-preview-2024-10-01": {"input": 2.50, "output": 10.00},
    
    # GPT-4o-realtime-preview versions
    "gpt-4o-realtime-preview-2024-12-17": {"input": 5.00, "cached_input": 2.50, "output": 20.00},
    "gpt-4o-realtime-preview-2024-10-01": {"input": 5.00, "cached_input": 2.50, "output": 20.00},
    
    # GPT-4o-mini versions
    "gpt-4o-mini-2024-07-18": {"input": 0.15, "cached_input": 0.075, "output": 0.60},
    
    # GPT-4o-mini-audio-preview versions
    "gpt-4o-mini-audio-preview-2024-12-17": {"input": 0.15, "output": 0.60},
    
    # GPT-4o-mini-realtime-preview versions
    "gpt-4o-mini-realtime-preview-2024-12-17": {"input": 0.60, "cached_input": 0.30, "output": 2.40},
    
    # O1 versions
    "o1-2024-12-17": {"input": 15.00, "cached_input": 7.50, "output": 60.00},
    "o1-preview-2024-09-12": {"input": 15.00, "cached_input": 7.50, "output": 60.00},
    
    # O3-mini versions
    "o3-mini-2025-01-31": {"input": 1.10, "cached_input": 0.55, "output": 4.40},
    
    # O1-mini versions
    "o1-mini-2024-09-12": {"input": 1.10, "cached_input": 0.55, "output": 4.40}
}

def calculate_costs(model_name, prompt_tokens, completion_tokens, is_cached=False):
    """Calculate costs based on token usage."""
    if model_name not in MODEL_COSTS:
        return None, None, None
    
    costs = MODEL_COSTS[model_name]
    input_rate = costs["cached_input"] if is_cached and "cached_input" in costs else costs["input"]
    output_rate = costs["output"]
    
    input_cost = (prompt_tokens / 1000) * input_rate
    output_cost = (completion_tokens / 1000) * output_rate
    total_cost = input_cost + output_cost
    
    return input_cost, output_cost, total_cost

logger = logging.getLogger(__name__)

sitename = "OmniGuard"

# --- Helper functions for API key and client initialization ---
def get_api_key():
    """Retrieve the API key based on session configuration."""
    if st.session_state.get("contribute_training_data"):
        return os.getenv("OPENROUTER_API_KEY")
    else:
        return st.session_state.get("api_key")

def get_openai_client():
    """Initialize and return the OpenAI client."""
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=get_api_key()
    )

def get_model_params(model_name, is_omniguard=False):
    """Get appropriate parameters based on model type."""
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
        
        # Create messages array with system prompt as first message
        full_messages = [{"role": "system", "content": st.session_state.assistant_system_prompt}]
        full_messages.extend(st.session_state.messages)
        
        # If evaluating assistant response, add it to messages
        if pending_assistant_response:
            full_messages.append({"role": "assistant", "content": pending_assistant_response})
            
        # Record preparation time
        timings['prep'] = time.time() - timings['start']
        
        # Format omniguard_evaluation_input with both configuration and input tags
        omniguard_config = st.session_state.omniguard_configuration
        conversation_json = json.dumps(full_messages, indent=2)
        
        omniguard_evaluation_input_str = (
            f"<configuration>{omniguard_config}</configuration>"
            f"<input><![CDATA[{{"
            f'    "id": "{st.session_state.conversation_id}",'
            f'    "messages": {conversation_json}'
            f"}}]]></input>"
        )

        omniguard_evaluation_input = [
            {"role": "developer", "content": omniguard_evaluation_input_str}
        ]
        
        # Get model-specific parameters
        model_params = get_model_params(st.session_state.selected_omniguard_model, is_omniguard=True)
        
        # API call timing
        api_start = time.time()
        response = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": st.session_state.get("site_url", "https://example.com"),
                "X-Title": st.session_state.get("site_name", sitename),
            },
            model=st.session_state.get("selected_omniguard_model", "o3-mini"),
            messages=omniguard_evaluation_input,
            response_format={"type": "json_object"},
            **model_params
        )
        timings['api'] = time.time() - api_start

        # Process timing start
        process_start = time.time()

        # Store messages in session state instead of displaying directly
        st.session_state.omniguard_input_message = omniguard_evaluation_input

        logger.debug("OmniGuard raw response: %s", response.choices[0].message.content)

        # Capture complete usage data
        usage_data = {}
        if hasattr(response, 'usage'):
            usage_data = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
            # Add completion tokens details if available
            if hasattr(response.usage, 'completion_tokens_details'):
                usage_data['completion_tokens_details'] = {
                    'reasoning_tokens': getattr(response.usage.completion_tokens_details, 'reasoning_tokens', 0),
                    'accepted_prediction_tokens': getattr(response.usage.completion_tokens_details, 'accepted_prediction_tokens', 0),
                    'rejected_prediction_tokens': getattr(response.usage.completion_tokens_details, 'rejected_prediction_tokens', 0)
                }

        raw_content = response.choices[0].message.content or ""

        # Attempt JSON parsing
        try:
            omniguard_raw_response = json.loads(raw_content)
        except json.JSONDecodeError:
            return {
                "response": {
                    "action": "UserInputRejection",
                    "UserInputRejection": "System error - invalid JSON response"
                }
            }

        # Validate expected structure
        if not isinstance(omniguard_raw_response, dict) or "response" not in omniguard_raw_response:
            return {
                "response": {
                    "action": "UserInputRejection",
                    "UserInputRejection": "System error - safety checks incomplete"
                }
            }

        # Store OmniGuard response in session state
        st.session_state.omniguard_output_message = omniguard_raw_response

        if st.session_state.get("contribute_training_data", False):
            response_data = omniguard_raw_response.get("response", {})
            action = response_data.get("action", "")
            user_violates_rules = (action == "UserInputRejection")
            assistant_violates_rules = (action == "AssistantOutputRejection")
            # Record process timing
            timings['process'] = time.time() - process_start
            
            # Calculate total latency
            latency = int((time.time() - timings['start']) * 1000)  # Convert to milliseconds
            
            # Calculate costs with error handling
            model_name = st.session_state.get("selected_omniguard_model")
            is_cached = st.session_state.get("use_cached_input", False)
            
            try:
                input_cost, output_cost, total_cost = calculate_costs(
                    model_name,
                    usage_data.get('prompt_tokens', 0),
                    usage_data.get('completion_tokens', 0),
                    is_cached
                )
            except Exception as e:
                logger.error(f"Cost calculation error: {e}")
                input_cost = output_cost = total_cost = 0
            
            save_conversation(
                st.session_state.conversation_id,
                user_violates_rules=user_violates_rules,
                assistant_violates_rules=assistant_violates_rules,
                omniguard_evaluation_input=omniguard_evaluation_input,
                omniguard_raw_response=omniguard_raw_response,
                model_name=model_name,
                reasoning_effort=st.session_state.get("selected_reasoning"),
                prompt_tokens=usage_data.get('prompt_tokens'),
                completion_tokens=usage_data.get('completion_tokens'),
                total_tokens=usage_data.get('total_tokens'),
                input_cost=input_cost,
                output_cost=output_cost,
                total_cost=total_cost,
                latency_ms=latency,
                usage_data=usage_data,
                request_timings=timings
            )
        return omniguard_raw_response

    except Exception as e:
        logger.exception("OmniGuard Error")

        return {
            "response": {
                "action": "UserInputRejection",
                "UserInputRejection": f"OmniGuard safety system unavailable - {e}"
            }
        }

def process_omniguard_result(omniguard_result, user_prompt, context):
    """
    Based on the OmniGuard response, either show the rejection message (if a violation is found)
    or query the Assistant and verify its response before showing.
    """
    try:
        if isinstance(omniguard_result, str):
            omniguard_raw_response = json.loads(omniguard_result)
        else:
            omniguard_raw_response = omniguard_result

        with st.chat_message("assistant"):
            # First check - user message
            action = omniguard_raw_response.get("response", {}).get("action")
            user_violates = action != "allow"
            
            if user_violates:
                # User message rejected
                st.session_state.rejection_count += 1
                response_text = (
                    omniguard_raw_response["response"].get("UserInputRejection")
                    or "Content blocked for safety reasons."
                )
                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})
                
                # Save user message rejection
                if st.session_state.get("contribute_training_data", False):
                    save_conversation(
                        st.session_state.conversation_id,
                        user_violates_rules=True,
                        assistant_violates_rules=False,
                        omniguard_evaluation_input=st.session_state.omniguard_input_message,
                        omniguard_raw_response=omniguard_raw_response
                    )
                return

            # Get assistant response if user message allowed
            with st.spinner("Assistant..."):
                assistant_response = fetch_assistant_response(user_prompt)
            
            # Second check - assistant response
            assistant_check = omniguard_check(pending_assistant_response=assistant_response)
            assistant_action = assistant_check.get("response", {}).get("action")
            assistant_violates = assistant_action != "allow"
            
            if assistant_violates:
                # Assistant response rejected
                st.session_state.rejection_count += 1
                response_text = (
                    assistant_check["response"].get("AssistantOutputRejection")
                    or "Assistant response blocked for safety reasons."
                )
            else:
                # Both checks passed
                response_text = assistant_response

            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            
            # Save conversation with both check results
            if st.session_state.get("contribute_training_data", False):
                save_conversation(
                    st.session_state.conversation_id,
                    user_violates_rules=False,  # User message passed first check
                    assistant_violates_rules=assistant_violates,
                    omniguard_evaluation_input=st.session_state.omniguard_input_message,
                    omniguard_raw_response=assistant_check,
                    assistant_output=assistant_response
                )

    except (json.JSONDecodeError, ValueError) as e:
        st.error(f"Error parsing OmniGuard result: {e}")
    except Exception as ex:
        st.error(f"Unexpected error: {ex}")

def fetch_assistant_response(prompt_text):
    """
    When OmniGuard allows the content, this queries the Assistant.
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

        # Store assistant messages in session state
        st.session_state.assistant_messages = assistant_messages

        # Get model-specific parameters
        model_params = get_model_params(st.session_state.selected_assistant_model)
        
        # Record preparation time
        timings['prep'] = time.time() - timings['start']
        
        # API call timing
        api_start = time.time()
        response = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": st.session_state.get("site_url", "https://example.com"),
                "X-Title": st.session_state.get("site_name", sitename),
            },
            model=st.session_state.selected_assistant_model,
            messages=assistant_messages,
            **model_params
        )
        timings['api'] = time.time() - api_start
        
        # Process timing start
        process_start = time.time()
        
        # Capture complete usage data
        usage_data = {}
        if hasattr(response, 'usage'):
            usage_data = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
            # Add completion tokens details if available
            if hasattr(response.usage, 'completion_tokens_details'):
                usage_data['completion_tokens_details'] = {
                    'reasoning_tokens': getattr(response.usage.completion_tokens_details, 'reasoning_tokens', 0),
                    'accepted_prediction_tokens': getattr(response.usage.completion_tokens_details, 'accepted_prediction_tokens', 0),
                    'rejected_prediction_tokens': getattr(response.usage.completion_tokens_details, 'rejected_prediction_tokens', 0)
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
        
        assistant_output = response.choices[0].message.content
        
        # Save usage data if contributing to training data
        if st.session_state.get("contribute_training_data", False):
            save_conversation(
                st.session_state.conversation_id,
                user_violates_rules=False,
                assistant_violates_rules=False,
                omniguard_evaluation_input=None,
                omniguard_raw_response=None,
                assistant_output=assistant_output,
                model_name=model_name,
                reasoning_effort=st.session_state.get("assistant_reasoning"),
                prompt_tokens=usage_data.get('prompt_tokens'),
                completion_tokens=usage_data.get('completion_tokens'),
                total_tokens=usage_data.get('total_tokens'),
                input_cost=input_cost,
                output_cost=output_cost,
                total_cost=total_cost,
                latency_ms=latency,
                usage_data=usage_data,
                request_timings=timings
            )
        
        return assistant_output

    except Exception as e:
        st.error(f"Assistant error: {e}")
        return "Assistant unavailable. Please try again."

def check_rule_violation(report_info, conversation_context):
    """
    Verify rule violation using full conversation context and report information.
    Returns a JSON object: {"input_violates_rules": bool, "output_violates_rules": bool}
    """
    try:
        # Track component timings
        timings = {
            'start': time.time(),
            'prep': 0,
            'api': 0,
            'process': 0
        }
        
        client = get_openai_client()
        # Format omniguard_evaluation_input with both configuration and input tags
        omniguard_evaluation_input_str = (
            f"<configuration>{st.session_state.omniguard_configuration}</configuration>"
            f"<input><![CDATA[{conversation_context}]]></input>"
        )
        
        prompt = (
            "Verify if any rules were violated using the full conversation context and report details. "
            "Return a JSON object with keys 'input_violates_rules' and 'output_violates_rules', both booleans. True "
            f"{omniguard_evaluation_input_str} "
            f"<report>{report_info}</report>"
        )
        
        # Get model-specific parameters for OmniGuard
        model_params = get_model_params(st.session_state.selected_omniguard_model, is_omniguard=True)
        
        # Record preparation time
        timings['prep'] = time.time() - timings['start']
        
        # API call timing
        api_start = time.time()
        response = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": st.session_state.get("site_url", "https://example.com"),
                "X-Title": st.session_state.get("site_name", sitename),
            },
            model=st.session_state.selected_omniguard_model,
            messages=[{"role": "system", "content": prompt}],
            **model_params
        )
        timings['api'] = time.time() - api_start
        
        # Process timing start
        process_start = time.time()
        
        # Capture complete usage data
        usage_data = {}
        if hasattr(response, 'usage'):
            usage_data = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
            # Add completion tokens details if available
            if hasattr(response.usage, 'completion_tokens_details'):
                usage_data['completion_tokens_details'] = {
                    'reasoning_tokens': getattr(response.usage.completion_tokens_details, 'reasoning_tokens', 0),
                    'accepted_prediction_tokens': getattr(response.usage.completion_tokens_details, 'accepted_prediction_tokens', 0),
                    'rejected_prediction_tokens': getattr(response.usage.completion_tokens_details, 'rejected_prediction_tokens', 0)
                }
        
        # Calculate costs with error handling
        model_name = st.session_state.selected_omniguard_model
        is_cached = st.session_state.get("use_cached_input", False)
        try:
            input_cost, output_cost, total_cost = calculate_costs(
                model_name,
                usage_data.get('prompt_tokens', 0),
                usage_data.get('completion_tokens', 0),
                is_cached
            )
        except Exception as e:
            logger.error(f"Cost calculation error in check_rule_violation: {e}")
            input_cost = output_cost = total_cost = 0
        
        result_text = response.choices[0].message.content.strip()
        violation_result = json.loads(result_text)
        
        # Record process timing
        timings['process'] = time.time() - process_start
        
        # Calculate total latency
        latency = int((time.time() - timings['start']) * 1000)
        
        # Save usage data if contributing to training data
        if st.session_state.get("contribute_training_data", False):
            save_conversation(
                st.session_state.conversation_id,
                user_violates_rules=violation_result.get('input_violates_rules', False),
                assistant_violates_rules=violation_result.get('output_violates_rules', False),
                omniguard_evaluation_input=None,
                omniguard_raw_response=None,
                model_name=model_name,
                reasoning_effort=st.session_state.get("selected_reasoning"),
                prompt_tokens=usage_data.get('prompt_tokens'),
                completion_tokens=usage_data.get('completion_tokens'),
                total_tokens=usage_data.get('total_tokens'),
                input_cost=input_cost,
                output_cost=output_cost,
                total_cost=total_cost,
                latency_ms=latency,
                usage_data=usage_data,
                request_timings=timings
            )
        
        return violation_result
    except Exception as e:
        print(f"Error in check_rule_violation: {e}")
        return {"input_violates_rules": False, "output_violates_rules": False}