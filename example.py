"""
Example FastAPI application using FastAuth for authentication.
Run with: uvicorn example:app --reload
"""
from fastapi import FastAPI, Depends
from sqlmodel import create_engine, SQLModel, Session
from User import User
from fastauth import FastAuth

# Create FastAPI app
app = FastAPI(title="FastAuth Example App")

# Database setup - using in-memory SQLite for demo
DATABASE_URL = "sqlite:///./example.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create tables on startup
def create_db_and_tables():
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

# Register startup event to create database tables
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Example protected route
@app.get("/protected", tags=["example"])
def protected_route(current_user = Depends(auth.get_current_active_user_dependency())):
    return {
        "message": f"Hello, {current_user.username}! This is a protected resource.",
        "user_info": {
            "username": current_user.username,
            "email": current_user.email,
            "active": not current_user.disabled
        }
    }

# Public route
@app.get("/", tags=["example"])
def home():
    return {
        "message": "Welcome to FastAuth Example App",
        "docs": "/docs",
        "available_endpoints": [
            "POST /token - Login and get tokens",
            "POST /token/refresh - Refresh access token",
            "POST /users - Register new user",
            "GET /users/me - Get current user info",
            "GET /protected - Example protected resource"
        ]
    }
