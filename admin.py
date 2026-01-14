"""Admin module for managing system settings and configurations."""
import streamlit as st
import os
from typing import Dict, Any
from database import get_database
from auth import require_admin, get_current_user, logout


def render_admin_page():
    """Render admin page with role-based access control."""
    # Require admin access
    require_admin()
    
    # Get current user
    user = get_current_user()
    
    # Add custom CSS for admin page
    st.markdown("""
        <style>
        .admin-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 10px;
            color: white;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .admin-header h1 {
            color: white;
            margin: 0;
            font-size: 2rem;
        }
        .admin-header p {
            color: rgba(255, 255, 255, 0.9);
            margin: 0.5rem 0 0 0;
        }
        .setting-card {
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            margin-bottom: 1.5rem;
            border: 1px solid #e0e0e0;
        }
        .setting-section {
            margin-bottom: 2rem;
        }
        .setting-section h3 {
            color: #667eea;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 0.5rem;
            margin-bottom: 1rem;
        }
        .user-card {
            background: white;
            padding: 1.25rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            margin-bottom: 1rem;
            border-left: 4px solid #4CAF50;
        }
        .user-card.admin {
            border-left-color: #FF9800;
        }
        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 500;
        }
        .status-active {
            background-color: #d4edda;
            color: #155724;
        }
        .status-inactive {
            background-color: #f8d7da;
            color: #721c24;
        }
        .role-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 600;
        }
        .role-admin {
            background-color: #fff3cd;
            color: #856404;
        }
        .role-user {
            background-color: #d1ecf1;
            color: #0c5460;
        }
        .info-box {
            background-color: #f5f5f5;
            border: 1px solid #e0e0e0;
            padding: 1rem;
            border-radius: 4px;
            margin: 1rem 0;
        }
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 8px;
            color: white;
            text-align: center;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            margin: 0.5rem 0;
        }
        .metric-label {
            font-size: 0.9rem;
            opacity: 0.9;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header with gradient
    st.markdown(f"""
        <div class="admin-header">
            <h1>⚙️ Admin Configuration</h1>
            <p>Manage system settings, agent configurations, and user accounts</p>
        </div>
    """, unsafe_allow_html=True)
    
    db = get_database()
    
    # Quick stats
    users = db.list_users()
    admin_count = sum(1 for u in users if u['role'] == 'admin')
    user_count = len(users) - admin_count
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total Users</div>
                <div class="metric-value">{len(users)}</div>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Admins</div>
                <div class="metric-value">{admin_count}</div>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Regular Users</div>
                <div class="metric-value">{user_count}</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tabs for different admin sections
    tab1, tab2, tab3 = st.tabs([
        "🤖 Model Settings",
        "🔬 Agent Settings",
        "👥 User Management"
    ])
    
    with tab1:
        render_model_settings(db)
    
    with tab2:
        render_agent_settings(db)
    
    with tab3:
        render_user_management(db)


def render_model_settings(db):
    """Render model settings configuration."""
    st.markdown("### 🤖 Model Settings")
    st.markdown("Configure OpenAI model and generation parameters for blog creation.")
    
    # Get current settings
    model_name = db.get_system_setting("model_name", "gpt-5")
    temperature = db.get_system_setting("temperature", 0.7)
    
    # Model selection card
    st.markdown('<div class="setting-card">', unsafe_allow_html=True)
    st.markdown("#### 🎯 Model Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_model_name = st.selectbox(
            "**Model Name**",
            ["gpt-5", "gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
            index=["gpt-5", "gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"].index(model_name) if model_name in ["gpt-5", "gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"] else 0,
            help="OpenAI model to use for blog generation. gpt-5 is the latest model, gpt-4o is recommended for best quality."
        )
        
        # Model info
        model_info = {
            "gpt-5": "Latest generation, most advanced and capable model",
            "gpt-4o": "Latest, fastest, most capable model",
            "gpt-4-turbo": "High quality, good for complex tasks",
            "gpt-4": "Original, slower but very capable",
            "gpt-3.5-turbo": "Faster, lower cost, good for simple tasks"
        }
        st.caption(f"💡 {model_info.get(new_model_name, '')}")
    
    with col2:
        new_temperature = st.slider(
            "**Temperature**",
            min_value=0.0,
            max_value=2.0,
            value=float(temperature),
            step=0.1,
            help="Controls randomness: Higher = more creative, Lower = more focused"
        )
        
        # Temperature indicator
        if new_temperature < 0.5:
            temp_label = "Very Focused"
            temp_color = "#4CAF50"
        elif new_temperature < 1.0:
            temp_label = "Balanced"
            temp_color = "#FF9800"
        else:
            temp_label = "Creative"
            temp_color = "#F44336"
        
        st.markdown(f'<p style="color: {temp_color}; font-weight: 500;">Current: {temp_label}</p>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Current settings display
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown("**📊 Current Settings:**")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Model:** {model_name}")
    with col2:
        st.write(f"**Temperature:** {temperature}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Save button
    if st.button("💾 Save Model Settings", type="primary", use_container_width=True):
        db.set_system_setting("model_name", new_model_name, "string", "OpenAI model to use")
        db.set_system_setting("temperature", new_temperature, "float", "Model temperature")
        
        # Note: Environment variables are only for credentials, not config
        # Config is stored in database and read from there
        
        st.success("✅ Model settings saved successfully!")
        st.rerun()


def render_agent_settings(db):
    """Render agent settings configuration."""
    st.markdown("### 🔬 Agent Settings")
    st.markdown("Configure agent behavior, research capabilities, and content constraints.")
    
    # Get current settings
    enable_web_search = db.get_system_setting("enable_web_search", True)
    max_research_sources = db.get_system_setting("max_research_sources", 10)
    min_word_count = db.get_system_setting("min_word_count", 500)
    max_word_count = db.get_system_setting("max_word_count", 1000)
    
    # Research settings card
    st.markdown('<div class="setting-card">', unsafe_allow_html=True)
    st.markdown("#### 🔍 Research Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_enable_web_search = st.checkbox(
            "**Enable Web Search**",
            value=enable_web_search,
            help="Allow the research agent to search the web for up-to-date information"
        )
        if new_enable_web_search:
            st.success("🌐 Web search is enabled")
        else:
            st.warning("⚠️ Web search is disabled - only local knowledge will be used")
    
    with col2:
        new_max_research_sources = st.number_input(
            "**Max Research Sources**",
            min_value=1,
            max_value=50,
            value=max_research_sources,
            step=1,
            help="Maximum number of research sources to fetch and analyze"
        )
        st.caption(f"📚 Will fetch up to {new_max_research_sources} sources per blog")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Word count settings card
    st.markdown('<div class="setting-card">', unsafe_allow_html=True)
    st.markdown("#### 📝 Content Word Count Settings")
    st.markdown("Configure minimum and maximum word count for blog content (inner content only, excludes references/FAQ).")
    
    col3, col4 = st.columns(2)
    
    with col3:
        new_min_word_count = st.number_input(
            "**Min Word Count**",
            min_value=300,
            max_value=2000,
            value=int(min_word_count),
            step=50,
            help="Minimum word count for blog content"
        )
        st.caption(f"📊 Minimum: {new_min_word_count} words")
    
    with col4:
        new_max_word_count = st.number_input(
            "**Max Word Count**",
            min_value=500,
            max_value=5000,
            value=int(max_word_count),
            step=50,
            help="Maximum word count for blog content"
        )
        st.caption(f"📊 Maximum: {new_max_word_count} words")
    
    # Word count range validation
    if new_min_word_count >= new_max_word_count:
        st.error("⚠️ Minimum word count must be less than maximum word count!")
    else:
        word_range = new_max_word_count - new_min_word_count
        st.info(f"✅ Content will be between {new_min_word_count} and {new_max_word_count} words (range: {word_range} words)")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Current settings display
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown("**📊 Current Settings:**")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.write(f"**Web Search:** {'✅ Enabled' if enable_web_search else '❌ Disabled'}")
    with col2:
        st.write(f"**Max Sources:** {max_research_sources}")
    with col3:
        st.write(f"**Min Words:** {min_word_count}")
    with col4:
        st.write(f"**Max Words:** {max_word_count}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Save button
    if st.button("💾 Save Agent Settings", type="primary", use_container_width=True):
        if new_min_word_count >= new_max_word_count:
            st.error("⚠️ Cannot save: Minimum word count must be less than maximum!")
        else:
            db.set_system_setting("enable_web_search", new_enable_web_search, "boolean", "Enable web search")
            db.set_system_setting("max_research_sources", new_max_research_sources, "integer", "Max research sources")
            db.set_system_setting("min_word_count", new_min_word_count, "integer", "Minimum word count for content")
            db.set_system_setting("max_word_count", new_max_word_count, "integer", "Maximum word count for content")
            st.success("✅ Agent settings saved successfully!")
            st.rerun()


def render_user_management(db):
    """Render user management interface."""
    st.markdown("### 👥 User Management")
    st.markdown("Manage user accounts, roles, and permissions.")
    
    # List users
    users = db.list_users()
    
    if users:
        st.markdown("#### 📋 Existing Users")
        
        for user in users:
            is_admin = user['role'] == 'admin'
            is_active = user.get('is_active', True)
            
            # User card
            card_class = "user-card admin" if is_admin else "user-card"
            st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
            
            # Header with username and role
            col_header1, col_header2 = st.columns([3, 1])
            with col_header1:
                role_icon = "👑" if is_admin else "👤"
                role_badge_class = "role-admin" if is_admin else "role-user"
                st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
                        <span style="font-size: 1.5rem;">{role_icon}</span>
                        <h4 style="margin: 0;">{user['username']}</h4>
                        <span class="role-badge {role_badge_class}">{user['role'].upper()}</span>
                        <span class="status-badge {'status-active' if is_active else 'status-inactive'}">
                            {'Active' if is_active else 'Inactive'}
                        </span>
                    </div>
                """, unsafe_allow_html=True)
            
            # User details
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**📧 Contact Information**")
                st.write(f"Email: {user.get('email', 'N/A')}")
            
            with col2:
                st.markdown("**📅 Account Information**")
                created = user.get('created_at', 'N/A')
                if created != 'N/A' and len(created) >= 10:
                    st.write(f"Created: {created[:10]}")
                else:
                    st.write(f"Created: N/A")
                
                last_login = user.get('last_login', None)
                if last_login:
                    st.write(f"Last Login: {last_login[:19] if len(last_login) >= 19 else last_login}")
                else:
                    st.write("Last Login: Never")
            
            with col3:
                st.markdown("**⚙️ Role Management**")
                new_role = st.selectbox(
                    "Change Role",
                    ["admin", "user"],
                    index=0 if is_admin else 1,
                    key=f"role_{user['id']}",
                    label_visibility="collapsed"
                )
                
                if new_role != user['role']:
                    if st.button(f"🔄 Update to {new_role.title()}", key=f"update_role_{user['id']}", use_container_width=True):
                        db.update_user_role(user['id'], new_role)
                        st.success(f"✅ Role updated to {new_role}!")
                        st.rerun()
                else:
                    st.info(f"Current role: {user['role']}")
            
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Create new user
    st.markdown("#### ➕ Create New User")
    st.markdown("Add a new user account to the system.")
    
    with st.form("create_user_form", clear_on_submit=True):
        st.markdown('<div class="setting-card">', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_username = st.text_input(
                "**Username** *",
                placeholder="Enter username",
                help="Unique username for the new user"
            )
            new_password = st.text_input(
                "**Password** *",
                type="password",
                placeholder="Enter password",
                help="Password for the new user account"
            )
        
        with col2:
            new_email = st.text_input(
                "**Email** (optional)",
                placeholder="user@example.com",
                help="Email address for the user (optional)"
            )
            new_role = st.selectbox(
                "**Role**",
                ["user", "admin"],
                index=0,
                help="User role: 'user' for regular access, 'admin' for full access"
            )
        
        st.caption("* Required fields")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.form_submit_button("✨ Create User", type="primary", use_container_width=True):
            if new_username and new_password:
                try:
                    db.create_user(new_username, new_password, new_role, new_email if new_email else None)
                    st.success(f"✅ User '{new_username}' created successfully as {new_role}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error creating user: {str(e)}")
            else:
                st.error("⚠️ Username and password are required.")

