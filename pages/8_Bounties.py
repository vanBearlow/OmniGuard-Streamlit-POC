import streamlit as st
import datetime
from database import get_active_bounties, create_bounty, record_donation

st.set_page_config(page_title="Bounties", page_icon="🏆")

def format_currency(amount):
    return f"${amount:,.2f}"

def main():
    st.title("🏆 Bounties")
    
    # Show active bounties
    st.header("Active Bounties")
    
    bounties = get_active_bounties()
    
    if not bounties:
        st.info("No active bounties at the moment.")
    else:
        for bounty in bounties:
            with st.expander(f"{bounty['title']} - Prize Pool: {format_currency(bounty['prize_pool_amount'])}"):
                st.write(bounty['description'])
                st.write(f"**Metric**: {bounty['metric']}")
                st.write(f"**Start Date**: {bounty['start_date']}")
                st.write(f"**End Date**: {bounty['end_date']}")
                
                # Show current leaders
                st.subheader("Current Leaders")
                if bounty['current_leaders']:
                    for i, leader in enumerate(bounty['current_leaders'], 1):
                        st.write(f"{i}. {leader['contributor']} - {leader['count']} contributions")
                else:
                    st.write("No contributions yet!")
                
                # Donation section
                st.subheader("Support this Bounty")
                donation_amount = st.number_input(
                    "Donation Amount ($)", 
                    min_value=1.0,
                    step=1.0,
                    key=f"donation_{bounty['bounty_id']}"
                )
                if st.button("Donate", key=f"donate_{bounty['bounty_id']}"):
                    if 'user_id' not in st.session_state:
                        st.error("Please log in to donate.")
                    else:
                        record_donation(
                            st.session_state.user_id,
                            donation_amount,
                            'bounty',
                            bounty['bounty_id']
                        )
                        st.success(f"Thank you for your donation of {format_currency(donation_amount)}!")
                        st.rerun()
    
    # Admin section for creating new bounties
    if st.session_state.get('is_admin', False):
        st.header("Create New Bounty")
        with st.form("new_bounty"):
            title = st.text_input("Bounty Title")
            description = st.text_area("Description")
            metric = st.selectbox(
                "Metric to Track",
                ['user_violations', 'assistant_violations', 'verification_accuracy'],
                format_func=lambda x: {
                    'user_violations': 'Most Harmful User Prompts Identified',
                    'assistant_violations': 'Most Assistant Output Violations Found',
                    'verification_accuracy': 'Most Accurate Human Verifier'
                }[x]
            )
            
            # Show metric description
            metric_descriptions = {
                'user_violations': """
                    This bounty rewards users who identify the most harmful user prompts that get verified by human reviewers.
                    To participate:
                    1. Submit conversations that may contain harmful prompts
                    2. Wait for human verification
                    3. Only verified harmful prompts count towards your score
                """,
                'assistant_violations': """
                    This bounty rewards users who identify the most cases where the AI assistant's output violates guidelines.
                    To participate:
                    1. Submit conversations where the assistant may have violated guidelines
                    2. Wait for human verification
                    3. Only verified violations count towards your score
                """,
                'verification_accuracy': """
                    This bounty rewards the most accurate human verifiers.
                    To participate:
                    1. Review and vote on submitted conversations
                    2. Your accuracy is measured by how well your votes align with final decisions
                    3. Minimum 10 verifications required to qualify
                """
            }
            st.info(metric_descriptions[metric])
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", min_value=datetime.date.today())
            with col2:
                end_date = st.date_input("End Date", min_value=start_date)
            
            if st.form_submit_button("Create Bounty"):
                if not all([title, description, metric, start_date, end_date]):
                    st.error("Please fill in all fields.")
                else:
                    # Convert dates to datetime with timezone
                    start_datetime = datetime.datetime.combine(
                        start_date, 
                        datetime.time.min
                    ).replace(tzinfo=datetime.timezone.utc)
                    end_datetime = datetime.datetime.combine(
                        end_date, 
                        datetime.time.max
                    ).replace(tzinfo=datetime.timezone.utc)
                    
                    create_bounty(
                        title,
                        description,
                        metric,
                        start_datetime,
                        end_datetime
                    )
                    st.success("Bounty created successfully!")
                    st.rerun()

if __name__ == "__main__":
    main()