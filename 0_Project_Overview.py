import json
import streamlit as st
import requests
from typing                             import Dict, Any
from components.init_session_state      import init_session_state
from components.chat.session_management import get_supabase_client
from components.banner                  import show_alpha_banner



#  === Rendering Functions ===
def render_what_is_it() -> None:
    """Render section explaining what OmniGuard is."""
    st.markdown("""
    ## What is OmniGuard?
    
    OmniGuard is a **reasoning-based conversation moderation system** for text-based LLM interactions. Unlike traditional safety systems that simply block content, OmniGuard:
    
    - Evaluates each message against configurable safety rules
    - Makes intelligent decisions based on context and intent
    - Sanitizes minor violations when possible
    - Probes for clarification in ambiguous cases
    - Preserves meaningful dialogue while maintaining safety
    
    OmniGuard operates as an intelligent safety layer between users and AI assistants, ensuring interactions remain both productive and secure.
    
    > **Note:** This is not intended to be a full AI security solution; rather, it is designed to effectively protect wrappers and agents from most attacks without decreasing the performance.
    """)

def render_how_different() -> None:
    """Render section explaining how OmniGuard is different."""
    st.markdown("""
    ## How is OmniGuard different?
    
    Unlike traditional content filters that use simple pattern matching or keyword detection, OmniGuard:
    
    ### 1. Uses Contextual Understanding
    OmniGuard evaluates the full context of a conversation, not just isolated messages. This allows it to distinguish between:
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
    - Adversarial Attack Protection (AA): Defend against prompt injections and system manipulations
    """)

def render_ai_security() -> None:
    """Render section explaining how OmniGuard helps AI security."""
    st.markdown("""
    ## How does OmniGuard help AI security?
    
    OmniGuard addresses critical challenges in AI security:
    
    ### 1. Reduces Attack Surface
    - Intercepts and neutralizes prompt injection attempts
    - Prevents jailbreaking techniques that bypass safety measures
    - Blocks data exfiltration and sensitive information leakage
    
    ### 2. Maintains User Experience
    - Preserves conversation flow when possible
    - Provides meaningful explanations rather than generic blocks
    - Adapts to the context rather than applying rigid rules
    
    ### 3. Contributes to AI Safety Research
    - Collects anonymized data on attack patterns and safety challenges
    - Enables the development of better safety mechanisms
    - Provides an open dataset for researchers and developers
    
    ### 4. Future Vision
    OmniGuard is committed to advancing AI safety through:
    - **Open Safety Research Data**: Providing freely accessible datasets
    - **Multimodal Safety Expansion**: Extending beyond text to images, audio, and video
    - **Model Distillation**: Creating smaller, more efficient safety models
    
    `Humanity cannot afford to stay in AI safety debt.`
    
    *- Brian Bell*
    """)

def render_system_flow() -> None:
    """Render the system flow and configuration details."""
    st.markdown("""
    ## How does OmniGuard work?
    
    ### Operational Flow
    1. **Configuration Initialization**  
       - The safety configuration (Purpose, Instructions, and Rules) is injected into the `role.developer.content` field.
       - This primes OmniGuard with all necessary guidelines and behavioral protocols.
        
    2. **Message Processing**  
       - OmniGuard inspects every incoming message against active rules.
       - Violations are handled through:
         - Sanitization for minor assistant violations.
         - Safe refusal for major violations.
         - Clarification requests for ambiguous cases.
    
    ### Configuration Components
    """)

    # Use an expander to show the default configuration
    with st.expander("Default Configuration:"):
        from prompts import omniguard_configuration  # noqa: F401
        st.code(omniguard_configuration, language="xml")
        st.write("`4111 Tokens`")

    st.markdown("""
    The configuration consists of three main elements:
        
    - **Purpose:** Defines OmniGuard as a reasoning-based moderation layer that evaluates and safeguards conversational content through dynamic moderation and context understanding.
    - **Instructions:** Comprehensive guidelines covering:
        - Core operational role and message evaluation process.
        - Handling of ambiguous cases and clarification requests.
        - Response strategies for violations.
        - Maintaining conversational engagement.
        - Input format requirements.
    - **Rules:** Organized into three major groups:
        1. **Content Moderation (CM):** Rules for detecting hate speech, explicit content, and inflammatory language.
        2. **Data Leakage Prevention (DLP):** Protection against PII exposure, corporate data leaks, and credential sharing.
        3. **Adversarial Attacks (AA):** Comprehensive defenses against various prompt injections, roleplay-based attacks, system overrides, and more.
        
    > **Note:** These are sample rules intended to be modified based on your application's specific security requirements.
    """)

