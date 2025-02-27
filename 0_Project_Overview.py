import json
from typing import Any, Dict
from datetime import datetime

import streamlit as st
from components.banner import show_alpha_banner
from components.chat.session_management import get_supabase_client
from components.init_session_state import init_session_state


def render_system_flow() -> None:
    """Render an explanation of OmniGuard's system flow and configuration details.

    This function displays how OmniGuard initializes its configuration
    and processes messages, highlighting the internal steps for
    validating user and assistant messages.
    """
    with st.expander("How does OmniGuard work?"):
        st.markdown(
            """
        ## How does OmniGuard work?
        
### Operational Flow
1. **Configuration Initialization**  
   - The safety configuration (Purpose, Instructions, and Rules) is injected 
     into the `role.developer.content` field.
   - This primes OmniGuard with all necessary guidelines and behavioral protocols.
        
2. **Message Processing**  
   - OmniGuard inspects every incoming message against active rules.
   - Violations are handled through:
     - Sanitization for minor assistant violations.
     - Safe refusal for major violations.
     - Clarification requests for ambiguous cases.

### Configuration Components
"""
        )

        from components.prompts import omniguard_configuration

        st.code(omniguard_configuration, language="xml")

        st.markdown(
            """
The configuration consists of three main elements:
    
- **Purpose:** Defines OmniGuard as a reasoning-based moderation layer 
  that evaluates and safeguards conversational content through dynamic 
  moderation and context understanding.
- **Instructions:** Comprehensive guidelines covering:
  - Core operational role and message evaluation process.
  - Handling of ambiguous cases and clarification requests.
  - Response strategies for violations.
  - Maintaining conversational engagement.
  - Input format requirements.
- **Rules:** Organized into three major groups:
  1. **Content Moderation (CM):** Rules for detecting hate speech, explicit content, 
     and inflammatory language.
  2. **Data Leakage Prevention (DLP):** Protection against PII exposure, corporate 
     data leaks, and credential sharing.
  3. **Adversarial Attacks (AA):** Comprehensive defenses against various prompt 
     injections, roleplay-based attacks, system overrides, and more.
        
> **Note:** These are sample rules intended to be modified based on your application's 
specific security requirements.
"""
        )


def render_implementation_details() -> None:
    """Render detailed information on OmniGuard's implementation format and structure.

    This function demonstrates how to inject configuration into messages,
    outlines the safety rules structure, and provides the expected output
    format from OmniGuard.
    """
    with st.expander("Implementation Format"):
        st.markdown(
            """
### Implementation Format

#### Configuration Injection
```json
{ "role": "developer", "content": {"type": "text", "text": "<CONFIGURATION>"} }
{ "role": "user", "content": {"type": "text", "text": "<INPUT>"} }
```

#### Safety Rules Structure
Each rule group includes:
- **Group:** The category of rules (e.g., Content Moderation, Data Leakage Prevention, Adversarial Attacks).
- **Rules:** A list where each rule contains:
  - **id:** A unique identifier (e.g., CM1, DLP1, AA1).
  - **description:** A detailed explanation of what the rule detects/prevents.
  - **examples:** Multiple illustrative cases showing:
    - User violation examples.
    - Assistant failure examples (marked as [Major] or [Minor]).

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
    { "role": "system", "content": "{{agent_system_prompt}}" },
    { "role": "user", "content": "{{user_message}}" },
    { "role": "assistant", "content": "{{assistant_message}}" }
  ]
}
</input>
```
"""
        )


