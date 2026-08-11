"""
Example FastAPI application using FastAuth for authentication and role-based authorization.
Run with: uv run fastapi dev example.py

This example demonstrates how to use FastAuth's authentication and role-based
authorization features with the minimal amount of setup code.
"""
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlmodel import Session, create_engine

from fastauth import FastAuth, User


# Database setup
DATABASE_URL = "sqlite:///./example.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


# Session dependency
def get_session():
    with Session(engine) as session:
        yield session


# Initialize FastAuth with your configuration
auth = FastAuth(
    secret_key="this-is-a-demo-secret-key-change-in-production",
    engine=engine,
    use_cookie=True,            # Also accept the token from an HTTP-only cookie
    token_url="/token",         # Login endpoint
    access_token_expires_in=30,   # minutes
    refresh_token_expires_in=7,   # days
)


# Initialize the database (tables, standard roles, superadmin) on startup.
# In production you can run this once with the CLI instead: fastauth example.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    auth.initialize_db(admin_username="superadmin", admin_password="admin123")
    yield


app = FastAPI(title="FastAuth Example App", lifespan=lifespan)

# One call wires up everything:
# POST /token, POST /token/refresh, POST /users, GET /users/me, POST /logout,
# the /roles/* management endpoints, and standardized error handling.
auth.setup(app, session_getter=get_session)


# Public route
@app.get("/", tags=["public"])
async def root():
    return {"message": "Welcome to the FastAuth example app. Try /docs to see the API."}


# Protected route - requires authentication only
@app.get("/protected", tags=["protected"])
async def protected_route(current_user: User = Depends(auth.current_user)):
    """The token can come from an HTTP-only cookie or an Authorization: Bearer header."""
    return {"message": "This is a protected route", "user": current_user.username}


# Admin-only route
@app.get("/admin", tags=["role-protected"])
async def admin_route(current_user: User = Depends(auth.is_admin())):
    return {"message": "This is an admin-only route", "user": current_user.username}


# Route requiring ANY of the listed roles
@app.get("/premium", tags=["role-protected"])
async def premium_route(current_user: User = Depends(auth.roles("premium", "admin"))):
    return {"message": "This is premium content", "user": current_user.username}


# Route requiring ALL of the listed roles
@app.get("/premium-verified", tags=["role-protected"])
async def premium_verified_route(
    current_user: User = Depends(auth.all_roles("premium", "verified")),
):
    return {"message": "This is premium verified content", "user": current_user.username}
