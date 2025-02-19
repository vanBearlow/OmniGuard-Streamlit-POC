import streamlit as st
from typing import Dict, Any
from components.init_session_state import init_session_state

def render_overview() -> None:
    st.markdown("""
    ## 1. Component Overview

    - **OmniGuard** is a reasoning based conversation moderation system for text-based LLM interactions.
    - It continuously runs rule violation assessment for each turn of user and assistant messages against a configurable set of content rules.
    - OmniGuard actively sanitizes minor violations and probes for clarification in ambiguous cases, thereby preserving an engaging and meaningful dialogue while upholding safety standards.
    - The system effectively mitigates the majority of potential violations and attacks through its comprehensive rule set and reasoning-based approach. Together, we're building a safer, more robust AI ecosystem. Each contribution strengthens our collective defense against emerging threats, benefiting the entire AI community.
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
        # We keep the string import logic for demonstration but removed database calls
        from prompts import omniguard_configuration
        st.code(omniguard_configuration, language="xml")
        st.write("`4111 Tokens`")

def render_dataset_content() -> None:
    st.markdown("## Dataset")
    st.info("Dataset statistics temporarily unavailable")
    
    with st.expander("Dataset Format Example"):
        st.markdown("""
        The dataset is provided in JSONL format, with each line representing a single evaluation instance:

        ```json
        {
          "conversation_id": "Unique identifier for this evaluation instance",
          "omniguard_evaluation_input": {
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
          "omniguard_raw_response": {
            "conversation_id": "string",
            "analysisSummary": "Short note on triggered rules or 'No violations'.",
            "response": {
              "action": "allow | UserInputRefusal | AssistantOutputRefusal",
              "UserInputRefusal": "string",
              "AssistantOutputRefusal": "string"
            }
          },
          "assistant_output": "Final response from assistant (if OmniGuard allowed the content)",
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
          "latency_ms": 0,
          "needed_human_verification": false
        }
        ```
        """)
    
    # TODO: Implement dataset export from Supabase or other data store
    st.info("Dataset export is not implemented. Replace with your Supabase download logic.")

def render_notes() -> None:
    st.markdown("""
    ## Additional Notes
    
    ### Format Details

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
      - **UserInputRefusal:** Returns a succinct, neutral refusal for problematic user inputs.
      - **AssistantOutputRefusal:** Provides a sanitized or generic refusal for problematic assistant outputs.

    ### Input Format

    Conversations must adhere to this structure:
    - **id:** A unique conversation identifier.
    - **messages:** An array of message objects. Each message includes:
      - **role:** "system", "user", "assistant".
      - **content:** The message text.

    Example:
    ```xml
    <input>
        {
          "id": "{{id}}",
          "messages": [
            { "role": "system", "content": "{{assistant_system_prompt}}" },
            { "role": "user", "content": "{{user_message}}" },
            { "role": "assistant", "content": "{{assistant_message}}" }
          ]
        }
    </input>
    ```

    ### Implementation Notes
    
    - **Severity Level:** Severity levels were tested, they are not applied in the final implementation to avoid any bias.
    - **DEEPSEEK-R1:** This is not used due to reliance on structured outputs. It may be incorporated once it supports such formats.
    """)

def main() -> None:
    """Main function to render the project overview page."""
    st.set_page_config(
        page_title="OmniGuard Overview",
        page_icon="🛡️"
    )
    
    init_session_state()
    
    st.title("OmniGuard - Conversation Moderation System (ALPHA)")
    
    # Create three tabs
    overview_tab, dataset_tab, notes_tab = st.tabs(["Overview", "Dataset", "Notes"])
    
    # Content for Overview tab
    with overview_tab:
        render_overview()
        render_system_flow()
        render_configuration_details()
    
    # Content for Dataset tab
    with dataset_tab:
        render_dataset_content()
    
    # Content for Notes tab
    with notes_tab:
        render_notes()

if __name__ == "__main__":
    main()
