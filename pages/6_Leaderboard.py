import streamlit as st
import plotly.express as px
import pandas as pd
from database import get_leaderboard_stats

st.set_page_config(page_title="Leaderboard", page_icon="🏆")

# Title and description
st.title("🏆 Contributor Leaderboard")
st.markdown("""
This leaderboard ranks contributors based on the number of human-verified harmful prompts they've identified.
""")

# Get leaderboard data
stats = get_leaderboard_stats()

if not stats:
    st.info("No leaderboard data available yet.")
else:
    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(stats)
    
    # Create two columns for metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Total Contributors",
            len(df),
            help="Number of unique contributors in the selected time period"
        )
    
    with col2:
        st.metric(
            "Total Verified Harmful Prompts",
            df["verified_harmful_prompts"].sum(),
            help="Total number of prompts verified as harmful by human reviewers"
        )
    
    # Visualization - Top Contributors Bar Chart
    top_n = min(10, len(df))  # Show top 10 or all if less than 10
    top_contributors = df.nlargest(top_n, "verified_harmful_prompts")
    
    fig = px.bar(
        top_contributors,
        x="contributor",
        y=["verified_harmful_prompts", "assistant_rejections"],
        title=f"Top {top_n} Contributors by Verified Harmful Prompts",
        labels={
            "contributor": "Contributor",
            "value": "Count",
            "variable": "Metric"
        },
        barmode="group"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Main leaderboard table
    st.subheader("Detailed Leaderboard")
    
    # Add rank column
    df = df.reset_index(drop=True)
    df.index = df.index + 1
    df = df.rename_axis("Rank")
    
    # Format success rate
    df["success_rate"] = df["success_rate"].map("{:.1f}%".format)
    
    # Rename columns for display
    df = df.rename(columns={
        "contributor": "Contributor",
        "verified_harmful_prompts": "Verified Harmful Prompts",
        "assistant_rejections": "Assistant Rejections",
        "total_contributions": "Total Contributions",
        "success_rate": "Success Rate"
    })
    
    st.dataframe(
        df,
        column_config={
            "Verified Harmful Prompts": st.column_config.NumberColumn(
                help="Number of prompts verified as harmful by human reviewers"
            ),
            "Assistant Rejections": st.column_config.NumberColumn(
                help="Number of prompts where the assistant output was flagged as harmful"
            ),
            "Success Rate": st.column_config.TextColumn(
                help="Percentage of contributions that were verified as harmful"
            )
        },
        hide_index=False
    )
    
    # Add explanation of metrics
    with st.expander("📊 Understanding the Metrics"):
        st.markdown("""
        ### Metric Definitions
        
        - **Verified Harmful Prompts**: Number of prompts that were verified as harmful through human review. This is our primary metric for ranking contributors.
        
        - **Assistant Rejections**: Cases where the prompt wasn't flagged as harmful by automated checks, but the assistant's output was flagged as harmful.
        
        - **Success Rate**: Percentage of a contributor's total submissions that were verified as harmful prompts.
        
        The leaderboard ranks contributors primarily by the number of verified harmful prompts they've identified, with assistant rejections as a secondary metric.
        """)