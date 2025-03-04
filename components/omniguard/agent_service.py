import time
import logging
import streamlit as st
import requests.exceptions
from openai import APIError, RateLimitError
from components.omniguard.client import get_openai_client, get_model_params


logger = logging.getLogger(__name__)
sitename = "OmniGuard"

def verify_configuration() -> bool:
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

    if not verify_configuration():
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
            extra_headers={
                "HTTP-Referer": st.session_state.get("site_url", "https://omniguard.streamlit.app"),
                "X-Title"    : st.session_state.get("site_name", sitename),
            },
            model=st.session_state.selected_agent_model,
            messages=agent_messages,
            **model_params
        )
    # Store the complete API response for potential further analysis (e.g. cost calculations)
    st.session_state.assistant_raw_api_response = response

    # Extract and return the agent's text output from the API response
    agent_output = response.choices[0].message.content
    return agent_output
