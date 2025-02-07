import json
import os
import time
import streamlit as st
from openai import OpenAI
from database import save_conversation
import logging

# Cost per token in USD based on model
MODEL_COSTS = {
    "gpt-4o": {"input": 2.50, "cached_input": 1.25, "output": 10.00},
    "gpt-4o-audio-preview": {"input": 2.50, "output": 10.00},
    "gpt-4o-realtime-preview": {"input": 5.00, "cached_input": 2.50, "output": 20.00},
    "gpt-4o-mini": {"input": 0.15, "cached_input": 0.075, "output": 0.60},
    "gpt-4o-mini-audio-preview": {"input": 0.15, "output": 0.60},
    "gpt-4o-mini-realtime-preview": {"input": 0.60, "cached_input": 0.30, "output": 2.40},
    "o1": {"input": 15.00, "cached_input": 7.50, "output": 60.00},
    "o3-mini": {"input": 1.10, "cached_input": 0.55, "output": 4.40},
    "o1-mini": {"input": 1.10, "cached_input": 0.55, "output": 4.40}
}

def calculate_costs(model_name, prompt_tokens, completion_tokens, is_cached=False):
    """Calculate costs based on token usage."""
    if model_name not in MODEL_COSTS:
        return None, None, None
    
    costs = MODEL_COSTS[model_name]
    input_rate = costs["cached_input"] if is_cached and "cached_input" in costs else costs["input"]
    output_rate = costs["output"]
    
    input_cost = (prompt_tokens / 1000) * input_rate
    output_cost = (completion_tokens / 1000) * output_rate
    total_cost = input_cost + output_cost
    
    return input_cost, output_cost, total_cost

logger = logging.getLogger(__name__)

sitename = "CMS"

# --- Helper functions for API key and client initialization ---
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

def get_model_params(model_name, is_cms=False):
    """Get appropriate parameters based on model type."""
    params = {}
    
    # For CMS, both o1 and o3 are reasoning models
    if is_cms:
        params["reasoning_effort"] = st.session_state.get("selected_reasoning", "medium")
    else:
        # For assistant, check model type
        if model_name.startswith(("o1", "o3")):
            params["reasoning_effort"] = st.session_state.get("assistant_reasoning", "medium")
        else:
            params["temperature"] = st.session_state.get("temperature", 1.0)
    
    return params

def CMS():
    try:
        start_time = time.time()
        
        # Initialize OpenRouter client with current session API key using the helper
        client = get_openai_client()
        
        # Create messages array with system prompt as first message
        full_messages = [{"role": "system", "content": st.session_state.assistant_system_prompt}]
        full_messages.extend(st.session_state.messages)
        
        conversation_context = f"""<input>
            <![CDATA[
                {{
                    "id": "{st.session_state.conversation_id}",
                    "messages": {json.dumps(full_messages, indent=2)}
                }}
            ]]>
        </input>"""

        omniguard_config = st.session_state.CMS_configuration
        cms_evaluation_input = [
            {"role": "developer", "content": f"<configuration>{omniguard_config}</configuration>"},
            {"role": "user", "content": conversation_context}
        ]
        
        # Get model-specific parameters
        model_params = get_model_params(st.session_state.selected_cms_model, is_cms=True)
        
        response = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": st.session_state.get("site_url", "https://example.com"),
                "X-Title": st.session_state.get("site_name", sitename),
            },
            model=st.session_state.get("selected_cms_model", "o3-mini"),
            messages=cms_evaluation_input,
            response_format={"type": "json_object"},
            **model_params
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
            # Calculate elapsed time
            latency = int((time.time() - start_time) * 1000)  # Convert to milliseconds
            
            # Get token usage from response
            usage = response.usage
            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens
            total_tokens = usage.total_tokens
            
            # Calculate costs
            model_name = st.session_state.get("selected_cms_model")
            is_cached = st.session_state.get("use_cached_input", False)
            input_cost, output_cost, total_cost = calculate_costs(
                model_name, prompt_tokens, completion_tokens, is_cached
            )
            
            save_conversation(
                st.session_state.conversation_id,
                user_violates_rules=user_violates_rules,
                assistant_violates_rules=assistant_violates_rules,
                cms_evaluation_input=cms_evaluation_input,
                cms_raw_response=cms_raw_response,
                model_name=model_name,
                reasoning_effort=st.session_state.get("selected_reasoning"),
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                input_cost=input_cost,
                output_cost=output_cost,
                total_cost=total_cost,
                latency_ms=latency
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
                # Increment rejection counter
                st.session_state.rejection_count += 1
                response_text = (
                    cms_raw_response["response"].get("UserInputRejection")
                    or cms_raw_response["response"].get("AssistantOutputRejection")
                    or "Content blocked for safety reasons."
                )
            else:
                with st.spinner("Assistant..."):
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
        
        # Use appropriate role based on model type
        role = "system" if st.session_state.selected_assistant_model.startswith(("o1", "o3")) else "developer"
        assistant_messages = [{"role": role, "content": main_prompt}]
        assistant_messages += [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]

        with st.expander("Messages to Assistant:"):
            st.write(assistant_messages)

        # Get model-specific parameters
        model_params = get_model_params(st.session_state.selected_assistant_model)
        
        response = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": st.session_state.get("site_url", "https://example.com"),
                "X-Title": st.session_state.get("site_name", sitename),
            },
            model=st.session_state.selected_assistant_model,
            messages=assistant_messages,
            **model_params
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
            "Return a JSON object with keys 'input_violates_rules' and 'output_violates_rules', both booleans. True "
            f"<configuration>{st.session_state.CMS_configuration}</configuration> "
            f"<input><![CDATA[{conversation_context}]]></input> "
            f"<report>{report_info}</report>"
        )
        
        # Get model-specific parameters for CMS
        model_params = get_model_params(st.session_state.selected_cms_model, is_cms=True)
        
        response = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": st.session_state.get("site_url", "https://example.com"),
                "X-Title": st.session_state.get("site_name", sitename),
            },
            model=st.session_state.selected_cms_model,
            messages=[{"role": "system", "content": prompt}],
            **model_params
        )
        result_text = response.choices[0].message.content.strip()
        violation_result = json.loads(result_text)
        return violation_result
    except Exception as e:
        print(f"Error in assess_rule_violation: {e}")
        return {"input_violates_rules": False, "output_violates_rules": False}
