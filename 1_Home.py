import streamlit as st
from prompts import CMS_configuration
from database import get_all_conversations, init_db, get_dataset_stats
from typing import Dict, Any

init_db()

st.set_page_config(page_title="OmniGuard", page_icon=":shield:")

def render_overview() -> None:
    st.title("OmniGuard - a Conversation Moderation System (CMS)")
    
    st.markdown("""
    ## 1. Component Overview

    - **OmniGuard** is a reasoning based moderation system for text-based LLM interactions.
    - It continuously runs rule violation assessment for each turn of user and assistant messages against a configurable set of content rules.
    - OmniGuard actively sanitizes minor violations and probes for clarification in ambiguous cases, thereby preserving an engaging and meaningful dialogue while upholding safety standards.
    - The system effectively mitigates the majority of potential violations and attacks through its comprehensive rule set and reasoning-based approach. Your contributions can make a real difference. **By sharing your insights and test cases, you'll help shape a safer, more robust AI ecosystem that benefits EVERYONE.**
    """)

    st.markdown("""
    **Disclaimer:** This system is designed to serve as a robust moderation layer rather than a comprehensive AI safety solution. OmniGuard segregates safety processes from the assistant's primary functions, ensuring that core operations remain performant while content is evaluated in real time.
    """)

def render_system_flow() -> None:
    st.markdown("---")
    st.markdown("""
    ## 2. System Flow

    1. **Configuration**  
       - The safety configuration which includes the Purpose, Instructions, and Rules is injected into the `role.developer.content` field.
       - This configuration primes OmniGuard with all necessary guidelines and behavioral protocols before any messages are processed.
    
    2. **Message Handling**  
       - OmniGuard inspects every incoming message to assess compliance with the active rules.
       - If a violation is detected, OmniGuard either sanitizes minor issues or, in cases of major violations, replaces the message with a safe, generic refusal.
       - When ambiguity exists, OmniGuard proactively asks for clarification to fully understand the user's intent before finalizing a moderation decision.
    """)

def render_configuration_details() -> None:
    st.markdown("---")
    st.markdown("""
    ## 3. Configuration Details

    ### 3.1 Configuration and Input Injection Strategy

    Inject these components using the following message format:

    ```json
    { "role": "developer", "content": {"type": "text", "text": "<CONFIGURATION>"} }
    { "role": "user", "content": {"type": "text", "text": "<CONVERSATION>"} }
    ```
    """)
    
    st.markdown("### 3.2 OmniGuard Configuration")
    st.markdown("""
    The configuration is composed of three main components:
    
    - **Purpose:** Clearly defines OmniGuard as a reasoning-based moderation layer that evaluates and safeguards conversational content.
    - **Instructions:** Detailed guidelines on evaluating messages, handling ambiguity, responding to violations, and maintaining conversational engagement.
    - **Rules:** Specific content policies that determine which messages are compliant or disallowed.
    """)
    
    with st.expander("Default Configuration:"):
        st.code(CMS_configuration, language="xml")
        st.write("`4111 Tokens`")

def render_format_details() -> None:
    st.markdown("""
    ### 3.3 Configuration Format Details

    #### Safety Rules

    Each rule group includes:
    - **Group:** The category of the rule.
    - **Rules:** A list where each rule contains:
      - **ruleId:** A unique identifier.
      - **description:** A concise summary of the rule.
      - **examples:** Illustrative cases of rule application.

    #### Operational Instructions

    Key components include:
    - **json_output_schema:** The structured JSON for OmniGuard's output.
    - **actions:** The possible responses:
      - **allow:** Proceeds normally if no violations are detected.
      - **UserInputRejection:** Returns a succinct, neutral refusal for problematic user inputs.
      - **AssistantOutputRejection:** Provides a sanitized or generic refusal for problematic assistant outputs.
    """)

