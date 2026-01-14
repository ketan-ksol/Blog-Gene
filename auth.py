"""Authentication and authorization module."""
import streamlit as st
from typing import Optional, Dict, Any
from database import get_database


def check_authentication() -> bool:
    """Check if user is authenticated.
    
    Returns:
        True if authenticated, False otherwise
    """
    return st.session_state.get("authenticated", False)


def get_current_user() -> Optional[Dict[str, Any]]:
    """Get current authenticated user.
    
    Returns:
        User dictionary or None
    """
    if check_authentication():
        return st.session_state.get("user")
    return None


def get_user_role() -> Optional[str]:
    """Get current user's role.
    
    Returns:
        User role (admin or user) or None
    """
    user = get_current_user()
    return user.get("role") if user else None


def is_admin() -> bool:
    """Check if current user is admin.
    
    Returns:
        True if user is admin, False otherwise
    """
    return get_user_role() == "admin"


def require_auth():
    """Require authentication - stops execution if not authenticated."""
    if not check_authentication():
        st.error("🔒 Please login to continue")
        st.stop()


def require_admin():
    """Require admin role - shows error if not admin."""
    require_auth()
    if not is_admin():
        st.error("🔒 Access Denied: Admin privileges required.")
        st.stop()


def login(username: str, password: str) -> bool:
    """Authenticate user and set session.
    
    Args:
        username: Username
        password: Password
    
    Returns:
        True if login successful, False otherwise
    """
    db = get_database()
    user = db.authenticate_user(username, password)
    
    if user:
        st.session_state["authenticated"] = True
        st.session_state["user"] = user
        return True
    
    return False


def logout():
    """Logout current user."""
    st.session_state["authenticated"] = False
    st.session_state["user"] = None


