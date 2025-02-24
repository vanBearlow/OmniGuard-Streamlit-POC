"""
Streamlit session management utilities for OmniGuard chat application.
Handles conversation state, database interactions, and session initialization.
"""

import uuid
import streamlit as st
from typing                 import Callable, Dict, Any, Optional
from dataclasses            import dataclass, asdict
from functools              import wraps
from st_supabase_connection import SupabaseConnection
from prompts                import omniguard_configuration, assistant_system_prompt

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
        self.messages = []
        self.base_conversation_id = str(uuid.uuid4())
        self.conversation_id = f"{self.base_conversation_id}-{self.turn_number}"
        self.omniguard_configuration = omniguard_configuration
        self.assistant_system_prompt = assistant_system_prompt

def ensure_session_state(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not hasattr(st, 'session_state'):
            st.session_state = {}
        return func(*args, **kwargs)
    return wrapper

@ensure_session_state
def generate_conversation_id(turn_number: int = 1) -> str:
    if "base_conversation_id" not in st.session_state:
        st.session_state.base_conversation_id = str(uuid.uuid4())
        st.session_state.turn_number = 1
    return f"{st.session_state.base_conversation_id}-{turn_number}"

@ensure_session_state
def reset_chat_session_state(update_conversation_context: Callable) -> None:
    defaults = SessionDefaults()
    for key, value in asdict(defaults).items():
        setattr(st.session_state, key, value)
    update_conversation_context()

@ensure_session_state
def init_chat_session_state(update_conversation_context: Callable) -> None:
    defaults = SessionDefaults()
    for key, value in asdict(defaults).items():
        if key not in st.session_state:
            setattr(st.session_state, key, value)
    
    if "conversation_context" not in st.session_state:
        update_conversation_context()

@st.cache_resource
def get_supabase_client() -> SupabaseConnection:
    return st.connection(
        "supabase",
        type=SupabaseConnection,
        url=st.secrets.supabase.SUPABASE_URL,
        key=st.secrets.supabase.SUPABASE_KEY
    )

def _extract_api_response(raw_response: Any) -> Optional[dict]:
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

def _build_metadata_json() -> dict:
    return {
        "raw_response": _extract_api_response(st.session_state.get("omniguard_raw_api_response")),
        "review_data": st.session_state.get("review_data"),
        "votes": {
            "count": 0,
            "user_violations": 0,
            "assistant_violations": 0,
            "compliant_votes": 0
        }
    }

@ensure_session_state
def upsert_conversation_turn() -> None:
    supabase = get_supabase_client()

    messages = st.session_state.omniguard_input_message.copy() if st.session_state.omniguard_input_message else []
    if not any(msg.get('role') == 'assistant' for msg in messages):
        if st.session_state.omniguard_output_message:
            messages.append({
                "role": "assistant",
                "content": st.session_state.omniguard_output_message
            })

    # 'verifier' shows if it's OmniGuard or pending/human
    verifier = "pending" if st.session_state.get("submitted_for_verification") else "omniguard"

    row_data = {
        "id": st.session_state.conversation_id,
        "conversation": {"messages": messages},
        "metadata": _build_metadata_json(),
        "verifier": verifier,
        "submitted_for_verification": st.session_state.get("submitted_for_verification", False),
        # Only store contributor_id (not name/social).
        "contributor_id": st.session_state.get("contributor_id")
    }

    supabase.table("interactions").upsert(row_data).execute()
