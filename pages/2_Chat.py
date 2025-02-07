import uuid
import streamlit as st
import logging
from dotenv import load_dotenv
from prompts import CMS_configuration, assistant_system_prompt
from database import save_conversation, init_db, get_dataset_stats
from CMS import CMS, process_CMS_result, assess_rule_violation

init_db()
load_dotenv()

st.set_page_config(page_title="CMS Chat", page_icon=":shield:")

def generate_conversation_id(turn_number=1):
    if "base_conversation_id" not in st.session_state:
        st.session_state.base_conversation_id = str(uuid.uuid4())
        st.session_state.turn_number = 1
    return f"{st.session_state.base_conversation_id}-{turn_number}"

def reset_session_state():
    """Reset session state variables to their initial values."""
    st.session_state.messages = []
    st.session_state.base_conversation_id = str(uuid.uuid4())
    st.session_state.turn_number = 1
    st.session_state.conversation_id = generate_conversation_id(st.session_state.turn_number)
    st.session_state.rejection_count = 0
    update_conversation_context()

def init_session_state():
    """Initialize all session state variables if they don't exist."""
    # Message Management
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Conversation Management
    if "base_conversation_id" not in st.session_state:
        st.session_state.base_conversation_id = str(uuid.uuid4())
    if "turn_number" not in st.session_state:
        st.session_state.turn_number = 1
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = generate_conversation_id(st.session_state.turn_number)
    
    # Configuration
    if "CMS_configuration" not in st.session_state:
        st.session_state.CMS_configuration = CMS_configuration
    if "assistant_system_prompt" not in st.session_state:
        st.session_state.assistant_system_prompt = assistant_system_prompt
    
    # UI State
    if "show_report_violation_form" not in st.session_state:
        st.session_state.show_report_violation_form = False
    
    # Metrics & Counters
    if "rejection_count" not in st.session_state:
        st.session_state.rejection_count = 0
    
    # Context Management
    if "conversation_context" not in st.session_state:
        update_conversation_context()
    
    # Message Display State
    if "cms_input_message" not in st.session_state:
        st.session_state.cms_input_message = None
    if "cms_output_message" not in st.session_state:
        st.session_state.cms_output_message = None
    if "assistant_messages" not in st.session_state:
        st.session_state.assistant_messages = None

def update_conversation_context():
    import json
    # Create messages array with system prompt as first message
    full_messages = [{"role": "system", "content": st.session_state.assistant_system_prompt}]
    full_messages.extend(st.session_state.messages)
    
    st.session_state.conversation_context = f"""<input>
        <![CDATA[
            {{
                "id": "{st.session_state.conversation_id}",
                "messages": {json.dumps(full_messages, indent=2)}
            }}
        ]]>
    </input>"""

def setup_sidebar():
    st.sidebar.markdown("---")
    if st.sidebar.button("Clear Conversation") and st.session_state.messages:
        reset_session_state()
        st.rerun()

    if st.sidebar.button("Report Violation"):
        st.session_state.show_report_violation_form = True

    if st.session_state.get("show_report_violation_form", False):
        with st.sidebar.form("report_violation_form"):
            st.write("Report Rule Violation")
            sources = st.multiselect("Source of the rule violation:", options=["User", "Assistant"])

            submitted = st.form_submit_button("Submit Report")
            if submitted:
                conversation_context = st.session_state.conversation_context
                report_info = f"Configuration: {st.session_state.CMS_configuration}. Sources: {', '.join(sources)}"
                violation_result = assess_rule_violation(report_info, conversation_context)
                st.write("Violation assessment result:", violation_result)
                if st.session_state.get("contribute_training_data", False):
                    save_conversation(
                        st.session_state.conversation_id,
                        user_violates_rules=violation_result.get("input_violates_rules", False),
                        assistant_violates_rules=violation_result.get("output_violates_rules", False)
                    )

def display_messages():
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

def process_user_message(user_input):
    if not user_input or not isinstance(user_input, str):
        return  # Skip processing empty or non-string messages
    user_input = user_input.strip()
    st.session_state.turn_number += 1
    st.session_state.conversation_id = generate_conversation_id(st.session_state.turn_number)
    st.session_state.messages.append({"role": "user", "content": user_input})
    update_conversation_context()  # Refresh context after adding the new message

    with st.chat_message("user"):
        st.markdown(user_input)
    try:
        with st.spinner("CMS..."):
            CMS_response = CMS()
    except Exception as ex:
        st.error(f"Error calling CMS: {ex}")
        logging.exception("Exception occurred during CMS call")
        CMS_response = {"response": {"action": "UserInputRejection", "UserInputRejection": "Safety system unavailable - please try again"}}
    last_msg = st.session_state.messages[-1] if st.session_state.messages else {}
    context = f"{last_msg['role']}: {last_msg['content']}" if last_msg else ""
    process_CMS_result(CMS_response, user_input, context)
def main():
    init_session_state()
    if st.session_state.get("contribute_training_data") is False and not st.session_state.get("api_key"):
        st.error("An API key is required when data sharing is disabled. Please go to the Configuration page to enter your API key.")
        st.stop()
    
    setup_sidebar()
    
    # Display rejection stats in sidebar
    stats = get_dataset_stats()
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Violation Statistics")
    
    # Display auto-detected and human-verified violations
    st.sidebar.markdown(f"""
    | Role | Auto-Detected | Human-Verified | Total |
    |------|--------------|----------------|-------|
    | User | `{stats['user_violations']}` | `{stats['human_verified_user_violations']}` | `{stats['total_user_violations']}` |
    | Assistant | `{stats['assistant_violations']}` | `{stats['human_verified_assistant_violations']}` | `{stats['total_assistant_violations']}` |
    """, help="""
    This table shows rule violation statistics:
    
    - Auto-Detected: Violations automatically identified by the OmniGuard
    - Human-Verified: Violations that have been manually confirmed by human reviewers
    - Total: Combined count of both auto-detected and human-verified violations
    
    For each role (User/Assistant), we track violations to maintain safety and improve the system's accuracy. A higher number of human-verified violations may indicate areas where the automatic detection needs improvement.""")
    # help needs to be wrritten better. this sucks at explaining the stats.
    # Display verification queue status
    if stats['needed_human_verification'] > 0:
        st.sidebar.warning(f"🔍 {stats['needed_human_verification']} conversations need human verification")
    
    # Main chat area
    display_messages()
    user_input = st.chat_input("Type your message here", max_chars=20000, key="chat_input")
    if user_input:  # st.chat_input already returns a string or None
        process_user_message(user_input)
    
    with st.expander("Message to CMS", expanded=True):
        if st.session_state.cms_input_message:
            st.json(st.session_state.cms_input_message)
        
    with st.expander("Message from CMS", expanded=True):
        if st.session_state.cms_output_message:
            st.json(st.session_state.cms_output_message)
        
    with st.expander("Messages to Assistant", expanded=True):
        if st.session_state.assistant_messages:
            st.write(st.session_state.assistant_messages)

if __name__ == "__main__":
    main()

