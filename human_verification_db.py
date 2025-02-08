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
        '''CREATE TABLE IF NOT EXISTS flagged_conversations (
            conversation_id TEXT PRIMARY KEY,
            conversation_messages TEXT,
            conversation_configuration TEXT,
            user_violation_votes INTEGER DEFAULT 0,
            assistant_violation_votes INTEGER DEFAULT 0,
            no_violation_votes INTEGER DEFAULT 0,
            reported_user_violation BOOLEAN DEFAULT FALSE,
            reported_assistant_violation BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )'''
    )
    cur.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'flagged_conversations'
    """)
    columns = [row[0] for row in cur.fetchall()]
    
    # Add vote columns if they don't exist
    if "user_violation_votes" not in columns:
        cur.execute("ALTER TABLE flagged_conversations ADD COLUMN user_violation_votes INTEGER DEFAULT 0")
    if "assistant_violation_votes" not in columns:
        cur.execute("ALTER TABLE flagged_conversations ADD COLUMN assistant_violation_votes INTEGER DEFAULT 0")
    if "no_violation_votes" not in columns:
        cur.execute("ALTER TABLE flagged_conversations ADD COLUMN no_violation_votes INTEGER DEFAULT 0")
    if "created_at" not in columns:
        cur.execute("ALTER TABLE flagged_conversations ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP")
    if "reported_user_violation" not in columns:
        cur.execute("ALTER TABLE flagged_conversations ADD COLUMN reported_user_violation BOOLEAN DEFAULT FALSE")
    if "reported_assistant_violation" not in columns:
        cur.execute("ALTER TABLE flagged_conversations ADD COLUMN reported_assistant_violation BOOLEAN DEFAULT FALSE")
    
    # Add final decision columns if they don't exist
    if "final_decision_made" not in columns:
        cur.execute("ALTER TABLE flagged_conversations ADD COLUMN final_decision_made BOOLEAN DEFAULT FALSE")
    if "final_decision_timestamp" not in columns:
        cur.execute("ALTER TABLE flagged_conversations ADD COLUMN final_decision_timestamp TIMESTAMP WITH TIME ZONE")
    if "final_decision_details" not in columns:
        cur.execute("ALTER TABLE flagged_conversations ADD COLUMN final_decision_details JSONB")
    if "archived" not in columns:
        cur.execute("ALTER TABLE flagged_conversations ADD COLUMN archived BOOLEAN DEFAULT FALSE")
    
    # Create votes tracking table
    cur.execute(
        '''CREATE TABLE IF NOT EXISTS flagged_votes (
            conversation_id TEXT,
            user_email TEXT,
            decision_comment TEXT,
            PRIMARY KEY (conversation_id, user_email)
        )'''
    )
    conn.commit()
    conn.close()

def get_flagged_conversations(export_format="jsonl"):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT conversation_id, conversation_messages, conversation_configuration,
               user_violation_votes, assistant_violation_votes, no_violation_votes,
               reported_user_violation, reported_assistant_violation,
               created_at
        FROM flagged_conversations
    """)
    rows = cur.fetchall()
    conn.close()
    if export_format == "jsonl":
        results = []
        for row in rows:
            results.append({
                "conversation_id": row[0],
                "conversation_messages": json.loads(row[1]),
                "conversation_configuration": row[2],
                "user_violation_votes": row[3],
                "assistant_violation_votes": row[4],
                "no_violation_votes": row[5],
                "reported_user_violation": bool(row[6]),
                "reported_assistant_violation": bool(row[7]),
                "created_at": row[8].isoformat() if row[8] else None
            })
        return "\n".join(json.dumps(conv) for conv in results)
    else:
        return json.dumps(rows)

def save_flagged_conversation(conversation_id, conversation_messages, conversation_configuration="",
                             user_violation_votes=0, assistant_violation_votes=0, no_violation_votes=0,
                             reported_user_violation=False, reported_assistant_violation=False):
    conn = get_connection()
    cur = conn.cursor()
    query = """
        INSERT INTO flagged_conversations
        (conversation_id, conversation_messages, conversation_configuration,
         user_violation_votes, assistant_violation_votes, no_violation_votes,
         reported_user_violation, reported_assistant_violation)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (conversation_id) DO UPDATE SET
            conversation_messages = EXCLUDED.conversation_messages,
            conversation_configuration = EXCLUDED.conversation_configuration,
            user_violation_votes = EXCLUDED.user_violation_votes,
            assistant_violation_votes = EXCLUDED.assistant_violation_votes,
            no_violation_votes = EXCLUDED.no_violation_votes,
            reported_user_violation = EXCLUDED.reported_user_violation,
            reported_assistant_violation = EXCLUDED.reported_assistant_violation
    """
    cur.execute(query, (
        conversation_id,
        f"""<input>
            <![CDATA[
                {{
                    "id": "{conversation_id}",
                    "messages": {json.dumps(conversation_messages, indent=2)}
                }}
            ]]>
        </input>""",
        conversation_configuration,
        user_violation_votes,
        assistant_violation_votes,
        no_violation_votes,
        reported_user_violation,
        reported_assistant_violation
    ))
    conn.commit()
    conn.close()
