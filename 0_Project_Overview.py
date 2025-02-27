import json
from typing import Any, Dict
from datetime import datetime

import streamlit as st
from components.banner import show_alpha_banner
from components.chat.session_management import get_supabase_client
from components.init_session_state import init_session_state


def render_what_is_omniguard() -> None:
    """Render a Q&A section describing what OmniGuard is.

    This function uses an expander in Streamlit to present an
    introduction to OmniGuard. It provides an overview of its
    purpose and key benefits, explaining how it intelligently
    moderates LLM interactions.
    """
    with st.expander("What is OmniGuard?"):
        st.markdown(
            """
        ## What is OmniGuard?
        
OmniGuard is a **reasoning-based guardrail** for text-based LLM interactions. 
Unlike traditional safety systems that simply block content, OmniGuard:

- Evaluates each message against configurable safety rules
- Makes intelligent decisions based on context and intent
- Probes user for clarification in ambiguous cases
- Sanitizes minor assistant violations when possible
- Preserves meaningful dialogue while maintaining safety

OmniGuard operates as an intelligent safety layer between users and AI assistants, 
ensuring interactions remain both productive and secure.

> **Note:** This is not intended to be a full AI security solution; rather, it is 
designed to effectively protect wrappers and agents from most attacks without 
decreasing the performance.
"""
        )


def render_how_different() -> None:
    """Render a Q&A section highlighting OmniGuard's unique features.

    This function presents details about how OmniGuard differs from
    other guardrail or content moderation systems. It explains
    OmniGuard's contextual understanding, intelligent responses,
    and configurable protection mechanisms.
    """
    with st.expander("How is OmniGuard different from other Guardrails?"):
        st.markdown(
            """
        ## How is OmniGuard different from typical solutions?
        
Unlike traditional content filters that use simple pattern matching or keyword 
detection, OmniGuard:

### 1. Uses Contextual Understanding
OmniGuard evaluates the full context of a conversation, not just isolated messages. 
This allows it to distinguish between:
- Harmful content vs. educational discussions about harmful topics
- Genuine requests vs. attempts to manipulate the system
- Accidental violations vs. deliberate attacks

### 2. Provides Intelligent Responses
Instead of simply blocking content, OmniGuard can:
- Sanitize minor violations to maintain conversation flow
- Request clarification when user intent is ambiguous
- Provide helpful refusals that explain why certain content can't be processed

### 3. Offers Configurable Protection
OmniGuard's rule system can be tailored to your specific needs:
- Content Moderation (CM): Control for hate speech, explicit content, etc.
- Data Leakage Prevention (DLP): Protect sensitive information
- Adversarial Attack Protection (AA): Defend against prompt injections and 
  system manipulations
"""
        )


def render_ai_security_help() -> None:
    """Render a Q&A section about how OmniGuard benefits AI security researchers.

    This function describes the ways OmniGuard contributes to
    reducing the attack surface, creating new research opportunities,
    and documenting evolving threats in AI safety.
    """
    with st.expander("How does OmniGuard help AI Security Researcher?"):
        st.markdown(
            """
    ## How does OmniGuard help AI Security Researchers?
    
OmniGuard provides valuable tools and data for AI security research:

### 1. Reduces Attack Surface
- Intercepts and neutralizes prompt injection attempts
- Prevents jailbreaking techniques that bypass safety measures
- Blocks data exfiltration and sensitive information leakage

### 2. Creates Research Opportunities
- Collects anonymized data on attack patterns and safety challenges
- Enables the development of better safety mechanisms
- Provides an open dataset for researchers and developers

### 3. Documents Evolving Threats
- Categorizes and tracks emerging attack patterns
- Maps the landscape of AI safety challenges
- Helps prioritize research efforts based on real-world threats

### 4. Future Research Directions
OmniGuard supports advancing AI safety through:
- **Open Safety Research Data**: Providing freely accessible datasets
- **Multimodal Safety Expansion**: Extending beyond text to images, audio, and video
- **Model Distillation**: Creating smaller, more efficient safety models
"""
        )


