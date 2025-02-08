import streamlit as st
from typing import Optional
import uuid
from datetime import datetime

def handle_crypto_donation(amount: float, allocation: str, user_id: str, tx_hash: str):
    """Record the crypto donation in the database."""
    from database import record_donation
    
    # Map allocation to use_for value
    use_for_map = {
        "Bounties": "bounty",
        "API Costs": "api_costs",
        "Creator Support": "creator_support"
    }
    use_for = use_for_map.get(allocation, "other")
    
    # Record the donation
    record_donation(
        user_id=user_id,
        amount=amount,
        use_for=use_for,
        bounty_id=None  # For now, not allocating to specific bounties
    )

def donations_page():
    st.title("Support Our Project")
    
    # Check if user is logged in
    if "user" not in st.session_state:
        st.warning("Please log in to record your donation.")
        return
    
    # Explanation section
    st.markdown("""
    Your donations help us maintain and improve this project. You can choose to allocate your donation to:
    - **Bounties**: Fund rewards for community contributions
    - **API Costs**: Help offset the costs of running the AI services
    - **Creator Support**: Support the development and maintenance of the platform
    """)
    
    # USDT Donation Instructions
    st.subheader("Donate with USDT")
    
    # Get wallet address from secrets
    wallet_address = st.secrets.crypto.USDT_WALLET
    
    st.markdown("""
    We accept donations in USDT (Tether) on the following networks:
    - **Tron (TRC20)**
    - **Ethereum (ERC20)**
    - **BNB Smart Chain (BEP20)**
    
    Please ensure you're sending USDT on a supported network to avoid loss of funds.
    """)
    
    st.code(wallet_address, language=None)
    
    # Copy button for wallet address
    if st.button("Copy Wallet Address"):
        st.write("Wallet address copied to clipboard!")
        st.markdown(f"<script>navigator.clipboard.writeText('{wallet_address}')</script>", unsafe_allow_html=True)
    
    # Form to record donation
    st.markdown("---")
    st.subheader("Record Your Donation")
    
    with st.form("donation_record"):
        donation_type = st.selectbox(
            "Donation allocation",
            ["Bounties", "API Costs", "Creator Support"],
            help="Choose where you'd like your donation to be allocated"
        )
        
        amount = st.number_input(
            "Amount (USDT)",
            value=10.0,
            min_value=1.0,
            help="Enter the amount you donated in USDT"
        )
        
        tx_hash = st.text_input(
            "Transaction Hash",
            help="Enter the transaction hash from your USDT transfer"
        )
        
        submitted = st.form_submit_button("Record Donation")
        
        if submitted:
            if not tx_hash:
                st.error("Please enter the transaction hash to record your donation.")
            else:
                handle_crypto_donation(
                    amount=amount,
                    allocation=donation_type,
                    user_id=st.session_state.user["user_id"],
                    tx_hash=tx_hash
                )
                st.success("""
                Thank you for your donation! Your contribution has been recorded.
                The funds will be allocated according to your preference.
                """)
    
    # Network-specific instructions
    st.markdown("---")
    st.subheader("Network Information")
    
    with st.expander("Network Details"):
        st.markdown("""
        **Tron (TRC20)**
        - Fastest and cheapest network for USDT transfers
        - Transaction fees are very low (usually less than $1)
        - Confirmations typically take 1-3 minutes
        
        **Ethereum (ERC20)**
        - Most widely supported network
        - Higher transaction fees (gas fees apply)
        - Confirmations may take 5-10 minutes
        
        **BNB Smart Chain (BEP20)**
        - Low transaction fees
        - Fast confirmations (3-5 minutes)
        - Widely supported by major exchanges
        
        **Important**: Always test with a small amount first if you're unsure about the network.
        """)
    
    # Security notice
    st.markdown("---")
    st.caption("""
    **Security Notice**: Always verify the wallet address before sending any funds.
    Only send USDT on supported networks to this address.
    Contact support if you need assistance with your donation.
    """)

if __name__ == "__main__":
    donations_page()