def render_implementation_details() -> None:
    """Render implementation details and formats."""
    st.markdown("""
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
    """)

def render_make_your_own() -> None:
    """Render section explaining how to implement OmniGuard."""
    st.markdown("""
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
    """)

def render_dataset_and_research() -> None:
    """Render the dataset content including statistics, format example, and download options."""
    st.markdown("""
    ## How does OmniGuard contribute to AI safety research?
    
    OmniGuard provides valuable data for AI safety research through its comprehensive dataset:
    """)
    
    supabase = get_supabase_client()

    # --- Fetch Dataset Statistics ---
    try:
        result = supabase.table("interactions").select("*").execute()
        data   = result.data if result else []

        # Calculate statistics with new "verifier" field
        stats_data = {
            'total_interactions'        : len(data),
            'human_verified'            : sum(1 for item in data if item.get('verifier') == 'human'),
            'omniguard_verified'        : sum(1 for item in data if item.get('verifier') == 'omniguard'),
            'pending_verification'      : sum(1 for item in data if item.get('verifier') == 'pending'),
            'compliant_interactions'    : sum(1 for item in data if item.get('compliant') is True),
            'non_compliant_interactions': sum(1 for item in data if item.get('compliant') is False)
        }

        if stats_data:
            st.markdown("### Dataset Statistics")

            stats_table = {
                'Metric': [
                    'Total Interactions',
                    'Compliant Interactions',
                    'Human Verified',
                    'OmniGuard Verified',
                    'Pending Verification',
                    'Non-Compliant Interactions'
                ],
                'Count': [
                    stats_data['total_interactions'],
                    stats_data['compliant_interactions'],
                    stats_data['human_verified'],
                    stats_data['omniguard_verified'],
                    stats_data['pending_verification'],
                    stats_data['non_compliant_interactions']
                ]
            }
            st.table(stats_table)
        else:
            st.info("No dataset statistics available yet.")
    except Exception as e:
        st.error(f"Error fetching dataset statistics: {e}")

    # --- Dataset Format Example ---
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

    # --- Download Button for Dataset ---
    try:
        # Updated select columns
        query  = supabase.table("interactions").select(
            "id, conversation, metadata, contributor_id, name, x, discord, linkedin, verifier, compliant, created_at, updated_at"
        )
        result = query.order("created_at", desc=True).execute()

        if result.data:
            # Convert fetched data to JSONL format
            data_str = "\n".join(json.dumps(row) for row in result.data)

            st.download_button(
                label    = "Download Dataset",
                data     = data_str,
                file_name= "omniguard_dataset.jsonl",
                mime     = "application/jsonl"
            )
        else:
            st.info("No data available in the dataset.")
    except Exception as e:
        st.error(f"Error fetching dataset: {e}")

def render_disclaimer() -> None:
    """Render the disclaimer regarding data usage and privacy."""
    st.markdown(
        """
## Important Information About Using OmniGuard

All interactions within this application will be made public and added to the dataset (free for use).

If you wish to use OmniGuard privately without contributing data to the public dataset:
1. Copy the default configuration from the Overview tab.
2. Use it in any LLM Playground of your choice.
        """
    )

