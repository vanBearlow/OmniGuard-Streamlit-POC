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
from functools import wraps
from time import perf_counter

# Configure logging
def monitor_query(query_name):
    """
    Decorator to monitor query performance.

    Args:
        query_name (str): Identifier for the query being monitored.

    Returns:
        function: A decorator function that wraps the original function to log and monitor query performance.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = perf_counter()
            try:
                result = func(*args, **kwargs)
                duration = (perf_counter() - start_time) * 1000  # Convert to milliseconds
                
                # Log query stats
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("SELECT log_query_stats(%s, %s)", (query_name, duration))
                conn.commit()
                conn.close()
                
                # Log slow queries (over 1000ms)
                if duration > 1000:
                    logger.warning(f"Slow query detected - {query_name}: {duration:.2f}ms")
                
                return result
            except Exception as e:
                logger.error(f"Query failed - {query_name}: {str(e)}")
                raise
        return wrapper
    return decorator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables for local development
load_dotenv()

def get_connection_with_retry(max_retries=3, retry_delay=1):
    """
    Establish a PostgreSQL database connection using retry logic.

    Args:
        max_retries (int): Maximum number of retry attempts (default is 3).
        retry_delay (int): Delay in seconds between retry attempts (default is 1).

    Returns:
        connection: A psycopg2 connection object.

    Raises:
        Exception: If connection fails after the specified number of retries.
    """
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
    Retrieve a PostgreSQL database connection using retry logic.

    Returns:
        connection: A psycopg2 connection object obtained via get_connection_with_retry.
    """
    return get_connection_with_retry()

