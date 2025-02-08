import streamlit as st
import pandas as pd
from database import get_dataset_stats

st.set_page_config(page_title="Thank You", page_icon="🙏")

def main():
    st.title("Thank You, Beta Testers! 🙏")
    
    # Get dataset statistics
    stats = get_dataset_stats()
    
    st.markdown("""
    ## Your Impact on AI Safety

    Welcome to OmniGuard's distinguished beta testing community. Your expertise and dedication have been instrumental in advancing our mission of creating a more secure AI ecosystem.
    """)

    # Display impact metrics
    st.markdown(f"""
    ### What You've Helped Accomplish:
    - **{stats['total_sets']:,}** test cases analyzed
    - **{stats['user_violations']:,}** potential user violations identified
    - **{stats['assistant_violations']:,}** assistant safety improvements made
    """)

    st.markdown("---")
    
    st.markdown("## Our Amazing Beta Testers")
    st.markdown("Thank you to everyone who has contributed to making OmniGuard better and safer!")
    
    # Beta testers data - each tester is a complete object
    beta_testers_data = [
        {
            "name": "CloakEngaged",
            "x_handle": "",
            "discord": "needyousky",
            "linkedin": ""
        },
        {
            "name": "N",
            "x_handle": "",
            "discord": "nicknamegg",
            "linkedin": ""
        },
        {
            "name": "Exocija",
            "x_handle": "",
            "discord": "c1j4",
            "linkedin": ""
        },
        {
            "name": "the_magician",
            "x_handle": "",
            "discord": "019ec6e2",
            "linkedin": ""
        }

    ]
    

    # Convert to DataFrame and display as a table
    df = pd.DataFrame(beta_testers_data)
    st.table(df.rename(columns={
        "name": "Name",
        "x_handle": "X Handle",
        "discord": "Discord",
        "linkedin": "LinkedIn"
    }))

    # Add note about adding new testers
    # with st.expander("➕ Add New Beta Tester"):
    #     st.code("""
    # # To add a new beta tester, copy this template and add it to beta_testers_data:
    # {
    #     "name": "Tester Name",
    #     "x_handle": "@handle",
    #     "discord": "username#0000",
    #     "linkedin": "linkedin.com/in/profile"
    # }
    # """, language="python")
    
    st.markdown("---")
    
    st.markdown("""
    ## Why Your Contribution Matters

    Each contribution advances our collective mission:
    - 🛡️ **Advancing Security**: Each test scenario strengthens our defense capabilities and enhances system resilience
    - 🔄 **Enhancing Precision**: Real-world validation drives continuous refinement of our moderation algorithms
    - 🌐 **Fostering Trust**: Rigorous testing and transparent feedback establish OmniGuard as an industry-leading solution
    - 🚀 **Pioneering Innovation**: Challenging edge cases drive the development of breakthrough solutions
    
    ## What's Next

    Your contributions continue to shape the future of AI safety. The insights gained from your test cases will:
    - Inform future updates to our rule sets
    - Help develop more nuanced moderation strategies
    - Guide the development of new safety features
    
    ## Thank You

    Your dedication to testing and providing valuable feedback has been crucial in developing a more secure and reliable AI ecosystem. Together, we're making AI interactions safer for everyone.
    """)

if __name__ == "__main__":
    main()