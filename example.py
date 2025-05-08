"""
Example FastAPI application using FastAuth for authentication and role-based authorization.
Run with: uvicorn example:app --reload

This example demonstrates how to use FastAuth's authentication and role-based authorization features.
"""
from fastapi import FastAPI, Depends, HTTPException, status
from sqlmodel import create_engine, SQLModel, Session

# Import directly from fastauth package
from fastauth import (
    FastAuth, User, Role, RoleCreate, UserRole,
    # New in v0.3.4: Custom exception classes
    CredentialsException, TokenException, UserNotFoundException, PermissionDeniedException
)

# The old direct import from fastauth.py still works but will issue a deprecation warning
# from fastauth import FastAuth  # from fastauth.py
# from User import User

# Create FastAPI app
app = FastAPI(title="FastAuth Example App")

# Database setup - using in-memory SQLite for demo
DATABASE_URL = "sqlite:///./example.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# There are two ways to initialize the database in FastAuth:
# 1. Using the CLI tool before starting the application:
#    fastauth example.py                  # Auto-detect settings from this file
#    # Or with explicit parameters
#    fastauth --db-url="sqlite:///./example.db" --secret-key="your-secret-key"
#
# 2. Programmatically during application startup (shown below)

# Set this to True to initialize the database during startup
# In production, you might want to use the CLI tool instead
INIT_DB_ON_STARTUP = True

@app.on_event("startup")
def on_startup():
    if INIT_DB_ON_STARTUP:
        # Initialize database with tables, roles, and superadmin
        print("Initializing database during startup...")
        result = auth.initialize_db(
            create_tables=True,         # Create database tables
            init_roles=True,            # Initialize standard roles
            create_admin=True,          # Create superadmin if doesn't exist
            admin_username="superadmin", # Default username
            admin_password="admin123"    # Default password
        )
        
        print("Database initialization results:")
        for key, value in result.items():
            print(f"  {key}: {value}")
    else:
        # Just make sure tables exist
        SQLModel.metadata.create_all(engine)
        print("Application started. Database checked.")
        print("Note: Use the CLI tool to initialize roles and superadmin:")
        print("python fastauth_init.py --db-url=\"sqlite:///./example.db\" --secret-key=\"your-secret-key\"")



# Session dependency
def get_session():
    with Session(engine) as session:
        yield session

# Initialize FastAuth with your configuration
auth = FastAuth(
    secret_key="this-is-a-demo-secret-key-change-in-production",
    algorithm="HS256",
    user_model=User,
    engine=engine,
    use_cookie=True,         # Enable cookie-based authentication
    token_url="/token",      # Login endpoint
    access_token_expires_in=30,  # 30 minutes
    refresh_token_expires_in=7   # 7 days
)

# Get pre-configured auth router (includes login, refresh, register, and user info endpoints)
auth_router = auth.get_auth_router(get_session)

# Get pre-configured role router (includes role management endpoints)
role_router = auth.get_role_router()

# Include the routers in your app
app.include_router(auth_router, tags=["authentication"])
app.include_router(role_router, tags=["roles"])

# Set up the standardized error handlers (new in v0.3.4)
auth.setup_exception_handlers(app)

# Protected route example - requires authentication only
@app.get("/protected", tags=["protected"])
async def protected_route(current_user = Depends(auth.get_current_active_user_dependency())):
    """
    This route is protected and requires a valid JWT token.
    The token can be provided via:
    1. Cookie (if use_cookie=True)
    2. Authorization header with Bearer scheme
    """
    return {
        "message": "This is a protected route",
        "user": current_user.username
    }

# Admin-only route example
@app.get("/admin", tags=["role-protected"])
async def admin_route(
    current_user = Depends(auth.is_admin()), 
    session: Session = Depends(get_session)
):
    """
    This route requires the user to have the 'admin' role.
    """
    return {
        "message": "This is an admin-only route",
        "user": current_user.username
    }

# Route requiring any of the specified roles
@app.get("/premium", tags=["role-protected"])
async def premium_route(
    current_user = Depends(auth.require_roles(["premium", "admin"])),
    session: Session = Depends(get_session)
):
    """
    This route requires the user to have EITHER the 'premium' OR 'admin' role.
    """
    return {
        "message": "This is premium content",
        "user": current_user.username
    }

# Route requiring all specified roles
@app.get("/premium-verified", tags=["role-protected"])
async def premium_verified_route(
    current_user = Depends(auth.require_all_roles(["premium", "verified"])),
    session: Session = Depends(get_session)
):
    """
    This route requires the user to have BOTH the 'premium' AND 'verified' roles.
    """
    return {
        "message": "This is premium verified content",
        "user": current_user.username
    }

# Public route
@app.get("/", tags=["public"])
async def root():
    """
    This is a public route that doesn't require authentication.
    """
    return {"message": "Welcome to the FastAuth example app. Try /docs to see the API."}

# Example routes demonstrating the new error handling (v0.3.4)
@app.get("/error/credentials", tags=["error-examples"])
async def credentials_error():
    """
    This route demonstrates how to use the CredentialsException.
    """
    raise CredentialsException("Example of credentials error")

@app.get("/error/token", tags=["error-examples"])
async def token_error():
    """
    This route demonstrates how to use the TokenException.
    """
    raise TokenException("Example of token error")

@app.get("/error/user-not-found", tags=["error-examples"])
async def user_not_found_error():
    """
    This route demonstrates how to use the UserNotFoundException.
    """
    raise UserNotFoundException("Example of user not found error")

@app.get("/error/permission", tags=["error-examples"])
async def permission_error():
    """
    This route demonstrates how to use the PermissionDeniedException.
    """
    raise PermissionDeniedException("Example of permission denied error")

# Utility endpoint to create roles and assign them to users
@app.post("/setup-roles", tags=["setup"])
async def setup_roles(session: Session = Depends(get_session)):
    """
    This utility endpoint creates common roles and assigns the admin role to the first user.
    In a real application, you would handle role creation and assignment differently.
    """
    # Create the role manager
    role_manager = auth.role_dependencies.get_role_manager()(db=session)
    
    # Create roles if they don't exist
    roles = {
        "admin": "Administrator with full privileges",
        "moderator": "Can moderate content",
        "premium": "Premium tier user",
        "verified": "Verified account",
        "user": "Standard user"
    }
    
    created_roles = []
    for role_name, description in roles.items():
        existing_role = role_manager.get_role(role_name=role_name)
        if not existing_role:
            role = role_manager.create_role(RoleCreate(name=role_name, description=description))
            created_roles.append({"name": role.name, "id": role.id})
    
    # Assign admin role to the first user (if any users exist)
    from sqlmodel import select
    first_user = session.exec(select(User)).first()
    if first_user:
        admin_role = role_manager.get_role(role_name="admin")
        if admin_role:
            try:
                assigned = role_manager.assign_role_to_user(first_user.id, admin_role.id)
                if assigned:
                    created_roles.append({"user": first_user.username, "assigned_role": admin_role.name})
            except HTTPException:
                # User already has this role
                pass
    
    return {
        "message": "Roles created and assigned",
        "created": created_roles
    }
