"""
Streamlit session management utilities for OmniGuard chat application.
Handles conversation state, database interactions, and session initialization.
"""

import uuid
import json
import streamlit as st
from typing                 import Callable, Dict, Any, Optional, List
from dataclasses            import dataclass, asdict
from functools              import wraps
from st_supabase_connection import SupabaseConnection
from components.prompts                import omnigaurd_developer_prompt, agent_system_prompt

@dataclass
class SessionDefaults:
    """Default values for session state initialization."""
    messages: list = None
    base_conversation_id: str = None
    turn_number: int = 0  # <--- START AT 0, updated requirement
    conversation_id: str = None
    omniguard_input_message: Optional[list] = None
    omniguard_output_message: Optional[str] = None
    agent_messages: Optional[list] = None
    show_report_violation_form: bool = False
    omnigaurd_developer_prompt: dict = None
    agent_system_prompt: str = None
    conversation_context: Optional[dict] = None
    schema_violation: bool = False
    schema_violation_context: Optional[str] = None  # Can be "user" or "assistant"
    compliant: Optional[bool] = None
    action: Optional[str] = None

    def __post_init__(self):
        self.messages = []
        self.base_conversation_id = str(uuid.uuid4())
        self.conversation_id = f"{self.base_conversation_id}-{self.turn_number}"
        self.omnigaurd_developer_prompt = omnigaurd_developer_prompt
        self.agent_system_prompt = agent_system_prompt

def ensure_session_state(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not hasattr(st, 'session_state'):
            st.session_state = {}
        return func(*args, **kwargs)
    return wrapper

@ensure_session_state
def generate_conversation_id(turn_number: int = 0) -> str:
    if "base_conversation_id" not in st.session_state:
        st.session_state.base_conversation_id = str(uuid.uuid4())
        st.session_state.turn_number = 0
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

# *** CONVERSATION UTILITIES ***
def build_conversation_json(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Constructs and returns a dictionary representing the conversation structure.
    
    Args:
        messages (List[Dict[str, str]]): List of message dictionaries, each containing 'role' and 'content' keys.
        
    Returns:
        Dict[str, Any]: Dictionary containing the conversation ID and full message history,
                        with the system prompt as the first message.
    """
    # Build full conversation by prepending the system prompt.
    system_prompt = st.session_state.agent_system_prompt
    full_messages  = [{"role": "system", "content": system_prompt}]
    full_messages.extend(messages)
    
    return {
        "id":       st.session_state.conversation_id,
        "messages": full_messages,
    }

def format_conversation_context(conversation: Dict[str, Any]) -> str:
    """
    Formats a conversation dictionary into the XML-like structure expected by the system.
    
    Args:
        conversation (Dict[str, Any]): Conversation data as a dictionary.
        
    Returns:
        str: XML-like formatted string representation of the conversation.
    """
    conversation_json = json.dumps(conversation, indent=4)
    return f"<input>\n{conversation_json}\n</input>"

@ensure_session_state
def upsert_conversation_turn() -> None:
    supabase = get_supabase_client()

    # Extract data from session state
    omniguard_input = st.session_state.get("omniguard_input_message", [])
    
    # Instructions: Developer prompt
    instructions = next(
        (msg["content"] for msg in omniguard_input if msg["role"] == "developer"),
        st.session_state.get("omnigaurd_developer_prompt", "")
    )
    
    # Input: Formatted conversation context
    input_str = next(
        (msg["content"] for msg in omniguard_input if msg["role"] == "user"),
        format_conversation_context(build_conversation_json(st.session_state.messages))
    )
    
    # Output: OmniGuard evaluation result
    output_str = st.session_state.get("omniguard_output_message", "")

    # Extract rules_violated from session state
    rules_violated = st.session_state.get("rules_violated", [])

    # Prepare metadata (without rules_violated or action)
    metadata = {
        "raw_response": _extract_api_response(st.session_state.get("omniguard_raw_api_response")),
        "review_data": st.session_state.get("review_data"),
    }

    # Fetch contributor details if contributor_id exists
    contributor_id = st.session_state.get("contributor_id")
    contributor_data = {
        "name": "",
        "x": "",
        "discord": "",
        "linkedin": ""
    }
    if contributor_id:
        try:
            res = (
                supabase.table("contributors")
                .select("name, x, discord, linkedin")
                .eq("contributor_id", contributor_id)
                .single()
                .execute()
            )
            if res.data:
                contributor_data = {
                    "name": res.data.get("name", ""),
                    "x": res.data.get("x", ""),
                    "discord": res.data.get("discord", ""),
                    "linkedin": res.data.get("linkedin", "")
                }
        except Exception as e:
            print(f"Error fetching contributor data: {e}")
            # Log error but proceed with empty values

    # Build row data with all fields (without conversation)
    row_data = {
        "id": st.session_state.conversation_id,
        "instructions": instructions,
        "input": input_str,
        "output": output_str,
        "rules_violated": rules_violated,  # Top-level field
        "metadata": metadata,
        "verifier": "pending" if st.session_state.get("submitted_for_review") else "omniguard",
        "submitted_for_review": st.session_state.get("submitted_for_review", False),
        "contributor_id": contributor_id,
        "name": contributor_data["name"],
        "x": contributor_data["x"],
        "discord": contributor_data["discord"],
        "linkedin": contributor_data["linkedin"],
        "compliant": st.session_state.get("compliant"),
        "action": st.session_state.get("action"),  # Added action as a top-level field
        "schema_violation": st.session_state.get("schema_violation", False),
        "schema_violation_context": st.session_state.get("schema_violation_context"),
    }

    # Upsert into the interactions table
    supabase.table("interactions").upsert(row_data).execute()
