import time
import logging
import streamlit as st
from openai import APIError, RateLimitError
import requests.exceptions
from components.omniguard.client import get_openai_client, get_model_params
from components.cost_utils import calculate_costs

logger = logging.getLogger(__name__)
sitename = "OmniGuard"

def verify_configuration():
    """
    Verify that the configuration values are properly set in session state.
    """
    if not st.session_state.get("assistant_system_prompt"):
        logger.error("Assistant system prompt is missing or empty")
        return False
    return True

def fetch_assistant_response(prompt_text):
    """
    When OmniGuard returns compliant=False, this queries the Assistant.
    
    This function fetches the assistant's response using a separate model
    (specified in session state). In this refactored version, we store the
    entire raw response object in session state instead of extracting fields
    that may not exist (e.g., usage tokens).
    """
    try:
        # Track component timings
        timings = {
            'start': time.time(),
            'prep': 0,
            'api': 0,
            'process': 0
        }
        
        # Create new OpenRouter client
        client = get_openai_client()

        # Verify configuration before proceeding
        if not verify_configuration():
            raise Exception("Invalid Assistant configuration state")

        main_prompt = st.session_state.get("assistant_system_prompt")
        if not main_prompt:
            raise Exception("Assistant system prompt is missing")
        
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
        
        # Store the entire response object to session state
        st.session_state.assistant_raw_api_response = response

        # (Optional) If you want to see usage tokens or other fields,
        # handle carefully in case they do not exist
        # usage_data = {}
        # if hasattr(response, 'usage'):
        #     usage_data = {
        #         'prompt_tokens': response.usage.prompt_tokens,
        #         'completion_tokens': response.usage.completion_tokens,
        #         'total_tokens': response.usage.total_tokens
        #     }

        # Optionally, you can still calculate costs if usage data is present:
        # is_cached = st.session_state.get("use_cached_input", False)
        # model_name = st.session_state.selected_assistant_model
        # try:
        #     input_cost, output_cost, total_cost = calculate_costs(
        #         model_name,
        #         usage_data.get('prompt_tokens', 0),
        #         usage_data.get('completion_tokens', 0),
        #         is_cached
        #     )
        # except Exception as e:
        #     logger.error(f"Cost calculation error in fetch_assistant_response: {e}")

        # Record process timing
        timings['process'] = time.time() - process_start
        
        # This is the raw assistant text
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
