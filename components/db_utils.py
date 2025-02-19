import json
import streamlit as st
from st_supabase_connection import SupabaseConnection, execute_query

@st.cache_resource
def get_db_connection():
    """
    Returns a cached Supabase connection using 
    the st-supabase-connection library.
    """
    return st.connection(name="supabase_connection", type=SupabaseConnection)

def save_conversation_turn():
    """
    Inserts or upserts the current turn into the 'conversation_turns' table.
    Call this after OmniGuard finalizes each turn 
    (e.g., after the assistant response is processed).
    """
    # 1. Build the conversation JSON
    conversation_data = {
        "omniguardConfiguration": st.session_state.omniguard_configuration,
        "messages": st.session_state.messages,
    }

    # 2. Build the metadata JSON
    metadata_data = {
        "submittedForReview": st.session_state.get("show_report_violation_form", False),
        "contributor": {
            "name": st.session_state.get("contributor_name", ""),
            "twitter": st.session_state.get("contributor_twitter", "")
        },
        "usageMetrics": {},
        "humanReview": {}
    }

    # 3. Prepare the row for insertion
    row = {
        "id": st.session_state.conversation_id,
        "base_conversation_id": st.session_state.base_conversation_id,
        "turn_number": st.session_state.turn_number,
        "conversation": conversation_data,
        "metadata": metadata_data
    }

    db = get_db_connection()

    # 4. Upsert the row to allow updating metadata later
    query = db.table("conversation_turns").upsert([row], on_conflict="id")
    response = execute_query(query)
    return response