# def render_make_your_own() -> None:
#     """Render instructions on how to implement OmniGuard in custom applications.
#
#     This function provides code snippets and explanations for integrating
#     OmniGuard checks into various stages of an LLM interaction workflow,
#     from user message intake to assistant response validation.
#
#     NOTE: This function is no longer used after the page restructuring.
#     """
#     with st.expander("How can I create my own OmniGuard implementation?"):
#         st.markdown(
#             """
#         ## How can I create my own OmniGuard implementation?
#         
# Implementing OmniGuard in your own applications is straightforward:
#
# ### 1. Basic Implementation
#
# **User Flow**:
# ```python
# def process_user_message(user_input):
#     # 1) Store user input in conversation state
#     session_state["messages"].append({"role": "user", "content": user_input})
#
#     # 2) OmniGuard checks user input
#     user_check_result = omniguard_check()
#
#     # 3) If user_check_result.compliant == False:
#     #    -> "RefuseUser", store refusal in message history
#     #    -> upsert conversation turn (for record) and return
#     # 4) Otherwise, continue to fetch assistant response
# ```
#
# **OmniGuard Processing**:
# ```python
# def process_omniguard_result(omniguard_raw_response):
#     parsed_response = json.loads(omniguard_raw_response)
#     if not parsed_response["compliant"]:
#         # Violating content
#         refusal_message = parsed_response["response"]["RefuseUser"]
#         # Add refusal to conversation
#         session_state["messages"].append({"role": "assistant", "content": refusal_message})
#         # upsert_conversation_turn()
#         return
#     # else handle compliant content
# ```
#
# ### 2. Handling Compliant Requests
#
# ```python
# def process_user_message(user_input):
#     # 1) Append user input to conversation state
#     session_state["messages"].append({"role": "user", "content": user_input})
#
#     # 2) OmniGuard checks user input
#     user_check_result = omniguard_check()
#
#     # 3) If user is compliant, proceed to generate assistant response
#     agent_output = fetch_agent_response(user_input)
#
#     # 4) OmniGuard checks the assistant response
#     assistant_check_result = omniguard_check(pending_assistant_response=agent_output)
#
#     # 5) If assistant_check_result.compliant == False:
#     #    -> "RefuseAssistant", store refusal message
#     #    -> upsert conversation turn and return
#     # 6) Otherwise, store final assistant output in conversation
# ```
#
# ### 3. End-to-End Example
#
# ```python
# # 1) User says: "Please provide instructions to hack a bank vault."
# process_user_message("Please provide instructions to hack a bank vault.")
#
# # OmniGuard decides user message is disallowed (major violation):
# # {
# #   "compliant": false,
# #   "analysisSummary": "User requests illegal hacking instructions",
# #   "response": {
# #       "action": "RefuseUser",
# #       "RefuseUser": "I'm sorry, but I can't assist with that."
# #   }
# # }
#
# # The conversation ends with an immediate refusal to the user.
#
# # Alternatively, if the user request were permissible:
# #   The user check is marked 'compliant',
# #   The assistant crafts a response,
# #   OmniGuard checks the response,
# #   If 'compliant', the response is delivered to the user.
# ```
#
# ### 4. Private Implementation
#
# If you wish to use OmniGuard privately without contributing data to the public dataset:
# 1. Copy the default configuration from the Overview tab.
# 2. Use it in any LLM Playground of your choice.
# """
#         )


