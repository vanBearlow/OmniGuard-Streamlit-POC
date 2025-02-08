import streamlit as st
from database import get_connection
import json
from components.auth import render_auth_status, get_auth_status
import time

# Define allowed social platforms
SOCIAL_PLATFORMS = ["x", "discord", "linkedin"]

def calculate_profile_completion(profile: dict) -> tuple[float, list[str]]:
    """Calculate profile completion percentage and missing fields."""
    required_fields = ['name']
    optional_fields = SOCIAL_PLATFORMS
    
    # Check required fields
    completed_required = sum(1 for field in required_fields if profile.get(field))
    required_score = completed_required / len(required_fields)
    
    # Check optional fields
    completed_optional = sum(1 for field in optional_fields if profile.get('social_handles', {}).get(field))
    optional_score = completed_optional / len(optional_fields)
    
    # Calculate total score (required fields are weighted more)
    total_score = (required_score * 0.7) + (optional_score * 0.3)
    
    # Get missing required fields
    missing_fields = [field for field in required_fields if not profile.get(field)]
    
    return total_score * 100, missing_fields

def update_user_profile(email, social_handles=None, name=None):
    """Update user profile with new information and timestamp."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        updates = ["last_updated = CURRENT_TIMESTAMP"]
        values = []
        
        if social_handles is not None:
            updates.append("social_handles = %s")
            values.append(json.dumps(social_handles))
            
        if name is not None:
            updates.append("name = %s")
            values.append(name)
        
        # Get Google profile info
        try:
            user = st.experimental_user
            user_id = user.id if hasattr(user, 'id') else None
            picture = user.picture if hasattr(user, 'picture') else None
            
            if user_id:
                updates.append("user_id = %s")
                values.append(user_id)
            
            if picture:
                updates.append("picture = %s")
                values.append(picture)
        except Exception as e:
            st.warning(f"Could not fetch Google profile info: {str(e)}")
        
        query = f"UPDATE users SET {', '.join(updates)} WHERE email = %s"
        values.append(email)
        cur.execute(query, values)
        
        # Create user record if it doesn't exist
        cur.execute("""
            INSERT INTO users (email, name, social_handles, user_id, picture, last_updated)
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (email) DO NOTHING
        """, (
            email,
            name,
            json.dumps(social_handles) if social_handles else '{}',
            user_id if 'user_id' in locals() else None,
            picture if 'picture' in locals() else None
        ))
        
        conn.commit()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)

def get_user_profile(email):
    """Get user profile including last update timestamp and Google profile info."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT social_handles, name,
                   to_char(last_updated, 'YYYY-MM-DD HH24:MI:SS') as last_updated,
                   user_id, picture,
                   to_char(created_at, 'YYYY-MM-DD HH24:MI:SS') as created_at
            FROM users WHERE email = %s
            """,
            (email,)
        )
        result = cur.fetchone()
        conn.close()
        
        if result:
            return {
                'social_handles': json.loads(result[0]) if result[0] else {},
                'name': result[1] if result[1] else '',
                'last_updated': result[2] if result[2] else 'Never',
                'user_id': result[3] if result[3] else None,
                'picture': result[4] if result[4] else None,
                'created_at': result[5] if result[5] else None
            }
        
        # If no profile exists, create one with Google info
        try:
            user = st.experimental_user
            profile = {
                'social_handles': {},
                'name': user.name if hasattr(user, 'name') else '',
                'last_updated': 'Never',
                'user_id': user.id if hasattr(user, 'id') else None,
                'picture': user.picture if hasattr(user, 'picture') else None,
                'created_at': None
            }
        except Exception as e:
            st.warning(f"Could not fetch Google profile info: {str(e)}")
            profile = {
                'social_handles': {},
                'name': '',
                'last_updated': 'Never',
                'user_id': None,
                'picture': None,
                'created_at': None
            }
        
        # Create initial profile
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO users (email, name, user_id, picture)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (email) DO NOTHING
            """,
            (email, profile['name'], profile['user_id'], profile['picture'])
        )
        conn.commit()
        conn.close()
        
        return profile
    except Exception as e:
        st.error(f"Error fetching profile: {str(e)}")
        return {
            'social_handles': {},
            'name': '',
            'last_updated': 'Never',
            'user_id': None,
            'picture': None,
            'created_at': None
        }

