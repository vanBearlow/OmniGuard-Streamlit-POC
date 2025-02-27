import streamlit as st
from components.banner import show_alpha_banner
from components.chat.session_management import get_supabase_client
from components.init_session_state import init_session_state


def render_system_flow() -> None:
    """Render a technical explanation of OmniGuard's system architecture and workflow.

    This function displays how OmniGuard initializes its configuration
    and processes messages, highlighting the internal steps for
    validating user and assistant messages.
    """
    with st.expander("System Architecture", expanded=False):
        st.markdown(
            """
        ## System Architecture
        
        ### Message Evaluation Pipeline
        
        ```
        User/Assistant Message → Configuration Injection → Safety Evaluation → Action Determination → Response Generation
        ```
        
        1. **Configuration Initialization**  
           - Safety rules are injected via the `role.developer.content` field
           - Rules are organized into hierarchical categories with examples
           - The model receives both configuration and message context
        
        2. **Contextual Analysis**
           - Each message is evaluated against active rule sets
           - Context window includes conversation history for intent recognition
           - Rule violations are classified by severity and confidence
        
        3. **Response Determination**
           - Safe content passes through unmodified
           - Minor violations trigger content sanitization
           - Major violations invoke appropriate refusal responses
           - Ambiguous cases prompt clarification requests
        """
        )

        from components.prompts import omniguard_configuration

        with st.popover("View Complete Configuration XML"):
            st.code(omniguard_configuration, language="xml")

        st.markdown(
            """
        ### Configuration Structure
        
        The system operates using three core components:
        
        1. **Purpose Definition**: Establishes OmniGuard as a reasoning-based safety layer
        
        2. **Instruction Set**: Defines operational parameters:
           - Message evaluation methodology
           - Ambiguity resolution procedures
           - Response generation protocols
           - Conversation flow maintenance
        
        3. **Rule Groups**: Structured categorization of safety rules:
           - **Content Moderation (CM)**: Harmful content detection
           - **Data Leakage Prevention (DLP)**: Sensitive information protection
           - **Adversarial Attacks (AA)**: Protection against prompt injections, jailbreaks, etc.
        
        Each rule includes examples of user violations and potential assistant failures, classified by severity.
        """
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
          "analysisSummary": "Brief explanation of evaluation",
          "compliant": true,
          "response": {
            "action": "RefuseUser",
            "RefuseUser": "Safety explanation response"
          }
        }
        ```
        
        ### Integration Patterns
        
        **Basic Request Flow:**
        
        1. Receive user message
        2. Pass to OmniGuard with context
        3. If non-compliant, display refusal message
        4. If compliant, pass to primary LLM
        5. Pass LLM response back to OmniGuard
        6. Deliver final (potentially sanitized) response to user
            
        **Advanced Integration Options:**
            
        - Batch evaluation for high-throughput applications
        - Tiered evaluation with lightweight pre-screening
        - Custom rule injection for domain-specific safety
        - Feedback loop integration for continuous improvement
        """
        )

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
        # Donation Wallet section
        st.markdown("## Donation Wallet")
        
        # Display wallet address
        st.code(wallet_address, language=None)
        st.info("⚠️ Please only send USDT on the Tron (TRC20) network to this address.")


def render_end_note() -> None:
    """Render the concluding note for the OmniGuard overview."""
    st.markdown("""
    ---
    
    > "The future of AI safety doesn't just depend on big labs. It requires a community of researchers, developers, and users working together to identify risks and build better solutions. Join me in making AI safer, one interaction at a time."
    
    `Humanity can not afford AI safety debt.`

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
    with st.expander("What is OmniGuard?", expanded=False):
        st.markdown("""
        ## What is OmniGuard?
        
        OmniGuard is an intelligent safety layer that applies reasoning-based evaluation to LLM interactions. Unlike traditional guardrails that rely on keyword matching or simplistic classification, OmniGuard examines message intent, context, and nuance to make informed moderation decisions while preserving meaningful conversation.
        
        The system operates as both:
        - A **practical safety mechanism** for protecting AI applications
        - A **research platform** generating valuable safety datasets
        
        > "Human safety and AI alignment require tools that understand intent, not just keywords."
        """)


def render_key_features() -> None:
    """Render the key features of OmniGuard with technical specificity."""
    with st.expander("Core Capabilities", expanded=False):
        st.markdown("""
        ## Core Capabilities
        
        ### Reasoning Engine
        - **Context-aware analysis** evaluates semantic content beyond surface patterns
        - **Intent recognition** differentiates between educational queries and harmful requests
        - **Response gradation** from sanitization to refusal based on violation severity
        
        ### Security Framework
        - **Adversarial attack mitigation** against 12+ prompt injection vectors
        - **Data leakage protection** for sensitive information
        - **Rule-based safety policies** with configurable priorities
        
        ### Research Infrastructure
        - **Structured dataset collection** of safety interactions
        - **Classification outcomes** with human verification system
        - **Attack pattern documentation** for evolving threat model development
        
        ### Implementation Architecture
        - **Language model agnostic** design works across providers
        - **JSON-based I/O protocol** with standardized schema
        - **Minimal integration requirements** for existing AI systems
        """)


def render_use_cases() -> None:
    """Render practical use cases focused on technical implementation scenarios."""
    with st.expander("Implementation Scenarios", expanded=False):
        st.markdown("""
        ## Implementation Scenarios
        
        ### Research Applications
        - **Safety Classifier Training**: Use the dataset to build specialized guardrails or distill smaller models
        - **Attack Vector Analysis**: Study patterns in successful vs. failed prompt injections
        - **Countermeasure Development**: Test defensive strategies against documented attack patterns
        - **Benchmarking**: Compare different safety approaches against standardized threats
        
        ### Production Deployment
        - **API Protection Layer**: Shield backend systems from prompt injection and jailbreaking
        - **Enterprise Compliance**: Enforce information security policies for sensitive domains
        - **Consumer Applications**: Provide safety guarantees for public-facing AI products
        - **Multi-LLM Environments**: Apply consistent safety standards across different model providers
        
        ### Development Lifecycle
        - **Pre-deployment Testing**: Evaluate model safety before production release
        - **Continuous Monitoring**: Identify emerging vulnerabilities in deployed systems
        - **Regulatory Alignment**: Document safety measures for compliance requirements
        """)


def render_dataset_applications() -> None:
    """Render section about dataset applications for research."""
    st.markdown("---")
    with st.expander("Using This Dataset", expanded=False):
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
    
    # Display dataset format example
    with st.expander("Dataset Example", expanded=False):
        
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


def render_research_opportunities() -> None:
    """Render information about research opportunities with OmniGuard.
    
    This function outlines potential research directions and questions
    that can be explored using the OmniGuard platform, and provides
    guidance on how researchers can contribute to and cite the project.
    """
    with st.expander("Research Vectors", expanded=False):
        st.markdown(
            """
            ### Research Repositories & Papers
            
            We invite researchers to use this dataset in academic work. If you publish findings based on OmniGuard data:
            1. Cite the dataset using the standard citation format (see Documentation tab)
            2. Consider contributing your findings back to the community
            3. Let us know about your work so we can feature it
            
            ### Specific Research Directions
            
            #### 1. AI Safety & Alignment
            - **Intent Recognition**: Develop models that better distinguish educational queries from harmful requests
            - **Attack Vector Analysis**: Identify patterns in successful vs. failed prompt injections
            - **Model Scaling Laws**: Quantify how safety performance correlates with model size and training data
            
            #### 2. Security & Robustness
            - **Lightweight Guardrails**: Create efficient safety classifiers that can run on edge devices
            - **Defense-in-Depth**: Measure the effectiveness of layered defensive techniques
            - **Safety-Utility Frontier**: Map the tradeoff curve between protection and model usefulness
            
            #### 3. Human-AI Interaction
            - **Circumvention Patterns**: Analyze how users attempt to bypass safety measures
            - **Refusal UX**: Design and test more effective explanations for content rejections
            - **Trust Calibration**: Develop methods to maintain user trust while enforcing safety boundaries
            
            ### Getting Started
            
            1. **Download the Dataset**: Use the download button in the Dataset tab
            2. **Explore the GitHub**: Find example code and documentation at our repository
            3. **Join the Community**: Connect with other researchers in our Discord server
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
    with st.expander("How to Contribute", expanded=False):
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
        page_title="OmniGuard",
        page_icon="🛡️",
        layout="wide"
    )

    init_session_state()
    show_alpha_banner()

    st.title("OmniGuard")
    st.markdown("*A reasoning-based guardrail with open research dataset*")

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
