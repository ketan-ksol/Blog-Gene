#!/usr/bin/env python3
"""Initialize a fresh database with default entries."""
import os
import sys
from pathlib import Path
from database import get_database, BlogDatabase

def init_fresh_database():
    """Create a new database with default entries."""
    print("🗄️  Initializing fresh database...")
    
    # Check for DB_PATH environment variable (for Docker)
    db_path = os.getenv("DB_PATH", "blog_generator.db")
    
    # Remove existing database file if it exists
    if os.path.exists(db_path):
        print(f"⚠️  Removing existing database: {db_path}")
        try:
            os.remove(db_path)
            print(f"✅ Removed existing database")
        except Exception as e:
            print(f"❌ Error removing database: {e}")
            return False
    
    # Also check for database in data directory
    data_db_path = os.path.join("data", "blog_generator.db")
    if os.path.exists(data_db_path):
        print(f"⚠️  Removing existing database: {data_db_path}")
        try:
            os.remove(data_db_path)
            print(f"✅ Removed existing database from data directory")
        except Exception as e:
            print(f"⚠️  Could not remove {data_db_path}: {e}")
    
    # Create new database instance (this will automatically initialize)
    print(f"📦 Creating new database at: {db_path}")
    try:
        db = BlogDatabase(db_path)
        print("✅ Database created successfully!")
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False
    
    # Verify default settings
    print("\n📋 Verifying default system settings...")
    default_settings = {
        "model_name": "gpt-5",
        "temperature": 0.7,
        "enable_web_search": True,
        "max_research_sources": 10,
        "min_word_count": 500,
        "max_word_count": 1000,
    }
    
    all_correct = True
    for key, expected_value in default_settings.items():
        actual_value = db.get_system_setting(key)
        if actual_value == expected_value:
            print(f"  ✅ {key}: {actual_value}")
        else:
            print(f"  ❌ {key}: Expected {expected_value}, got {actual_value}")
            all_correct = False
    
    # Verify default users
    print("\n👥 Verifying default users...")
    users = db.list_users()
    admin_exists = any(u['username'] == 'admin' for u in users)
    user_exists = any(u['username'] == 'user' for u in users)
    
    if admin_exists:
        print("  ✅ Admin user exists")
    else:
        print("  ❌ Admin user not found")
        all_correct = False
    
    if user_exists:
        print("  ✅ Default user exists")
    else:
        print("  ⚠️  Default user not found (optional)")
    
    if all_correct:
        print("\n🎉 Database initialization complete! All default entries are in place.")
        print("\n📝 Default credentials:")
        print("   Admin: username='admin', password='admin123'")
        print("   User:  username='user', password='user123'")
        print("\n⚠️  Please change these passwords in production!")
        return True
    else:
        print("\n⚠️  Database created but some default entries may be missing.")
        return False

if __name__ == "__main__":
    success = init_fresh_database()
    sys.exit(0 if success else 1)

