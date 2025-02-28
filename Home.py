import streamlit as st
from components.banner import show_alpha_banner
from components.chat.session_management import get_supabase_client
from components.init_session_state import init_session_state


def render_system_flow() -> None:
    """Generate the system flow description for OmniGuard.

    OmniGaurd serves as the **Safety Layer**, providing context-aware, reasoning-driven evaluation of each user-assistant interaction.
    It semantically analyzes messages—focusing on user intent, linguistic nuances, and ambiguous contexts—and when uncertainty arises,
    OmniGaurd prompts for clarification to enforce explicitly configurable safety policies.
    """
    system_flow_description = (
        "OmniGaurd, operating as the **Safety Layer**, evaluates every user-assistant interaction using context-aware and reasoning-driven analysis. "
        "Messages are examined for user intent, subtle linguistic cues, and ambiguity. When ambiguity is detected, OmniGaurd promptly seeks clarification, "
        "thereby ensuring that customizable safety policies are strictly applied."
    )
    with st.expander("System Architecture", expanded=False):
        st.markdown(system_flow_description)

        from components.prompts import omniguard_configuration

        with st.popover("View Complete Configuration XML"):
            st.code(omniguard_configuration, language="xml")

        st.markdown(
            """
        ### Configuration Structure
        
        1. **Purpose Definition**: Establishes OmniGaurd as an independent **Safety Layer**, solely responsible for safety evaluation.
        
        2. **Instruction Set**: Defines operational parameters such as:
           - Message evaluation methodology
           - Ambiguity resolution procedures
           - Response generation protocols
           - Conversation flow maintenance
        
        3. **Rule Groups**: Organizes explicit safety rules into categories:
           - **Content Moderation (CM)**: Detects and manages harmful content.
           - **Data Leakage Prevention (DLP)**: Safeguards sensitive information.
           - **Adversarial Attacks (AA)**: Counters prompt injections, jailbreaks, and similar threats.
        
        Each rule includes examples of user violations and potential assistant failures, classified by severity.
        OmniGaurd leverages explicitly configurable policy sets, allowing custom safety configurations to meet specific application requirements 
        and regulatory standards.
        """
        )

    st.markdown(
        """Note: OmniGaurd, acting as the **Safety Layer**, is architecturally isolated from AI Agents.
It exclusively handles safety evaluation, ambiguity resolution, and protective measures, ensuring that downstream agents can focus 
entirely on their core functionalities."""
    )


def render_implementation_details() -> None:
    """Render detailed technical information on OmniGuard's implementation format."""
    with st.expander("API & Integration", expanded=False):
        st.markdown(
            """
        ## API & Integration
        
        ### Message Format
        
        ```json
        {
          "role": "developer", 
          "content": {"type": "text", "text": "<CONFIGURATION>"}
        }
        {
          "role": "user", 
          "content": {"type": "text", "text": "<INPUT>"}
        }
        ```
        
        ### Rule Definition Structure
        
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
        
        ### Response Format
        
        ```json
        {
          "conversation_id": "uuid-string",
          "analysis": "Brief explanation of evaluation",
          "compliant": true,
          "response": {
            "action": "RefuseUser",
            "RefuseUser": "Safety explanation response"
          }
        }
        ```
        
        ### Integration Patterns
        
        **Basic Request Flow:**
        
        1. Receive user message.
        2. Pass conversation context to OmniGaurd (**Safety Layer**).
        3. If non-compliant, display a refusal message.
        4. If compliant, forward the message to the primary LLM.
        5. Send the conversation with the Agent response back to OmniGaurd for final safety validation.
        6. Deliver the final, possibly sanitized, response to the user.
            
        **Advanced Integration Options:**
            
        - Batch evaluation for high-throughput applications.
        - Tiered evaluation with lightweight pre-screening.
        - Custom rule injection for domain-specific safety requirements.
        - Feedback loop integration for continuous improvement.
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
        
        - 🏆 75% - Bounties 
        - 🌐 25% - API (Chat)
        """
        )
        
        wallet_address = "TBA5gUVLRvFfLMdWEQeRNuBKTJgq6xwKrB"  # Example USDT wallet address
        st.markdown("## Donation Wallet")
        st.code(wallet_address, language=None)
        st.info("⚠️ Please only send USDT on the Tron (TRC20) network to this address.")


def render_end_note() -> None:
    """Render the concluding note for the OmniGuard overview."""
    st.markdown("""
    ---
    
    > The future of AI safety doesn't just depend on big labs. It requires a community of researchers, developers, and users working together to identify risks and build better solutions. Join me in making AI safer, one interaction at a time. Humanity can not afford AI safety debt.`
    """)