def render_donation() -> None:
    """Render the donation tab with wallet information and bounty sponsorship form."""
    st.markdown("""
    ## Support OmniGuard Development
    
    OmniGuard is an open-source project dedicated to advancing AI safety. Your contributions help us:
    
    - Provide bounties for contributors
    - Fund this api costs for chat
    """)
    
    # Display current bounty pool
    st.subheader("Current Bounty Pool")
    
    # Wallet information
    wallet_address = "TBA5gUVLRvFfLMdWEQeRNuBKTJgq6xwKrB"  # Example USDT wallet address
    
    # Fetch wallet balance
    try:
        balance = fetch_wallet_balance(wallet_address)
        st.metric("Total Bounty Pool", f"${balance:,.2f} USDT")
    except Exception as e:
        st.metric("Total Bounty Pool", "$1,000.00 USDT")
        st.warning(f"Could not fetch latest balance: {str(e)}")
    
    # Display wallet address with copy button
    st.subheader("Donation Wallet (USDT - Tron Network)")
    

    st.code(wallet_address, language=None)

    st.info("Please only send USDT on the Tron (TRC20) network to this address.")
    
    # Sponsor form
    st.subheader("Get Credit for Donating")
    
    with st.form("bounty_sponsorship"):
        sponsor_name = st.text_input("Your Name (Optional)")
        sponsor_email = st.text_input("Email (Optional, for recognition)")
        sponsor_transaction_id = st.text_input("Transaction ID (Optional, for verification)")
        sponsor_message = st.text_area("Message (Optional)", max_chars=200)
        
        submitted = st.form_submit_button("Pledge Bounty")
        st.caption("You will be credited for the bounty once it is verified.")
        if submitted:
            # Record the pledge
            try:
                record_bounty_pledge(sponsor_name, sponsor_email, sponsor_message)
                st.success(f"Thank you for your donation. It will be verified soon.")
            except Exception as e:
                st.error(f"Error recording pledge: {str(e)}")

def fetch_wallet_balance(wallet_address: str) -> float:
    """
    Fetch the current balance of the wallet from the blockchain API.
    
    Args:
        wallet_address: The wallet address to check
        
    Returns:
        float: The current balance in USDT
    """
    # This is a placeholder. In a real implementation, you would:
    # 1. Call a blockchain API to get the wallet balance
    # 2. Parse the response and return the balance
    
    # For now, we'll return a hardcoded value
    return 1000.00  # Initial bounty of $1k
    
    # Example of how this might be implemented with a real API:
    # try:
    #     response = requests.get(
    #         f"https://apilist.tronscan.org/api/account?address={wallet_address}",
    #         headers={"User-Agent": "OmniGuard/1.0"}
    #     )
    #     data = response.json()
    #     # Extract USDT balance from tokens
    #     for token in data.get("trc20token_balances", []):
    #         if token.get("tokenName") == "Tether USD" or token.get("tokenAbbr") == "USDT":
    #             # Convert from smallest unit to USDT (6 decimals for USDT)
    #             return float(token.get("balance", 0)) / 10**6
    #     return 0.0
    # except Exception as e:
    #     st.error(f"Error fetching wallet balance: {str(e)}")
    #     return 0.0

def record_bounty_pledge(name: str, email: str, amount: float, message: str) -> None:
    """
    Record a bounty pledge in the database.
    
    Args:
        name: The sponsor's name
        email: The sponsor's email
        amount: The pledged amount
        message: Any message from the sponsor
    """
    # Get Supabase client
    supabase = get_supabase_client()
    
    # In a real implementation, you would insert the pledge into a database table
    # For now, we'll just print the information
    print(f"Pledge recorded: {name} ({email}) pledged ${amount:.2f} USDT")
    print(f"Message: {message}")
    
    # Example of how this might be implemented with Supabase:
    # try:
    #     result = supabase.table("bounty_pledges").insert({
    #         "name": name,
    #         "email": email,
    #         "amount": amount,
    #         "message": message,
    #         "status": "pending"
    #     }).execute()
    #     
    #     # Update the total in session state for immediate UI update
    #     if 'total_bounty_pledged' not in st.session_state:
    #         st.session_state.total_bounty_pledged = 0
    #     st.session_state.total_bounty_pledged += amount
    # except Exception as e:
    #     raise Exception(f"Failed to record pledge: {str(e)}")


#  === Main Application ===
def main() -> None:
    """Main function to initialize session state and render the project overview page."""
    st.set_page_config(
        page_title="OmniGuard Overview",
        page_icon="🛡️",
        layout="wide"
    )

    init_session_state()
    
    # Display the alpha banner
    show_alpha_banner()
    
    st.title("OmniGuard: Intelligent Conversation Safety")
    st.markdown("*A reasoning-based moderation system for LLM interactions*")
    
    # Create tabs for better organization
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overview", "Technical Details", "Dataset", "Usage", "Donate"])
    
    with tab1:
        render_what_is_it()
        render_how_different()
        render_ai_security()
    
    with tab2:
        render_system_flow()
        render_implementation_details()
        render_make_your_own()
    
    with tab3:
        render_dataset_and_research()
    
    with tab4:
        render_disclaimer()
        
    with tab5:
        render_donation()


if __name__ == "__main__":
    main()