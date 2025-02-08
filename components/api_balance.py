import streamlit as st
from streamlit_autorefresh import st_autorefresh
from database import get_dataset_stats
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@st.cache_data(ttl=60)  # Cache for 1 minute
def get_api_balance():
    """Get API balance with fallbacks and error handling"""
    try:
        # Get budget from secrets
        try:
            budget = float(st.secrets.get("api_budget", 1000.00))
        except (KeyError, ValueError, TypeError):
            logger.warning("Could not get api_budget from secrets, using default")
            budget = 1000.00
            
        try:
            # Try to get total cost from database
            stats = get_dataset_stats()
            total_cost = stats.get("total_cost", 0)
            logger.info(f"Got total cost from database: ${total_cost:.2f}")
        except Exception as e:
            # Use session state for last known cost if database fails
            logger.warning(f"Database error: {str(e)}")
            total_cost = st.session_state.get("last_known_total_cost", 0)
            logger.info(f"Using cached total cost: ${total_cost:.2f}")
        
        # Store current cost in session state
        st.session_state.last_known_total_cost = total_cost
        
        # Calculate remaining balance
        remaining_balance = budget - total_cost
        
        # Store in session state
        st.session_state.last_known_balance = remaining_balance
        
        return remaining_balance
    except Exception as e:
        logger.error(f"Error calculating API balance: {str(e)}")
        return st.session_state.get("last_known_balance", 1000.00)

def display_api_balance(refresh_interval=60, dynamic_refresh=True):
    """Display API balance with optional auto-refresh
    
    Args:
        refresh_interval (int): Base refresh interval in seconds
        dynamic_refresh (bool): If True, adjusts refresh rate based on usage patterns
    """
    try:
        container = st.empty()
        with container:
            if refresh_interval > 0:
                # Adjust refresh rate based on usage patterns if dynamic refresh is enabled
                if dynamic_refresh:
                    # Check if there's been significant change in last update
                    significant_change = (
                        'prev_balance' in st.session_state
                        and abs(balance - st.session_state.prev_balance) > 0.01
                    )
                    
                    # Get current refresh rate or use default
                    current_refresh = st.session_state.get('refresh_rate', refresh_interval)
                    
                    # Adjust refresh rate based on activity
                    if significant_change and current_refresh > 15:  # Minimum 15 seconds
                        # Decrease interval (faster updates) when there's activity
                        new_refresh = max(15, current_refresh - 15)
                    elif not significant_change and current_refresh < refresh_interval:
                        # Gradually return to base interval during inactivity
                        new_refresh = min(refresh_interval, current_refresh + 5)
                    else:
                        new_refresh = current_refresh
                    
                    st.session_state.refresh_rate = new_refresh
                    actual_refresh = new_refresh
                else:
                    actual_refresh = refresh_interval
                
                st_autorefresh(interval=actual_refresh * 1000, key="balance_refresh")
            
            # Get current balance
            balance = get_api_balance()
            
            # Get previous balance from session state
            prev_balance = st.session_state.get('prev_balance', balance)
            
            # Calculate delta
            delta = balance - prev_balance if prev_balance is not None else None
            
            # Calculate percentage change for delta
            if delta is not None and prev_balance != 0:
                pct_change = (delta / prev_balance) * 100
                delta_text = f"${delta:.2f} ({pct_change:.1f}%)"
            else:
                delta_text = None

            # Display metric
            st.metric(
                "API Balance",
                f"${balance:.2f}",
                delta=delta_text,
                delta_color="inverse"  # Red when spending money (negative delta)
            )
            
            # Update session state
            st.session_state.prev_balance = balance
            
            # Show warning if using cached data
            if "last_known_total_cost" in st.session_state:
                st.warning("⚠️ Using cached cost data - some values may be outdated", icon="⚠️")
    except Exception as e:
        logger.error(f"Error displaying API balance: {str(e)}")
        with container:
            st.error("Error displaying API balance - showing last known value")
            # Get last known good value
            last_balance = st.session_state.get("last_known_balance")
            if last_balance is not None:
                st.metric(
                    "API Balance",
                    f"${last_balance:.2f} (cached)",
                    delta=None
                )
            else:
                st.metric(
                    "API Balance",
                    "No data available",
                    delta=None
                )