def render_input_format() -> None:
    st.markdown("""
    ### 3.4 Input Format

    Conversations must adhere to this structure:
    - **id:** A unique conversation identifier.
    - **messages:** An array of message objects. Each message includes:
      - **role:** "system", "user", "assistant".
      - **content:** The message text.

    Example:
    ```xml
    <input>
      <![CDATA[
        {
          "id": "{{id}}",
          "messages": [
            { "role": "system", "content": "{{assistant_system_prompt}}" },
            { "role": "user", "content": "{{user_message}}" },
            { "role": "assistant", "content": "{{assistant_message}}" }
          ]
        }
      ]]>
    </input>
    ```
    """)

def render_additional_notes() -> None:
    st.markdown("""
    ### 3.5 Additional Notes
    
    - **Severity Level:** Severity levels were tested, they are not applied in the final implementation to avoid any bias.
    - **DEEPSEEK-R1:** This is not used due to reliance on structured outputs. It may be incorporated once it supports such formats.
    """)

def render_dataset_stats(stats: Dict[str, Any]) -> None:
    st.markdown("---")
    st.markdown("## Dataset")
    
    st.markdown(f"""
    ### Total Interactions: `{stats['total_sets']:,}`\n
    ### Successfully Rejected:
      - User: `{stats['user_violations']:,}`
      - Assistant: `{stats['assistant_violations']:,}`
    ### Contributors: `{stats['total_contributors']:,}`
    
    ### Token Usage:
      - Input: `{stats['total_prompt_tokens']:,}`
      - Output: `{stats['total_completion_tokens']:,}`
      - Total: `{stats['total_tokens']:,}`
    
    ### Costs (USD):
      - Input: `${stats['total_input_cost']:,.2f}`
      - Output: `${stats['total_output_cost']:,.2f}`
      - Total: `${stats['total_cost']:,.2f}`
    
    ### Average Latency: `{stats['avg_latency_ms']:,}ms`
    """)

def render_dataset_format() -> None:
    with st.expander("Dataset Format Example"):
        st.markdown("""
        The dataset is provided in JSONL format, with each line representing a single evaluation instance:

        ```json
        {
          "conversation_id": "Unique identifier for this evaluation instance",
          "cms_evaluation_input": {
            "configuration": "<configuration>Safety configuration with rules and instructions</configuration>",
            "conversation": "<input><![CDATA[{
              \\"id\\": \\"string\\",
              \\"messages\\": [
                {\\"role\\": \\"system\\", \\"content\\": \\"\\"},
                {\\"role\\": \\"user\\", \\"content\\": \\"\\"},
                {\\"role\\": \\"assistant\\", \\"content\\": \\"\\"}
              ]
            }]]></input>"
          },
          "cms_raw_response": {
            "conversation_id": "string",
            "analysisSummary": "Short note on triggered rules or 'No violations'.",
            "response": {
              "action": "allow | UserInputRejection | AssistantOutputRejection",
              "UserInputRejection": "string",
              "AssistantOutputRejection": "string"
            }
          },
          "assistant_output": "Final response from assistant (if CMS allowed the content)",
          "user_violates_rules": true,
          "assistant_violates_rules": false,
          "model_name": "Model used for OmniGuard evaluation",
          "reasoning_effort": "Level of reasoning effort applied",
          "contributor": "Who contributed this data point",
          "created_at": "2024-02-07T13:30:03.123Z",
          "prompt_tokens": 0,
          "completion_tokens": 0,
          "total_tokens": 0,
          "input_cost": 0.0000,
          "output_cost": 0.0000,
          "total_cost": 0.0000,
          "latency_ms": 0
        }
        ```
        """)

def render_dataset_download() -> None:
    training_data_jsonl = get_all_conversations(export_format="jsonl")
    st.download_button(
        label="Download Dataset",
        data=training_data_jsonl,
        file_name="training_data.jsonl",
        mime="application/jsonl"
    )

def main() -> None:
    render_overview()
    render_system_flow()
    render_configuration_details()
    render_format_details()
    render_input_format()
    render_additional_notes()
    
    stats = get_dataset_stats()
    render_dataset_stats(stats)
    render_dataset_format()
    render_dataset_download()

if __name__ == "__main__":
    main()
