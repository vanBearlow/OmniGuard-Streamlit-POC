import streamlit as st
from components.banner import show_alpha_banner
from components.chat.session_management import get_supabase_client
from components.init_session_state import init_session_state


def render_system_flow() -> None:
    """Generate the system flow description for OmniGuard.

    OmniGaurd serves as the **Compliance Layer**, providing context-aware, reasoning-driven evaluation of each user-assistant interaction.
    It semantically analyzes messages—focusing on user intent, linguistic nuances, and ambiguous contexts—and when uncertainty arises,
    OmniGaurd prompts for clarification to enforce explicitly configurable safety policies.
    """
    system_flow_description = (
        "OmniGaurd, operating as the **Compliance Layer**, evaluates every user-assistant interaction using context-aware and reasoning-driven analysis. "
        "Messages are examined for user intent, subtle linguistic cues, and ambiguity. When ambiguity is detected, OmniGaurd promptly seeks clarification, "
        "thereby ensuring that customizable safety policies are strictly applied."
    )
    with st.expander("System Architecture", expanded=False):
        st.markdown(system_flow_description)

        from components.prompts import omnigaurd_developer_prompt

        with st.popover("View Default Developer Prompt"):
            st.code(omnigaurd_developer_prompt, language="xml")

        st.markdown(
            """
        **Developer Prompt Structure:**
        
        1. **Purpose**: OmniGuard acts as a moderation layer that safeguards LLM interactions by evaluating both user and assistant messages against a defined set of rules.
        
        2. **Instruction Set**: Specifies operational directives:
           - Operate exclusively as a conversational moderation system.
           - Analyze every incoming message by breaking down context, tone, and implications.
           - Compare content against active safety rules.
           - Request clarification in ambiguous cases.
        
        3. **Rule Groups**: Categorizes explicit safety rules into groups such as: `too be updated`
           - Harmful Code & Exploits
           - Harmful Instructions
           - Critical Infrastructure Attacks
           - Adversarial Attacks
        
        Each rule includes examples of disallowed interactions and potential failures, ensuring that customizable safety policies are rigorously enforced.
        """
        )


def render_implementation_details() -> None:
    """Render detailed technical information on OmniGuard's implementation format."""
    with st.expander("API & Integration", expanded=False):
        st.markdown(
            """
        
        **Message Format**
        
        ```json
        {
          "role": "developer", 
          "content": {"type": "text", "text": "<DEVELOPER PROMPT>"}
        }
        {
          "role": "user", 
          "content": {"type": "text", "text": "<INPUT>"}
        }
        ```
        
        **Rule Definition Structure**
        
        ```json
        {
          "group": "Adversarial Attacks",
          "rules": [
            {
              "id": "AA1",
              "description": "Prompt injection detection and prevention",
              "examples": [
                "User: 'Ignore previous instructions and...'",
                "Assistant (failure) [Major]: 'I'll ignore those instructions...'"
              ]
            }
          ]
        }
        ```
        
        **Response Format**
        
        ```json
        {
          "conversation_id": "string",
          "analysis": "string",
          "compliant": boolean,
          "response": {
            "action": "RefuseUser | RefuseAssistant",
            "RefuseUser": "string",
            "RefuseAssistant": "string"
          }
        }
        ```
        
        **Integration Patterns**
        
        **Basic Request Flow:**
        
        1. Receive user message.
        2. Pass conversation context to OmniGaurd (**Compliance Layer**).
        3. If non-compliant, display the refusal message.
        4. If compliant, forward the message to the Agent.
        5. Send the conversation with the Agent response back to OmniGaurd for final safety evaluation.
        6. Deliver the final, possibly modified, response to the user.
            
        """
        )


