import streamlit as st
import pandas as pd
from components.chat.session_management import get_supabase_client
from components.init_session_state import init_session_state
from components.banner import show_alpha_banner
from datetime import datetime
import pytz

st.set_page_config(page_title="Leaderboard", page_icon="🏆")

# Show alpha banner
show_alpha_banner()

@st.cache_data(ttl=300)
def get_top_contributors():
    """
    Get contributors with the most interactions from the database.
    
    Returns:
        list: A list of dictionaries containing contributor information and interaction counts.
    """
    supabase = get_supabase_client()
    try:
        # Get all interactions
        interactions = supabase.table("interactions").select("*").execute().data
        
        # Count interactions per contributor
        contributor_counts = {}
        for interaction in interactions:
            contributor_id = interaction.get("contributor_id")
            if contributor_id:
                if contributor_id not in contributor_counts:
                    contributor_counts[contributor_id] = {"count": 0, "contributor_id": contributor_id}
                contributor_counts[contributor_id]["count"] += 1
        
        # Sort by count (descending) and take top 10
        top_contributors = sorted(contributor_counts.values(), key=lambda x: x["count"], reverse=True)[:10]
        
        # Fetch contributor info for each top contributor
        for contributor in top_contributors:
            profile = supabase.table("contributors").select("*").eq("contributor_id", contributor["contributor_id"]).execute()
            if profile.data:
                contributor_info = profile.data[0]
                contributor["name"] = contributor_info.get("name") or "Anonymous"
                contributor["x"] = contributor_info.get("x") or ""
                contributor["discord"] = contributor_info.get("discord") or ""
                contributor["linkedin"] = contributor_info.get("linkedin") or ""
            contributor["contribution_count"] = contributor.pop("count")  # Rename for clarity
        
        return top_contributors
    except Exception as e:
        st.error(f"Error fetching top contributors: {e}")
        return []

@st.cache_data(ttl=300)
def get_top_agent_refusals():
    """
    Get contributors with the most agent refusals.
    
    Returns:
        list: A list of dictionaries containing contributor information and refusal counts.
    """
    supabase = get_supabase_client()
    try:
        # Get all interactions with action='RefuseAssistant'
        interactions = supabase.table("interactions").select("*").eq("action", "RefuseAssistant").execute().data
        
        # Count interactions per contributor
        contributor_counts = {}
        for interaction in interactions:
            contributor_id = interaction.get("contributor_id")
            if contributor_id:
                if contributor_id not in contributor_counts:
                    contributor_counts[contributor_id] = {"count": 0, "contributor_id": contributor_id}
                contributor_counts[contributor_id]["count"] += 1
        
        # Sort by count (descending) and take top 10
        top_contributors = sorted(contributor_counts.values(), key=lambda x: x["count"], reverse=True)[:10]
        
        # Fetch contributor info for each top contributor
        for contributor in top_contributors:
            profile = supabase.table("contributors").select("*").eq("contributor_id", contributor["contributor_id"]).execute()
            if profile.data:
                contributor_info = profile.data[0]
                contributor["name"] = contributor_info.get("name") or "Anonymous"
                contributor["x"] = contributor_info.get("x") or ""
                contributor["discord"] = contributor_info.get("discord") or ""
                contributor["linkedin"] = contributor_info.get("linkedin") or ""
            contributor["refusal_count"] = contributor.pop("count")  # Rename for clarity
        
        return top_contributors
    except Exception as e:
        st.error(f"Error fetching top agent refusals: {e}")
        return []

@st.cache_data(ttl=300)
def get_pending_verifications():
    """
    Get contributors with pending verifications sorted by created_at.
    
    Returns:
        list: A list of dictionaries containing contributor information and pending review counts.
    """
    supabase = get_supabase_client()
    try:
        # Get all interactions with submitted_for_review=True and verifier='pending'
        interactions = supabase.table("interactions").select("*").eq("submitted_for_review", True).eq("verifier", "pending").order("created_at", desc=True).execute().data
        
        # Group by contributor_id and track the most recent created_at
        contributor_info = {}
        for interaction in interactions:
            contributor_id = interaction.get("contributor_id")
            if contributor_id:
                if contributor_id not in contributor_info:
                    contributor_info[contributor_id] = {
                        "contributor_id": contributor_id,
                        "latest_verification": interaction.get("created_at"),
                        "pending_count": 0
                    }
                contributor_info[contributor_id]["pending_count"] += 1
        
        # Convert to list and sort by latest_verification
        contributors = list(contributor_info.values())
        contributors.sort(key=lambda x: x["latest_verification"], reverse=True)
        
        # Fetch contributor info for each contributor
        for contributor in contributors:
            profile = supabase.table("contributors").select("*").eq("contributor_id", contributor["contributor_id"]).execute()
            if profile.data:
                contributor_info = profile.data[0]
                contributor["name"] = contributor_info.get("name") or "Anonymous"
                contributor["x"] = contributor_info.get("x") or ""
                contributor["discord"] = contributor_info.get("discord") or ""
                contributor["linkedin"] = contributor_info.get("linkedin") or ""
            
            # Format the timestamp to be more readable and convert to EST
            if contributor["latest_verification"]:
                try:
                    # Parse the ISO format timestamp
                    dt = datetime.fromisoformat(contributor["latest_verification"].replace("Z", "+00:00"))
                    
                    # Convert from UTC to EST
                    est_timezone = pytz.timezone('US/Eastern')
                    dt = dt.replace(tzinfo=pytz.UTC).astimezone(est_timezone)
                    
                    # Format with timezone indicator
                    contributor["latest_verification"] = dt.strftime("%Y-%m-%d %H:%M:%S %Z")
                except (ValueError, AttributeError):
                    pass  # Keep original format if parsing fails
        
        return contributors
    except Exception as e:
        st.error(f"Error fetching pending verifications: {e}")
        return []

