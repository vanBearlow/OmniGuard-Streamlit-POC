# -*- coding: utf-8 -*-
"""                                                                                      
Streamlit session management utilities for OmniGuard chat application.
Handles conversation state, database interactions, and session initialization.
"""

import uuid
from typing import Callable, Dict, Any, Optional
from dataclasses import dataclass, asdict
from functools import wraps

import streamlit as st
from st_supabase_connection import SupabaseConnection
from prompts import omniguard_configuration, assistant_system_prompt

# Type aliases for better readability
ConversationId = str
JsonDict = Dict[str, Any]

@dataclass
class SessionDefaults:
    """Default values for session state initialization."""
    messages: list = None
    base_conversation_id: str = None
    turn_number: int = 1
    conversation_id: str = None
    omniguard_input_message: Optional[list] = None
    omniguard_output_message: Optional[str] = None
    assistant_messages: Optional[list] = None
    show_report_violation_form: bool = False
    omniguard_configuration: dict = None
    assistant_system_prompt: str = None
    conversation_context: Optional[dict] = None

    def __post_init__(self):
        """Initialize computed fields after instance creation."""
        self.messages = []
        self.base_conversation_id = str(uuid.uuid4())
        self.conversation_id = f"{self.base_conversation_id}-{self.turn_number}"
        self.omniguard_configuration = omniguard_configuration
        self.assistant_system_prompt = assistant_system_prompt

def ensure_session_state(func: Callable) -> Callable:
    """Decorator to ensure session state exists before function execution."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not hasattr(st, 'session_state'):
            st.session_state = {}
        return func(*args, **kwargs)
    return wrapper

@ensure_session_state
def generate_conversation_id(turn_number: int = 1) -> ConversationId:
    """Generate a unique conversation ID combining base ID and turn number."""
    if "base_conversation_id" not in st.session_state:
        st.session_state.base_conversation_id = str(uuid.uuid4())
        st.session_state.turn_number = 1
    return f"{st.session_state.base_conversation_id}-{turn_number}"

@ensure_session_state
def reset_session_state(update_conversation_context: Callable) -> None:
    """Reset session state to initial values and update conversation context."""
    defaults = SessionDefaults()
    for key, value in asdict(defaults).items():
        setattr(st.session_state, key, value)
    update_conversation_context()

@ensure_session_state
def init_session_state(update_conversation_context: Callable) -> None:
    """Initialize session state with default values if not already set."""
    defaults = SessionDefaults()
    for key, value in asdict(defaults).items():
        if key not in st.session_state:
            setattr(st.session_state, key, value)
    
    # Ensure conversation context is updated
    if "conversation_context" not in st.session_state:
        update_conversation_context()

@st.cache_resource
def get_supabase_client() -> SupabaseConnection:
    """Return cached Supabase client connection."""
    return st.connection(
        "supabase",
        type=SupabaseConnection,
        url=st.secrets.supabase.SUPABASE_URL,
        key=st.secrets.supabase.SUPABASE_KEY
    )

def _extract_api_response(raw_response: Any) -> Optional[JsonDict]:
    """Extract serializable parts from API response."""
    if not raw_response:
        return None
    
    return {
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

def _build_metadata_json() -> JsonDict:
    """Build metadata JSON for conversation turn."""
    return {
        "raw_response": _extract_api_response(st.session_state.get("omniguard_raw_api_response")),
        "review_data": st.session_state.get("review_data"),
        "votes": {
            "count": 0,
            "user_violations": 0,
            "assistant_violations": 0,
            "safe_votes": 0
        }
    }

def _build_contributor_json() -> Optional[JsonDict]:
    """Build contributor JSON from session state."""
    contributor_data = st.session_state.get("contributor", {})
    return {
        field: value
        for field in ["name", "x", "discord", "linkedin"]
        if (value := contributor_data.get(field))
    } or None

def upsert_conversation_turn() -> None:
    """Insert or update the current conversation turn in Supabase."""
    supabase = get_supabase_client()
    
    # Prepare messages
    messages = st.session_state.omniguard_input_message.copy()
    if not any(msg.get("role") == "assistant" for msg in messages):
        messages.append({
            "role": "assistant",
            "content": st.session_state.omniguard_output_message
        })

    # Determine verification status
    verification_status = (
        "pending" if st.session_state.get("submitted_for_verification") 
        else "omniguard"
    )

    # Prepare row data
    row_data = {
        "id": st.session_state.conversation_id,
        "conversation": {"messages": messages},
        "metadata": _build_metadata_json(),
        "contributor": _build_contributor_json(),
        "verification_status": verification_status,
        "submitted_for_verification": st.session_state.get("submitted_for_verification", False)
    }

    # Upsert data
    supabase.table("interactions").upsert(row_data).execute()
