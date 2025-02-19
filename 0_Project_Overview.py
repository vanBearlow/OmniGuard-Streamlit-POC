import streamlit as st
from typing import Dict, Any
from components.init_session_state import init_session_state

def render_overview() -> None:
    st.markdown("""
    ## 1. Component Overview

    - **OmniGuard** is a reasoning based conversation moderation system for text-based LLM interactions.
    - It assesses each turn of user and assistant messages against a configurable set of content rules.
    - OmniGuard can sanitize minor violations and probe for clarification in ambiguous cases, thereby preserving an engaging and meaningful dialogue while upholding safety standards.
    - The system effectively mitigates the majority of potential violations and attacks through its comprehensive rule set and reasoning capabilities.
      
    
    > **Note:** This is not intended to be a full AI security solution; rather, it is designed to effectively protect wrappers and agents from most attacks without decreasing the performance.
    """)

def render_system_and_configuration() -> None:
    st.markdown("---")
    st.markdown("""    ## 2. System Flow and Configuration

    ### 2.1 Operational Flow
    1. **Configuration Initialization**  
       - The safety configuration (Purpose, Instructions, and Rules) is injected into the `role.developer.content` field
       - This primes OmniGuard with all necessary guidelines and behavioral protocols
    
    2. **Message Processing**  
       - OmniGuard inspects every incoming message against active rules
       - Violations are handled through:
         - Sanitization for minor issues
         - Safe, generic refusal for major violations
         - Clarification requests for ambiguous cases

    ### 2.2 Configuration Components""")

    with st.expander("Default Configuration:"):
        # We keep the string import logic for demonstration but removed database calls
        from prompts import omniguard_configuration
        st.code(omniguard_configuration, language="xml")
        st.write("`4111 Tokens`")

    st.markdown("""


    The configuration consists of three main elements:
    
    - **Purpose:** Defines OmniGuard as a reasoning-based moderation layer that evaluates and safeguards conversational content through dynamic moderation and context understanding.
    - **Instructions:** Comprehensive guidelines covering:
        - Core operational role and message evaluation process
        - Handling of ambiguous cases and clarification requests
        - Response strategies for violations
        - Maintaining conversational engagement
        - Input format requirements
    - **Rules:** Organized into three major groups :
        1. **Content Moderation (CM):** Rules for detecting hate speech, explicit content, and inflammatory language
        2. **Data Leakage Prevention (DLP):** Protection against PII exposure, corporate data leaks, and credential sharing
        3. **Adversarial Attacks (AA):** Comprehensive defenses against:
            - Direct/Indirect Prompt Injection
            - Contextual/Few-Shot Injection
            - Encoding/Obfuscation Techniques
            - Multi-Step/Progressive Escalation
            - Roleplay-Based Attacks
            - System Override Attempts
            - Instructional Inconsistency Exploitation
            - Model Inversion/Data Extraction
            - Prompt Leakage Exploits
            - Jailbreak Chaining Methods
            - Instruction-Following Bias Exploitation
            - Multimodal Adversarial Attacks
            > **Note:** These are sample rules intended to be modified based on your application's specific security requirements.

    ### 2.3 Implementation Format

    #### Configuration Injection
    ```json
    { "role": "developer", "content": {"type": "text", "text": "<CONFIGURATION>"} }
    { "role": "user", "content": {"type": "text", "text": "<INPUT>"} }
    ```

    #### Safety Rules Structure
    Each rule group includes:
    - **Group:** The category of rules (e.g., Content Moderation, Data Leakage Prevention, Adversarial Attacks)
    - **Rules:** A list where each rule contains:
      - **id:** A unique identifier (e.g., CM1, DLP1, AA1)
      - **description:** A detailed explanation of what the rule detects/prevents
      - **examples:** Multiple illustrative cases showing:
        - User violation examples
        - Assistant failure examples (marked as [Major] or [Minor])

    #### OmniGuard Output Format
    ```json
    {
        "conversation_id": "string",
        "analysisSummary": "string",
        "compliant": boolean,
        "response": {
            "action": "RefuseUser | RefuseAssistant",
            "RefuseUser | RefuseAssistant": "string"
        }
    }
    ```

    #### Input Structure
    ```json
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
    """)
    


    st.markdown("> **Note:** The rules presented above are configured as test rules for this application. They are designed to be modified and updated based on your specific needs. You can customize the rule sets, add new rules, or modify existing ones to align with your organization's security requirements and use cases.")

def render_goals() -> None:
    st.markdown("---")
    st.markdown("""
    ## 4. Goals and Future Vision

    OmniGuard is committed to advancing the field of AI safety through three key initiatives:

    1. **Open Safety Research Data**
       - Providing a comprehensive, freely accessible dataset of safety-related interactions
       - Enabling researchers and developers to study, analyze, and improve AI safety mechanisms
       - Contributing to the collective understanding of AI safety challenges and solutions

    2. **Multimodal Safety Expansion**
       - Extending OmniGuard's capabilities beyond text to include:
         - Image moderation and safety analysis
         - Audio content verification
         - Video content safety assessment
       - Developing unified safety protocols across different modalities

    3. **Model Distillation**
       - Leveraging the collected dataset to create smaller, more efficient safety models.
       - Reducing computational overhead while maintaining robust safety standards.
       - Making AI safety more accessible and deployable across different scales of applications.

    Through these initiatives, OmniGuard aims to foster innovation in AI safety while ensuring that safety mechanisms remain accessible and effective for the entire AI community.
    """)

def render_dataset_content() -> None:

    st.info("Dataset statistics temporarily unavailable")
    
    with st.expander("Dataset Format Example"):
        st.markdown("""
        The dataset is provided in JSONL format, with each line representing a single evaluation instance:

        ```json
        {TODO: Add example}
        ```
        """)
    
    # TODO: Implement dataset export from Supabase or other data store
    st.info("Dataset export is not implemented. Replace with your Supabase download logic.")

def render_disclaimer() -> None:
    #Todo: Update this when all data is confirmed.
    
    st.markdown("""

    ### Using OmniGuard
                
    All interactions within this application will be made public and added to the dataset. (Free for use)

    If you wish to use OmniGuard privately without contributing data to the public dataset:
    1. Copy the default configuration from the Overview tab
    2. Use it in any LLM Playground of your choice.
    """)

def main() -> None:
    """Main function to render the project overview page."""
    st.set_page_config(
        page_title="OmniGuard Overview",
        page_icon="🛡️"
    )
    
    init_session_state()
    
    st.title("OmniGuard - Conversation Moderation System (ALPHA)")
    
    # Updated tabs to remove notes tab
    overview_tab, dataset_tab, disclaimer_tab = st.tabs(["Overview", "Dataset", "Disclaimer"])
    
    # Content for all tabs
    with overview_tab:
        render_overview()
        render_system_and_configuration()
        render_goals()
      
    with dataset_tab:
        render_dataset_content()
        
    with disclaimer_tab:
        render_disclaimer()

if __name__ == "__main__":
    main()
