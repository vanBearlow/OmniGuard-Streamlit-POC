import uuid
import streamlit as st
from typing import Callable
from prompts import omniguard_configuration, assistant_system_prompt

from st_supabase_connection import SupabaseConnection, execute_query

def generate_conversation_id(turn_number: int = 1) -> str:
    """Generate a unique conversation ID combining base ID and turn number."""
    if "base_conversation_id" not in st.session_state:
        st.session_state.base_conversation_id = str(uuid.uuid4())
        st.session_state.turn_number = 1
    return f"{st.session_state.base_conversation_id}-{turn_number}"

def reset_session_state(update_conversation_context: Callable) -> None:
    """
    Reset session state variables to their initial values.
    
    Args:
        update_conversation_context: Function to update the conversation context
    """
    st.session_state.messages = []
    st.session_state.base_conversation_id = str(uuid.uuid4())
    st.session_state.turn_number = 1
    st.session_state.conversation_id = generate_conversation_id(st.session_state.turn_number)
    st.session_state.omniguard_input_message = None
    st.session_state.omniguard_output_message = None
    st.session_state.assistant_messages = None
    update_conversation_context()

def init_session_state(update_conversation_context: Callable) -> None:
    """
    Initialize all session state variables if they don't exist.
    
    Args:
        update_conversation_context: Function to update the conversation context
    """
    # Message Management
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Conversation Management
    if "base_conversation_id" not in st.session_state:
        st.session_state.base_conversation_id = str(uuid.uuid4())
    if "turn_number" not in st.session_state:
        st.session_state.turn_number = 1
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = generate_conversation_id(st.session_state.turn_number)
    
    # Configuration
    if "omniguard_configuration" not in st.session_state:
        st.session_state.omniguard_configuration = omniguard_configuration
    if "assistant_system_prompt" not in st.session_state:
        st.session_state.assistant_system_prompt = assistant_system_prompt
    
    # UI State
    if "show_report_violation_form" not in st.session_state:
        st.session_state.show_report_violation_form = False
    
    # Context Management
    if "conversation_context" not in st.session_state:
        update_conversation_context()
    
    # Message Display State
    if "omniguard_input_message" not in st.session_state:
        st.session_state.omniguard_input_message = None
    if "omniguard_output_message" not in st.session_state:
        st.session_state.omniguard_output_message = None
    if "assistant_messages" not in st.session_state:
        st.session_state.assistant_messages = None

@st.cache_resource  # Use cache_resource for database connections
def get_supabase_client():
    """
    Return the st_supabase_connection object for DB operations.
    Use a short TTL or no caching to ensure immediate updates.
    """
    # Get connection using credentials from [supabase] section in .streamlit/secrets.toml
    return st.connection(
        "supabase",
        type=SupabaseConnection,
        url=st.secrets.supabase.SUPABASE_URL,
        key=st.secrets.supabase.SUPABASE_KEY
    )

def upsert_conversation_turn():
    """
    Insert or update the current turn into Supabase table 'conversation_turns'.
    This function is invoked after we've finalized the user + assistant messages for this turn.
    """
    supabase = get_supabase_client()

    # Unique row ID is conversation_id
    row_id = st.session_state.conversation_id

    messages = st.session_state.omniguard_input_message
    messages.append({"role": "assistant", "content": st.session_state.omniguard_output_message})
    
    # Build 'conversation' JSON for this turn
    conversation_json = {
        "messages": messages}

    # Extract serializable parts of the raw API response
    raw_response = st.session_state.omniguard_raw_api_response
    serializable_response = None
    if raw_response:
        serializable_response = {
            "id": raw_response.id,
            "created": raw_response.created,
            "model": raw_response.model,
            "object": raw_response.object,
            "choices": [{
                "finish_reason": choice.finish_reason,
                "index": choice.index,
                "message": {
                    "content": choice.message.content,
                    "role": choice.message.role
                }
            } for choice in raw_response.choices],
            "usage": {
                "completion_tokens": raw_response.usage.completion_tokens,
                "prompt_tokens": raw_response.usage.prompt_tokens,
                "total_tokens": raw_response.usage.total_tokens
            } if raw_response.usage else None
        }

    # Build 'metadata' JSON
    metadata_json = {
        "submittedForReview": st.session_state.get("submitted_for_review", False),
        "verified": st.session_state.get("verified", False),
        "raw_response": serializable_response
    }

    # Get contributor info from session state and format as JSONB
    contributor_data = st.session_state.get("contributor", {})
    contributor_json = {}
    # Only add fields that exist and have non-empty values
    for field in ["name", "x", "discord", "linkedin"]:
        if value := contributor_data.get(field):  # Using walrus operator to get and check value
            contributor_json[field] = value

    # Prepare row data for Supabase
    row_data = {
        "id": row_id,
        "conversation": conversation_json,
        "metadata": metadata_json,
        "contributor": contributor_json if contributor_json else None,  # Only include if we have any contributor data
        # up to you to handle created_at/updated_at in DB, e.g., with triggers or default values
    }

    # Use upsert so that if we call multiple times for the same ID, we update instead of insert
    supabase.table("conversation_turns").upsert(row_data).execute()
