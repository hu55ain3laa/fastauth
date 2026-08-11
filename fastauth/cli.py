"""
Command-line utilities for FastAuth management.
"""
import argparse
import getpass
import importlib.util
import os
import re
import sys
from typing import Optional

from sqlmodel import Session, select

from fastauth.models.role import Role
from fastauth.models.user import UserRole

STANDARD_ROLES = {
    "superadmin": "Super administrator with all privileges",
    "admin": "Administrator with management privileges",
    "moderator": "User with content moderation privileges",
    "premium": "Premium tier user",
    "verified": "Verified user",
    "user": "Standard user with basic privileges",
}


def create_superadmin(auth_instance, username: Optional[str] = None, password: Optional[str] = None):
    """Create a superadmin user if one does not exist.

    Args:
        auth_instance: FastAuth instance
        username: Optional username (will prompt if not provided)
        password: Optional password (will prompt if not provided)

    Returns:
        dict: Information about the created or existing superadmin user
    """
    user_model = auth_instance.user_model

    with Session(auth_instance.engine) as session:
        superadmin_role = session.exec(
            select(Role).where(Role.name == "superadmin")
        ).first()

        if not superadmin_role:
            superadmin_role = Role(
                name="superadmin", description="Super administrator with all privileges"
            )
            session.add(superadmin_role)
            session.commit()
            session.refresh(superadmin_role)
            print("Created 'superadmin' role")

        # If any user already has the superadmin role, we're done
        admin_association = session.exec(
            select(UserRole).where(UserRole.role_id == superadmin_role.id)
        ).first()

        if admin_association:
            superadmin = session.get(user_model, admin_association.user_id)
            print(f"Superadmin already exists: {superadmin.username}")
            return {
                "id": superadmin.id,
                "username": superadmin.username,
                "email": superadmin.email,
                "is_new": False,
            }

        if getattr(auth_instance, "production", False):
            if not password:
                raise ValueError(
                    "In production, pass an explicit superadmin password "
                    "(create_superadmin(username=..., password=...))."
                )
            if password == "admin123":
                raise ValueError(
                    "Refusing to use the default password 'admin123' in production. "
                    "Choose a strong superadmin password."
                )

        if not username:
            username = input("Enter superadmin username [superadmin]: ").strip() or "superadmin"

        existing_user = session.exec(
            select(user_model).where(user_model.username == username)
        ).first()

        if existing_user:
            user = existing_user
            is_new = False
            print(f"User '{username}' already exists. Assigning superadmin role.")
        else:
            if not password:
                password = getpass.getpass("Enter superadmin password [admin123]: ") or "admin123"
                if password == "admin123":
                    print("WARNING: using the default password 'admin123' — change it in production!")

            user = user_model(
                username=username,
                email=f"{username}@example.com",  # Default email
                hashed_password=auth_instance.get_password_hash(password),
                disabled=False,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            is_new = True
            print(f"Created new superadmin user: {username}")

        existing_association = session.exec(
            select(UserRole).where(
                (UserRole.user_id == user.id) & (UserRole.role_id == superadmin_role.id)
            )
        ).first()

        if not existing_association:
            session.add(UserRole(user_id=user.id, role_id=superadmin_role.id))
            session.commit()
            print(f"Assigned superadmin role to {username}")

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_new": is_new,
        }


def initialize_roles(auth_instance):
    """Initialize standard roles in the database.

    Args:
        auth_instance: FastAuth instance
    """
    with Session(auth_instance.engine) as session:
        for role_name, description in STANDARD_ROLES.items():
            existing_role = session.exec(
                select(Role).where(Role.name == role_name)
            ).first()

            if not existing_role:
                session.add(Role(name=role_name, description=description))
                print(f"Created role: {role_name}")

        session.commit()
        print("Roles initialized successfully")


