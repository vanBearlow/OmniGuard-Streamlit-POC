# WARNING: This is a PUBLIC database file that will be downloaded by users.
# DO NOT store any sensitive information, credentials, or secrets in this file.
# All sensitive data should be stored in secrets.toml or environment variables.

import os
import psycopg2
import json
import streamlit as st
from dotenv import load_dotenv
from datetime import datetime, timezone
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables for local development
load_dotenv()

def get_connection_with_retry(max_retries=3, retry_delay=1):
    """Get database connection with retry logic"""
    last_error = None
    for attempt in range(max_retries):
        try:
            # Try to get credentials from Streamlit secrets first
            try:
                host = st.secrets["postgres"]["host"]
                port = st.secrets["postgres"]["port"]
                user = st.secrets["postgres"]["user"]
                password = st.secrets["postgres"]["password"]
                database = st.secrets["postgres"]["database"]
                logger.info(f"Using database credentials from secrets (attempt {attempt + 1})")
            except (KeyError, AttributeError):
                # Fall back to environment variables for local development
                host = os.getenv("RDS_HOST")
                port = int(os.getenv("RDS_PORT", "5432"))
                user = os.getenv("RDS_USER")
                password = os.getenv("RDS_PASSWORD")
                database = os.getenv("RDS_DATABASE")
                logger.info(f"Using database credentials from environment (attempt {attempt + 1})")

            conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                sslmode="prefer",
                connect_timeout=10
            )
            logger.info("Database connection successful")
            return conn
        except Exception as e:
            last_error = e
            logger.warning(f"Database connection attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            
    logger.error(f"All database connection attempts failed: {str(last_error)}")
    raise last_error

def get_connection():
    """
    Backwards compatible connection function that uses retry logic
    """
    return get_connection_with_retry()

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    
    # Create users table
    
    # Add performance indexes
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_conversations_contributor
        ON conversations(contributor);
    """)
    
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_conversations_verification
        ON conversations(needed_human_verification);
    """)
    
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_conversations_contributor_verification
        ON conversations(contributor, needed_human_verification);
    """)
    
    cur.execute(
        '''CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            picture TEXT,
            api_keys JSONB DEFAULT '{}',
            social_handles JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP WITH TIME ZONE,
            last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )'''
    )
    
    # Add last_updated column if it doesn't exist
    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'last_updated'
    """)
    if not cur.fetchone():
        cur.execute("""
            ALTER TABLE users
            ADD COLUMN last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        """)
    
    # Create conversations table with updated column names
    cur.execute(
        '''CREATE TABLE IF NOT EXISTS conversations (
            conversation_id TEXT PRIMARY KEY,
            omniguard_evaluation_input TEXT,
            omniguard_raw_response TEXT,
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
            latency_ms INTEGER,
            usage_data JSONB DEFAULT '{}',
            request_timings JSONB DEFAULT '{}'
        )'''
    )
    
    # Use PostgreSQL-compatible schema inspection
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'conversations';")
    columns = [row[0] for row in cur.fetchall()]
    
    # Handle column renames from cms_* to omniguard_*
    if "cms_evaluation_input" in columns and "omniguard_evaluation_input" not in columns:
        cur.execute("ALTER TABLE conversations ADD COLUMN omniguard_evaluation_input TEXT")
        cur.execute("UPDATE conversations SET omniguard_evaluation_input = cms_evaluation_input")
        cur.execute("ALTER TABLE conversations DROP COLUMN cms_evaluation_input")
    
    if "cms_raw_response" in columns and "omniguard_raw_response" not in columns:
        cur.execute("ALTER TABLE conversations ADD COLUMN omniguard_raw_response TEXT")
        cur.execute("UPDATE conversations SET omniguard_raw_response = cms_raw_response")
        cur.execute("ALTER TABLE conversations DROP COLUMN cms_raw_response")
    
    # Add any missing columns
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
    if "needed_human_verification" not in columns:
        cur.execute("ALTER TABLE conversations ADD COLUMN needed_human_verification BOOLEAN DEFAULT FALSE")
    
    conn.commit()
    conn.close()