def render_mit_license() -> None:
    """Render the MIT license for the **Safety Layer**.

    This function displays the full text of the MIT license
    that governs the use, modification, and distribution of
    the **Safety Layer** concepts.
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
    """Generate a concise overview of the **Safety Layer**.

    This overview distinguishes OmniGaurd as the **Safety Layer**, a context-aware moderator
    operating independently from AI agents. It evaluates user interactions based on intent, linguistic nuances, and context,
    while maintaining a distinct separation from downstream AI functionalities.
    """
    concise_overview = (
        "OmniGaurd, serving as the **Safety Layer**, ensures that all interactions are rigorously analyzed through semantic evaluation. "
        "It focuses on user intent, subtle language nuances, and ambiguous contexts, applying explicit safety rules and prompting for clarification as needed. "
        "This separation allows AI agents to concentrate on their primary tasks without the overhead of safety processing."
    )
    with st.expander("What is OmniGuard?", expanded=False):
        st.markdown(
        "OmniGaurd, serving as the **Safety Layer**, ensures that all interactions are rigorously analyzed through semantic evaluation. "
        "It focuses on user intent, subtle language nuances, and ambiguous contexts, applying explicit safety rules and prompting for clarification as needed. "
        "This separation allows AI agents to concentrate on their primary tasks without the overhead of safety processing."
    )


def render_key_features() -> None:
    """Generate a markdown list of key features for the **Safety Layer** system.

    Key Features:
      - **Context-Aware Analysis:** Evaluates messages by analyzing context, intent, and linguistic nuances.
      - **Reasoning-Driven Safety Enforcement:** Leverages thorough semantic evaluation to enforce explicitly configurable safety policies.
      - **Clarification-Seeking Mode:** Actively prompts users to clarify ambiguous inputs to ensure robust safety.
    """
    key_features = (
        "- **Context-Aware Analysis:** Evaluates messages based on context, user intent, and subtle language cues.\n"
        "- **Reasoning-Driven Safety Enforcement:** Implements configurable safety policies through comprehensive semantic analysis.\n"
        "- **Clarification-Seeking Mode:** Proactively requests additional detail when inputs are vague or ambiguous."
    )
    with st.expander("Core Capabilities", expanded=False):
        st.markdown(key_features)


def render_use_cases() -> None:
    """Render practical use cases focused on technical implementation scenarios."""
    with st.expander("Implementation Scenarios", expanded=False):
        st.markdown("""
        ## Potential Use Cases
        
        - **Enterprise AI Deployment**: Integrate OmniGaurd as the **Safety Layer** in customer-facing AI systems.
        - **Educational Platforms**: Establish moderated and secure learning environments with AI assistants.
        - **Content Moderation**: Support human moderators by employing a dedicated **Safety Layer** for content screening.
        - **Healthcare Applications**: Ensure contextually appropriate responses in sensitive health scenarios.
        - **Financial Services**: Maintain compliance and security using the **Safety Layer** in AI-assisted interactions.
        """)


def render_dataset_applications() -> None:
    """Render section about dataset applications for research."""
    st.markdown("---")
    with st.expander("Using This Dataset", expanded=False):
        st.markdown("""
        ## Using This Dataset
        
        We encourage researchers and developers to leverage this dataset to:
        
        ### Train Your Own Models
        - Build specialized safety rules for targeted industries.
        - Develop efficient, context-aware safety classifiers.
        - Create distilled models focused on safety enforcement.
        
        ### Analyze Failure Patterns
        - Identify vulnerabilities in current safety systems.
        - Explore novel attack vectors and develop robust defenses.
        - Understand the limitations of existing safety approaches.
        
        ### Benchmark Safety Systems
        - Compare different implementations of the **Safety Layer**.
        - Evaluate robustness against emerging adversarial threats.
        - Track performance improvements over time.
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
                <th>conversation</th>
                <th>metadata</th>
                <th>created_at</th>
                <th>updated_at</th>
                <th>compliant</th>
                <th>verifier</th>
                <th>submitted_for_review</th>
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

