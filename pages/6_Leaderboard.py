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

# Donor Leaderboard Section
st.divider()
st.subheader("🎁 Top Donors")
st.markdown("""
This leaderboard recognizes the generous donors who support our mission. Thank you for your contributions!
""")

from database import get_top_donors

top_donors = get_top_donors()

if not top_donors:
    st.info("No donations recorded yet.")
else:
    # Create a DataFrame for the donors
    donor_df = pd.DataFrame(top_donors, columns=["Donor", "Total Amount"])
    donor_df["Total Amount"] = donor_df["Total Amount"].apply(lambda x: f"${x:,.2f}")
    
    # Display donor metrics
    total_donors = len(donor_df)
    total_amount = sum(float(amt.replace('$', '').replace(',', '')) for amt in donor_df["Total Amount"])
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            "Total Donors",
            total_donors,
            help="Number of unique donors (including anonymous)"
        )
    with col2:
        st.metric(
            "Total Donations",
            f"${total_amount:,.2f}",
            help="Total amount donated"
        )
    
    # Display the donor leaderboard
    st.dataframe(
        donor_df,
        column_config={
            "Donor": st.column_config.TextColumn(
                help="Donor name (or Anonymous)"
            ),
            "Total Amount": st.column_config.TextColumn(
                help="Total amount donated"
            )
        },
        hide_index=True
    )
    
    with st.expander("💝 About Donations"):
        st.markdown("""
        ### About the Donor Leaderboard
        
        - **Donor Name**: By default, your name will appear on the leaderboard. You can choose to remain anonymous when making a donation.
        - **Total Amount**: The cumulative amount of all donations made by each donor.
        
        ### How Donations Work
        
        Donations can be used for:
        - Contributing to bounty prize pools
        - Supporting API costs and infrastructure
        - Funding research initiatives
        
        ### Making a Donation
        
        To make a donation, visit the Donations page where you can:
        - Choose how your donation will be used
        - Set a custom display name or remain anonymous
        - Select a specific bounty to fund (optional)
        
        All donations are tracked transparently, and the leaderboard is updated in real-time.
        """)
        st.markdown("""
        ### Metric Definitions
        
        - **Verified Harmful Prompts**: Number of prompts that were verified as harmful through human review. This is our primary metric for ranking contributors.
        
        - **Assistant Rejections**: Cases where the prompt wasn't flagged as harmful by automated checks, but the assistant's output was flagged as harmful.
        
        - **Success Rate**: Percentage of a contributor's total submissions that were verified as harmful prompts.
        
        The leaderboard ranks contributors primarily by the number of verified harmful prompts they've identified, with assistant rejections as a secondary metric.
        """)