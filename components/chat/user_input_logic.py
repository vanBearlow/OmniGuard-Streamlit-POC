"""
User Input Processing Logic Module

This module contains the core business logic for processing user input in the OmniGuard system,
separated from UI rendering concerns. It provides a clean separation of concerns by handling
the data processing and state management aspects of user input without UI dependencies.

Key responsibilities:
- Validating and sanitizing user input
- Managing conversation state updates
- Executing safety checks through the OmniGuard service
- Processing safety evaluation results
- Determining appropriate responses to safety violations
"""
import logging
from typing import Dict, Any, Optional, Callable
from components.chat.session_management import StateManager


def validate_user_input(user_message: str) -> Optional[str]:
    """
    Validate and sanitize user input for security and formatting.
    
    This function performs basic validation on user input to ensure it meets
    the minimum requirements for processing. It checks for null values,
    incorrect types, and removes extraneous whitespace.
    
    Args:
        user_message: Raw user input text to validate
        
    Returns:
        str: Sanitized input if valid
        None: If input is invalid or empty
        
    Note:
        This is only the first level of validation. Additional security
        checks are performed by the OmniGuard service.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Log the input for debugging
    logger.debug(f"Validating user input: {type(user_message)}")
    
    # Check for null or incorrect type
    if user_message is None:
        logger.error("User message is None")
        return None
    
    if not isinstance(user_message, str):
        logger.error(f"User message is not a string: {type(user_message)}")
        return None
    
    if not user_message:
        logger.error("User message is empty")
        return None
    
    # Remove leading/trailing whitespace
    sanitized = user_message.strip()
    
    # Log the result
    if not sanitized:
        logger.error("User message is only whitespace")
        return None
    
    logger.debug(f"User input validated successfully: '{sanitized}'")
    return sanitized


def update_conversation_with_user_message(
    user_message: str,
    generate_conversation_id: Callable[[int], str],
    update_conversation_context: Callable[[], None]
) -> None:
    """
    Update conversation state with a new user message.
    
    This function manages the conversation state updates when a new user
    message is received. It increments the turn counter, generates a new
    conversation ID, adds the message to history, and updates the context.
    
    Args:
        user_message: Validated and sanitized user message
        generate_conversation_id: Function to generate unique conversation IDs
        update_conversation_context: Function to update the conversation context
        
    Note:
        This function modifies session state directly and does not return a value.
        The conversation context update is critical for maintaining conversation flow.
    """
    # Increment the conversation turn counter
    turn_number = StateManager.get("turn_number", 0) + 1
    StateManager.set("turn_number", turn_number)
    
    # Generate a new conversation ID based on the updated turn number
    StateManager.set("conversation_id", generate_conversation_id(turn_number))
    
    # Add the user message to the conversation history
    StateManager.append_to_list("messages", {"role": "user", "content": user_message})
    
    # Update the conversation context with the new message
    update_conversation_context()


def execute_safety_check(
    user_message: str,
    omniguard_check_fn: Callable[[Optional[str]], Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Execute the OmniGuard safety check on user input.
    
    This function prepares the conversation context and calls the OmniGuard
    service to evaluate the safety of the user input. It stores both the
    input and output of the safety check in session state for auditing.
    
    Args:
        user_message: Validated user message to check for safety
        omniguard_check_fn: Function to call the OmniGuard service
        
    Returns:
        Dict[str, Any]: The response from the OmniGuard safety service
        
    Note:
        This function handles the core safety evaluation logic without
        any UI-specific code, making it easier to test and maintain.
    """
    # Get the current conversation context for safety evaluation
    conversation_context = StateManager.get("conversation_context")
    
    # Store the safety evaluation input for debugging and auditing
    StateManager.set("safety_evaluation_input", conversation_context)
    
    # Call the OmniGuard service to evaluate the conversation
    omniguard_response = omniguard_check_fn(conversation_context)
    
    # Store the safety evaluation output for debugging and auditing
    StateManager.set("safety_evaluation_output", omniguard_response)
    
    # Return the response for further processing
    return omniguard_response


def prepare_context_for_safety_processing() -> Dict[str, Any]:
    """
    Prepare the context needed for safety evaluation result processing.
    
    This function gathers the necessary context information from session state
    that is required for processing the safety evaluation results, including
    conversation IDs and turn numbers.
    
    Returns:
        Dict[str, Any]: Context dictionary with conversation metadata
        
    Note:
        This context is used by the safety evaluation result handler to
        properly process and store the evaluation results.
    """
    # Gather relevant context information from session state
    return {
        "conversation_id": StateManager.get("conversation_id"),
        "turn_number": StateManager.get("turn_number"),
        "base_conversation_id": StateManager.get("base_conversation_id")
    }


def should_refuse_user_input(omniguard_response: Dict[str, Any]) -> bool:
    """
    Determine if user input should be refused based on safety evaluation.
    
    This function analyzes the OmniGuard response to determine if the
    user input should be refused due to safety concerns. It checks for
    the "RefuseUser" action in the response.
    
    Args:
        omniguard_response: Response from the OmniGuard safety service
        
    Returns:
        bool: True if the input should be refused, False otherwise
        
    Note:
        This is a critical security function that enforces safety boundaries
        by preventing unsafe content from being processed further.
    """
    # Check if the response contains a valid structure
    if not omniguard_response or "response" not in omniguard_response:
        return True  # Refuse by default if response is invalid
    
    # Check if the action is to refuse the user input
    return omniguard_response["response"].get("action") == "RefuseUser"


def get_refusal_message(omniguard_response: Dict[str, Any]) -> str:
    """
    Get the appropriate refusal message for rejected user input.
    
    This function extracts the refusal message from the OmniGuard response
    or provides a default message if none is specified. The message explains
    to the user why their input was rejected.
    
    Args:
        omniguard_response: Response from the OmniGuard safety service
        
    Returns:
        str: User-friendly message explaining why the input was refused
        
    Note:
        The refusal message is designed to be informative without revealing
        sensitive details about the safety evaluation system.
    """
    # Default refusal message if none is provided
    default_message = "Your message could not be processed due to content safety concerns."
    
    # Check if the response contains a valid structure
    if not omniguard_response or "response" not in omniguard_response:
        return default_message
    
    # Extract the refusal message or use the default
    response = omniguard_response["response"]
    return response.get("RefuseUser", default_message)