# Page Layout
st.set_page_config(page_title="Profile", page_icon="👤", layout="wide")

# Add authentication status to sidebar
render_auth_status()

# Check if user is logged in
is_authenticated, _ = get_auth_status()
if not is_authenticated:
    st.info("Please log in to manage your profile")
    st.stop()

# Get user email from experimental_user
try:
    user_email = st.experimental_user.email
except Exception as e:
    st.error(f"Could not get user email: {str(e)}")
    st.stop()

# Get current profile
profile = get_user_profile(user_email)

# Calculate profile completion
completion_percentage, missing_fields = calculate_profile_completion(profile)

# Profile Header
st.title("Profile Settings")

# Profile Header with Picture and Info
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    if profile.get('picture'):
        st.image(profile['picture'], width=100)
    else:
        st.markdown("### 👤")  # Default avatar emoji if no picture

with col2:
    st.progress(completion_percentage / 100, f"Profile Completion: {completion_percentage:.0f}%")
    if missing_fields:
        st.info(f"Complete your profile by adding: {', '.join(missing_fields)}")

with col3:
    st.write("Account Info")
    st.caption(f"📧 {user_email}")
    st.caption(f"🕒 Last Updated: {profile.get('last_updated', 'Never')}")
    if profile.get('created_at'):
        st.caption(f"📅 Joined: {profile['created_at']}")

# Profile content
with st.form("profile_form"):
    # Name field (required)
    name = st.text_input(
        "Name (required)",
        value=profile.get('name', ''),
        placeholder="Your name on leaderboards",
        help="This name will be displayed on leaderboards and in conversations"
    )
    
    # Social handles
    st.subheader("Social Media Handles")
    social_handles = profile['social_handles']
    new_social_handles = {}
    
    platform_labels = {
        "x": "X (Twitter)",
        "discord": "Discord",
        "linkedin": "LinkedIn"
    }
    
    cols = st.columns(len(SOCIAL_PLATFORMS))
    for idx, platform in enumerate(SOCIAL_PLATFORMS):
        with cols[idx]:
            handle = st.text_input(
                platform_labels[platform],
                value=social_handles.get(platform, ''),
                placeholder=f"Your {platform_labels[platform]} handle",
                help=f"Enter your {platform_labels[platform]} username"
            )
            if handle:
                new_social_handles[platform] = handle

    submitted = st.form_submit_button("Save Profile", type="primary", use_container_width=True)
    
    if submitted:
        if not name:
            st.error("Name is required")
        else:
            success, error = update_user_profile(
                user_email,
                social_handles=new_social_handles if new_social_handles else None,
                name=name
            )
            if success:
                st.success("Profile saved successfully!")
                time.sleep(1)  # Brief delay for better UX
                st.rerun()
            else:
                st.error(f"Failed to save profile: {error}")

# Account Management
with st.expander("Account Management"):
    st.write("Here you can manage your account settings and data.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Export Profile Data", use_container_width=True):
            profile_data = {
                "email": user_email,
                "name": profile.get('name'),
                "social_handles": profile.get('social_handles'),
                "user_id": profile.get('user_id'),
                "picture": profile.get('picture'),
                "created_at": profile.get('created_at'),
                "last_updated": profile.get('last_updated'),
                "completion": f"{completion_percentage:.0f}%"
            }
            st.download_button(
                "Download Profile Data",
                data=json.dumps(profile_data, indent=2),
                file_name="profile_data.json",
                mime="application/json",
                use_container_width=True
            )
    
    with col2:
        if st.button("Delete Account", type="secondary", use_container_width=True):
            st.error("⚠️ Are you sure you want to delete your account? This action cannot be undone.")
            if st.button("Yes, Delete My Account", type="primary"):
                # TODO: Implement account deletion
                st.warning("Account deletion is not yet implemented.")