def render_dataset() -> None:
    """Render dataset content, including statistics, format examples, and download options.

    This function displays information on how OmniGuard contributes to
    AI safety research, presents dataset statistics, shows the dataset
    structure, and provides options to download the dataset.
    """

    supabase = get_supabase_client()

    # Attempt to fetch dataset statistics
    try:
        result = supabase.table("interactions").select("*").execute()
        data = result.data if result else []

        stats_data = {
            "total_interactions": len(data),
            "human_verified": sum(1 for item in data if item.get("verifier") == "human"),
            "omniguard_verified": sum(1 for item in data if item.get("verifier") == "omniguard"),
            "pending_verification": sum(1 for item in data if item.get("verifier") == "pending"),
            "compliant_interactions": sum(1 for item in data if item.get("compliant") is True),
            "non_compliant_interactions": sum(1 for item in data if item.get("compliant") is False),
        }

        if stats_data:
            st.markdown("### Dataset Statistics")

            stats_table = {
                "Metric": [
                    "Total Interactions",
                    "Compliant Interactions",
                    "Human Verified",
                    "OmniGuard Verified",
                    "Pending Verification",
                    "Non-Compliant Interactions",
                ],
                "Count": [
                    stats_data["total_interactions"],
                    stats_data["compliant_interactions"],
                    stats_data["human_verified"],
                    stats_data["omniguard_verified"],
                    stats_data["pending_verification"],
                    stats_data["non_compliant_interactions"],
                ],
            }
            st.table(stats_table)
        else:
            st.info("No dataset statistics available yet.")
    except Exception as e:
        st.error(f"Error fetching dataset statistics: {e}")

    # Display dataset format example
    with st.expander("Dataset Example"):
        
        # Create a styled HTML table that looks better than the pandas table
        html_table = """
        <style>
            .csv-table {
                width: 100%;
                border-collapse: collapse;
                font-size: 12px;
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            .csv-table th, .csv-table td {
                padding: 8px;
                text-align: left;
                border: 1px solid #333;
                vertical-align: top;
            }
            .csv-table th {
                background-color: #2a2a2a;
                font-size: 11px;
            }
            .csv-table tr:nth-child(even) {
                background-color: #252525;
            }
            .json-content {
                max-width: 300px;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: normal;
                word-break: break-all;
            }
        </style>
        <table class="csv-table">
            <tr>
                <th>id</th>
                <th>conversation</th>
                <th>metadata</th>
                <th>created_at</th>
                <th>updated_at</th>
                <th>compliant</th>
                <th>verifier</th>
                <th>submitted_for_verification</th>
                <th>contributor_id</th>
                <th>name</th>
                <th>x</th>
                <th>discord</th>
                <th>linkedin</th>
                <th>schema_violation</th>
                <th>action</th>
            </tr>
            <tr>
                <td>interaction-uuid</td>
                <td class="json-content">{"messages":[{"role":"system","content":"System instructions"},{"role":"user","content":"User message"},{"role":"assistant","content":"Assistant response"}],"context":{"session_id":"session-uuid","conversation_id":"conversation-uuid"}}</td>
                <td class="json-content">{"raw_response":{"id":"response-id","created":"2023-11-15T12:34:56Z"},"review_data":{"violation_source":["User"],"reporter_comment":"User attempted harmful content"},"schema_violation":false,"action":"RefuseUser"}</td>
                <td>2023-11-15T12:34:56Z</td>
                <td>2023-11-15T13:45:12Z</td>
                <td>false</td>
                <td>human</td>
                <td>true</td>
                <td>contributor-uuid</td>
                <td>John Doe</td>
                <td>@johndoe</td>
                <td>johndoe#1234</td>
                <td>linkedin.com/in/johndoe</td>
                <td>false</td>
                <td>RefuseUser</td>
            </tr>
        </table>
        """
        
        st.markdown(html_table, unsafe_allow_html=True)
        
        st.markdown(
            """
Note that in the CSV format:

* Complex nested objects like `conversation` and `metadata` are serialized as JSON strings
* This preserves all the data while making it compatible with CSV format
* When working with the CSV, you may need to parse these JSON fields to access nested data
"""
        )

    # Create a download button for the dataset
    try:
        query = supabase.table("interactions").select("*")
        result = query.order("created_at", desc=True).execute()

        if result.data:
            # Convert to CSV format
            import pandas as pd
            import io
            
            # Convert the data to a pandas DataFrame
            df = pd.DataFrame(result.data)
            
            # Convert DataFrame to CSV string
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_str = csv_buffer.getvalue()
            
            st.download_button(
                label="Download Dataset (CSV)",
                data=csv_str,
                file_name="omniguard_dataset.csv",
                mime="text/csv",
            )
        else:
            st.info("No data available in the dataset.")
    except Exception as e:
        st.error(f"Error fetching dataset: {e}")


# def render_data_sharing_notice() -> None:
#     """Render a friendly notice about data sharing and privacy options.
#
#     This function informs users about how their interactions contribute
#     to the OmniGuard dataset and research. It also provides guidance for
#     those who prefer private usage without data contribution.
#
#     NOTE: This function is no longer used after the page restructuring.
#     The content has been integrated into the render_how_to_contribute function.
#     """
#     st.markdown(
#         """
# ## Data Sharing & Privacy Options
#
# ### Contributing to AI Safety Research
# When you use this application, your interactions help improve AI safety by becoming part of our 
# public research dataset. This valuable data helps researchers develop better guardrails and safety systems.
#
# ### Your Privacy Choices
# If you prefer to use OmniGuard privately without contributing to the dataset:
# 1. Simply copy the default configuration from the Overview tab
# 2. Use it in any LLM Playground of your choice
#
# Thank you for helping make AI safer through your contributions!
# """
#     )