@st.cache_data(ttl=1800)  # Cache for 30 minutes
def get_all_conversations(export_format="jsonl", page_size=1000, page=1):
    """
    Get all conversations with pagination support.
    
    Args:
        export_format: Format of the output ("jsonl" or "json")
        page_size: Number of records per page
        page: Page number (1-based)
    
    Returns:
        Tuple of (data, total_pages)
        - data: Formatted conversation data
        - total_pages: Total number of pages available
    
    Note:
        Results are cached for 30 minutes to improve performance
    """
    conn = get_connection()
    cur = conn.cursor()
    
    # Get total count for pagination
    cur.execute("SELECT COUNT(*) FROM conversations")
    total_records = cur.fetchone()[0]
    total_pages = (total_records + page_size - 1) // page_size
    
    # Get paginated data with updated column names
    cur.execute("""
        SELECT conversation_id, omniguard_evaluation_input, omniguard_raw_response,
               assistant_output, user_violates_rules, assistant_violates_rules,
               model_name, reasoning_effort, contributor, created_at,
               prompt_tokens, completion_tokens, total_tokens,
               input_cost, output_cost, total_cost, latency_ms,
               needed_human_verification
        FROM conversations
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
    """, (page_size, (page - 1) * page_size))
    rows = cur.fetchall()
    conn.close()
    if export_format == "jsonl":
        results = []
        for row in rows:
            results.append({
                "conversation_id": row[0],
                "omniguard_evaluation_input": {
                    "configuration": row[1].split("<configuration>")[1].split("</configuration>")[0] if row[1] and "<configuration>" in row[1] else "",
                    "conversation": row[1].split("<input>")[1].split("</input>")[0] if row[1] and "<input>" in row[1] else ""
                } if row[1] else None,
                "omniguard_raw_response": json.loads(row[2]) if row[2] else None,
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
                "latency_ms": row[16],
                "needed_human_verification": bool(row[17]) if row[17] is not None else False
            })
        data = "\n".join(json.dumps(conv) for conv in results)
    else:
        data = json.dumps(results)
    
    return {
        "data": data,
        "total_pages": total_pages,
        "current_page": page,
        "page_size": page_size,
        "total_records": total_records
    }