def _find_in_file(file_path: str, patterns) -> Optional[str]:
    """Return the first regex group matched by any pattern in a file."""
    if not os.path.exists(file_path):
        return None

    with open(file_path, "r") as file:
        content = file.read()

    for pattern in patterns:
        # MULTILINE so the end-of-value anchors match per line, not per file.
        match = re.search(pattern, content, re.MULTILINE)
        if match:
            return match.group(1)

    return None


# Each pattern requires the string literal to be the *complete* value: either
# the end of the assignment, or the whole first argument. Without that, a
# concatenated expression like
#     create_engine("sqlite:///" + name)
# matches and yields "sqlite:///" — a URL that looks plausible and points
# nowhere. Refusing to match lets the module-import fallback evaluate the
# expression properly instead.
_END_OF_VALUE = r"\s*(?:#.*)?$"

DB_URL_PATTERNS = [
    r"DATABASE_URL\s*=\s*['\"]([^'\"]+)['\"]" + _END_OF_VALUE,
    r"db_url\s*=\s*['\"]([^'\"]+)['\"]" + _END_OF_VALUE,
    r"engine\s*=\s*create_engine\(\s*['\"]([^'\"]+)['\"]\s*[,)]",
]

SECRET_KEY_PATTERNS = [
    r"SECRET_KEY\s*=\s*['\"]([^'\"]+)['\"]" + _END_OF_VALUE,
    r"secret_key\s*=\s*['\"]([^'\"]+)['\"]" + _END_OF_VALUE,
]


def load_environment_variables():
    """Load environment variables from the system and a .env file if present.

    The real environment always wins. A .env file only fills in what is not
    already set, matching how dotenv tooling behaves everywhere else — and,
    more importantly, so that a stale .env left in a deployed image cannot
    silently override the SECRET_KEY the environment provides. Signing tokens
    with the wrong key fails in ways that are very hard to trace back here.

    Returns:
        dict: Dictionary of environment variables
    """
    env_vars = dict(os.environ)

    env_paths = [
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.path.dirname(os.getcwd()), ".env"),
    ]

    for env_path in env_paths:
        if not os.path.exists(env_path):
            continue
        print(f"Found .env file at {env_path}")
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                if key in os.environ:
                    continue  # the deployed environment takes precedence
                env_vars[key] = value.strip().strip("'\"")

    return env_vars


def import_module_variables(file_path: str) -> dict:
    """Dynamically import a Python module and extract its variables.

    Args:
        file_path: Path to the Python file to import

    Returns:
        dict: Dictionary of variables from the module
    """
    if not os.path.exists(file_path) or not file_path.endswith(".py"):
        return {}

    try:
        module_name = os.path.basename(file_path).replace(".py", "")
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            return {}

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        return {
            name: getattr(module, name)
            for name in dir(module)
            if not name.startswith("_")
        }
    except Exception as e:
        print(f"Error importing module {file_path}: {e}")
        return {}


def _settings_from_file(file_path: str, db_url: Optional[str], secret_key: Optional[str]):
    """Try to fill in missing settings from one Python file.

    Checks regex patterns first, then imports the module and inspects its
    variables (engine objects, DATABASE_URL, SECRET_KEY).

    Returns:
        tuple: (db_url, secret_key) with any newly discovered values
    """
    if not db_url:
        db_url = _find_in_file(file_path, DB_URL_PATTERNS)
        if db_url:
            print(f"Found database URL in {os.path.basename(file_path)}")

    if not secret_key:
        secret_key = _find_in_file(file_path, SECRET_KEY_PATTERNS)
        if secret_key:
            print(f"Found secret key in {os.path.basename(file_path)}")

    if not db_url or not secret_key:
        config_vars = import_module_variables(file_path)

        if not db_url:
            engine = config_vars.get("engine")
            if engine is not None and hasattr(engine, "url"):
                db_url = str(engine.url)
                print(f"Found database URL from engine in {os.path.basename(file_path)}")
            elif "DATABASE_URL" in config_vars:
                db_url = config_vars["DATABASE_URL"]
                print(f"Found database URL in {os.path.basename(file_path)}")

        if not secret_key and "SECRET_KEY" in config_vars:
            secret_key = config_vars["SECRET_KEY"]
            print(f"Found secret key in {os.path.basename(file_path)}")

    return db_url, secret_key


