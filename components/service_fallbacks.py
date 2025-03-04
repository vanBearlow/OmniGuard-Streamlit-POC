"""
Module: service_fallbacks.py
Description:
    Provides utility functions for handling API key retrieval.
    Includes graceful error handling with user feedback via Streamlit.
"""

import streamlit as st
import logging
from typing import Optional

logger = logging.getLogger(__name__)


#*** API KEY CHECK FUNCTION  ***
def check_api_key() -> Optional[str]:
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    if not api_key:
        st.error("API key not configured. Notify Brian")
    return api_key