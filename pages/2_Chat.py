import uuid
import streamlit as st
import logging
from dotenv import load_dotenv
from prompts import CMS_configuration, assistant_system_prompt
from database import save_conversation, init_db
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
        st.session_state.conversation_context = json.dumps({
            "conversation_id": st.session_state.conversation_id,
            "messages": st.session_state.messages,
            "configuration": st.session_state.CMS_configuration
        })

def update_conversation_context():
    import json
    st.session_state.conversation_context = json.dumps({
        "conversation_id": st.session_state.conversation_id,
        "messages": st.session_state.messages,
        "configuration": st.session_state.CMS_configuration
    })

def setup_sidebar():
    with st.sidebar.popover("Model Settings", help="Select the CMS model and reasoning effort", icon="⚙️"):
        selected_model = st.selectbox("Select model", ["o1-2024-12-17", "o3-mini-2025-01-31"], index=1)
        selected_reasoning = st.selectbox("Select reasoning effort", ["low", "medium", "high"], index=1)
        st.session_state.selected_model = selected_model
        st.session_state.selected_reasoning = selected_reasoning

    if st.sidebar.button("Clear Conversation") and st.session_state.messages:
        st.session_state.messages.clear()
        st.session_state.base_conversation_id = str(uuid.uuid4())
        st.session_state.turn_number = 1
        st.session_state.conversation_id = generate_conversation_id(st.session_state.turn_number)
        update_conversation_context()
        st.rerun()

    if st.sidebar.button("Report Violation"):
        st.session_state.show_report_violation_form = True

    if st.session_state.get("show_report_violation_form", False):
        with st.sidebar.form("report_violation_form"):
            st.write("Report Rule Violation")
            sources = st.multiselect("Source of the rule violation:", options=["User", "Assistant"])
            st.markdown("---")
            st.write("You will be publicly credited for your contribution.")
            contributor_name = st.text_input("Name:")
            x_handle = st.text_input("X:")
            discord_handle = st.text_input("Discord:")
            linkedin_url = st.text_input("LinkedIn Profile URL:")

            submitted = st.form_submit_button("Submit Report")
            if submitted:
                if not (contributor_name.strip() or x_handle.strip() or discord_handle.strip() or linkedin_url.strip()):
                    st.error("At least one identifier is required!")
                else:
                    parts = []
                    if contributor_name.strip():
                        parts.append(contributor_name.strip())
                    if x_handle.strip():
                        parts.append(f"https://x.com/{x_handle.strip()}")
                    if discord_handle.strip():
                        parts.append(f"Discord: {discord_handle.strip()}")
                    if linkedin_url.strip():
                        parts.append(linkedin_url.strip())
                    contributor_info = ", ".join(parts)
                    conversation_context = st.session_state.conversation_context
                    report_info = f"Configuration: {st.session_state.CMS_configuration}. Sources: {', '.join(sources)}. Contributor: {contributor_info}"
                    violation_result = assess_rule_violation(report_info, conversation_context)
                    st.write("Violation assessment result:", violation_result)
                    if st.session_state.get("contribute_training_data", False):
                        save_conversation(
                            st.session_state.conversation_id,
                            user_violates_rules=violation_result.get("input_violates_rules", False),
                            assistant_violates_rules=violation_result.get("output_violates_rules", False),
                            contributor=contributor_info
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
        with st.spinner("Waiting for CMS response..."):
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
    user_input = st.chat_input("Type your message here", max_chars=20000)
    if user_input:
        process_user_message(user_input)

if __name__ == "__main__":
    main()
