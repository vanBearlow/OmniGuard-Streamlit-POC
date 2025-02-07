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

def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "base_conversation_id" not in st.session_state:
        st.session_state.base_conversation_id = str(uuid.uuid4())
        st.session_state.turn_number = 1
        st.session_state.conversation_id = generate_conversation_id(st.session_state.turn_number)
    if "CMS_configuration" not in st.session_state:
        st.session_state.CMS_configuration = CMS_configuration
    if "assistant_system_prompt" not in st.session_state:
        st.session_state.assistant_system_prompt = assistant_system_prompt
    if "conversation_context" not in st.session_state:
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
    if st.sidebar.button("Clear Conversation") and st.session_state.messages:
        st.session_state.messages.clear()
        st.session_state.base_conversation_id = str(uuid.uuid4())
        st.session_state.turn_number = 1
        st.session_state.conversation_id = generate_conversation_id(st.session_state.turn_number)
        st.session_state.rejection_count = 0  # Reset rejection counter
        update_conversation_context()
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
    user_input = user_input.strip()
    if not user_input:
        return  # Skip processing empty messages
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
    display_messages()
    
    # Display rejection stats
    stats = get_dataset_stats()
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Violation Statistics")
    
    # Display auto-detected and human-verified violations
    st.sidebar.markdown(f"""
    | Role | Auto-Detected | Human-Verified | Total |
    |------|--------------|----------------|-------|
    | User | `{stats['user_violations']}` | `{stats['human_verified_user_violations']}` | `{stats['total_user_violations']}` |
    | Assistant | `{stats['assistant_violations']}` | `{stats['human_verified_assistant_violations']}` | `{stats['total_assistant_violations']}` |
    """)
    
    # Display verification queue status
    if stats['needed_human_verification'] > 0:
        st.sidebar.warning(f"🔍 {stats['needed_human_verification']} conversations need human verification")



    user_input = st.chat_input("Type your message here", max_chars=20000, key="chat_input")
    if user_input:
        process_user_message(user_input)

if __name__ == "__main__":
    main()
