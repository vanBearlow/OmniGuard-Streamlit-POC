import json
import os
import streamlit as st
from openai import OpenAI
from database import save_conversation
import logging

logger = logging.getLogger(__name__)

sitename = "CMS"

# --- New: Helper functions for API key and client initialization ---
def get_api_key():
    """Retrieve the API key based on session configuration."""
    if st.session_state.get("contribute_training_data"):
        return os.getenv("OPENROUTER_API_KEY")
    else:
        return st.session_state.get("api_key")

def get_openai_client():
    """Initialize and return the OpenAI client."""
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=get_api_key()
    )
# --- End of new helper functions ---

def CMS():
    try:
        # Initialize OpenRouter client with current session API key using the helper
        client = get_openai_client()
        
        conversation_context = json.dumps({
            "conversation_id": st.session_state.conversation_id,
            "messages": st.session_state.messages
        })

        omni_config = st.session_state.CMS_configuration
        cms_evaluation_input = [
            {"role": "developer", "content": omni_config},
            {"role": "user", "content": conversation_context}
        ]
        response = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": st.session_state.get("site_url", "https://example.com"),
                "X-Title": st.session_state.get("site_name", sitename),
            },
            model=st.session_state.get("selected_model", "openai/o3-mini"),
            messages=cms_evaluation_input,
            response_format={"type": "json_object"}
        )

        with st.expander("Message to CMS:"):
            st.json(cms_evaluation_input)

        logger.debug("CMS raw response: %s", response.choices[0].message.content)

        raw_content = response.choices[0].message.content or ""

        # Attempt JSON parsing
        try:
            cms_raw_response = json.loads(raw_content)
        except json.JSONDecodeError:
            return {
                "response": {
                    "action": "UserInputRejection",
                    "UserInputRejection": "System error - invalid JSON response"
                }
            }

        # Validate expected structure
        if not isinstance(cms_raw_response, dict) or "response" not in cms_raw_response:
            return {
                "response": {
                    "action": "UserInputRejection",
                    "UserInputRejection": "System error - safety checks incomplete"
                }
            }

        with st.expander("Message from CMS:"):
            st.json(cms_raw_response)

        if st.session_state.get("contribute_training_data", False):
            response_data = cms_raw_response.get("response", {})
            action = response_data.get("action", "")
            user_violates_rules = (action == "UserInputRejection")
            assistant_violates_rules = (action == "AssistantOutputRejection")
            save_conversation(
                st.session_state.conversation_id,
                user_violates_rules=user_violates_rules,
                assistant_violates_rules=assistant_violates_rules,
                cms_evaluation_input=cms_evaluation_input,
                cms_raw_response=cms_raw_response,
                model_name=st.session_state.get("selected_model"),
                reasoning_effort=st.session_state.get("selected_reasoning")
            )
        return cms_raw_response

    except Exception as e:
        logger.exception("CMS Error")

        return {
            "response": {
                "action": "UserInputRejection",
                "UserInputRejection": f"CMS safety system unavailable - {e}"
            }
        }

def process_CMS_result(CMS_result, user_prompt, context):
    """
    Based on the CMS response, either show the rejection message (if a violation is found)
    or query the Assistant if the action is 'allow'.
    """
    try:
        if isinstance(CMS_result, str):
            cms_raw_response = json.loads(CMS_result)
        else:
            cms_raw_response = CMS_result

        with st.chat_message("assistant"):
            action = cms_raw_response.get("response", {}).get("action")
            if action != "allow":
                response_text = (
                    cms_raw_response["response"].get("UserInputRejection")
                    or cms_raw_response["response"].get("AssistantOutputRejection")
                    or "Content blocked for safety reasons."
                )
            else:
                response_text = assistant_query(user_prompt)

            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})

    except (json.JSONDecodeError, ValueError) as e:
        st.error(f"Error parsing CMS result: {e}")
    except Exception as ex:
        st.error(f"Unexpected error: {ex}")

def assistant_query(prompt_text):
    """
    When CMS allows the content, this queries the Assistant.
    """
    try:
        # Create new OpenRouter client using the helper function
        client = get_openai_client()

        main_prompt = st.session_state.assistant_system_prompt
        assistant_messages = [{"role": "system", "content": main_prompt}]
        assistant_messages += [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]

        with st.expander("Messages to Assistant:"):
            st.write(assistant_messages)

        response = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": st.session_state.get("site_url", "https://example.com"),
                "X-Title": st.session_state.get("site_name", sitename),
            },
            model="openai/gpt-4o-mini",
            messages=assistant_messages,
            temperature=1
        )

        assistant_output = response.choices[0].message.content
        return assistant_output

    except Exception as e:
        st.error(f"Assistant error: {e}")
        return "Assistant unavailable. Please try again."

def assess_rule_violation(report_info, conversation_context):
    """
    Verify rule violation using full conversation context and report information.
    Returns a JSON object: {"input_violates_rules": bool, "output_violates_rules": bool}
    """
    try:
        client = get_openai_client()
        prompt = (
            "Verify if any rules were violated using the full conversation context and report details. "
            "Return a JSON object with keys 'input_violates_rules' and 'output_violates_rules', both booleans. True if a rule was violated, False otherwise."
            "<configuration>" + st.session_state.CMS_configuration + "</configuration> "
            "<conversation>" + conversation_context + "</conversation> "
            "<report>" + report_info + "</report>"
        )
        response = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": st.session_state.get("site_url", "https://example.com"),
                "X-Title": st.session_state.get("site_name", sitename),
            },
            model="openai/o3-mini",
            messages=[{"role": "system", "content": prompt}],
            reasoning_effort="high"
        )
        result_text = response.choices[0].message.content.strip()
        violation_result = json.loads(result_text)
        return violation_result
    except Exception as e:
        print(f"Error in assess_rule_violation: {e}")
        return {"input_violates_rules": False, "output_violates_rules": False}
