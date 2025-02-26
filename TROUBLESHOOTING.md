# OmniGuard Troubleshooting Guide

## Common Issues and Solutions

### UserInputError on Chat Page

**Error Message:**
```
Error in process_and_validate_user_message: UserInputError - Your message could not be processed. Please try again with a different message.
```

**Cause:**
This error typically occurs when there are issues with the session state initialization or when required configuration variables are missing. The most common causes are:

1. Missing or invalid assistant system prompt
2. Missing or invalid OmniGuard configuration
3. Issues with conversation context initialization
4. Corrupted session state

**Solutions:**

#### 1. Use the Reset Session Button

The simplest solution is to use the "Reset Session" button that appears in the top-right corner of the chat page. This will:
- Reset all session state variables to their default values
- Reinitialize the conversation context
- Clear the message history

#### 2. Refresh the Page

If the Reset Session button doesn't resolve the issue, try refreshing the page completely. This will force Streamlit to reinitialize the entire application.

#### 3. Clear Browser Cache

If the issue persists, try clearing your browser cache and cookies, then restart the application.

#### 4. Run the Session State Test Tool

For more detailed diagnostics, run the session state test tool:

```bash
streamlit run test_session_state.py
```

This tool will:
- Test the initialization of all critical session state variables
- Display the current values of these variables
- Provide a way to reset the session state
- Show detailed debug information

#### 5. Check Logs

If you're running the application locally, check the console logs for more detailed error messages. Look for:
- Errors related to session state initialization
- Missing configuration variables
- Exceptions in the conversation context update process

## Advanced Troubleshooting

If the above solutions don't resolve the issue, you may need to check:

1. **Configuration Files**: Ensure that `prompts.py` contains valid values for `assistant_system_prompt` and `omniguard_configuration`.

2. **Session State Initialization**: Check that `init_session_state()` and `init_chat_session_state()` are being called correctly in `pages/2_Chat.py`.

3. **Conversation Context**: Verify that `update_conversation_context()` is properly formatting the conversation context.

4. **Browser Storage**: Try using a different browser or incognito mode to rule out browser-specific issues.

## Recent Code Changes

The following changes have been made to address the UserInputError issue:

1. Added more detailed logging to `validate_user_input()` in `components/chat/user_input_logic.py`
2. Enhanced error handling in `process_and_validate_user_message()` in `components/chat/user_input.py`
3. Improved session state initialization in `init_chat_session_state()` in `components/chat/session_management.py`
4. Added a Reset Session button to the chat page in `pages/2_Chat.py`
5. Created a session state test tool (`test_session_state.py`) for diagnostics

These changes should help diagnose and resolve the UserInputError issue in most cases.
