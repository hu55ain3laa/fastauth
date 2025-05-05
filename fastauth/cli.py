"""
Command-line utilities for FastAuth management.
"""
import os
import sys
import re
import getpass
import argparse
import importlib.util
from typing import Optional, Dict
from pathlib import Path
from sqlmodel import Session, select

from fastauth.models.user import User, UserCreate
from fastauth.models.role import Role, RoleCreate
from fastauth.models.user import UserRole


def create_superadmin(auth_instance, username: Optional[str] = None, password: Optional[str] = None):
    """Create a superadmin user if one does not exist.
    
    Args:
        auth_instance: FastAuth instance
        username: Optional username (will prompt if not provided)
        password: Optional password (will prompt if not provided)
        
    Returns:
        dict: Information about the created or existing superadmin user
    """
    with Session(auth_instance.engine) as session:
        # Check if superadmin role exists
        superadmin_role = session.exec(
            select(Role).where(Role.name == "superadmin")
        ).first()
        
        if not superadmin_role:
            # Create superadmin role
            superadmin_role = Role(name="superadmin", description="Super administrator with all privileges")
            session.add(superadmin_role)
            session.commit()
            session.refresh(superadmin_role)
            print("Created 'superadmin' role")
        
        # Check if any user has the superadmin role
        admin_associations = session.exec(
            select(UserRole).where(UserRole.role_id == superadmin_role.id)
        ).all()
        
        if admin_associations:
            # Get the first superadmin user
            superadmin = session.get(User, admin_associations[0].user_id)
            print(f"Superadmin already exists: {superadmin.username}")
            # Extract user info before returning to avoid DetachedInstanceError
            return {
                "id": superadmin.id,
                "username": superadmin.username,
                "email": superadmin.email,
                "is_new": False
            }
            
        # Prompt for username if not provided
        if not username:
            username = input("Enter superadmin username [superadmin]: ").strip() or "superadmin"
            
        # Check if username already exists
        existing_user = session.exec(
            select(User).where(User.username == username)
        ).first()
        
        if existing_user:
            # User exists, make them a superadmin
            user = existing_user
            print(f"User '{username}' already exists. Assigning superadmin role.")
        else:
            # Prompt for password if not provided
            if not password:
                password = getpass.getpass("Enter superadmin password [admin123]: ") or "admin123"
                
            # Create new user
            hashed_password = auth_instance.get_password_hash(password)
            user = User(
                username=username,
                email=f"{username}@example.com",  # Default email
                hashed_password=hashed_password,
                disabled=False
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            print(f"Created new superadmin user: {username}")
            
        # Assign superadmin role if not already assigned
        existing_association = session.exec(
            select(UserRole).where(
                (UserRole.user_id == user.id) & (UserRole.role_id == superadmin_role.id)
            )
        ).first()
        
        if not existing_association:
            # Create the association
            user_role = UserRole(user_id=user.id, role_id=superadmin_role.id)
            session.add(user_role)
            session.commit()
            print(f"Assigned superadmin role to {username}")
        
        # Extract user info before returning to avoid DetachedInstanceError
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_new": True
        }


def initialize_roles(auth_instance):
    """Initialize standard roles in the database.
    
    Args:
        auth_instance: FastAuth instance
    """
    standard_roles = {
        "superadmin": "Super administrator with all privileges",
        "admin": "Administrator with management privileges",
        "moderator": "User with content moderation privileges",
        "premium": "Premium tier user",
        "verified": "Verified user",
        "user": "Standard user with basic privileges"
    }
    
    with Session(auth_instance.engine) as session:
        for role_name, description in standard_roles.items():
            existing_role = session.exec(
                select(Role).where(Role.name == role_name)
            ).first()
            
            if not existing_role:
                role = Role(name=role_name, description=description)
                session.add(role)
                print(f"Created role: {role_name}")
                
        session.commit()
        print("Roles initialized successfully")


