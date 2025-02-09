import streamlit as st
from prompts import omniguard_configuration
from database import get_all_conversations, init_db, get_dataset_stats
from typing import Dict, Any
from components.auth import render_auth_status
from components.init_session_state import init_session_state
from components.api_balance import display_api_balance

# Initialize database and session
init_db()
init_session_state()

st.set_page_config(page_title="OmniGuard", page_icon=":shield:")  # never use layout="wide"

# Render authentication status in sidebar
render_auth_status()

# Table of Contents in sidebar
st.sidebar.markdown("## Table of Contents")
st.sidebar.markdown("""
- [Overview](#overview)
- [System Flow](#system-flow)
- [Configuration Details](#configuration-details)
- [Dataset](#dataset)
- [Project Info](#project-info)
""", unsafe_allow_html=True)

def render_overview() -> None:
    st.markdown('<a name="overview"></a>', unsafe_allow_html=True)
    st.title("OmniGuard - Conversation Moderation System (BETA)")
  
    st.markdown("""
    ## 1. Component Overview

    - **OmniGuard** is a reasoning based conversation moderation system for text-based LLM interactions.
    - It continuously runs rule violation assessment for each turn of user and assistant messages against a configurable set of content rules.
    - OmniGuard actively sanitizes minor violations and probes for clarification in ambiguous cases, thereby preserving an engaging and meaningful dialogue while upholding safety standards.
    - The system effectively mitigates the majority of potential violations and attacks through its comprehensive rule set and reasoning-based approach. Together, we're building a safer, more robust AI ecosystem. Each contribution strengthens our collective defense against emerging threats, benefiting the entire AI community.
    """)
  
def render_system_flow() -> None:
    st.markdown('<a name="system-flow"></a>', unsafe_allow_html=True)
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
    st.markdown('<a name="configuration-details"></a>', unsafe_allow_html=True)
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
        st.code(omniguard_configuration, language="xml")
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

@st.cache_data(show_spinner=False)
def cached_get_dataset_stats() -> Dict[str, Any]:
    return get_dataset_stats()

def render_dataset_stats(stats: Dict[str, Any]) -> None:
    st.markdown("---")
    st.markdown('<a name="dataset"></a>', unsafe_allow_html=True)
    st.markdown("## Dataset")
    
    if not stats:
        st.warning("⚠️ Dataset statistics temporarily unavailable")
        return
        
    # Calculate percentage of conversations needing human verification
    verification_percentage = (stats['needed_human_verification'] / stats['total_sets'] * 100) if stats['total_sets'] > 0 else 0
    
    st.markdown(f"""
    ### Total Interactions: `{stats['total_sets']:,}`  
    ### Successfully Rejected:
      - User: `{stats['user_violations']:,}`
      - Assistant: `{stats['assistant_violations']:,}`
    ### Human Verification Needed: `{stats['needed_human_verification']:,}` (`{verification_percentage:.1f}%`)
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
              "action": "allow | UserInputRejection | AssistantOutputRejection",
              "UserInputRejection": "string",
              "AssistantOutputRejection": "string"
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

def render_dataset_download() -> None:
    # Initialize download progress
    progress_placeholder = st.empty()
    
    # Get first page to get total pages
    result = get_all_conversations(export_format="jsonl", page=1)
    total_pages = result["total_pages"]
    
    if total_pages == 0:
        st.info("No data available for download.")
        return
    
    # Collect all pages
    all_data = []
    progress_bar = st.progress(0)
    
    for page in range(1, total_pages + 1):
        progress_placeholder.text(f"Preparing download... Page {page} of {total_pages}")
        result = get_all_conversations(export_format="jsonl", page=page)
        all_data.append(result["data"])
        progress_bar.progress(page / total_pages)
    
    # Combine all pages
    complete_data = "\n".join(all_data)
    
    # Clear progress indicators
    progress_placeholder.empty()
    progress_bar.empty()
    
    # Show download button with improved tooltip for accessibility
    st.download_button(
        label="Download Complete Dataset",
        data=complete_data,
        file_name="training_data.jsonl",
        mime="application/jsonl",
        help="Click to download the complete dataset. Contains all records available."
    )

def render_project_info() -> None:
    st.markdown("---")
    st.markdown('<a name="project-info"></a>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.header("Project Costs")
        st.markdown("""
- **Development and Testing**: $25  
- **API Usage**: See dataset costs above  
- **Infrastructure**: $0 (Using Streamlit Community Cloud)
        """)
    with col2:
        st.header("Project Development Time")
        st.markdown("""
- **Start Date**: 2025-02-01  
- **Current Status**: Beta Testing  
- **Development Duration**: 1 week  
- **Testing Phase**: Ongoing
        """)

def main() -> None:
    render_overview()
    render_system_flow()
    render_configuration_details()
    render_format_details()
    render_input_format()
    render_additional_notes()
    
    with st.spinner("Loading dataset statistics..."):
        stats = cached_get_dataset_stats()
    render_dataset_stats(stats)
    render_dataset_format()
    render_dataset_download()
    render_project_info()

if __name__ == "__main__":
    main()