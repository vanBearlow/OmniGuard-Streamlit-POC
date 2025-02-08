#!/usr/bin/env python3
"""
Scheduled task to check for completed bounties and award winners.
This script should be run daily via cron/scheduler.

Example cron entry (run daily at midnight):
0 0 * * * /path/to/python /path/to/complete_bounties.py
"""

import os
import sys
import logging
from datetime import datetime, timezone
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from database import get_connection, complete_bounty

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / 'logs' / 'complete_bounties.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_completed_bounties():
    """Get bounties that have ended but haven't been awarded yet."""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute('''
        SELECT 
            bounty_id,
            title,
            metric,
            start_date,
            end_date
        FROM bounties
        WHERE status = 'active'
        AND end_date <= CURRENT_TIMESTAMP
    ''')
    
    bounties = cur.fetchall()
    conn.close()
    return bounties

def get_winner_for_bounty(bounty_id, metric, start_date, end_date):
    """Determine the winner for a completed bounty."""
    conn = get_connection()
    cur = conn.cursor()
    
    if metric == 'user_violations':
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
            LIMIT 1
        ''', (start_date, end_date))
    elif metric == 'assistant_violations':
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
            LIMIT 1
        ''', (start_date, end_date))
    elif metric == 'verification_accuracy':
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
            LIMIT 1
        ''', (start_date, end_date))
    
    winner = cur.fetchone()
    conn.close()
    
    if winner:
        # Get user_id from contributor name
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT user_id 
            FROM users 
            WHERE name = %s
        ''', (winner[0],))
        user = cur.fetchone()
        conn.close()
        
        if user:
            return user[0]
    
    return None

def main():
    """Main function to process completed bounties."""
    logger.info("Starting bounty completion check")
    
    try:
        completed_bounties = get_completed_bounties()
        
        for bounty in completed_bounties:
            bounty_id, title, metric, start_date, end_date = bounty
            logger.info(f"Processing completed bounty: {title}")
            
            winner_id = get_winner_for_bounty(bounty_id, metric, start_date, end_date)
            
            if winner_id:
                logger.info(f"Winner found for bounty {title}: {winner_id}")
                complete_bounty(bounty_id, winner_id)
                # TODO: Implement notification system
                logger.info(f"Bounty {title} marked as completed")
            else:
                logger.warning(f"No winner found for bounty {title}")
        
        logger.info("Bounty completion check finished")
        
    except Exception as e:
        logger.error(f"Error processing bounties: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()