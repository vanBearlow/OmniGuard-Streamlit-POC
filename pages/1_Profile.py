import streamlit as st
from database import get_connection
import json
from components.auth import render_auth_status, get_auth_status
import time
import uuid

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
            user_id = user.id if hasattr(user, 'id') and user.id is not None else str(uuid.uuid4())
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
                'user_id': user.id if hasattr(user, 'id') and user.id is not None else str(uuid.uuid4()),
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

# Check if user is logged in or running in dev mode
dev_mode = bool(st.secrets.get("development_mode", False))
try:
    user = st.experimental_user
    user_email = user.email if hasattr(user, "email") and user.email else None
except Exception:
    user_email = None

if not user_email:
    if dev_mode:
        user_email = "devuser@local.dev"
    else:
        st.info("Please log in to manage your profile.")
        st.stop()

# Get current profile
profile = get_user_profile(user_email)
st.header("Your Profile")
if profile.get('picture'):
    st.image(profile['picture'], width=150)
completion, missing_fields = calculate_profile_completion(profile)
st.markdown("#### Profile Completion")
st.progress(int(completion))
st.markdown(f"Profile is {completion:.0f}% complete.")
if missing_fields:
    st.info("Missing fields: " + ", ".join(missing_fields))
st.caption(f"📧 {user_email}")
if profile.get('created_at'):
    st.caption(f"📅 Joined: {profile['created_at']}")

# Profile content
with st.form("profile_form",):
    # Name field (required)
    st.markdown("#### Complete your profile to get credit for your contributions!")
    name = st.text_input(
        "Name (required)",
        value=profile.get('name', ''),
        placeholder="Your name on leaderboards",
        help="This name will be displayed on leaderboards and in conversations"
    )
    # Social handles
    st.markdown("#### Social Media Handles")
    social_handles = profile['social_handles']
    new_social_handles = {}

    platform_labels = {
        "x": "X",
        "discord": "Discord",
        "linkedin": "LinkedIn"
    }
    
    cols = st.columns(len(SOCIAL_PLATFORMS))
    for idx, platform in enumerate(SOCIAL_PLATFORMS):
        with cols[idx]:
            if platform == "linkedin":
                handle = st.text_input(
                    platform_labels[platform],
                    value=social_handles.get(platform, ''),
                    placeholder="Your Linkedin Url",
                    help="Enter your Linkedin URL"
                )
            else:
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
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"Failed to save profile: {error}")

if st.button("Export Profile Data", use_container_width=True):
    profile_data = {
        "email": user_email,
        "name": profile.get('name'),
        "social_handles": profile.get('social_handles'),
        "created_at": profile.get('created_at'),
        "completion": "N/A"
    }
    st.download_button(
        "Download Profile Data",
        data=json.dumps(profile_data, indent=2),
        file_name="profile_data.json",
        mime="application/json",
        use_container_width=True
    )