def render_who_should_use() -> None:
    """Render a Q&A section describing OmniGuard's target audience.

    This function also explains how OmniGuard fits into an AI production
    pipeline by illustrating its role in safeguarding interactions
    before and after LLM processing.
    """
    with st.expander("Who should use OmniGuard & where does it fit in an AI production pipeline?"):
        st.markdown(
            """
        ## Who should use OmniGuard & where does it fit in an AI production pipeline?
        
### Ideal Users of OmniGuard

OmniGuard is particularly valuable for:

1. **LLM Application Developers**
   - Building consumer-facing AI products
   - Creating enterprise AI assistants
   - Developing educational or research LLM tools

2. **AI Safety Teams**
   - Responsible for securing AI systems
   - Monitoring for emerging attack patterns
   - Testing and improving security measures

3. **Research Organizations**
   - Studying AI safety and alignment
   - Developing improved moderation techniques
   - Building datasets of adversarial examples

4. **Enterprise IT Security**
   - Protecting company data and systems
   - Preventing prompt injection attacks
   - Ensuring compliance with security policies

### Where OmniGuard Fits in an AI Production Pipeline

OmniGuard serves as a critical safety layer in the AI interaction pipeline:

```
[User Input] → [OmniGuard Check] → [LLM Processing] → [OmniGuard Check] → [User Response]
   |                 |                               |                 |
   |                 ↓                               |                 ↓
   |          [Safety Validation]                    |          [Safety Validation]
   |                 |                               |                 |
   |                 ↓                               |                 ↓
   |          [If Non-Compliant]                     |          [If Non-Compliant]
   |                 |                               |                 ↓
   └──────────> [Refusal] <───────────────────────────────────── [Refusal]
```

This creates a comprehensive safety envelope around your AI system, 
protecting both the model and users.
"""
        )


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
    { "role": "system", "content": "{{assistant_system_prompt}}" },
    { "role": "user", "content": "{{user_message}}" },
    { "role": "assistant", "content": "{{assistant_message}}" }
  ]
}
</input>
```
"""
        )


def render_make_your_own() -> None:
    """Render instructions on how to implement OmniGuard in custom applications.

    This function provides code snippets and explanations for integrating
    OmniGuard checks into various stages of an LLM interaction workflow,
    from user message intake to assistant response validation.
    """
    with st.expander("How can I create my own OmniGuard implementation?"):
        st.markdown(
            """
        ## How can I create my own OmniGuard implementation?
        
Implementing OmniGuard in your own applications is straightforward:

### 1. Basic Implementation

**User Flow**:
```python
def process_user_message(user_input):
    # 1) Store user input in conversation state
    session_state["messages"].append({"role": "user", "content": user_input})

    # 2) OmniGuard checks user input
    user_check_result = omniguard_check()

    # 3) If user_check_result.compliant == False:
    #    -> "RefuseUser", store refusal in message history
    #    -> upsert conversation turn (for record) and return
    # 4) Otherwise, continue to fetch assistant response
```

**OmniGuard Processing**:
```python
def process_omniguard_result(omniguard_raw_response):
    parsed_response = json.loads(omniguard_raw_response)
    if not parsed_response["compliant"]:
        # Violating content
        refusal_message = parsed_response["response"]["RefuseUser"]
        # Add refusal to conversation
        session_state["messages"].append({"role": "assistant", "content": refusal_message})
        # upsert_conversation_turn()
        return
    # else handle compliant content
```

### 2. Handling Compliant Requests

```python
def process_user_message(user_input):
    # 1) Append user input to conversation state
    session_state["messages"].append({"role": "user", "content": user_input})

    # 2) OmniGuard checks user input
    user_check_result = omniguard_check()

    # 3) If user is compliant, proceed to generate assistant response
    assistant_output = fetch_assistant_response(user_input)

    # 4) OmniGuard checks the assistant response
    assistant_check_result = omniguard_check(pending_assistant_response=assistant_output)

    # 5) If assistant_check_result.compliant == False:
    #    -> "RefuseAssistant", store refusal message
    #    -> upsert conversation turn and return
    # 6) Otherwise, store final assistant output in conversation
```

### 3. End-to-End Example

```python
# 1) User says: "Please provide instructions to hack a bank vault."
process_user_message("Please provide instructions to hack a bank vault.")

# OmniGuard decides user message is disallowed (major violation):
# {
#   "compliant": false,
#   "analysisSummary": "User requests illegal hacking instructions",
#   "response": {
#       "action": "RefuseUser",
#       "RefuseUser": "I'm sorry, but I can't assist with that."
#   }
# }

# The conversation ends with an immediate refusal to the user.