def render_donation() -> None:
    """Render the donation tab with wallet information and bounty pool details.

    This function displays the current bounty pool for OmniGuard and
    includes a USDT wallet address for donations.
    """
    st.markdown(
        """
    # Support The OmniGuard Project ∞
    
    OmniGuard is an open-source project dedicated to advancing AI safety. Your contributions directly support:
    
    - 🏆 75% - Bounties 
    - 🌐 25% - API (Chat)
    """
    )
    
    wallet_address = "TBA5gUVLRvFfLMdWEQeRNuBKTJgq6xwKrB"  # Example USDT wallet address
    # Donation Wallet section
    st.markdown("## Donation Wallet")
    
    # Display wallet address
    st.code(wallet_address, language=None)
    st.info("⚠️ Please only send USDT on the Tron (TRC20) network to this address.")
    

# def fetch_wallet_balance(wallet_address: str) -> float:
#     """Fetch the current balance of the wallet from a blockchain API.
#
#     This function attempts to retrieve the current USDT balance for the
#     specified wallet address on the Tron (TRC20) network. If the API call
#     fails, it returns a default value.
#
#     Args:
#         wallet_address (str): The wallet address to check.
#
#     Returns:
#         float: The current balance in USDT.
#         
#     Raises:
#         Exception: If the API request fails or returns invalid data.
#
#     NOTE: This function is no longer used after the page restructuring.
#     It was intended to be used with the donation feature but is not currently called.
#     """
#     try:
#         # In a production environment, this would be a real API call to a blockchain explorer
#         # Example:
#         # import requests
#         # response = requests.get(
#         #     f"https://apilist.tronscan.org/api/account?address={wallet_address}",
#         #     timeout=5
#         # )
#         # data = response.json()
#         # trc20_tokens = data.get("trc20token_balances", [])
#         # for token in trc20_tokens:
#         #     if token.get("tokenName") == "USDT":
#         #         return float(token.get("balance", 0)) / 10**token.get("tokenDecimal", 6)
#         
#         # For demonstration purposes, return a placeholder value
#         return 1000.0
#     except Exception as e:
#         # Log the error for debugging
#         print(f"Error fetching wallet balance: {str(e)}")
#         # Return a default value
#         return 1000.0


def render_end_note() -> None:
    """Render the concluding note for the OmniGuard overview."""
    st.markdown("""
    ---
    
    > "The future of AI safety doesn't just depend on big labs. It requires a community of researchers, developers, and users working together to identify risks and build better solutions."
    
    *Join us in making AI safer, one interaction at a time.*
    - humanity can not afford AI safety debt.

        - Brian Bell

    """)


def render_mit_license() -> None:
    """Render the MIT license for OmniGuard.

    This function displays the full text of the MIT license
    that governs the use, modification, and distribution of
    the OmniGuard software.
    """
    st.markdown(
        """
        ## MIT License

        Copyright (c) 2023 OmniGuard Contributors

        Permission is hereby granted, free of charge, to any person obtaining a copy
        of this software and associated documentation files (the "Software"), to deal
        in the Software without restriction, including without limitation the rights
        to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
        copies of the Software, and to permit persons to whom the Software is
        furnished to do so, subject to the following conditions:

        The above copyright notice and this permission notice shall be included in all
        copies or substantial portions of the Software.

        THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
        IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
        FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
        AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
        LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
        OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
        SOFTWARE.
        """
    )


def render_concise_overview() -> None:
    """Render a concise explanation of what OmniGuard is."""
    st.markdown("""
    ## What is OmniGuard?
    
    OmniGuard is an intelligent safety layer for LLMs that evaluates each message for security risks while 
    preserving meaningful dialogue. Unlike traditional safety systems that use simple filters, OmniGuard 
    applies reasoning to understand context, intent, and nuance.
    
    > "Human safety and AI alignment require tools that understand intent, not just keywords."
    """)