def find_db_url_in_file(file_path):
    """Extract database URL from a Python file."""
    if not os.path.exists(file_path):
        return None
        
    with open(file_path, 'r') as file:
        content = file.read()
        
    # Look for common database URL patterns
    patterns = [
        r"DATABASE_URL\s*=\s*['\"]([^'\"]+)['\"]",
        r"db_url\s*=\s*['\"]([^'\"]+)['\"]",
        r"engine\s*=\s*create_engine\(['\"]([^'\"]+)['\"]",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            return match.group(1)
            
    return None


def find_secret_key_in_file(file_path):
    """Extract secret key from a Python file."""
    if not os.path.exists(file_path):
        return None
        
    with open(file_path, 'r') as file:
        content = file.read()
        
    # Look for common secret key patterns
    patterns = [
        r"SECRET_KEY\s*=\s*['\"]([^'\"]+)['\"]",
        r"secret_key\s*=\s*['\"]([^'\"]+)['\"]",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            return match.group(1)
            
    return None


def load_environment_variables():
    """Load environment variables from system and .env file if present.
    
    Returns:
        Dict[str, str]: Dictionary of environment variables
    """
    env_vars = {}
    
    # Copy system environment variables
    for key, value in os.environ.items():
        env_vars[key] = value
    
    # Check for .env file
    env_paths = [
        os.path.join(os.getcwd(), '.env'),
        os.path.join(os.path.dirname(os.getcwd()), '.env'),
    ]
    
    for env_path in env_paths:
        if os.path.exists(env_path):
            print(f"Found .env file at {env_path}")
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):  # Skip comments and empty lines
                        continue
                    
                    # Handle key=value format
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if (value.startswith("'") and value.endswith("'")) or \
                           (value.startswith('"') and value.endswith('"')):
                            value = value[1:-1]
                            
                        env_vars[key] = value
    
    return env_vars


def import_module_variables(file_path):
    """Dynamically import a Python module and extract its variables.
    
    Args:
        file_path: Path to the Python file to import
        
    Returns:
        dict: Dictionary of variables from the module
    """
    if not os.path.exists(file_path) or not file_path.endswith('.py'):
        return {}
    
    try:
        # Get the module name from the file path
        module_name = os.path.basename(file_path).replace('.py', '')
        
        # Create a spec for the module
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None:
            return {}
            
        # Create a module based on the spec
        module = importlib.util.module_from_spec(spec)
        
        # Execute the module
        spec.loader.exec_module(module)
        
        # Extract variables from the module
        variables = {}
        for name in dir(module):
            if not name.startswith('_'):  # Skip private/internal variables
                variables[name] = getattr(module, name)
                
        return variables
    except Exception as e:
        print(f"Error importing module {file_path}: {e}")
        return {}


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="FastAuth CLI utilities")
    # First positional argument is the app file
    parser.add_argument('app_file', nargs='?', help="Python application file to extract settings from")
    parser.add_argument('--db-url', help="Database URL (e.g., sqlite:///./app.db)")
    parser.add_argument('--secret-key', help="Secret key for JWT tokens")
    parser.add_argument('--init-db', action='store_true', help="Initialize database tables")
    parser.add_argument('--init-roles', action='store_true', help="Initialize standard roles")
    parser.add_argument('--create-superadmin', action='store_true', help="Create superadmin user")
    parser.add_argument('--username', help="Superadmin username (default: superadmin)")
    parser.add_argument('--password', help="Superadmin password (default: admin123)")
    
    args = parser.parse_args()
    
    # Import here to avoid circular imports
    from sqlmodel import create_engine, SQLModel
    from fastauth import FastAuth, User
    
    # Extract database URL and secret key from app file if provided
    db_url = args.db_url
    secret_key = args.secret_key
    
    # Try to load from environment variables first
    env_vars = load_environment_variables()
    if not db_url and "DATABASE_URL" in env_vars:
        db_url = env_vars["DATABASE_URL"]
        print(f"Found database URL from environment variable")
    if not secret_key and "SECRET_KEY" in env_vars:
        secret_key = env_vars["SECRET_KEY"]
        print(f"Found secret key from environment variable")
    
    # Get app file from positional argument
    app_file = args.app_file
    
    if app_file:
        print(f"Looking for settings in {app_file}...")
        app_path = os.path.abspath(app_file)
        
        # Get the directory containing the app file
        app_dir = os.path.dirname(app_path)
        
        # Check the app file itself first
        if not db_url:
            db_url = find_db_url_in_file(app_path)
            if db_url:
                print(f"Found database URL: {db_url}")
                
        if not secret_key:
            secret_key = find_secret_key_in_file(app_path)
            if secret_key:
                print(f"Found secret key in application file")
                
        # Try to import the app file to access variables like engine
        if (not db_url or not secret_key) and app_path.endswith('.py'):
            config_vars = import_module_variables(app_path)
            
            if not db_url and 'engine' in config_vars:
                # Try to extract URL from engine
                engine = config_vars['engine']
                if hasattr(engine, 'url'):
                    db_url = str(engine.url)
                    print(f"Found database URL from imported engine")
            
            if not db_url and 'DATABASE_URL' in config_vars:
                db_url = config_vars['DATABASE_URL']
                print(f"Found database URL from imported module")
                
            if not secret_key and 'SECRET_KEY' in config_vars:
                secret_key = config_vars['SECRET_KEY']
                print(f"Found secret key from imported module")
        
        # If we still don't have what we need, look for common config files
        if not db_url or not secret_key:
            common_files = [
                "config.py", 
                "settings.py", 
                "db.py", 
                "database.py",
                "models.py"
            ]
            
            for file_name in common_files:
                file_path = os.path.join(app_dir, file_name)
                if os.path.exists(file_path):
                    print(f"Checking {file_name} for settings...")
                    
                    if not db_url:
                        db_url = find_db_url_in_file(file_path)
                        if db_url:
                            print(f"Found database URL in {file_name}")
                    
                    if not secret_key:
                        secret_key = find_secret_key_in_file(file_path)
                        if secret_key:
                            print(f"Found secret key in {file_name}")
                    
                    # Try to import variables from this module too
                    if not db_url or not secret_key:
                        config_vars = import_module_variables(file_path)
                        
                        if not db_url and 'engine' in config_vars:
                            engine = config_vars['engine']
                            if hasattr(engine, 'url'):
                                db_url = str(engine.url)
                                print(f"Found database URL from imported engine in {file_name}")
                        
                        if not db_url and 'DATABASE_URL' in config_vars:
                            db_url = config_vars['DATABASE_URL']
                            print(f"Found database URL from {file_name}")
                            
                        if not secret_key and 'SECRET_KEY' in config_vars:
                            secret_key = config_vars['SECRET_KEY']
                            print(f"Found secret key from {file_name}")
                            
                    if db_url and secret_key:
                        break
    
    # Validate required settings
    if not db_url:
        print("Error: Database URL is required. Please provide it with --db-url or specify an app file")
        print("Tip: Make sure your database URL is defined in your app file, config.py, or as an environment variable (DATABASE_URL)")
        return 1
        
    if not secret_key:
        print("Error: Secret key is required. Please provide it with --secret-key or specify an app file")
        print("Tip: Make sure your secret key is defined in your app file, config.py, or as an environment variable (SECRET_KEY)")
        return 1
    
    # Create the engine and FastAuth instance
    print(f"Connecting to database: {db_url}")
    engine = create_engine(db_url)
    
    auth = FastAuth(
        secret_key=secret_key,
        engine=engine,
        user_model=User
    )
    
    # Process commands
    if args.init_db:
        print("Creating database tables...")
        SQLModel.metadata.create_all(engine)
        print("Database tables created successfully.")
    
    if args.init_roles:
        print("Initializing standard roles...")
        initialize_roles(auth)
        print("Roles initialized successfully.")
    
    if args.create_superadmin:
        print("Creating/verifying superadmin user...")
        user_info = create_superadmin(auth, username=args.username, password=args.password)
        print(f"Superadmin user '{user_info['username']}' is ready.")
    
    if not any([args.init_db, args.init_roles, args.create_superadmin]):
        # If no specific commands were given, do everything
        print("Initializing database, roles, and superadmin...")
        
        SQLModel.metadata.create_all(engine)
        print("Database tables created.")
        
        initialize_roles(auth)
        print("Standard roles initialized.")
        
        user_info = create_superadmin(auth, username=args.username, password=args.password)
        print(f"Superadmin user '{user_info['username']}' is ready.")
    
    print("\nInitialization completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
