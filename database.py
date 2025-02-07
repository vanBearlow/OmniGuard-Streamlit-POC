import os
import psycopg2
import json
import streamlit as st
from dotenv import load_dotenv

# Load environment variables for local development
load_dotenv()

def get_connection():
    try:
        # Try to get credentials from Streamlit secrets first
        try:
            host = st.secrets["postgres"]["host"]
            port = st.secrets["postgres"]["port"]
            user = st.secrets["postgres"]["user"]
            password = st.secrets["postgres"]["password"]
            database = st.secrets["postgres"]["database"]
        except (KeyError, AttributeError):
            # Fall back to environment variables for local development
            host = os.getenv("RDS_HOST")
            port = int(os.getenv("RDS_PORT", "5432"))
            user = os.getenv("RDS_USER")
            password = os.getenv("RDS_PASSWORD")
            database = os.getenv("RDS_DATABASE")

        return psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            sslmode="prefer"
        )
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        raise

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        '''CREATE TABLE IF NOT EXISTS conversations (
            conversation_id TEXT PRIMARY KEY,
            cms_evaluation_input TEXT,
            cms_raw_response TEXT,
            assistant_output TEXT,
            user_violates_rules INTEGER,
            assistant_violates_rules INTEGER,
            model_name TEXT,
            reasoning_effort TEXT,
            contributor TEXT
        )'''
    )
    # Use PostgreSQL-compatible schema inspection
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'conversations';")
    columns = [row[0] for row in cur.fetchall()]
    
    if "cms_evaluation_input" not in columns:
        cur.execute("ALTER TABLE conversations ADD COLUMN cms_evaluation_input TEXT")
    if "cms_raw_response" not in columns:
        cur.execute("ALTER TABLE conversations ADD COLUMN cms_raw_response TEXT")
    if "assistant_output" not in columns:
        cur.execute("ALTER TABLE conversations ADD COLUMN assistant_output TEXT")
    if "user_violates_rules" not in columns:
        cur.execute("ALTER TABLE conversations ADD COLUMN user_violates_rules INTEGER")
    if "assistant_violates_rules" not in columns:
        cur.execute("ALTER TABLE conversations ADD COLUMN assistant_violates_rules INTEGER")
    if "model_name" not in columns:
        cur.execute("ALTER TABLE conversations ADD COLUMN model_name TEXT")
    if "reasoning_effort" not in columns:
        cur.execute("ALTER TABLE conversations ADD COLUMN reasoning_effort TEXT")
    if "contributor" not in columns:
        cur.execute("ALTER TABLE conversations ADD COLUMN contributor TEXT")
    
    conn.commit()
    conn.close()

def get_all_conversations(export_format="jsonl"):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT conversation_id, cms_evaluation_input, cms_raw_response, 
               assistant_output, user_violates_rules, assistant_violates_rules,
               model_name, reasoning_effort, contributor
        FROM conversations
    """)
    rows = cur.fetchall()
    conn.close()
    if export_format == "jsonl":
        results = []
        for row in rows:
            results.append({
                "conversation_id": row[0],
                "cms_evaluation_input": json.loads(row[1]) if row[1] else None,
                "cms_raw_response": json.loads(row[2]) if row[2] else None,
                "assistant_output": row[3],
                "user_violates_rules": bool(row[4]),
                "assistant_violates_rules": bool(row[5]),
                "model_name": row[6],
                "reasoning_effort": row[7],
                "contributor": row[8]
            })
        return "\n".join(json.dumps(conv) for conv in results)
    else:
        return json.dumps(rows)

def save_conversation(conversation_id, user_violates_rules=False,
                     assistant_violates_rules=False, contributor="", cms_evaluation_input=None,
                     cms_raw_response=None, assistant_output=None, model_name=None,
                     reasoning_effort=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO conversations
            (conversation_id, cms_evaluation_input, cms_raw_response, assistant_output,
             user_violates_rules, assistant_violates_rules,
             model_name, reasoning_effort, contributor)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (conversation_id) DO UPDATE
            SET cms_evaluation_input = EXCLUDED.cms_evaluation_input,
                cms_raw_response = EXCLUDED.cms_raw_response,
                assistant_output = EXCLUDED.assistant_output,
                user_violates_rules = EXCLUDED.user_violates_rules,
                assistant_violates_rules = EXCLUDED.assistant_violates_rules,
                model_name = EXCLUDED.model_name,
                reasoning_effort = EXCLUDED.reasoning_effort,
                contributor = EXCLUDED.contributor
        """,
        (
            conversation_id,
            json.dumps(cms_evaluation_input) if cms_evaluation_input else None,
            json.dumps(cms_raw_response) if cms_raw_response else None,
            assistant_output,
            1 if user_violates_rules else 0,
            1 if assistant_violates_rules else 0,
            model_name,
            reasoning_effort,
            contributor
        )
    )
    conn.commit()
    conn.close()

def get_conversation(conversation_id):
    """
    Check if a conversation exists in the main dataset.
    Returns the conversation data if found, None otherwise.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT conversation_id, cms_evaluation_input, cms_raw_response,
               assistant_output, user_violates_rules, assistant_violates_rules,
               model_name, reasoning_effort, contributor
        FROM conversations
        WHERE conversation_id = %s
        """,
        (conversation_id,)
    )
    result = cur.fetchone()
    conn.close()
    if result:
        return {
            "conversation_id": result[0],
            "cms_evaluation_input": json.loads(result[1]) if result[1] else None,
            "cms_raw_response": json.loads(result[2]) if result[2] else None,
            "assistant_output": result[3],
            "user_violates_rules": bool(result[4]),
            "assistant_violates_rules": bool(result[5]),
            "model_name": result[6],
            "reasoning_effort": result[7],
            "contributor": result[8]
        }
    return None

def remove_conversation(conversation_id):
    """
    Remove a conversation from the main dataset.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM conversations WHERE conversation_id = %s",
        (conversation_id,)
    )
    conn.commit()
    conn.close()