def save_conversation(conversation_id, user_violates_rules=False,
                     assistant_violates_rules=False, contributor="", omniguard_evaluation_input=None,
                     omniguard_raw_response=None, assistant_output=None, model_name=None,
                     reasoning_effort=None, prompt_tokens=None, completion_tokens=None,
                     total_tokens=None, input_cost=None, output_cost=None, total_cost=None,
                     latency_ms=None, needed_human_verification=False, usage_data=None,
                     request_timings=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO conversations
            (conversation_id, omniguard_evaluation_input, omniguard_raw_response, assistant_output,
             user_violates_rules, assistant_violates_rules,
             model_name, reasoning_effort, contributor,
             prompt_tokens, completion_tokens, total_tokens,
             input_cost, output_cost, total_cost, latency_ms,
             needed_human_verification, usage_data, request_timings)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (conversation_id) DO UPDATE
            SET omniguard_evaluation_input = EXCLUDED.omniguard_evaluation_input,
                omniguard_raw_response = EXCLUDED.omniguard_raw_response,
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
                latency_ms = EXCLUDED.latency_ms,
                needed_human_verification = EXCLUDED.needed_human_verification,
                usage_data = EXCLUDED.usage_data,
                request_timings = EXCLUDED.request_timings
        """,
        (
            conversation_id,
            # Format omniguard_evaluation_input with both configuration and input tags
            (lambda x: (
                x if isinstance(x, str) else
                f"""<configuration>{st.session_state.omniguard_configuration}</configuration>
                <input><![CDATA[
                    {{
                        "id": "{conversation_id}",
                        "messages": {json.dumps(x, indent=2) if x else "[]"}
                    }}
                ]]>
                </input>"""
            ))(omniguard_evaluation_input) if omniguard_evaluation_input else None,
            json.dumps(omniguard_raw_response) if omniguard_raw_response else None,
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
            latency_ms,
            needed_human_verification,
            json.dumps(usage_data) if usage_data else '{}',
            json.dumps(request_timings) if request_timings else '{}'
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
        SELECT conversation_id, omniguard_evaluation_input, omniguard_raw_response,
               assistant_output, user_violates_rules, assistant_violates_rules,
               model_name, reasoning_effort, contributor, created_at,
               prompt_tokens, completion_tokens, total_tokens,
               input_cost, output_cost, total_cost, latency_ms,
               needed_human_verification
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
            "omniguard_evaluation_input": {
                "configuration": result[1].split("<configuration>")[1].split("</configuration>")[0] if result[1] and "<configuration>" in result[1] else "",
                "conversation": result[1].split("<input>")[1].split("</input>")[0] if result[1] and "<input>" in result[1] else ""
            } if result[1] else None,
            "omniguard_raw_response": json.loads(result[2]) if result[2] else None,
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
            "latency_ms": result[16],
            "needed_human_verification": bool(result[17]) if result[17] is not None else False
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

@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_leaderboard_stats():
    """
    Get leaderboard statistics for contributors, showing their effectiveness in identifying harmful prompts
    and assistant rejections.
    
    Returns:
        List of dictionaries containing contributor stats
        
    Note:
        Results are cached for 10 minutes to improve performance
    """
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        WITH contributor_stats AS (
            SELECT
                contributor,
                COUNT(*) as total_contributions,
                -- Human verified harmful prompts (primary metric)
                SUM(CASE
                    WHEN needed_human_verification = TRUE
                    AND user_violates_rules = 1
                    THEN 1 ELSE 0
                END) as verified_harmful_prompts,
                -- Assistant rejections
                SUM(CASE
                    WHEN user_violates_rules = 0
                    AND assistant_violates_rules = 1
                    AND needed_human_verification = TRUE
                    THEN 1 ELSE 0
                END) as assistant_rejections
            FROM conversations
            WHERE contributor IS NOT NULL
            AND contributor != ''
            GROUP BY contributor
        )
        SELECT
            contributor,
            total_contributions,
            verified_harmful_prompts,
            assistant_rejections,
            ROUND(CAST(verified_harmful_prompts AS NUMERIC) /
                NULLIF(total_contributions, 0) * 100, 2) as success_rate
        FROM contributor_stats
        ORDER BY verified_harmful_prompts DESC, assistant_rejections DESC
    """)
    
    results = []
    for row in cur.fetchall():
        results.append({
            "contributor": row[0],
            "total_contributions": row[1],
            "verified_harmful_prompts": row[2],
            "assistant_rejections": row[3],
            "success_rate": float(row[4]) if row[4] is not None else 0.0
        })
    
    conn.close()
    return results

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_dataset_stats():
    """
    Get statistics about the dataset including total sets, contributors,
    and violations handled for both user and assistant.
    
    Returns:
        Dictionary containing dataset statistics
        
    Note:
        Results are cached for 5 minutes to improve performance
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
            -- Auto-detected violations (not human verified)
            SUM(CASE WHEN user_violates_rules = 1 AND needed_human_verification = FALSE THEN 1 ELSE 0 END) as auto_user_violations,
            SUM(CASE WHEN assistant_violates_rules = 1 AND needed_human_verification = FALSE THEN 1 ELSE 0 END) as auto_assistant_violations,
            -- Human-verified violations
            SUM(CASE WHEN user_violates_rules = 1 AND needed_human_verification = TRUE THEN 1 ELSE 0 END) as human_verified_user_violations,
            SUM(CASE WHEN assistant_violates_rules = 1 AND needed_human_verification = TRUE THEN 1 ELSE 0 END) as human_verified_assistant_violations,
            -- Usage statistics
            SUM(prompt_tokens) as total_prompt_tokens,
            SUM(completion_tokens) as total_completion_tokens,
            SUM(total_tokens) as total_all_tokens,
            SUM(input_cost) as total_input_cost,
            SUM(output_cost) as total_output_cost,
            SUM(total_cost) as total_all_cost,
            AVG(latency_ms) as avg_latency,
            -- Verification status
            SUM(CASE WHEN needed_human_verification = TRUE THEN 1 ELSE 0 END) as needed_human_verification_count
        FROM conversations
    """)
    stats = cur.fetchone()
    auto_user_violations = stats[0] or 0
    auto_assistant_violations = stats[1] or 0
    human_verified_user_violations = stats[2] or 0
    human_verified_assistant_violations = stats[3] or 0
    total_prompt_tokens = stats[4] or 0
    total_completion_tokens = stats[5] or 0
    total_all_tokens = stats[6] or 0
    total_input_cost = float(stats[7] or 0)
    total_output_cost = float(stats[8] or 0)
    total_all_cost = float(stats[9] or 0)
    avg_latency = int(stats[10] or 0)
    needed_verification_count = int(stats[11] or 0)
    
    conn.close()
    
    return {
        "total_sets": total_sets,
        "total_contributors": total_contributors,
        # Auto-detected violations
        "user_violations": auto_user_violations,
        "assistant_violations": auto_assistant_violations,
        # Human-verified violations
        "human_verified_user_violations": human_verified_user_violations,
        "human_verified_assistant_violations": human_verified_assistant_violations,
        # Total violations (auto + human-verified)
        "total_user_violations": auto_user_violations + human_verified_user_violations,
        "total_assistant_violations": auto_assistant_violations + human_verified_assistant_violations,
        # Usage statistics
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "total_tokens": total_all_tokens,
        "total_input_cost": total_input_cost,
        "total_output_cost": total_output_cost,
        "total_cost": total_all_cost,
        "avg_latency_ms": avg_latency,
        # Verification status
        "needed_human_verification": needed_verification_count
    }
