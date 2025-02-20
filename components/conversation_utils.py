"""
This module provides utility functions for handling conversation data.
It includes functions to build conversation JSON structures, extract messages from CDATA wrapped input,
and format conversation context into an XML-like structure.
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


#*** CDATA MESSAGE EXTRACTION ***

def extract_messages_from_input(input_text: str) -> Optional[List[Dict[str, str]]]:
    """
    Extracts the messages array from the conversation input text wrapped in CDATA.
    
    Args:
        input_text (str): String containing the conversation input, potentially wrapped in CDATA.
        
    Returns:
        Optional[List[Dict[str, str]]]: List of message dictionaries if extraction succeeds, otherwise None.
    """
    start_tag: str = "<![CDATA["
    end_tag:   str = "]]>"
    
    # Locate the start of the CDATA block.
    start_idx = input_text.find(start_tag)
    if start_idx == -1:
        return None
    start_idx += len(start_tag)  # Move index past the start tag.
    
    # Locate the end of the CDATA block.
    end_idx = input_text.find(end_tag, start_idx)
    if end_idx == -1:
        return None
    
    try:
        json_str          = input_text[start_idx:end_idx].strip()
        conversation_data = json.loads(json_str)
        return conversation_data.get("messages", [])
    except (json.JSONDecodeError, AttributeError, KeyError) as error:
        print(f"Error extracting messages from input: {error}")
        return None


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