@st.cache_data(ttl=300)
def get_top_schema_violations():
    """
    Get contributors with the most schema violations.
    
    Returns:
        list: A list of dictionaries containing contributor information and schema violation counts.
    """
    supabase = get_supabase_client()
    try:
        # Get all interactions with schema_violation=True
        interactions = supabase.table("interactions").select("*").eq("schema_violation", True).execute().data
        
        # Count interactions per contributor
        contributor_counts = {}
        for interaction in interactions:
            contributor_id = interaction.get("contributor_id")
            if contributor_id:
                if contributor_id not in contributor_counts:
                    contributor_counts[contributor_id] = {"count": 0, "contributor_id": contributor_id}
                contributor_counts[contributor_id]["count"] += 1
        
        # Sort by count (descending) and take top 10
        top_contributors = sorted(contributor_counts.values(), key=lambda x: x["count"], reverse=True)[:10]
        
        # Fetch contributor info for each top contributor
        for contributor in top_contributors:
            profile = supabase.table("contributors").select("*").eq("contributor_id", contributor["contributor_id"]).execute()
            if profile.data:
                contributor_info = profile.data[0]
                contributor["name"] = contributor_info.get("name") or "Anonymous"
                contributor["x"] = contributor_info.get("x") or ""
                contributor["discord"] = contributor_info.get("discord") or ""
                contributor["linkedin"] = contributor_info.get("linkedin") or ""
            contributor["violation_count"] = contributor.pop("count")  # Rename for clarity
        
        return top_contributors
    except Exception as e:
        st.error(f"Error fetching schema violations: {e}")
        return []

def display_leaderboard():
    """
    Display the leaderboard with four sections:
    - Most Contributions
    - Most Agent Refusals
    - Pending Verifications
    - Most Schema Violations
    """
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Most Contributions", 
        "🛑 Most Agent Refusals", 
        "⏳ Pending Verifications",
        "❌ Most Schema Violations"
    ])
    
    with tab1:
        st.subheader("Top Contributors")
        top_contributors = get_top_contributors()
        if top_contributors:
            # Ensure all required columns exist
            for contributor in top_contributors:
                contributor.setdefault("name", "Anonymous")
                contributor.setdefault("contribution_count", 0)
                contributor.setdefault("x", "")
                contributor.setdefault("discord", "")
                contributor.setdefault("linkedin", "")
            
            contributor_df = pd.DataFrame(top_contributors)
            contributor_df = contributor_df[["name", "contribution_count", "x", "discord", "linkedin"]]
            contributor_df.columns = ["Contributor", "Contributions", "X", "Discord", "LinkedIn"]
            st.table(contributor_df)
        else:
            st.info("No contribution data available.")
    
    with tab2:
        st.subheader("Top Agent Refusals")
        top_refusals = get_top_agent_refusals()
        if top_refusals:
            # Ensure all required columns exist
            for refusal in top_refusals:
                refusal.setdefault("name", "Anonymous")
                refusal.setdefault("refusal_count", 0)
                refusal.setdefault("x", "")
                refusal.setdefault("discord", "")
                refusal.setdefault("linkedin", "")
            
            refusal_df = pd.DataFrame(top_refusals)
            refusal_df = refusal_df[["name", "refusal_count", "x", "discord", "linkedin"]]
            refusal_df.columns = ["Contributor", "Refusals", "X", "Discord", "LinkedIn"]
            st.table(refusal_df)
        else:
            st.info("No agent refusal data available.")
    
    with tab3:
        st.subheader("Pending Verifications")
        pending_verifications = get_pending_verifications()
        if pending_verifications:
            # Ensure all required columns exist
            for review in pending_verifications:
                review.setdefault("name", "Anonymous")
                review.setdefault("pending_count", 0)
                review.setdefault("latest_verification", "")
                review.setdefault("x", "")
                review.setdefault("discord", "")
                review.setdefault("linkedin", "")
            
            verification_df = pd.DataFrame(pending_verifications)
            verification_df = verification_df[["name", "pending_count", "latest_verification", "x", "discord", "linkedin"]]
            verification_df.columns = ["Contributor", "Pending Count", "Latest Submission", "X", "Discord", "LinkedIn"]
            st.table(verification_df)
        else:
            st.info("No pending verifications available.")
    
    with tab4:
        st.subheader("Schema Violations")
        schema_violations = get_top_schema_violations()
        if schema_violations:
            # Ensure all required columns exist
            for violation in schema_violations:
                violation.setdefault("name", "Anonymous")
                violation.setdefault("violation_count", 0)
                violation.setdefault("x", "")
                violation.setdefault("discord", "")
                violation.setdefault("linkedin", "")
            
            violation_df = pd.DataFrame(schema_violations)
            violation_df = violation_df[["name", "violation_count", "x", "discord", "linkedin"]]
            violation_df.columns = ["Contributor", "Violations", "X", "Discord", "LinkedIn"]
            st.table(violation_df)
        else:
            st.info("No schema violation data available.")

def main():
    """Initialize session state and display the leaderboard."""
    # Initialize session state
    init_session_state()
    
    # Display the leaderboard
    display_leaderboard()

if __name__ == "__main__":
    main()