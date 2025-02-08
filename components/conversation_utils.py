"""
This module provides utility functions for handling conversation data.
It includes functions to build conversation JSON structures, extract messages from CDATA wrapped input,
and format conversation context into an XML-like structure.
"""

import streamlit as st
import json
from typing import List, Dict, Any, Optional


def build_conversation_json(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Constructs and returns a dictionary representing the conversation structure.
    
    Args:
        messages: List of message dictionaries, each containing 'role' and 'content' keys
        
    Returns:
        Dictionary containing conversation ID and full message history including system prompt
    """
    # Create messages array with system prompt as first message
    full_messages = [{"role": "system", "content": st.session_state.assistant_system_prompt}]
    full_messages.extend(messages)
    
    return {
        "id": st.session_state.conversation_id,
        "messages": full_messages
    }


def extract_messages_from_input(input_text: str) -> Optional[List[Dict[str, str]]]:
    """
    Extracts the messages array from conversation input text that is wrapped in CDATA.
    
    Args:
        input_text: String containing the conversation input, potentially wrapped in CDATA
        
    Returns:
        List of message dictionaries if extraction succeeds, None if parsing fails
    """
    try:
        # Find the JSON block within CDATA
        start_idx = input_text.find("<![CDATA[")
        if start_idx != -1:
            start_idx += 9  # Length of "<![CDATA["
            end_idx = input_text.find("]]>", start_idx)
            if end_idx != -1:
                json_str = input_text[start_idx:end_idx].strip()
                conversation_data = json.loads(json_str)
                return conversation_data.get("messages", [])
    except (json.JSONDecodeError, AttributeError, KeyError) as e:
        print(f"Error extracting messages from input: {e}")
        return None
    
    return None


def format_conversation_context(conversation: Dict[str, Any]) -> str:
    """
    Formats a conversation dictionary into the XML-like structure expected by the system.
    
    Args:
        conversation: Dictionary containing conversation data
        
    Returns:
        Formatted string with conversation JSON wrapped in input and CDATA tags
    """
    conversation_json = json.dumps(conversation, indent=2)
    return f"""<input>
        <![CDATA[
            {conversation_json}
        ]]>
    </input>"""