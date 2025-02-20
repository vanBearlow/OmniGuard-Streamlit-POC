import json
import streamlit as st
from typing import Dict, Any
from components.init_session_state import init_session_state
from components.chat.session_management import get_supabase_client



#  === Rendering Functions ===
def render_overview() -> None:
    """Render the component overview markdown."""
    st.markdown(
        """
## 1. Component Overview

- **OmniGuard** is a reasoning based conversation moderation system for text-based LLM interactions.
- It assesses each turn of user and assistant messages against a configurable set of content rules.
- OmniGuard can sanitize minor violations and probe for clarification in ambiguous cases, thereby preserving an engaging and meaningful dialogue while upholding safety standards.
- The system effectively mitigates the majority of potential violations and attacks through its comprehensive rule set and reasoning capabilities.
    
> **Note:** This is not intended to be a full AI security solution; rather, it is designed to effectively protect wrappers and agents from most attacks without decreasing the performance.
        """
    )


def render_system_and_configuration() -> None:
    """Render the system flow, configuration, and default configuration example."""
    st.markdown("---")
    st.markdown(
        """
## 2. System Flow and Configuration

### 2.1 Operational Flow
1. **Configuration Initialization**  
   - The safety configuration (Purpose, Instructions, and Rules) is injected into the `role.developer.content` field.
   - This primes OmniGuard with all necessary guidelines and behavioral protocols.
    
2. **Message Processing**  
   - OmniGuard inspects every incoming message against active rules.
   - Violations are handled through:
     - Sanitization for minor issues.
     - Safe, generic refusal for major violations.
     - Clarification requests for ambiguous cases.

### 2.2 Configuration Components
        """
    )

    # Use an expander to show the default configuration
    with st.expander("Default Configuration:"):
        from prompts import omniguard_configuration  # noqa: F401
        st.code(omniguard_configuration, language="xml")
        st.write("`4111 Tokens`")

    st.markdown(
        """
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

### 2.3 Implementation Format

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


def render_goals() -> None:
    """Render the goals and future vision markdown."""
    st.markdown("---")
    st.markdown(
        """
## 4. Goals and Future Vision

OmniGuard is committed to advancing the field of AI safety through three key initiatives:

1. **Open Safety Research Data**
   - Providing a comprehensive, freely accessible dataset of safety-related interactions.
   - Enabling researchers and developers to study, analyze, and improve AI safety mechanisms.
   - Contributing to the collective understanding of AI safety challenges and solutions.

2. **Multimodal Safety Expansion**
   - Extending OmniGuard's capabilities beyond text to include:
     - Image moderation and safety analysis.
     - Audio content verification.
     - Video content safety assessment.
   - Developing unified safety protocols across different modalities.

3. **Model Distillation**
   - Leveraging the collected dataset to create smaller, more efficient safety models.
   - Reducing computational overhead while maintaining robust safety standards.
   - Making AI safety more accessible and deployable across different scales of applications.

Through these initiatives, OmniGuard aims to foster innovation in AI safety while ensuring that safety mechanisms remain accessible and effective for the entire AI community.
        """
    )


def render_dataset_content() -> None:
    """Render the dataset content including statistics, format example, and download options."""
    supabase = get_supabase_client()

    # --- Fetch Dataset Statistics ---
    try:
        result = supabase.table("interactions").select("*").execute()
        data   = result.data if result else []

        # Calculate statistics (vertically aligned for clarity)
        stats_data = {
            'total_interactions'        : len(data),
            'human_verified'            : sum(1 for item in data if item.get('verification_status') == 'human'),
            'omniguard_verified'        : sum(1 for item in data if item.get('verification_status') == 'omniguard'),
            'pending_verification'      : sum(1 for item in data if item.get('verification_status') == 'pending'),
            'compliant_interactions'    : sum(1 for item in data if item.get('compliant') is True),
            'non_compliant_interactions': sum(1 for item in data if item.get('compliant') is False)
        }

        if stats_data:
            st.markdown("## Dataset Statistics")

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

    st.markdown("---")

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
            {"role": "assistant", "content": "<OUTPUT>"}
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
            "safe_votes": integer
        }
    },
    "contributor": {
        "name": "string",
        "x": "string",
        "discord": "string",
        "linkedin": "string"
    },
    "verification_status": "omniguard" | "pending" | "human",
    "compliant": boolean,
    "created_at": timestamp,
    "updated_at": timestamp
}
```
            """
        )

    st.markdown("---")

    # --- Download Button for Dataset ---
    try:
        query  = supabase.table("interactions").select(
                     "id", "conversation", "metadata", "contributor",
                     "verification_status", "compliant", "created_at", "updated_at"
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
### Using OmniGuard

All interactions within this application will be made public and added to the dataset (free for use).

If you wish to use OmniGuard privately without contributing data to the public dataset:
1. Copy the default configuration from the Overview tab.
2. Use it in any LLM Playground of your choice.
        """
    )
# endregion


# region === Main Application ===
def main() -> None:
    """Main function to initialize session state and render the project overview page."""
    st.set_page_config(
        page_title="OmniGuard Overview",
        page_icon="🛡️"
    )

    init_session_state()
    st.title("OmniGuard - Conversation Moderation System (ALPHA)")

    # Updated tabs to remove the notes tab
    overview_tab, dataset_tab, disclaimer_tab = st.tabs(["Overview", "Dataset", "Disclaimer"])

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
