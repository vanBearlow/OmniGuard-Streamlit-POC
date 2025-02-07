import requests
import streamlit as st
import json
from human_verification_db import get_connection, init_db as hv_init_db

st.set_page_config(page_title="Human Verification", page_icon=":shield:")

def get_flagged_conversations():
    """
    Retrieve conversations flagged for human verification.
    This function queries for conversations with a vote count 
    either missing or below the threshold of 100.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT conversation_id, conversation_messages, conversation_configuration,
               COALESCE(user_violation_votes, 0) as user_violation_votes, 
               COALESCE(assistant_violation_votes, 0) as assistant_violation_votes, 
               COALESCE(no_violation_votes, 0) as no_violation_votes
        FROM flagged_conversations
        WHERE COALESCE(user_violation_votes, 0) + 
              COALESCE(assistant_violation_votes, 0) + 
              COALESCE(no_violation_votes, 0) < 100
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return rows

def record_vote(conversation_id, api_key, sources):
    """
    Send a verification request using the provided API key.
    The request uses the 4o mini model with max_tokens set to 1.
    If the response is successful (HTTP 200), increment the vote counts
    in the database for the provided conversation_id based on selected sources.
    """
    url = "https://openrouter.ai/api/v1/verify"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "prompt": "HI",
        "max_tokens": 1,
        "model": "openai/4o-mini"
    }
    
    try:
        # Post verification request with timeout.
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            user_vote = 1 if "User" in sources else 0
            assistant_vote = 1 if "Assistant" in sources else 0
            no_rule_vote = 1 if "No Rule Violations" in sources else 0
            conn = get_connection()
            cursor = conn.cursor()
            # Store last 8 characters of API key to prevent duplicate votes.
            short_api_key = api_key[-8:]
            cursor.execute("SELECT 1 FROM flagged_votes WHERE conversation_id = %s AND api_key = %s",
                            (conversation_id, short_api_key))
            if cursor.fetchone():
                conn.close()
                return "already_voted"

            cursor.execute(
                """
                UPDATE flagged_conversations
                SET user_violation_votes = COALESCE(user_violation_votes, 0) + %s,
                    assistant_violation_votes = COALESCE(assistant_violation_votes, 0) + %s,
                    no_violation_votes = COALESCE(no_violation_votes, 0) + %s
                WHERE conversation_id = %s
                """, (user_vote, assistant_vote, no_rule_vote, conversation_id)
            )
            cursor.execute("INSERT INTO flagged_votes (conversation_id, api_key) VALUES (%s, %s)",
                            (conversation_id, short_api_key))
            conn.commit()

            # Re-query updated conversation details.
            cursor.execute(
                """
                SELECT conversation_messages, conversation_configuration,
                       COALESCE(user_violation_votes, 0) as user_votes,
                       COALESCE(assistant_violation_votes, 0) as assistant_votes,
                       COALESCE(no_violation_votes, 0) as no_rule_votes
                FROM flagged_conversations
                WHERE conversation_id = %s
                """, (conversation_id,)
            )
            result = cursor.fetchone()
            conn.close()

            if result:
                conversation_messages, conversation_configuration, user_votes, assistant_votes, no_rule_votes = result
                total_votes = user_votes + assistant_votes + no_rule_votes

                if total_votes >= 100:
                    import json
                    from CMS import assess_rule_violation
                    # Build a JSON report of the vote counts.
                    report_info = json.dumps({
                        "user_votes": user_votes,
                        "assistant_votes": assistant_votes,
                        "no_rule_votes": no_rule_votes
                    })
                    # Combine conversation content and configuration.
                    conversation_context = f"""<input>
                        <![CDATA[
                            {{
                                "id": "{conversation_id}",
                                "messages": {conversation_messages}
                            }}
                        ]]>
                    </input>"""

                    violation_result = assess_rule_violation(report_info, conversation_context)

                    # If model finds no automatic violations, check for promotion criteria.
                    if violation_result.get("input_violates_rules") == False and violation_result.get("output_violates_rules") == False:
                        from database import get_conversation, save_conversation
                        existing = get_conversation(conversation_id)
                        # Example criteria: if "No Rule Violations" votes are dominant.
                        if not existing and no_rule_votes >= (user_votes + assistant_votes):
                            save_conversation(conversation_id, conversation_messages, conversation_configuration, user_votes, assistant_votes, no_rule_votes)
                    else:
                        # If a violation is indicated and the conversation exists in main dataset, remove it.
                        from database import get_conversation, remove_conversation
                        existing = get_conversation(conversation_id)
                        if existing:
                            remove_conversation(conversation_id)

            return True
        else:
            # Provide subtle feedback while logging full details separately
            st.warning(f"Verification endpoint returned {response.status_code}: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error during API key verification: {e}. Please check your API key and your network connection.")
        return False

def display_conversation(conv):
    """
    Format and display a single conversation entry along with its current vote count,
    and provide a voting form that accepts an API key for verification.
    """
    conversation_id, conversation_messages, conversation_configuration, user_violation_votes, assistant_violation_votes, no_violation_votes = conv
    st.markdown(f"**Conversation ID:** ")
    st.code(f"{conversation_id}")
    with st.expander("Show Configuration"):
        st.code(conversation_configuration, language="xml")
    with st.expander("Show Messages"):
        st.json(json.loads(conversation_messages))

    with st.form(key=f"vote_form_{conversation_id}"):
        st.markdown("Are any rule violations present? Be sure to verify configuration before voting. If so, select the sources of the violations.")
        
        user_rule = st.checkbox("User")
        assistant_rule = st.checkbox("Assistant")
        no_rule = st.checkbox("No Rule Violations")
        sources = []
        if no_rule:
            sources.append("No Rule Violations")
        if user_rule:
            sources.append("User")
        if assistant_rule:
            sources.append("Assistant")
        vote_submit = st.form_submit_button("Submit")
        if vote_submit:
            api_key = st.session_state.get("api_key")
            if not api_key:
                st.error("An API key is required to vote. Please set it in the sidebar.")
            else:
                vote_result = record_vote(conversation_id, api_key, sources)
                if vote_result == True:
                    st.success("Success")
                elif vote_result == "already_voted":
                    st.error("You have already voted for this conversation.")
                else:
                    st.error("Vote failed. Please ensure your API key is valid and try voting again.")
    st.markdown(f"**Current Results:** User Violations: {user_violation_votes} | Assistant Violations: {assistant_violation_votes} | No Violations: {no_violation_votes}")

def main():
    """
    Main function to render the Human Verification Dashboard.
    This page lists flagged conversations and provides the voting interface.
    """
    hv_init_db()
    with st.sidebar:
        st.markdown(
            """
            # Human Verification Dashboard

            Review interactions that were reported as containing violations, but OmniGuard doesn't agree.


            - **Authentication:** To avoid spam, each session is verified using **OpenAI or Open Router API**.""")

        with st.sidebar.expander("Verification Request"):
            st.code("""response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": [{"type": "text", "text": "Return: True"}]}],
    response_format={"type": "text"},
    temperature=0,
    max_completion_tokens=1
    )""")
        st.markdown("""
             - **Threshold:** Once a reported interaction reaches **100 total votes**, it will be recorded to the interactions database.
             """)
    
        st.markdown("---")

        st.text_input("Authenticate with OpenAI or OpenRouter API Key:", type="password", key="api_key", help="This is used to verify the session. It is not stored. Refreshing the page will reset your authentication status.")
    


    api_key = st.session_state.get("api_key")
    if not api_key:
        st.error("An API key is required to view conversations.")
        st.stop()
    else:
        if api_key.startswith("sk-or"):
            st.session_state["api_type"] = "openrouter"
        else:
            st.session_state["api_type"] = "openai"
    
    conversations = get_flagged_conversations()
    if not conversations:
        st.write("No conversations require verification at this time.")
    else:
        for conv in conversations:
            st.markdown("---")
            display_conversation(conv)

if __name__ == "__main__":
    main()