def init_db():
    conn = get_connection()
    conn.autocommit = True
    cur = conn.cursor()
    
    # Create materialized view for leaderboard stats
    cur.execute('''
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_leaderboard_stats AS
        WITH contributor_stats AS (
            SELECT
                contributor,
                COUNT(*) as total_contributions,
                SUM(CASE
                    WHEN needed_human_verification = TRUE
                    AND user_violates_rules = 1
                    THEN 1 ELSE 0
                END) as verified_harmful_prompts,
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
    ''')
    
    # Create function to refresh materialized view
    cur.execute('''
        CREATE OR REPLACE FUNCTION refresh_mv_leaderboard_stats()
        RETURNS void AS $$
        BEGIN
            REFRESH MATERIALIZED VIEW mv_leaderboard_stats;
        END;
        $$ LANGUAGE plpgsql;
    ''')
    
    # Schedule refresh (requires pg_cron extension)
    cur.execute("SELECT extname FROM pg_extension WHERE extname = 'pg_cron';")
    if cur.fetchone() is not None:
        try:
            cur.execute('''
                SELECT cron.schedule('0 * * * *', $$
                    SELECT refresh_mv_leaderboard_stats();
                $$);
            ''')
            logger.info("Materialized view refresh schedule set successfully.")
        except Exception as e:
            logger.warning(f"Error scheduling materialized view refresh: {str(e)}")
    else:
        logger.info("pg_cron extension not found. Manual refresh of mv_leaderboard_stats will be required.")
    
    # Create query_stats table for monitoring
    cur.execute('''
        CREATE TABLE IF NOT EXISTS query_stats (
            query_name TEXT PRIMARY KEY,
            avg_duration NUMERIC,
            max_duration NUMERIC,
            call_count INTEGER,
            last_slow_query TIMESTAMP WITH TIME ZONE,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create function to log query performance
    cur.execute('''
        CREATE OR REPLACE FUNCTION log_query_stats(
            p_query_name TEXT,
            p_duration NUMERIC
        ) RETURNS void AS $$
        BEGIN
            INSERT INTO query_stats (query_name, avg_duration, max_duration, call_count)
            VALUES (p_query_name, p_duration, p_duration, 1)
            ON CONFLICT (query_name) DO UPDATE
            SET avg_duration = (query_stats.avg_duration * query_stats.call_count + p_duration) / (query_stats.call_count + 1),
                max_duration = GREATEST(query_stats.max_duration, p_duration),
                call_count = query_stats.call_count + 1,
                last_slow_query = CASE
                    WHEN p_duration > query_stats.max_duration THEN CURRENT_TIMESTAMP
                    ELSE query_stats.last_slow_query
                END,
                updated_at = CURRENT_TIMESTAMP;
        END;
        $$ LANGUAGE plpgsql;
    ''')
    
    # Create bounties table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS bounties (
            bounty_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            metric TEXT NOT NULL,
            start_date TIMESTAMP WITH TIME ZONE NOT NULL,
            end_date TIMESTAMP WITH TIME ZONE NOT NULL,
            prize_pool_amount NUMERIC(10,2) DEFAULT 0.00,
            status TEXT DEFAULT 'active',
            winner_id TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (winner_id) REFERENCES users(user_id)
        )
    ''')
    
    # Create donations table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS donations (
            donation_id TEXT PRIMARY KEY,
            user_id TEXT,  -- Nullable for anonymous donations
            display_name TEXT,  -- Can be NULL for anonymous or custom display name
            amount NUMERIC(10,2) NOT NULL,
            use_for TEXT NOT NULL,  -- 'bounty', 'api_costs', etc.
            bounty_id TEXT,  -- NULL if not for a specific bounty
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (bounty_id) REFERENCES bounties(bounty_id)
        )
    ''')
    
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
    
    # Add new optimized indexes for common queries
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_conversations_contributor_metrics
        ON conversations(contributor, needed_human_verification, user_violates_rules, assistant_violates_rules);
    """)
    
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_conversations_verification_metrics
        ON conversations(needed_human_verification, user_violates_rules, assistant_violates_rules);
    """)
    
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_conversations_created_at
        ON conversations(created_at DESC);
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
            request_timings JSONB DEFAULT '{}'
        )'''
    )
    
    # Add usage_data column if it doesn't exist
    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'conversations' AND column_name = 'usage_data'
    """)
    if not cur.fetchone():
        cur.execute("""
            ALTER TABLE conversations
            ADD COLUMN usage_data JSONB DEFAULT '{}'
        """)
    
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
    
    # Add usage_data column if it doesn't exist
    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'conversations' AND column_name = 'usage_data'
    """)
    if not cur.fetchone():
        cur.execute("""
            ALTER TABLE conversations
            ADD COLUMN usage_data JSONB DEFAULT '{}'
        """)
    
    # Add request_timings column if it doesn't exist
    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'conversations' AND column_name = 'request_timings'
    """)
    if not cur.fetchone():
        cur.execute("""
            ALTER TABLE conversations
            ADD COLUMN request_timings JSONB DEFAULT '{}'
        """)
    
    conn.commit()
    conn.close()

@st.cache_data(ttl=900)  # Cache for 15 minutes - reduced from 30 to balance freshness and performance
@monitor_query("get_all_conversations")
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
        Results are cached for 15 minutes to improve performance while ensuring reasonable data freshness
    """
    conn = get_connection()
    cur = conn.cursor()
    
    # Optimized query combining pagination data and total count
    cur.execute("""
        WITH conversation_data AS (
            SELECT conversation_id, omniguard_evaluation_input, omniguard_raw_response,
                   assistant_output, user_violates_rules, assistant_violates_rules,
                   model_name, reasoning_effort, contributor, created_at,
                   prompt_tokens, completion_tokens, total_tokens,
                   input_cost, output_cost, total_cost, latency_ms,
                   needed_human_verification
            FROM conversations
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        ),
        total_count AS (
            SELECT COUNT(*) as total
            FROM conversations
        )
        SELECT cd.*, tc.total
        FROM conversation_data cd
        CROSS JOIN total_count tc
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
    
    # Get total count from the last column of our result
    total_records = rows[0][-1] if rows else 0
    total_pages = (total_records + page_size - 1) // page_size
    
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

@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes with time period granularity
@monitor_query("get_leaderboard_stats")
def get_leaderboard_stats(time_period="all"):
    """
    Get leaderboard statistics for contributors with optional time period filtering.
    
    Args:
        time_period: Time period to filter results ("all", "month", "week", "day")
    
    Returns:
        List of dictionaries containing contributor stats
        
    Note:
        Results are cached for 5 minutes per time period
    """
    conn = get_connection()
    cur = conn.cursor()
    
    # If using "all", get data from materialized view
    if time_period == "all":
        cur.execute("""
            SELECT * FROM mv_leaderboard_stats
            ORDER BY verified_harmful_prompts DESC, assistant_rejections DESC
        """)
    else:
        # Calculate date range based on time period
        cur.execute("""
            WITH contributor_stats AS (
                SELECT
                    contributor,
                    COUNT(*) as total_contributions,
                    SUM(CASE
                        WHEN needed_human_verification = TRUE
                        AND user_violates_rules = 1
                        THEN 1 ELSE 0
                    END) as verified_harmful_prompts,
                    SUM(CASE
                        WHEN user_violates_rules = 0
                        AND assistant_violates_rules = 1
                        AND needed_human_verification = TRUE
                        THEN 1 ELSE 0
                    END) as assistant_rejections
                FROM conversations
                WHERE contributor IS NOT NULL
                AND contributor != ''
                AND created_at >= CASE %s
                    WHEN 'month' THEN CURRENT_TIMESTAMP - INTERVAL '1 month'
                    WHEN 'week' THEN CURRENT_TIMESTAMP - INTERVAL '1 week'
                    WHEN 'day' THEN CURRENT_TIMESTAMP - INTERVAL '1 day'
                    ELSE CURRENT_TIMESTAMP
                END
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
        """, (time_period,))
    
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

@st.cache_data(ttl=60)  # Cache for 1 minute - reduced from 5 minutes since this is used frequently in Chat page
@monitor_query("get_dataset_stats")
def get_dataset_stats(max_retries=3, retry_delay=1):
    """
    Get statistics about the dataset including total sets, contributors,
    and violations handled for both user and assistant.
    
    Returns:
        Dictionary containing dataset statistics
        
    Note:
        Results are cached for 5 minutes to improve performance
    """
    from components.service_fallbacks import with_database_fallback
    
    @with_database_fallback({
        "total_sets": 0,
        "total_contributors": 0,
        "user_violations": 0,
        "assistant_violations": 0,
        "human_verified_user_violations": 0,
        "human_verified_assistant_violations": 0,
        "total_user_violations": 0,
        "total_assistant_violations": 0,
        "total_prompt_tokens": 0,
        "total_completion_tokens": 0,
        "total_tokens": 0,
        "total_input_cost": 0.0,
        "total_output_cost": 0.0,
        "total_cost": 0.0,
        "avg_latency_ms": 0,
        "needed_human_verification": 0
    })
    def _get_stats():
        last_error = None
        for attempt in range(max_retries):
            try:
                conn = get_connection()
                cur = conn.cursor()
                
                # Combined query for all stats
                cur.execute("""
                    WITH stats AS (
                        SELECT
                            COUNT(*) as total_sets,
                            COUNT(DISTINCT CASE WHEN contributor IS NOT NULL AND contributor != '' THEN contributor END) as total_contributors,
                            SUM(CASE WHEN user_violates_rules = 1 AND needed_human_verification = FALSE THEN 1 ELSE 0 END) as auto_user_violations,
                            SUM(CASE WHEN assistant_violates_rules = 1 AND needed_human_verification = FALSE THEN 1 ELSE 0 END) as auto_assistant_violations,
                            SUM(CASE WHEN user_violates_rules = 1 AND needed_human_verification = TRUE THEN 1 ELSE 0 END) as human_verified_user_violations,
                            SUM(CASE WHEN assistant_violates_rules = 1 AND needed_human_verification = TRUE THEN 1 ELSE 0 END) as human_verified_assistant_violations,
                            SUM(prompt_tokens) as total_prompt_tokens,
                            SUM(completion_tokens) as total_completion_tokens,
                            SUM(total_tokens) as total_all_tokens,
                            SUM(input_cost) as total_input_cost,
                            SUM(output_cost) as total_output_cost,
                            SUM(total_cost) as total_all_cost,
                            AVG(latency_ms) as avg_latency,
                            SUM(CASE WHEN needed_human_verification = TRUE THEN 1 ELSE 0 END) as needed_verification_count
                        FROM conversations
                    )
                    SELECT * FROM stats
                """)
                
                stats = cur.fetchone()
                conn.close()
                
                if stats is None:
                    stats = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0, 0)
                    
                return {
                    "total_sets": stats[0] or 0,
                    "total_contributors": stats[1] or 0,
                    "user_violations": stats[2] or 0,
                    "assistant_violations": stats[3] or 0,
                    "human_verified_user_violations": stats[4] or 0,
                    "human_verified_assistant_violations": stats[5] or 0,
                    "total_user_violations": (stats[2] or 0) + (stats[4] or 0),
                    "total_assistant_violations": (stats[3] or 0) + (stats[5] or 0),
                    "total_prompt_tokens": stats[6] or 0,
                    "total_completion_tokens": stats[7] or 0,
                    "total_tokens": stats[8] or 0,
                    "total_input_cost": float(stats[9] or 0),
                    "total_output_cost": float(stats[10] or 0),
                    "total_cost": float(stats[11] or 0),
                    "avg_latency_ms": int(stats[12] or 0),
                    "needed_human_verification": int(stats[13] or 0)
                }
            except Exception as e:
                last_error = e
                logger.warning(f"Database connection attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                break
        
        logger.error(f"All database connection attempts failed: {str(last_error)}")
        return None
        
        # Combined query for all stats
        cur.execute("""
            WITH stats AS (
                SELECT
                    COUNT(*) as total_sets,
                    COUNT(DISTINCT CASE WHEN contributor IS NOT NULL AND contributor != '' THEN contributor END) as total_contributors,
                    SUM(CASE WHEN user_violates_rules = 1 AND needed_human_verification = FALSE THEN 1 ELSE 0 END) as auto_user_violations,
                    SUM(CASE WHEN assistant_violates_rules = 1 AND needed_human_verification = FALSE THEN 1 ELSE 0 END) as auto_assistant_violations,
                    SUM(CASE WHEN user_violates_rules = 1 AND needed_human_verification = TRUE THEN 1 ELSE 0 END) as human_verified_user_violations,
                    SUM(CASE WHEN assistant_violates_rules = 1 AND needed_human_verification = TRUE THEN 1 ELSE 0 END) as human_verified_assistant_violations,
                    SUM(prompt_tokens) as total_prompt_tokens,
                    SUM(completion_tokens) as total_completion_tokens,
                    SUM(total_tokens) as total_all_tokens,
                    SUM(input_cost) as total_input_cost,
                    SUM(output_cost) as total_output_cost,
                    SUM(total_cost) as total_all_cost,
                    AVG(latency_ms) as avg_latency,
                    SUM(CASE WHEN needed_human_verification = TRUE THEN 1 ELSE 0 END) as needed_verification_count
                FROM conversations
            )
            SELECT * FROM stats
        """)
        
        stats = cur.fetchone()
        if stats is None:
            stats = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0, 0)
        total_sets = stats[0] or 0
        total_contributors = stats[1] or 0
        auto_user_violations = stats[2] or 0
        auto_assistant_violations = stats[3] or 0
        human_verified_user_violations = stats[4] or 0
        human_verified_assistant_violations = stats[5] or 0
        total_prompt_tokens = stats[6] or 0
        total_completion_tokens = stats[7] or 0
        total_all_tokens = stats[8] or 0
        total_input_cost = float(stats[9] or 0)
        total_output_cost = float(stats[10] or 0)
        total_all_cost = float(stats[11] or 0)
        avg_latency = int(stats[12] or 0)
        needed_verification_count = int(stats[13] or 0)
        
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

def create_bounty(title, description, metric, start_date, end_date):
    """
    Create a new bounty contest.
    
    Args:
        title: Title of the bounty
        description: Detailed description of the bounty
        metric: Metric to track (e.g., 'user_violations', 'assistant_violations')
        start_date: When the bounty contest starts
        end_date: When the bounty contest ends
    
    Returns:
        bounty_id: ID of the created bounty
    """
    bounty_id = f"bounty_{int(time.time())}"
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute('''
        INSERT INTO bounties (bounty_id, title, description, metric, start_date, end_date)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING bounty_id
    ''', (bounty_id, title, description, metric, start_date, end_date))
    
    conn.commit()
    conn.close()
    return bounty_id
def record_donation(amount, use_for, user_id=None, display_name=None, bounty_id=None):
    """
    Record a donation and update relevant prize pools.
    
    Args:
        amount: Donation amount
        use_for: Purpose of donation ('bounty', 'api_costs', etc.)
        user_id: Optional ID of the donor (None for anonymous)
        display_name: Optional display name for the donor (None for anonymous)
        bounty_id: Optional specific bounty to fund
    """
    donation_id = f"donation_{int(time.time())}"
    conn = get_connection()
    cur = conn.cursor()
    
    # Record the donation
    cur.execute('''
        INSERT INTO donations (donation_id, user_id, display_name, amount, use_for, bounty_id)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', (donation_id, user_id, display_name, amount, use_for, bounty_id))
    
    # If donation is for a specific bounty, update its prize pool
    if bounty_id and use_for == 'bounty':
        cur.execute('''
            UPDATE bounties
            SET prize_pool_amount = prize_pool_amount + %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE bounty_id = %s
        ''', (amount, bounty_id))
    
    conn.commit()
    conn.close()

@st.cache_data(ttl=3600)  # Cache for 1 hour - increased from 5 minutes since bounties change infrequently
def get_active_bounties():
    """
    Get all active bounties with their current standings.
    
    Returns:
        List of dictionaries containing bounty details and current leaders
    """
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute('''
        SELECT
            b.bounty_id,
            b.title,
            b.description,
            b.metric,
            b.start_date,
            b.end_date,
            b.prize_pool_amount,
            b.status,
            COALESCE(SUM(d.amount), 0) as total_donations
        FROM bounties b
        LEFT JOIN donations d ON b.bounty_id = d.bounty_id
        WHERE b.status = 'active'
        AND b.end_date > CURRENT_TIMESTAMP
        GROUP BY b.bounty_id, b.title, b.description, b.metric,
                 b.start_date, b.end_date, b.prize_pool_amount, b.status
        ORDER BY b.end_date ASC
    ''')
    
    bounties = []
    for row in cur.fetchall():
        bounty = {
            'bounty_id': row[0],
            'title': row[1],
            'description': row[2],
            'metric': row[3],
            'start_date': row[4].isoformat(),
            'end_date': row[5].isoformat(),
            'prize_pool_amount': float(row[6]),
            'status': row[7],
            'total_donations': float(row[8])
        }
        
        # Get current leaders based on the metric
        if bounty['metric'] == 'user_violations':
            cur.execute('''
                SELECT
                    contributor,
                    COUNT(*) as count
                FROM conversations
                WHERE user_violates_rules = 1
                AND needed_human_verification = TRUE
                AND created_at BETWEEN %s AND %s
                GROUP BY contributor
                ORDER BY count DESC
                LIMIT 3
            ''', (bounty['start_date'], bounty['end_date']))
        elif bounty['metric'] == 'assistant_violations':
            cur.execute('''
                SELECT
                    contributor,
                    COUNT(*) as count
                FROM conversations
                WHERE assistant_violates_rules = 1
                AND needed_human_verification = TRUE
                AND created_at BETWEEN %s AND %s
                GROUP BY contributor
                ORDER BY count DESC
                LIMIT 3
            ''', (bounty['start_date'], bounty['end_date']))
        elif bounty['metric'] == 'verification_accuracy':
            # Calculate verification accuracy based on alignment with final decisions
            cur.execute('''
                WITH verification_stats AS (
                    SELECT
                        v.contributor,
                        COUNT(*) as total_verifications,
                        SUM(CASE
                            WHEN (v.vote = TRUE AND c.user_violates_rules = 1) OR
                                 (v.vote = FALSE AND c.user_violates_rules = 0)
                            THEN 1
                            ELSE 0
                        END) as correct_verifications
                    FROM human_verifications v
                    JOIN conversations c ON v.conversation_id = c.conversation_id
                    WHERE v.created_at BETWEEN %s AND %s
                    GROUP BY v.contributor
                    HAVING COUNT(*) >= 10  -- Minimum verifications threshold
                )
                SELECT
                    contributor,
                    ROUND(CAST(correct_verifications AS NUMERIC) /
                          NULLIF(total_verifications, 0) * 100, 2) as accuracy
                FROM verification_stats
                ORDER BY accuracy DESC
                LIMIT 3
            ''', (bounty['start_date'], bounty['end_date']))
        
        leaders = []
        for leader_row in cur.fetchall():
            leaders.append({
                'contributor': leader_row[0],
                'count': leader_row[1]
            })
        
        bounty['current_leaders'] = leaders
        bounties.append(bounty)
    
    conn.close()
    return bounties

@st.cache_data(ttl=60)  # Cache for 1 minute
def get_top_donors():
    """
    Get the top donors ranked by total donation amount.
    
    Returns:
        List of tuples containing (display_name, total_amount)
        Anonymous donations are grouped together
    """
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT
            COALESCE(display_name, 'Anonymous') as donor,
            SUM(amount) as total_amount
        FROM donations
        GROUP BY COALESCE(display_name, 'Anonymous')
        ORDER BY total_amount DESC
        LIMIT 10
    """)
    
    results = cur.fetchall()
    conn.close()
    return results

def complete_bounty(bounty_id, winner_id):
    """
    Mark a bounty as completed and record the winner.
    
    Args:
        bounty_id: ID of the bounty to complete
        winner_id: ID of the winning user
    """
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute('''
        UPDATE bounties
        SET status = 'completed',
            winner_id = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE bounty_id = %s
    ''', (winner_id, bounty_id))
    
    conn.commit()
    conn.close()
