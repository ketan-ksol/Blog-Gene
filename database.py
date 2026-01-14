"""Database module for storing configurations and blog history."""
import sqlite3
import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path


class BlogDatabase:
    """Database manager for blog generator configurations and history."""
    
    def __init__(self, db_path: str = "data/blog_generator.db"):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        # Ensure directory exists and is writable
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Ensure the database directory exists and is writable."""
        db_dir = Path(self.db_path).parent
        if db_dir and not db_dir.exists():
            try:
                db_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                print(f"Warning: Could not create database directory {db_dir}: {e}")
        
        # If db_path is just a filename, use current directory
        if not Path(self.db_path).parent or Path(self.db_path).parent == Path('.'):
            # Use absolute path to avoid permission issues
            import os
            self.db_path = os.path.abspath(self.db_path)
    
    def _init_database(self):
        """Initialize database tables."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
        except sqlite3.OperationalError as e:
            # Try to create directory if it doesn't exist
            db_dir = Path(self.db_path).parent
            if db_dir and str(db_dir) != '.' and not db_dir.exists():
                db_dir.mkdir(parents=True, exist_ok=True)
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
            else:
                raise Exception(f"Unable to open database file at {self.db_path}. Error: {str(e)}. Please check file permissions and directory access.")
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        """)
        
        # Configuration table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS configurations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                config_data TEXT NOT NULL,
                is_default INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Blog history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blog_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                topic TEXT NOT NULL,
                output_file TEXT,
                metadata TEXT,
                config_used TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # System settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT NOT NULL,
                setting_type TEXT DEFAULT 'string',
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        
        # Initialize default system settings if not exists
        self._init_default_system_settings()
        
        # Initialize default admin user if not exists
        self._init_default_users()
    
    def _get_default_settings(self) -> Dict[str, tuple]:
        """Get default system settings dictionary.
        
        Returns:
            Dictionary mapping setting keys to (value, type, description) tuples
        """
        return {
            "model_name": ("gpt-5", "string", "OpenAI model to use"),
            "temperature": ("0.7", "float", "Model temperature (0.0-2.0)"),
            "enable_web_search": ("true", "boolean", "Enable web search for research"),
            "max_research_sources": ("10", "integer", "Maximum research sources to fetch"),
            "ssl_verify": ("true", "boolean", "SSL certificate verification"),
            "min_word_count": ("500", "integer", "Minimum word count for blog content"),
            "max_word_count": ("1000", "integer", "Maximum word count for blog content"),
        }
    
    def _init_default_system_settings(self):
        """Initialize default system settings."""
        self._ensure_default_settings()
    
    def _ensure_default_settings(self):
        """Ensure all default system settings exist in the database."""
        default_settings = self._get_default_settings()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for key, (value, value_type, description) in default_settings.items():
            # Check if setting exists
            cursor.execute("SELECT id FROM system_settings WHERE setting_key = ?", (key,))
            if not cursor.fetchone():
                # Setting doesn't exist, insert it
                cursor.execute("""
                    INSERT INTO system_settings (setting_key, setting_value, setting_type, description)
                    VALUES (?, ?, ?, ?)
                """, (key, value, value_type, description))
        
        conn.commit()
        conn.close()
    
    def _init_default_users(self):
        """Initialize default admin and user accounts if not exists."""
        import hashlib
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if admin user exists
        cursor.execute("SELECT id FROM users WHERE username = ?", ("admin",))
        if not cursor.fetchone():
            # Default admin password: admin123 (should be changed in production)
            password_hash = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("""
                INSERT INTO users (username, password_hash, role, email, is_active)
                VALUES (?, ?, ?, ?, ?)
            """, ("admin", password_hash, "admin", "admin@example.com", 1))
        
        # Check if default user exists
        cursor.execute("SELECT id FROM users WHERE username = ?", ("user",))
        if not cursor.fetchone():
            # Default user password: user123 (should be changed in production)
            password_hash = hashlib.sha256("user123".encode()).hexdigest()
            cursor.execute("""
                INSERT INTO users (username, password_hash, role, email, is_active)
                VALUES (?, ?, ?, ?, ?)
            """, ("user", password_hash, "user", "user@example.com", 1))
        
        conn.commit()
        conn.close()
    
    def save_configuration(self, name: str, config: Dict[str, Any], is_default: bool = False) -> int:
        """Save a configuration.
        
        Args:
            name: Configuration name
            config: Configuration dictionary
            is_default: Whether this is the default configuration
        
        Returns:
            Configuration ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        config_json = json.dumps(config)
        
        cursor.execute("""
            INSERT OR REPLACE INTO configurations (name, config_data, is_default, updated_at)
            VALUES (?, ?, ?, ?)
        """, (name, config_json, 1 if is_default else 0, datetime.now().isoformat()))
        
        # If this is set as default, unset other defaults
        if is_default:
            cursor.execute("""
                UPDATE configurations SET is_default = 0 WHERE name != ?
            """, (name,))
        
        config_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return config_id
    
    def get_configuration(self, name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get a configuration by name, or default if name is None.
        
        Args:
            name: Configuration name, or None for default
        
        Returns:
            Configuration dictionary or None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if name:
            cursor.execute("SELECT config_data FROM configurations WHERE name = ?", (name,))
        else:
            cursor.execute("SELECT config_data FROM configurations WHERE is_default = 1 LIMIT 1")
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return json.loads(row[0])
        return None
    
    def list_configurations(self) -> List[Dict[str, Any]]:
        """List all configurations.
        
        Returns:
            List of configuration dictionaries with metadata
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, config_data, is_default, created_at, updated_at
            FROM configurations
            ORDER BY is_default DESC, updated_at DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "name": row[1],
                "config": json.loads(row[2]),
                "is_default": bool(row[3]),
                "created_at": row[4],
                "updated_at": row[5]
            }
            for row in rows
        ]
    
    def delete_configuration(self, name: str) -> bool:
        """Delete a configuration.
        
        Args:
            name: Configuration name
        
        Returns:
            True if deleted, False if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM configurations WHERE name = ?", (name,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    def get_system_setting(self, key: str, default: Any = None) -> Any:
        """Get a system setting value.
        
        Args:
            key: Setting key
            default: Default value if not found
        
        Returns:
            Setting value (converted to appropriate type)
        """
        # Ensure defaults exist (in case database was created before defaults were added)
        self._ensure_default_settings()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT setting_value, setting_type FROM system_settings WHERE setting_key = ?
        """, (key,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return default
        
        value, value_type = row
        
        # Handle None or empty values
        if value is None:
            return default
        
        # Convert to appropriate type
        if value_type == "boolean":
            # Handle string representations of booleans
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes", "on")
            # Handle actual boolean values (shouldn't happen but be safe)
            return bool(value)
        elif value_type == "integer":
            return int(value)
        elif value_type == "float":
            return float(value)
        elif value_type == "list":
            return json.loads(value)
        else:
            return value
    
    def set_system_setting(self, key: str, value: Any, value_type: str = "string", description: Optional[str] = None):
        """Set a system setting.
        
        Args:
            key: Setting key
            value: Setting value
            value_type: Type of value (string, integer, float, boolean, list)
            description: Optional description
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convert value to string for storage
        if value_type == "list":
            value_str = json.dumps(value)
        elif value_type == "boolean":
            # Store boolean as lowercase "true" or "false" string
            value_str = "true" if bool(value) else "false"
        else:
            value_str = str(value)
        
        cursor.execute("""
            INSERT OR REPLACE INTO system_settings (setting_key, setting_value, setting_type, description, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (key, value_str, value_type, description, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_all_system_settings(self) -> Dict[str, Any]:
        """Get all system settings.
        
        Returns:
            Dictionary of all system settings
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT setting_key, setting_value, setting_type FROM system_settings
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        settings = {}
        for key, value, value_type in rows:
            if value is None:
                continue  # Skip None values
            if value_type == "boolean":
                # Handle string representations of booleans
                if isinstance(value, str):
                    settings[key] = value.lower() in ("true", "1", "yes", "on")
                else:
                    settings[key] = bool(value)
            elif value_type == "integer":
                settings[key] = int(value)
            elif value_type == "float":
                settings[key] = float(value)
            elif value_type == "list":
                settings[key] = json.loads(value)
            else:
                settings[key] = value
        
        return settings
    
    def save_blog_history(self, topic: str, output_file: str, metadata: Dict[str, Any], config_used: Dict[str, Any], user_id: Optional[int] = None) -> int:
        """Save blog generation history.
        
        Args:
            topic: Blog topic
            output_file: Path to output file
            metadata: Blog metadata
            config_used: Configuration used for generation
            user_id: Optional user ID who generated the blog
        
        Returns:
            History record ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO blog_history (user_id, topic, output_file, metadata, config_used)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, topic, output_file, json.dumps(metadata), json.dumps(config_used)))
        
        history_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return history_id
    
    def get_blog_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get blog generation history.
        
        Args:
            limit: Maximum number of records to return
        
        Returns:
            List of blog history records
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, topic, output_file, metadata, config_used, created_at
            FROM blog_history
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "topic": row[1],
                "output_file": row[2],
                "metadata": json.loads(row[3]),
                "config_used": json.loads(row[4]),
                "created_at": row[5]
            }
            for row in rows
        ]
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user.
        
        Args:
            username: Username
            password: Plain text password
        
        Returns:
            User dictionary if authenticated, None otherwise
        """
        import hashlib
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute("""
            SELECT id, username, role, email, is_active
            FROM users
            WHERE username = ? AND password_hash = ? AND is_active = 1
        """, (username, password_hash))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            # Update last login
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users SET last_login = ? WHERE id = ?
            """, (datetime.now().isoformat(), row[0]))
            conn.commit()
            conn.close()
            
            return {
                "id": row[0],
                "username": row[1],
                "role": row[2],
                "email": row[3],
                "is_active": bool(row[4])
            }
        
        return None
    
    def create_user(self, username: str, password: str, role: str = "user", email: Optional[str] = None) -> int:
        """Create a new user.
        
        Args:
            username: Username
            password: Plain text password
            role: User role (admin or user)
            email: Optional email
        
        Returns:
            User ID
        """
        import hashlib
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute("""
            INSERT INTO users (username, password_hash, role, email, is_active)
            VALUES (?, ?, ?, ?, ?)
        """, (username, password_hash, role, email, 1))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return user_id
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID.
        
        Args:
            user_id: User ID
        
        Returns:
            User dictionary or None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, role, email, is_active, created_at, last_login
            FROM users
            WHERE id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row[0],
                "username": row[1],
                "role": row[2],
                "email": row[3],
                "is_active": bool(row[4]),
                "created_at": row[5],
                "last_login": row[6]
            }
        
        return None
    
    def list_users(self) -> List[Dict[str, Any]]:
        """List all users.
        
        Returns:
            List of user dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, role, email, is_active, created_at, last_login
            FROM users
            ORDER BY created_at DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "id": row[0],
                "username": row[1],
                "role": row[2],
                "email": row[3],
                "is_active": bool(row[4]),
                "created_at": row[5],
                "last_login": row[6]
            }
            for row in rows
        ]
    
    def update_user_role(self, user_id: int, role: str) -> bool:
        """Update user role.
        
        Args:
            user_id: User ID
            role: New role (admin or user)
        
        Returns:
            True if updated, False if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users SET role = ? WHERE id = ?
        """, (role, user_id))
        
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return updated


# Global database instance
_db_instance: Optional[BlogDatabase] = None


def get_database() -> BlogDatabase:
    """Get global database instance."""
    global _db_instance
    if _db_instance is None:
        # Check for DB_PATH environment variable (for Docker)
        # Default to data directory for consistency between local and Docker
        db_path = os.getenv("DB_PATH", "data/blog_generator.db")
        _db_instance = BlogDatabase(db_path)
        # Ensure defaults exist (in case database was created before defaults were added)
        _db_instance._ensure_default_settings()
    return _db_instance

