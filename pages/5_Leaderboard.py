import streamlit as st

st.set_page_config(page_title="Leaderboard", page_icon="🏆")

def init_leaderboard_state():
    """Initialize leaderboard state in session."""
    if 'leaderboard_stats' not in st.session_state:
        st.session_state.leaderboard_stats = {
            'contributors': [],
            'total_conversations': 0,
            'total_messages': 0,
            'total_violations_caught': 0
        }
    if 'donor_stats' not in st.session_state:
        st.session_state.donor_stats = []

@st.cache_data(ttl=60)
def get_leaderboard_stats():
    """Get leaderboard statistics from session state."""
    init_leaderboard_state()
    return st.session_state.leaderboard_stats

@st.cache_data(ttl=60)
def get_top_donors():
    """Get top donors from session state."""
    init_leaderboard_state()
    return st.session_state.donor_stats

def update_leaderboard_stats(contributor_email, messages_count=0, violations_caught=0):
    """Update leaderboard statistics."""
    init_leaderboard_state()
    stats = st.session_state.leaderboard_stats
    
    contributor_found = False
    for contributor in stats['contributors']:
        if contributor['email'] == contributor_email:
            contributor['messages'] += messages_count
            contributor['violations_caught'] += violations_caught
            contributor_found = True
            break
    
    if not contributor_found:
        stats['contributors'].append({
            'email': contributor_email,
            'messages': messages_count,
            'violations_caught': violations_caught
        })
    
    stats['total_messages'] += messages_count
    stats['total_violations_caught'] += violations_caught
    if not contributor_found:
        stats['total_conversations'] += 1
    
    st.session_state.leaderboard_stats = stats

def update_donor_stats(donor_email, donation_amount):
    """Update donor statistics."""
    init_leaderboard_state()
    donor_found = False
    for donor in st.session_state.donor_stats:
        if donor['email'] == donor_email:
            donor['amount'] += donation_amount
            donor_found = True
            break
    
    if not donor_found:
        st.session_state.donor_stats.append({
            'email': donor_email,
            'amount': donation_amount
        })

# Page Layout
st.title("🏆 Leaderboard")

tabs = st.tabs(["🏆 Contributors", "🎁 Donors"])

with tabs[0]:
    st.subheader("Coming Soon")

with tabs[1]:
    st.subheader("Coming Soon")