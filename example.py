"""
Example FastAPI application using FastAuth for authentication.
Run with: uvicorn example:app --reload

This example shows both the legacy and recommended import methods.
"""
from fastapi import FastAPI, Depends
from sqlmodel import create_engine, SQLModel, Session

# Import directly from fastauth package
from fastauth import FastAuth, User

# The old direct import from fastauth.py still works but will issue a deprecation warning
# from fastauth import FastAuth  # from fastauth.py
# from User import User

# Create FastAPI app
app = FastAPI(title="FastAuth Example App")

# Database setup - using in-memory SQLite for demo
DATABASE_URL = "sqlite:///./example.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create tables on startup
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

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

# Include the auth router in your app
app.include_router(auth_router, tags=["authentication"])

# Protected route example - requires authentication
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

# Public route
@app.get("/", tags=["public"])
async def root():
    """
    This is a public route that doesn't require authentication.
    """
    return {"message": "Welcome to the FastAuth example app. Try /docs to see the API."}