def discover_settings(app_file: Optional[str], db_url: Optional[str], secret_key: Optional[str]):
    """Discover database URL and secret key from the environment and app files.

    Args:
        app_file: Optional path to the application file to inspect
        db_url: Already-known database URL (kept if set)
        secret_key: Already-known secret key (kept if set)

    Returns:
        tuple: (db_url, secret_key), either value may still be None
    """
    env_vars = load_environment_variables()
    if not db_url and "DATABASE_URL" in env_vars:
        db_url = env_vars["DATABASE_URL"]
        print("Found database URL from environment variable")
    if not secret_key and "SECRET_KEY" in env_vars:
        secret_key = env_vars["SECRET_KEY"]
        print("Found secret key from environment variable")

    if not app_file:
        return db_url, secret_key

    print(f"Looking for settings in {app_file}...")
    app_path = os.path.abspath(app_file)
    app_dir = os.path.dirname(app_path)

    candidate_files = [app_path] + [
        os.path.join(app_dir, name)
        for name in ("config.py", "settings.py", "db.py", "database.py", "models.py")
    ]

    for file_path in candidate_files:
        if db_url and secret_key:
            break
        if os.path.exists(file_path):
            db_url, secret_key = _settings_from_file(file_path, db_url, secret_key)

    return db_url, secret_key


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="FastAuth CLI utilities")
    parser.add_argument("app_file", nargs="?", help="Python application file to extract settings from")
    parser.add_argument("--db-url", help="Database URL (e.g., sqlite:///./app.db)")
    parser.add_argument("--secret-key", help="Secret key for JWT tokens")
    parser.add_argument("--init-db", action="store_true", help="Initialize database tables")
    parser.add_argument("--init-roles", action="store_true", help="Initialize standard roles")
    parser.add_argument("--create-superadmin", action="store_true", help="Create superadmin user")
    parser.add_argument("--username", help="Superadmin username (default: superadmin)")
    parser.add_argument("--password", help="Superadmin password")

    args = parser.parse_args()

    # Import here to avoid circular imports
    from sqlmodel import create_engine, SQLModel
    from fastauth import FastAuth, User

    db_url, secret_key = discover_settings(args.app_file, args.db_url, args.secret_key)

    if not db_url:
        print("Error: Database URL is required. Please provide it with --db-url or specify an app file")
        print("Tip: Make sure your database URL is defined in your app file, config.py, or as an environment variable (DATABASE_URL)")
        return 1

    if not secret_key:
        print("Error: Secret key is required. Please provide it with --secret-key or specify an app file")
        print("Tip: Make sure your secret key is defined in your app file, config.py, or as an environment variable (SECRET_KEY)")
        return 1

    print(f"Connecting to database: {db_url}")
    engine = create_engine(db_url)

    auth = FastAuth(secret_key=secret_key, engine=engine, user_model=User)

    run_all = not any([args.init_db, args.init_roles, args.create_superadmin])
    if run_all:
        print("Initializing database, roles, and superadmin...")

    if args.init_db or run_all:
        print("Creating database tables...")
        SQLModel.metadata.create_all(engine)
        print("Database tables created successfully.")

    if args.init_roles or run_all:
        print("Initializing standard roles...")
        initialize_roles(auth)

    if args.create_superadmin or run_all:
        print("Creating/verifying superadmin user...")
        user_info = create_superadmin(auth, username=args.username, password=args.password)
        print(f"Superadmin user '{user_info['username']}' is ready.")

    print("\nInitialization completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
