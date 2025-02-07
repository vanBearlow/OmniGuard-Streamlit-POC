import streamlit as st
from prompts import CMS_configuration
from database import get_all_conversations, init_db
init_db()

st.set_page_config(page_title="CMS", page_icon=":shield:")


def main():
    st.title("CMS - Conversational Moderation System")
    
    st.markdown("""
    ## 1. Component Overview

    - **CMS** is an advanced, reasoning-based moderation system for text-based LLM interactions.
    - It acts as an intelligent safeguard by continuously evaluating both user and assistant messages against a configurable set of content rules.
    - Leveraging advanced reasoning, CMS goes beyond simple keyword filtering understanding context, nuance, and user intent to ensure that only compliant, safe content progresses in the conversation.
    - CMS actively sanitizes minor violations and probes for clarification in ambiguous cases, thereby preserving an engaging and meaningful dialogue while upholding safety standards.
    """)


    st.markdown("""
    **Disclaimer:** This methodology is designed to serve as a robust moderation layer rather than a comprehensive AI safety solution. CMS segregates safety processes from the assistant’s primary functions, ensuring that core operations remain performant while content is evaluated in real time.
    """)
    
    st.markdown("---")
    
    st.markdown("""
    ## 2. System Flow

    1. **Configuration**  
       - The safety configuration which includes the Purpose, Instructions, and Rules is injected into the `role.developer.content` field.
       - This configuration primes CMS with all necessary guidelines and behavioral protocols before any messages are processed.
    
    2. **Message Handling**  
       - CMS inspects every incoming message to assess compliance with the active rules.
       - If a violation is detected, CMS either sanitizes minor issues or, in cases of major violations, replaces the message with a safe, generic refusal.
       - When ambiguity exists, CMS proactively asks for clarification to fully understand the user's intent before finalizing a moderation decision.
    """)
    
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
    
    st.markdown("### 3.2 CMS Configuration")
    st.markdown("""
    The configuration is composed of three main components:
    
    - **Purpose:** Clearly defines CMS as a reasoning-based moderation layer that evaluates and safeguards conversational content.
    - **Instructions:** Detailed guidelines on evaluating messages, handling ambiguity, responding to violations, and maintaining conversational engagement.
    - **Rules:** Specific content policies that determine which messages are compliant or disallowed.
    """)
    
    with st.expander("Default Configuration:"):
        st.code(CMS_configuration, language="xml")
        st.write("`4111 Tokens`")


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
    - **json_output_schema:** The structured JSON for CMS’s output.
    - **actions:** The possible responses:
      - **allow:** Proceed normally if no violations are detected.
      - **UserInputRejection:** Return a succinct, neutral refusal for problematic user inputs.
      - **AssistantOutputRejection:** Provide a sanitized or generic refusal for problematic assistant outputs.
    """)
    
    st.markdown("""
    ### 3.4 Input Format

    Conversations must adhere to this structure:
    - **id:** A unique conversation identifier.
    - **messages:** An array of message objects. Each message includes:
      - **role:** "user" or "assistant".
      - **content:** The message text.

    Example:

    ```json
    {
      "id": "{{id}}",
      "messages": [
        {"role": "user", "content": "{{message}}"},
        {"role": "assistant", "content": "{{message}}"}
      ]
    }
    ```
    """)
    
    st.markdown("""
    ### 3.5 Additional Notes
    
    - **Severity Level:** Severity levels were tested, they are not applied in the final implementation to avoid any bias.
    - **DEEPSEEK-R1:** This is not used due to reliance on structured outputs. It may be incorporated once it supports such formats.
    """)
    
    st.markdown("---")
    st.markdown("## Dataset")
    
    st.markdown("""
    The dataset is provided in JSONL format, with each line representing a single evaluation instance:

    ```json
    {
      "conversation_id": "Unique identifier for this evaluation instance",
      "cms_evaluation_input": [
        {
          "role": "developer",
          "content": "Safety configuration with rules and instructions"
        },
        {
          "role": "user",
          "content": "Current conversation context"
        }
      ],
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
      "model_name": "Model used for CMS evaluation",
      "reasoning_effort": "Level of reasoning effort applied",
      "contributor": "Who contributed this data point"
    }
    ```
    """)
    
    training_data_jsonl = get_all_conversations(export_format="jsonl")
    
    st.download_button(
        label="Download Dataset",
        data=training_data_jsonl,
        file_name="training_data.jsonl",
        mime="application/jsonl"
    )

if __name__ == "__main__":
    main()