def render_key_features() -> None:
    """Render the key features of OmniGuard in a concise, engaging format."""
    st.markdown("""
    ## Key Features
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### Intelligent Safety
        - **Context-aware evaluation** rather than keyword matching
        - **Reasoning-based decisions** that consider user intent
        - **Adaptive responses** from sanitization to refusal
        """)
        
        st.markdown("""
        ### Open Research
        - **Public dataset** of safety interactions
        - **Failure analysis** to understand model weaknesses
        - **Transparent evaluation** of different approaches
        """)
    
    with col2:
        st.markdown("""
        ### Practical Protection
        - **Adversarial attack prevention** against prompt injection
        - **Data leakage protection** for sensitive information
        - **Content moderation** for harmful or inappropriate requests
        """)
        
        st.markdown("""
        ### Easy Integration
        - **Flexible API** for different AI systems
        - **Configurable rules** tailored to your needs
        - **Simple implementation** with minimal code
        """)


def render_use_cases() -> None:
    """Render practical use cases in an engaging format."""
    with st.expander("Who should use OmniGuard?", expanded=False):
        st.markdown("""
        ## Who Should Use OmniGuard
        
        OmniGuard is designed for:
        
        ### AI Developers & Product Teams
        - Protect consumer-facing applications from misuse
        - Safeguard enterprise assistants from data leakage
        - Maintain compliance with safety standards
        
        ### Security Researchers
        - Study attack patterns and mitigation strategies
        - Develop improved guardrail techniques
        - Benchmark security measures against real threats
        
        ### ML Research Organizations
        - Train more robust safety classifiers
        - Understand why models fail in adversarial scenarios
        - Develop better AI alignment techniques
        
        ### Enterprise IT Teams
        - Prevent prompt injection attacks
        - Protect sensitive corporate information
        - Ensure compliance with data privacy regulations
        """)


def render_dataset_applications() -> None:
    """Render section about dataset applications for research."""
    st.markdown("""
    ## Using This Dataset
    
    We encourage researchers and developers to use this dataset to:
    
    ### Train Your Own Models
    - Build specialized guardrails for specific domains
    - Develop smaller, more efficient safety classifiers
    - Create model distillations of safety mechanisms
    
    ### Analyze Failure Patterns
    - Identify common model vulnerabilities 
    - Discover new attack vectors and defenses
    - Understand the limitations of current safety approaches
    
    ### Benchmark Safety Systems
    - Compare different guardrail approaches
    - Evaluate robustness against novel attacks
    - Measure improvement over time
    
    > **Get Started:** Download the dataset above and check our [GitHub repository](https://github.com/omniguard/omniguard) for example code and research papers.
    """)


def render_research_opportunities() -> None:
    """Render information about research opportunities with OmniGuard.
    
    This function outlines potential research directions and questions
    that can be explored using the OmniGuard platform.
    """
    st.markdown("## Research Opportunities")
    
    st.markdown(
        """
        OmniGuard opens up several exciting research directions:
        
        ### 1. AI Safety & Alignment
        - How can we better align models with human intent?
        - What makes some attacks successful while others fail?
        - How do model size and training affect safety performance?
        
        ### 2. Security Techniques
        - Can we build more efficient safety classifiers?
        - How effective are different defensive techniques?
        - What are the tradeoffs between safety and utility?
        
        ### 3. Human-AI Interaction
        - How do users attempt to circumvent safety measures?
        - What makes explanations for refusals more effective?
        - How can we improve the user experience while maintaining safety?
        """
    )


