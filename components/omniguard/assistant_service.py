import time
import logging
import streamlit as st
from openai import APIError, RateLimitError
import requests.exceptions
from components.omniguard.client import get_openai_client, get_model_params
from components.cost_utils import calculate_costs

logger = logging.getLogger(__name__)
sitename = "OmniGuard"

def verify_configuration() -> bool:
    """
    Verify that essential configuration values (like the assistant system prompt) are set
    in session state.

    Returns:
        bool: True if 'assistant_system_prompt' is present, False otherwise.
    """
    if not st.session_state.get("assistant_system_prompt"):
        logger.error("Assistant system prompt is missing or empty")
        return False
    return True

def fetch_assistant_response(prompt_text: str) -> str:
    """
    Fetch the assistant's response using the designated model. The entire raw API response
    is stored in session state (for future reference like calculating costs).

    Note:
        The 'prompt_text' parameter is not used because the system prompt is fetched from
        session state; it is retained for interface consistency.

    Parameters:
        prompt_text (str): The prompt text for querying the assistant.

    Returns:
        str: The assistant's response extracted from the API, or an error message in case of issues.
    """
    try:
        client = get_openai_client()

        if not verify_configuration():
            raise Exception("Invalid Assistant configuration state")

        main_prompt = st.session_state.get("assistant_system_prompt")
        if not main_prompt:
            raise Exception("Assistant system prompt is missing")

        # Determine role based on model type for clarity in assistant messages
        role = "system" if st.session_state.selected_assistant_model.startswith(("o1", "o3")) else "developer"
        assistant_messages = [{"role": role, "content": main_prompt}]
        assistant_messages += [
            {"role": message["role"], "content": message["content"]}
            for message in st.session_state.messages
        ]
        st.session_state.assistant_messages = assistant_messages

        # Get model-specific parameters for the API call
        model_params = get_model_params(st.session_state.selected_assistant_model)

        try:
            response = client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": st.session_state.get("site_url", "https://omniguard.streamlit.app"),
                    "X-Title"    : st.session_state.get("site_name", sitename),
                },
                model=st.session_state.selected_assistant_model,
                messages=assistant_messages,
                **model_params
            )
        except RateLimitError as e:
            logger.error(f"Rate limit exceeded: {e}")
            raise
        except APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error: {e}")
            raise

        # Store the complete API response for potential further analysis (e.g. cost calculations)
        st.session_state.assistant_raw_api_response = response

        # Extract and return the assistant's text output from the API response
        assistant_output = response.choices[0].message.content
        return assistant_output

    except RateLimitError:
        logger.exception("Rate limit exceeded during assistant response fetch")
        return ("Assistant temporarily unavailable due to rate limiting. "
                "Please try again in a moment.")
    except APIError:
        logger.exception("OpenAI API Error encountered during assistant response fetch")
        return "Assistant temporarily unavailable. Please try again."
    except requests.exceptions.RequestException:
        logger.exception("Network error encountered during assistant response fetch")
        return ("Unable to reach assistant due to network issues. "
                "Please check your connection.")
    except Exception:
        logger.exception("Unexpected error during assistant response fetch")
        return "An unexpected error occurred. Please try again."