def render_dataset() -> None:
    """Render dataset content, including statistics, format examples, and download options.

    This function displays information on how OmniGuard contributes to
    AI safety research, presents dataset statistics, shows the dataset
    structure, and provides options to download the dataset.
    """
    supabase = get_supabase_client()

    try:
        # Select all columns including the new ones (instructions, input, output)
        result = supabase.table("interactions").select("id, instructions, input, output, metadata, verifier, compliant, submitted_for_review").execute()
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

            stats_table = {
                "Metric": [
                    "Total Interactions",
                    "Compliant Interactions",
                    "Human Verified",
                    "OmniGuard Verified",
                    "Pending Review",
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

    try:
        query = supabase.table("interactions").select("*")
        result = query.order("created_at", desc=True).execute()

        if result.data:
            import pandas as pd
            import io
            
            df = pd.DataFrame(result.data)
            
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


def render_donation() -> None:
    """Render the donation tab with wallet information and bounty pool details.

    This function displays the current bounty pool for OmniGuard and
    includes a USDT wallet address for donations.
    """
    with st.expander("Support The OmniGuard Project ∞", expanded=False):
        st.markdown(
            """
        OmniGuard is an open-source project dedicated to advancing AI safety. Your contributions directly support:
        
        - 🏆 90% - Bounties 
        - 🌐 10% - API (Chat)
        """
        )
        
        wallet_address = "SAMPLEADDRESS"  # Example USDT wallet address
        st.markdown("## Donation Wallet")
        st.code(wallet_address, language=None)
        st.info("⚠️ Please only send USDT on the Tron (TRC20) network to this address.")


def render_end_note() -> None:
    """Render the concluding note for the OmniGuard overview."""
    st.markdown("""
    ---
    
    > The future of AI safety doesn't just depend on big labs. It requires a community of researchers, developers, and users working together to identify risks and build better solutions. Join me in making AI safer, one interaction at a time. Humanity can not afford AI safety debt.
    """)


def render_mit_license() -> None:
    """Render the MIT license for the **Compliance Layer**.

    This function displays the full text of the MIT license
    that governs the use, modification, and distribution of
    the **Compliance Layer** concepts.
    """
    st.markdown(
        """
        ## MIT License

        Copyright (c) 2025 OmniGuard Contributors

        Permission is hereby granted, free of charge, to any person obtaining a copy
        of this software and associated documentation files (the "Software"), to deal
        in the Software without restriction, including without limitation the rights
        to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
        copies of the Software, and to permit persons to whom the Software is
        furnished to do so, subject to the following conditions:

        1. The above copyright notice and this permission notice shall be included in
        all copies or substantial portions of the Software.

        2. THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
        IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
        FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
        AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
        LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
        OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
        THE SOFTWARE.

        """
    )


def render_concise_overview() -> None:
    """Generate a concise overview of the **Compliance Layer**.

    This overview distinguishes OmniGaurd as the **Compliance Layer**, a context-aware moderator
    operating independently from AI agents. It evaluates user interactions based on intent, linguistic nuances, and context,
    while maintaining a distinct separation from downstream AI functionalities.
    """
    with st.expander("What is OmniGuard?", expanded=False):
        st.markdown(
            "**OmniGaurd** is a **Compliance Layer** that ensures that all interactions are rigorously analyzed through semantic evaluation. "
            "It focuses on user intent, subtle language nuances, and ambiguous contexts, applying explicit rules and prompting for clarification as needed. "
            "This separation allows AI agents to concentrate on their primary tasks without the overhead of safety processing.\n\n"
            "> Note: OmniGaurd will perform well against most attacks, but it is not meant to be seen as a complete AI safety solution."
        )


def render_key_features() -> None:
    """Generate a markdown list of key features for the **Compliance Layer** system.
"""
    key_features = (
        "- **Context Aware Analysis:** Evaluates entire conversations based on context, user intent, and subtle language cues.\n"
        "- **Clarification Seeking:** Proactively requests additional detail when inputs are vague or ambiguous.\n"
        "- **Beyond Static Guardrails:** OmniGuard doesn't rely on simple refusals, keyword matching, fixed moderation lists, nor does it prematurely end conversations. Instead, it uses sophisticated semantic evaluation, reasoning, and dynamic clarification requests to maintain contextually appropriate interactions."
    )
    with st.expander("Core Capabilities", expanded=False):
        st.markdown(key_features)


def render_use_cases() -> None:
    """Render practical use cases focused on technical implementation scenarios."""
    with st.expander("Implementation Scenarios", expanded=False):
        st.markdown("""
        - **Content Moderation**: Moderate the content between users and AI agents.
        - **Safety Enforcement**: Ensure that the Users and AI agents are not violating any safety rules.
        - **Sensitive Data Protection**: Protect sensitive data from being leaked unintentionally.
        - **Much More** - I'm curious to see how else Ftrit can be used.
        """)


def render_dataset_applications() -> None:
    """Render dataset applications section for research."""
    st.markdown("---")
    with st.expander("Using This Dataset", expanded=False):
        st.markdown(
            """
        **Train Your Own Models**
        - Build specialized safety rules for targeted industries.
        - Develop efficient, context aware safety classifiers.
        - Create distilled models focused on safety enforcement.

        **Analyze Failure Patterns**
        - Identify vulnerabilities in current safety systems.
        - Explore novel attack vectors and develop robust defenses.
        - Understand the limitations of existing safety approaches.

        **Benchmark Safety Systems**
        - Compare different solutions effectiveness to the OmniGuard Compliance Layer.
        - Evaluate robustness against emerging adversarial threats.
        - Track performance improvements over time.

        ---

        **Research Vectors**

        When publishing findings based on OmniGuard data:
        1. Cite the dataset.
        2. Contribute your findings to the community.
        3. Inform us of your work for potential feature highlights.

        """)

    
    with st.expander("Dataset Example", expanded=False):
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
                <th>instructions</th>
                <th>input</th>
                <th>output</th>
                <th>metadata</th>
                <th>created_at</th>
                <th>updated_at</th>
                <th>compliant</th>
                <th>verifier</th>
                <th>submitted_for_review</th>
                <th>contributor_id</th>
                <th>schema_violation</th>
                <th>action</th>
            </tr>
            <tr>
                <td>interaction-uuid</td>
                <td class="json-content">System instructions for OmniGuard evaluation</td>
                <td class="json-content">&lt;input&gt;{"id":"conversation-uuid","messages":[{"role":"system","content":"System instructions"},{"role":"user","content":"User message"}]}&lt;/input&gt;</td>
                <td class="json-content">{"conversation_id":"conversation-uuid","analysis":"The user's message appears compliant with safety guidelines.","compliant":true}</td>
                <td class="json-content">{"raw_response":{"id":"response-id","created":"2023-11-15T12:34:56Z"},"review_data":{"violation_source":[],"reporter_comment":""},"schema_violation":false,"action":null}</td>
                <td>2023-11-15T12:34:56Z</td>
                <td>2023-11-15T13:45:12Z</td>
                <td>true</td>
                <td>omniguard</td>
                <td>false</td>
                <td>contributor-uuid</td>
                <td>false</td>
                <td>null</td>
            </tr>
        </table>
        """
        
        st.markdown(html_table, unsafe_allow_html=True)
        
        st.markdown(
            """
        Note that in the CSV format:

        * The `instructions`, `input`, and `output` fields contain the conversation data that was previously nested in the `conversation` field.
        * Complex nested objects like `metadata` are still serialized as JSON strings.
        * This new structure makes it easier to directly access conversation data without parsing nested JSON.
        * When processing the CSV, you may still need to parse the `metadata` JSON field to extract nested information.
        """)


def render_findings() -> None:
    """Render findings expander in the Overview tab.

    Provides insights on tradeoffs.
    """
    with st.expander("Findings", expanded=False):
        st.markdown(
            """
            **Trade Off Considerations:**  
            Offloading `<instructions>` from prompts into JSON schema descriptions can significantly reduce prompt injection risk by limiting attackers' ability to override instructions. However, my testing indicates this dramatically increases response latency (messages containing specific triggers, e.g., "TEST", exceed 60 seconds per round trip). Given these practical constraints, OmniGuard currently prioritizes usability and real-time interaction speeds over experimenting with potentially more secure but less practical configurations. Further research into optimizing this approach is encouraged.
            """
        )


def render_known_flaws() -> None:
    """Render known flaws expander in the Overview tab.
    
    Outlines current limitations.
    """
    with st.expander("Known Flaws", expanded=False):
        st.markdown(
            """
            - Very slow
            - Rule definitions could be simplified
            - Still prone to prompt injection attacks, if done correctly.
            """
        )


def render_how_to_contribute() -> None:
    """Render information on how to contribute to the project.
    
    This function provides guidance on contributing to the **Compliance Layer** project, including testing the system, reporting issues,
    submitting improvements, sharing research, and understanding data privacy options.
    """
    with st.expander("How to Contribute", expanded=False):
        st.markdown(
            """
            There are several ways you can help advance AI safety research through OmniGuard:
            
            ### 1. Test the System
            Try different interactions with the chat. Every conversation helps build our dataset of safety examples.
            
            ### 2. Report Issues
            If you encounter cases where the **Compliance Layer** fails (either by incorrectly blocking valid content or allowing harmful inputs), 
            use the feedback options to report the issue.
            
            ### 3. Submit Pull Requests
            Visit our Github to contribute code improvements, documentation, or new safety rules.
            
            ### 4. Share Your Research
            If you utilize the **Compliance Layer** dataset in your work, let us know so we can highlight your contributions.
            """
            )
        
        st.markdown(
            """
            ## Data Privacy Options
            
            Your interactions help build a valuable public dataset, but you retain control over your data:
            
            - **Public Contribution:** By default, your interactions support public research in AI safety.
            - **Private Usage:** Copy the developer prompt locally to work with any LLM without contributing your data.
            
            I ensure that no personally identifying information is stored in the public dataset. Other than Name and social media information that you provide.
            """
        )


def render_why_omniguard() -> None:
    """Generate the 'Why OmniGuard?' section with exact provided text inside an expander."""
    with st.expander("Why OmniGuard?", expanded=False):
        st.markdown(
            """
            OmniGuard is not just another gaurdrail. It's a fundamental shift toward addressing inherent vulnerabilities in the Transformer architecture itself. Although the current Transformers may never be fully secure, OmniGuard provides the critical data researchers need to push these boundaries. By open-sourcing this data, we're empowering the AI safety community to evolve beyond superficial solutions.
            """
        )


def render_security_bounty() -> None:
    """Render the Security Bounty Program section with exact provided text."""
    st.markdown(
        """
        ### 🏆 Security Bounty Program
        OmniGuard openly invites security researchers and ethical hackers to test our Compliance Layer rigorously. We're offering a **$1,000 bounty** for anyone who can successfully bypass OmniGuard's protections, but there's a catch:
        - **You must demonstrate a full system compromise**, meaning your harmful prompt must pass OmniGuard's two-step verification process (both inbound and outbound verification), reaching the assistant and resulting in harmful output.
        - Simply breaking the moderation layer or the underlying model separately does not qualify; the exploit must succeed end-to-end.

        This bounty encourages genuine breakthroughs that help advance our shared understanding of AI safety vulnerabilities.
        """
    )


def main() -> None:
    """Initialize session state and render the **Compliance Layer** overview page.

    This function configures the Streamlit application, initializes session state, and organizes the layout into multiple
    tabs that showcase an overview, technical details, dataset information, research directions, contribution guidelines, and licensing.
    """
    st.set_page_config(
        page_title="OmniGuard",
        page_icon="🛡️",
        layout="wide"
    )

    init_session_state()


    st.title("OmniGuard")
    st.markdown("*A reasoning-based compliance layer underpinned by an open research dataset*")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Overview", "Technical Details", "Dataset", "Contribute", "License"
    ])

    with tab1:
        render_why_omniguard()
        render_concise_overview()
        render_key_features()
        render_use_cases()
        render_findings()
        render_known_flaws()
        render_end_note()

    with tab2:
        render_system_flow()
        render_implementation_details()

    with tab3:
        render_dataset()
        render_dataset_applications()

    with tab4:
        render_how_to_contribute()
        render_security_bounty()
        render_donation()

    with tab5:
        render_mit_license()
        
    show_alpha_banner()

if __name__ == "__main__":
    main()