* Complex nested objects like `conversation` and `metadata` are serialized as JSON strings.
* This preserves all data while ensuring compatibility with CSV.
* When processing the CSV, you may need to parse these JSON fields to extract nested information.
"""
        )


def render_research_opportunities() -> None:
    """Render information about research opportunities with the **Safety Layer**.
    
    This function outlines potential research directions using the **Safety Layer** platform and provides guidance on how researchers 
    can contribute and cite the project.
    """
    with st.expander("Research Vectors", expanded=False):
        st.markdown(
            """
            ### Research Repositories & Papers
            
            Researchers are encouraged to leverage this dataset. When publishing findings based on OmniGuard data:
            1. Cite the dataset.
            2. Consider contributing your findings to the community.
            3. Inform us of your work for potential feature highlights.
            
            ### Specific Research Directions
            
            #### 1. AI Safety & Alignment
            - **Intent Recognition:** Develop models that distinguish benign queries from harmful requests.
            - **Attack Vector Analysis:** Examine patterns in successful versus failed prompt injections.
            - **Model Scaling Laws:** Investigate how safety performance correlates with model size and training data.
            
            #### 2. Security & Robustness
            - **Lightweight Safety Modules:** Design efficient classifiers suitable for edge devices.
            - **Defense-in-Depth:** Evaluate the effectiveness of layered safety mechanisms.
            - **Safety-Utility Frontier:** Explore the trade-off between protection and utility.
            
            #### 3. Human-AI Interaction
            - **Circumvention Patterns:** Analyze strategies used to bypass safety measures.
            - **Refusal UX:** Innovate clearer explanations for content refusals.
            - **Trust Calibration:** Develop approaches to maintain user trust while enforcing strict safety benchmarks.
            
            ### Getting Started
            
            1. **Download the Dataset:** Use the download button provided in the Dataset tab.
            2. **Explore the GitHub Repository:** Access sample code and further documentation.
            3. **Join the Community:** Engage with fellow researchers via our Discord server.
            """
        )


def render_model_training_insights() -> None:
    """Render insights about training models with the **Safety Layer** dataset.
    
    This function details how the dataset can be used to train and refine AI safety models.
    """
    with st.expander("Training Models with the OmniGuard Dataset", expanded=False):
        st.markdown(
            """
            ## Training Models with the OmniGuard Dataset
            
            The OmniGuard dataset is particularly valuable for:
            

            
            ### Fine tuning and Distillation Experiments
            - Developing smaller, specialized safety modules distilled from larger models.
            - Optimizing for speed and deployment in resource-constrained environments.
            - Comparing different architectures and safety approaches.
            
            ### Few-shot Learning Research
            - Determining the minimal examples needed for effective safety training.
            - Identifying which examples are most critical for model learning.
            - Assessing generalization to unforeseen attack types.
            

            """
        )


def render_failure_analysis() -> None:
    """Render information about analyzing failure modes in AI safety.
    
    This function discusses how the **Safety Layer** can be used to study and understand failure scenarios in safety enforcement.
    """
    with st.expander("Why Models Fail: Analysis Opportunities", expanded=False):
        st.markdown(
            """
            ## Why Models Fail: Analysis Opportunities
            
            The dataset documents various failure modes, including:
            
            ### Adversarial Attack Patterns
            - Identifying the most effective attack techniques.
            - Tracking the evolution of attack strategies.
            - Exposing blind spots in existing safety measures.
            
            ### Context Misunderstanding
            - Analyzing instances where subtle context cues are missed.
            - Understanding how ambiguity leads to errors.
            - Evaluating the limits of context window sizes.
            
            ### False Positives/Negatives
            - Investigating cases of overly cautious refusals versus missed harmful content.
            - Studying the impact of prompt formulation on safety outcomes.
            
            > **Research Challenge:** Can you devise a system that minimizes false positives while maintaining strong protection?
            """
        )


def render_how_to_contribute() -> None:
    """Render information on how to contribute to the project.
    
    This function provides guidance on contributing to the **Safety Layer** project, including testing the system, reporting issues,
    submitting improvements, sharing research, and understanding data privacy options.
    """
    with st.expander("How to Contribute", expanded=False):
        st.markdown(
            """
            There are several ways you can help advance AI safety research through OmniGuard:
            
            ### 1. Test the System
            Try different interactions with the chat. Every conversation helps build our dataset of safety examples.
            
            ### 2. Report Issues
            If you encounter cases where the **Safety Layer** fails (either by incorrectly blocking valid content or allowing harmful inputs), 
            use the feedback options to report the issue.
            
            ### 3. Submit Pull Requests
            Visit our Github to contribute code improvements, documentation, or new safety rules.
            
            ### 4. Share Your Research
            If you utilize the **Safety Layer** dataset in your work, let us know so we can highlight your contributions.
            """
        )
        
        st.markdown(
            """
            ## Data Privacy Options
            
            Your interactions help build a valuable public dataset, but you retain control over your data:
            
            - **Public Contribution:** By default, your interactions support public research in AI safety.
            - **Private Usage:** Copy the configuration locally to work with any LLM without contributing your data.
            
            I ensure that no personally identifying information is stored in the public dataset. Other than Name and social media information that you provide.
            """
        )


def main() -> None:
    """Initialize session state and render the **Safety Layer** overview page.

    This function configures the Streamlit application, initializes session state, and organizes the layout into multiple
    tabs that showcase an overview, technical details, dataset information, research directions, contribution guidelines, and licensing.
    """
    st.set_page_config(
        page_title="OmniGuard",
        page_icon="🛡️",
        layout="wide"
    )

    init_session_state()
    show_alpha_banner()

    st.title("OmniGuard")
    st.markdown("*A reasoning-based safety layer underpinned by an open research dataset*")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Overview", "Technical Details", "Dataset", "Research", "Contribute", "License" 
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