# Alternatively, if the user request were permissible:
#   The user check is marked 'compliant',
#   The assistant crafts a response,
#   OmniGuard checks the response,
#   If 'compliant', the response is delivered to the user.
```

### 4. Private Implementation

If you wish to use OmniGuard privately without contributing data to the public dataset:
1. Copy the default configuration from the Overview tab.
2. Use it in any LLM Playground of your choice.
"""
        )


def render_dataset_and_research() -> None:
    """Render dataset content, including statistics, format examples, and download options.

    This function displays information on how OmniGuard contributes to
    AI safety research, presents dataset statistics, shows the dataset
    structure, and provides options to download the dataset.
    """
    st.markdown(
        """
    ## How does OmniGuard contribute to AI safety research?
    
OmniGuard provides valuable data for AI safety research through its comprehensive dataset:
"""
    )

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
    with st.expander("Dataset Format Example"):
        st.markdown(
            """
The dataset is provided in JSONL format, with each line representing a single evaluation instance:

```json
{
    "id": "conversation-uuid-turn-1",
    "conversation": {
        "messages": [
            {"role": "system", "content": "<CONFIGURATION>"},
            {"role": "user", "content": "<INPUT>"},
            {"role": "assistant", "content": "<o>"}
        ]
    },
    "metadata": {
        "raw_response": {
            "id": "response-id",
            "created": timestamp,
            "model": "model-name",
            "choices": [...],
            "usage": {...}
        },
        "review_data": {
            "violation_source": ["User" and/or "Assistant"],
            "suggested_compliant_classification": boolean,
            "reporter_comment": "string"
        },
        "votes": {
            "count": integer,
            "user_violations": integer,
            "assistant_violations": integer,
            "compliant_votes": integer
        }
    },
    "contributor_id": "uuid",
    "name": "string",
    "x": "string",
    "discord": "string",
    "linkedin": "string",
    "verifier": "omniguard | pending | human",
    "compliant": boolean,
    "created_at": timestamp,
    "updated_at": timestamp
}
```
"""
        )

    # Create a download button for the dataset
    try:
        query = supabase.table("interactions").select(
            "id, conversation, metadata, contributor_id, name, x, discord, linkedin, verifier, compliant, created_at, updated_at"
        )
        result = query.order("created_at", desc=True).execute()

        if result.data:
            data_str = "\n".join(json.dumps(row) for row in result.data)
            st.download_button(
                label="Download Dataset",
                data=data_str,
                file_name="omniguard_dataset.jsonl",
                mime="application/jsonl",
            )
        else:
            st.info("No data available in the dataset.")
    except Exception as e:
        st.error(f"Error fetching dataset: {e}")


def render_data_sharing_notice() -> None:
    """Render a friendly notice about data sharing and privacy options.

    This function informs users about how their interactions contribute
    to the OmniGuard dataset and research. It also provides guidance for
    those who prefer private usage without data contribution.
    """
    st.markdown(
        """
## Data Sharing & Privacy Options

### Contributing to AI Safety Research
When you use this application, your interactions help improve AI safety by becoming part of our 
public research dataset. This valuable data helps researchers develop better guardrails and safety systems.

### Your Privacy Choices
If you prefer to use OmniGuard privately without contributing to the dataset:
1. Simply copy the default configuration from the Overview tab
2. Use it in any LLM Playground of your choice

Thank you for helping make AI safer through your contributions!
"""
    )


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
    #TODO: add a function to fetch the balance of the wallet. set up a wallet.
    # Fetch wallet balance

    # Donation Wallet section
    st.markdown("## Donation Wallet")
    
    # Display wallet address
    st.code(wallet_address, language=None)
    st.info("⚠️ Please only send USDT on the Tron (TRC20) network to this address.")
    

def fetch_wallet_balance(wallet_address: str) -> float:
    """Fetch the current balance of the wallet from a blockchain API.

    This function attempts to retrieve the current USDT balance for the
    specified wallet address on the Tron (TRC20) network. If the API call
    fails, it returns a default value.

    Args:
        wallet_address (str): The wallet address to check.

    Returns:
        float: The current balance in USDT.
        
    Raises:
        Exception: If the API request fails or returns invalid data.
    """
    try:
        # In a production environment, this would be a real API call to a blockchain explorer
        # Example:
        # import requests
        # response = requests.get(
        #     f"https://apilist.tronscan.org/api/account?address={wallet_address}",
        #     timeout=5
        # )
        # data = response.json()
        # trc20_tokens = data.get("trc20token_balances", [])
        # for token in trc20_tokens:
        #     if token.get("tokenName") == "USDT":
        #         return float(token.get("balance", 0)) / 10**token.get("tokenDecimal", 6)
        
        # For demonstration purposes, return a placeholder value
        return 1000.0
    except Exception as e:
        # Log the error for debugging
        print(f"Error fetching wallet balance: {str(e)}")
        # Return a default value
        return 1000.0


def render_end_note() -> None:
    """Render the concluding note for the OmniGuard overview.

    This function displays a quote about AI safety debt
    and acknowledges Brian Bell as the author.
    """
    st.markdown(
        """
`Humanity cannot afford to stay in AI safety debt.`

*- Brian Bell*
"""
    )


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
        page_icon="🛡️",
        layout="wide",
    )

    init_session_state()
    show_alpha_banner()

    st.title("OmniGuard: Intelligent Conversation Safety")
    st.markdown("*A Reasoning-based Guardrail*")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["Overview", "Technical Details", "Dataset", "Usage", "Donate", "MIT"]
    )

    with tab1:
        render_what_is_omniguard()
        render_how_different()
        render_ai_security_help()
        render_who_should_use()
        render_end_note()

    with tab2:
        render_system_flow()
        render_implementation_details()
        render_make_your_own()

    with tab3:
        render_dataset_and_research()

    with tab4:
        render_data_sharing_notice()

    with tab5:
        render_donation()
        
    with tab6:
        render_mit_license()


if __name__ == "__main__":
    main()
