"""
This module provides utility functions for handling conversation data.
It includes functions to build conversation JSON structures and format conversation context into an XML-like structure.
"""

# Standard Libraries
import json
from typing import List, Dict, Any, Optional

# Third Party Libraries
import streamlit as st

#*** CONVERSATION JSON BUILDING FUNCTIONS ***

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
    system_prompt = st.session_state.assistant_system_prompt
    full_messages  = [{"role": "system", "content": system_prompt}]
    full_messages.extend(messages)
    
    return {
        "id":       st.session_state.conversation_id,
        "messages": full_messages,
    }

#*** CONVERSATION CONTEXT FORMATTING ***

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