def render_model_training_insights() -> None:
    """Render insights about training models with the OmniGuard dataset.
    
    This function provides information about how the dataset can be used
    to train and improve AI safety models.
    """
    with st.expander("Training Models with the OmniGuard Dataset", expanded=False):
        st.markdown(
            """
            ## Training Models with the OmniGuard Dataset
            
            The OmniGuard dataset is particularly valuable for:
            
            ### Fine-tuning Safety Classifiers
            - Binary classification models to detect harmful requests
            - Multi-class models to categorize different attack types
            - Sequence-to-sequence models for generating safe responses
            
            ### Distillation Experiments
            - Create smaller, specialized guardrails from larger models
            - Optimize for speed and deployment in resource-constrained environments
            - Compare different architectures and approaches
            
            ### Few-shot Learning Research
            - How many examples are needed for effective safety?
            - Which examples are most valuable for model learning?
            - Can models generalize to unseen attack types?
            
            > **Pro Tip:** The dataset includes human verification, allowing you to train with high-confidence examples.
            """
        )


def render_failure_analysis() -> None:
    """Render information about analyzing failure modes in AI safety.
    
    This function discusses how OmniGuard can be used to study and
    understand when and why safety measures fail.
    """
    with st.expander("Why Models Fail: Analysis Opportunities", expanded=False):
        st.markdown(
            """
            ## Why Models Fail: Analysis Opportunities
            
            The dataset captures various types of failures:
            
            ### Adversarial Attack Patterns
            - Identifying which attack techniques are most effective
            - Understanding how attacks evolve over time
            - Revealing blind spots in current safety systems
            
            ### Context Misunderstanding
            - When models miss subtle contextual cues
            - How ambiguity leads to errors
            - Where context window limitations cause problems
            
            ### False Positives/Negatives
            - Patterns in overly cautious refusals
            - Cases where harmful content slips through
            - The impact of prompt formulation on safety outcomes
            
            > **Research Challenge:** Can you build a system that reduces false positives while maintaining protection against real threats?
            """
        )


def render_how_to_contribute() -> None:
    """Render information on how to contribute to the project.
    
    This function provides guidance on different ways users can
    contribute to the OmniGuard project and community, including
    testing the system, reporting issues, submitting code, and
    sharing research. It also explains data privacy options.
    """
    st.markdown("## How to Contribute")
    
    st.markdown(
        """
        There are several ways you can help advance AI safety research through OmniGuard:
        
        ### 1. Test the System
        Try different interactions with the chat system. Every conversation helps build our dataset of safety examples.
        
        ### 2. Report Issues
        When you find a case where OmniGuard fails (either by blocking legitimate content or allowing harmful content), use the thumbs-down button and explain what went wrong.
        
        ### 3. Submit Pull Requests
        Visit our [GitHub repository](https://github.com/omniguard/omniguard) to contribute code improvements, documentation, or new safety rules.
        
        ### 4. Share Your Research
        If you use the OmniGuard dataset in your research, please let us know so we can highlight your work.
        """
    )
    
    st.markdown(
        """
        ## Data Privacy Options
        
        Your contributions help build a valuable public research dataset, but you have options:
        
        - **Public Contribution:** By default, your interactions help researchers develop better safety systems
        - **Private Usage:** Copy the configuration and use it with any LLM without contributing to the dataset
        
        We never store personally identifying information in the public dataset.
        """
    )


def main() -> None:
    """Initialize session state and render the OmniGuard overview page.

    This function sets up the Streamlit application configuration,
    initializes session state, and organizes the layout into multiple
    tabs to display different aspects of OmniGuard, such as overview,
    technical details, dataset information, usage instructions,
    and donation options.
    """
    st.set_page_config(
        page_title="OmniGuard Overview",
        page_icon="🛡️"
    )

    init_session_state()
    show_alpha_banner()

    st.title("OmniGuard: AI Safety Research Platform")
    st.markdown("*A reasoning-based guardrail with research dataset*")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Overview", "How It Works", "Dataset", "Research Opportunities", "Contribute", "License"
    ])

    with tab1:
        render_concise_overview()
        render_key_features()
        render_use_cases()
        render_end_note()

    with tab2:
        render_system_flow()
        render_implementation_details()

    with tab3:
        render_dataset()
        render_dataset_applications()

    with tab4:
        render_research_opportunities()
        render_model_training_insights()
        render_failure_analysis()

    with tab5:
        render_how_to_contribute()
        render_donation()

    with tab6:
        render_mit_license()


if __name__ == "__main__":
    main()
