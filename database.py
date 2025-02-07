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
    
    # Create users table
    cur.execute(
        '''CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            picture TEXT,
            api_keys JSONB DEFAULT '{}',
            social_handles JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP WITH TIME ZONE
        )'''
    )
    
    # Create conversations table
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
            contributor TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            total_tokens INTEGER,
            input_cost NUMERIC(10,4),
            output_cost NUMERIC(10,4),
            total_cost NUMERIC(10,4),
            latency_ms INTEGER
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
    if "created_at" not in columns:
        cur.execute("ALTER TABLE conversations ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP")
    if "prompt_tokens" not in columns:
        cur.execute("ALTER TABLE conversations ADD COLUMN prompt_tokens INTEGER")
    if "completion_tokens" not in columns:
        cur.execute("ALTER TABLE conversations ADD COLUMN completion_tokens INTEGER")
    if "total_tokens" not in columns:
        cur.execute("ALTER TABLE conversations ADD COLUMN total_tokens INTEGER")
    if "input_cost" not in columns:
        cur.execute("ALTER TABLE conversations ADD COLUMN input_cost NUMERIC(10,4)")
    if "output_cost" not in columns:
        cur.execute("ALTER TABLE conversations ADD COLUMN output_cost NUMERIC(10,4)")
    if "total_cost" not in columns:
        cur.execute("ALTER TABLE conversations ADD COLUMN total_cost NUMERIC(10,4)")
    if "latency_ms" not in columns:
        cur.execute("ALTER TABLE conversations ADD COLUMN latency_ms INTEGER")
    
    conn.commit()
    conn.close()

def get_all_conversations(export_format="jsonl"):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT conversation_id, cms_evaluation_input, cms_raw_response,
               assistant_output, user_violates_rules, assistant_violates_rules,
               model_name, reasoning_effort, contributor, created_at,
               prompt_tokens, completion_tokens, total_tokens,
               input_cost, output_cost, total_cost, latency_ms
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
                "contributor": row[8],
                "created_at": row[9].isoformat() if row[9] else None,
                "prompt_tokens": row[10],
                "completion_tokens": row[11],
                "total_tokens": row[12],
                "input_cost": float(row[13]) if row[13] else None,
                "output_cost": float(row[14]) if row[14] else None,
                "total_cost": float(row[15]) if row[15] else None,
                "latency_ms": row[16]
            })
        return "\n".join(json.dumps(conv) for conv in results)
    else:
        return json.dumps(rows)

def save_conversation(conversation_id, user_violates_rules=False,
                     assistant_violates_rules=False, contributor="", cms_evaluation_input=None,
                     cms_raw_response=None, assistant_output=None, model_name=None,
                     reasoning_effort=None, prompt_tokens=None, completion_tokens=None,
                     total_tokens=None, input_cost=None, output_cost=None, total_cost=None,
                     latency_ms=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO conversations
            (conversation_id, cms_evaluation_input, cms_raw_response, assistant_output,
             user_violates_rules, assistant_violates_rules,
             model_name, reasoning_effort, contributor,
             prompt_tokens, completion_tokens, total_tokens,
             input_cost, output_cost, total_cost, latency_ms)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (conversation_id) DO UPDATE
            SET cms_evaluation_input = EXCLUDED.cms_evaluation_input,
                cms_raw_response = EXCLUDED.cms_raw_response,
                assistant_output = EXCLUDED.assistant_output,
                user_violates_rules = EXCLUDED.user_violates_rules,
                assistant_violates_rules = EXCLUDED.assistant_violates_rules,
                model_name = EXCLUDED.model_name,
                reasoning_effort = EXCLUDED.reasoning_effort,
                contributor = EXCLUDED.contributor,
                prompt_tokens = EXCLUDED.prompt_tokens,
                completion_tokens = EXCLUDED.completion_tokens,
                total_tokens = EXCLUDED.total_tokens,
                input_cost = EXCLUDED.input_cost,
                output_cost = EXCLUDED.output_cost,
                total_cost = EXCLUDED.total_cost,
                latency_ms = EXCLUDED.latency_ms
        """,
        (
            conversation_id,
            (f"""<input>
                <![CDATA[
                    {{
                        "id": "{conversation_id}",
                        "messages": {json.dumps(cms_evaluation_input, indent=2) if cms_evaluation_input else "[]"}
                    }}
                ]]>
            </input>""") if cms_evaluation_input else None,
            json.dumps(cms_raw_response) if cms_raw_response else None,
            assistant_output,
            1 if user_violates_rules else 0,
            1 if assistant_violates_rules else 0,
            model_name,
            reasoning_effort,
            contributor,
            prompt_tokens,
            completion_tokens,
            total_tokens,
            input_cost,
            output_cost,
            total_cost,
            latency_ms
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
               model_name, reasoning_effort, contributor, created_at,
               prompt_tokens, completion_tokens, total_tokens,
               input_cost, output_cost, total_cost, latency_ms
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
            "contributor": result[8],
            "created_at": result[9].isoformat() if result[9] else None,
            "prompt_tokens": result[10],
            "completion_tokens": result[11],
            "total_tokens": result[12],
            "input_cost": float(result[13]) if result[13] else None,
            "output_cost": float(result[14]) if result[14] else None,
            "total_cost": float(result[15]) if result[15] else None,
            "latency_ms": result[16]
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

def get_dataset_stats():
    """
    Get statistics about the dataset including total sets, contributors,
    and violations handled for both user and assistant.
    """
    conn = get_connection()
    cur = conn.cursor()
    
    # Get total conversations
    cur.execute("SELECT COUNT(*) FROM conversations")
    total_sets = cur.fetchone()[0]
    
    # Get unique contributors
    cur.execute("SELECT COUNT(DISTINCT contributor) FROM conversations WHERE contributor IS NOT NULL AND contributor != ''")
    total_contributors = cur.fetchone()[0]
    
    # Get total violations and usage statistics
    cur.execute("""
        SELECT
            SUM(CASE WHEN user_violates_rules = 1 THEN 1 ELSE 0 END) as user_violations,
            SUM(CASE WHEN assistant_violates_rules = 1 THEN 1 ELSE 0 END) as assistant_violations,
            SUM(prompt_tokens) as total_prompt_tokens,
            SUM(completion_tokens) as total_completion_tokens,
            SUM(total_tokens) as total_all_tokens,
            SUM(input_cost) as total_input_cost,
            SUM(output_cost) as total_output_cost,
            SUM(total_cost) as total_all_cost,
            AVG(latency_ms) as avg_latency
        FROM conversations
    """)
    stats = cur.fetchone()
    user_violations = stats[0] or 0
    assistant_violations = stats[1] or 0
    total_prompt_tokens = stats[2] or 0
    total_completion_tokens = stats[3] or 0
    total_all_tokens = stats[4] or 0
    total_input_cost = float(stats[5] or 0)
    total_output_cost = float(stats[6] or 0)
    total_all_cost = float(stats[7] or 0)
    avg_latency = int(stats[8] or 0)
    
    conn.close()
    
    return {
        "total_sets": total_sets,
        "total_contributors": total_contributors,
        "user_violations": user_violations,
        "assistant_violations": assistant_violations,
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "total_tokens": total_all_tokens,
        "total_input_cost": total_input_cost,
        "total_output_cost": total_output_cost,
        "total_cost": total_all_cost,
        "avg_latency_ms": avg_latency
    }

