import streamlit as st
from database import get_dataset_stats
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@st.cache_data(ttl=60)  # Cache for 1 minute
def get_api_balance():
    """
    Retrieve the current API balance by calculating the difference between the allocated budget and the total cost.

    This function attempts to obtain the API budget from Streamlit secrets, defaulting to 1000.00 if not provided.
    It then tries to fetch the total cost from the database via get_dataset_stats. In the event of a database error,
    the function uses the last known total cost from the session state. The remaining balance is stored in the session
    state and returned.

    Returns:
        float: The calculated API balance.
    """
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

def display_api_balance():
    """
    Display the current API balance on the Streamlit interface and update the display accordingly.

    This function retrieves the API balance using get_api_balance, calculates the delta compared to the previous balance,
    and displays the metric using st.metric. It also updates the session state with the current balance and shows a warning
    if cached data is being used.

    Returns:
        None
    """
    try:
        container = st.empty()
        
        # Get current balance and previous balance
        balance = get_api_balance()
        prev_balance = st.session_state.get('prev_balance', balance)
        
        # Calculate delta
        delta = balance - prev_balance if prev_balance is not None else None
        if delta is not None and prev_balance != 0:
            pct_change = (delta / prev_balance) * 100
            delta_text = f"${delta:.2f} ({pct_change:.1f}%)"
        else:
            delta_text = None
        
        # Display metric
        with container:
            st.metric(
                "API Balance",
                f"${balance:.2f}",
                delta=delta_text,
                delta_color="inverse"  # Red when spending money (negative delta)
            )
        
        # Update session state with current balance
        st.session_state.prev_balance = balance
        
        # Show warning if using cached data
        if "last_known_total_cost" in st.session_state:
            st.warning("⚠️ Using cached cost data - some values may be outdated", icon="⚠️")
    except Exception as e:
        logger.error(f"Error displaying API balance: {str(e)}")
        with container:
            st.error("Error displaying API balance - showing last known value")
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