from typing import Optional, Callable, Type, Dict, Any, Union, List
from fastapi import Depends, HTTPException, status, Request, Response, APIRouter, FastAPI
from fastapi.security import OAuth2PasswordBearer, OAuth2, OAuth2PasswordRequestForm
from sqlmodel import SQLModel, Session, select
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security.utils import get_authorization_scheme_param
from starlette.status import HTTP_401_UNAUTHORIZED

from fastauth.security.password import PasswordManager
from fastauth.security.tokens import TokenManager
from fastauth.dependencies.auth import AuthDependencies
from fastauth.dependencies.roles import RoleDependencies
from fastauth.routers.auth import AuthRouter
from fastauth.routers.roles import RoleRouter
from fastauth.models.user import User, UserRole
from fastauth.models.role import Role, RoleCreate
from fastauth.models.tokens import Token, TokenData
from fastauth.cli import create_superadmin, initialize_roles
from fastauth.exceptions import FastAuthException, setup_exception_handlers


class OAuth2PasswordBearerWithCookie(OAuth2):
    """OAuth2 password bearer authentication with cookie support."""
    
    def __init__(
        self,
        tokenUrl: str,
        scheme_name: Optional[str] = None,
        scopes: Optional[Dict[str, str]] = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        # Try to get token from cookie first
        token = request.cookies.get("access_token")
        
        # If no token in cookie, fall back to Authorization header
        if not token:
            authorization = request.headers.get("Authorization")
            scheme, param = get_authorization_scheme_param(authorization)
            if not authorization or scheme.lower() != "bearer":
                if self.auto_error:
                    raise HTTPException(
                        status_code=HTTP_401_UNAUTHORIZED,
                        detail="Not authenticated",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                else:
                    return None
            token = param
            
        # Don't return None when token exists but is empty
        if not token and self.auto_error:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return token


class FastAuth:
    """FastAuth is a comprehensive authentication library for FastAPI applications.
    
    It provides JWT-based authentication with both cookie and bearer token support,
    password hashing, token management, and integration with SQLModel for database operations.
    """
    
    def __init__(
        self, 
        secret_key: str, 
        engine: SQLModel, 
        algorithm: str = "HS256", 
        use_cookie: bool = True, 
        token_url: str = "token", 
        access_token_expires_in: int = 30, 
        refresh_token_expires_in: int = 7, 
        user_model: Type[SQLModel] = User
    ):
        """Initialize the FastAuth instance.
        
        Args:
            secret_key: Secret key for JWT encoding/decoding
            engine: SQLModel engine for database operations
            algorithm: Algorithm for JWT signing
            use_cookie: Enable cookie-based authentication
            token_url: URL for token endpoint
            access_token_expires_in: Access token expiration in minutes
            refresh_token_expires_in: Refresh token expiration in days
            user_model: User model class for database operations
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.user_model = user_model
        self.engine = engine
        self.session = Session(engine)
        self.use_cookie = use_cookie
        self.access_token_expires_in = access_token_expires_in
        self.refresh_token_expires_in = refresh_token_expires_in
        
        # Initialize specialized components
        self.token_manager = TokenManager(
            secret_key=secret_key,
            algorithm=algorithm,
            access_token_expires_minutes=access_token_expires_in,
            refresh_token_expires_days=refresh_token_expires_in
        )
        
        self.password_manager = PasswordManager()
        
        # Choose the appropriate authentication scheme based on use_cookie flag
        if use_cookie:
            self.oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl=token_url)
        else:
            self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl=token_url)
            
        # Setup dependencies and routers
        self.dependencies = AuthDependencies(self)
        self.router = AuthRouter(self)
        
        # Initialize role dependencies after auth dependencies
        self.role_dependencies = RoleDependencies(self.dependencies)
        self.role_router = RoleRouter(self.role_dependencies)

    def get_user(self, session: Session, username: str):
        """Get a user from the database by username.
        
        Args:
            session: The database session
            username: The username to look up
            
        Returns:
            User: The user object if found, None otherwise
        """
        return session.exec(select(self.user_model).where(self.user_model.username == username)).first()
    
    def authenticate_user(self, username: str, password: str):
        """Authenticate a user by username and password.
        
        Args:
            username: The username to authenticate
            password: The password to verify
            
        Returns:
            User: The user object if authentication succeeds, False otherwise
        """
        user = self.get_user(self.session, username)
        if not user:
            return False
        if not self.password_manager.verify_password(password, user.hashed_password):
            return False
        return user
        
    def verify_password(self, plain_password, hashed_password):
        """Verify a plain password against a hashed password.
        
        Args:
            plain_password: The plain text password to verify
            hashed_password: The hashed password to compare against
            
        Returns:
            bool: True if the password matches, False otherwise
        """
        return self.password_manager.verify_password(plain_password, hashed_password)
        
    def get_password_hash(self, password):
        """Hash a password using configured algorithms.
        
        Args:
            password: The plain text password to hash
            
        Returns:
            str: The hashed password
        """
        return self.password_manager.get_password_hash(password)
        
    def create_access_token(self, data: dict, expires_delta: Optional[Any] = None):
        """Create a JWT access token.
        
        Args:
            data: The data to encode in the token
            expires_delta: Optional custom expiration time
            
        Returns:
            str: The encoded JWT token
        """
        return self.token_manager.create_access_token(data, expires_delta)
        
    def create_refresh_token(self, data: dict, expires_delta: Optional[Any] = None):
        """Create a JWT refresh token with longer expiration.
        
        Args:
            data: The data to encode in the token
            expires_delta: Optional custom expiration time
            
        Returns:
            str: The encoded JWT refresh token
        """
        return self.token_manager.create_refresh_token(data, expires_delta)
        
    def get_current_user_dependency(self):
        """Get a FastAPI dependency for current user authentication.
        
        Returns:
            callable: A dependency that extracts and validates the JWT token
        """
        return self.dependencies.get_current_user()
        
    def get_current_active_user_dependency(self):
        """Get a FastAPI dependency for active user authentication.
        
        Returns:
            callable: A dependency that validates the user is active
        """
        return self.dependencies.get_current_active_user()
        
    def get_auth_router(self, session_getter=None):
        """Get a router with authentication endpoints.
        
        Args:
            session_getter: Function that returns a database session
            
        Returns:
            APIRouter: Router with auth endpoints
        """
        return self.router.get_router(session_getter)
        
    def get_role_router(self):
        """Get a router with role management endpoints.
        
        Returns:
            APIRouter: Router with role endpoints
        """
        return self.role_router.router
        
    def setup_exception_handlers(self, app: FastAPI):
        """Set up exception handlers for a FastAPI application.
        
        This configures standardized error responses for all FastAuth exceptions.
        
        Args:
            app: FastAPI application instance to set up exception handlers for
        """
        setup_exception_handlers(app)
        
    def require_roles(self, required_roles):
        """Get a FastAPI dependency that requires specific roles.
        
        Args:
            required_roles: List of role names required to access the endpoint
            
        Returns:
            callable: A dependency that validates if the user has any of the required roles
        """
        return self.role_dependencies.require_roles(required_roles)
        
    def require_all_roles(self, required_roles):
        """Get a FastAPI dependency that requires all specified roles.
        
        Args:
            required_roles: List of role names, all of which are required
            
        Returns:
            callable: A dependency that validates if the user has all required roles
        """
        return self.role_dependencies.require_all_roles(required_roles)
        
    def is_admin(self):
        """Get a FastAPI dependency that requires the 'admin' role.
        
        Returns:
            callable: A dependency that validates if the user has admin role
        """
        return self.role_dependencies.is_admin()
        
    def get_role_manager(self):
        """Get a RoleManager instance as a FastAPI dependency.
        
        Returns:
            callable: A dependency that provides a RoleManager
        """
        return self.role_dependencies.get_role_manager()
        
    def initialize_db(self, create_tables: bool = True, init_roles: bool = True, create_admin: bool = True, 
                     admin_username: Optional[str] = None, admin_password: Optional[str] = None):
        """Initialize the database with tables and optionally create initial roles and admin user.
        
        Args:
            create_tables: Whether to create database tables
            init_roles: Whether to initialize standard roles
            create_admin: Whether to create superadmin user
            admin_username: Optional username for superadmin (will prompt if None and interactive)
            admin_password: Optional password for superadmin (will prompt if None and interactive)
            
        Returns:
            dict: Initialization results
        """
        results = {}
        
        if create_tables:
            from sqlmodel import SQLModel
            SQLModel.metadata.create_all(self.engine)
            results["tables_created"] = True
            
        if init_roles:
            initialize_roles(self)
            results["roles_initialized"] = True
            
        if create_admin:
            admin_user_info = create_superadmin(self, username=admin_username, password=admin_password)
            results["superadmin_created"] = (admin_user_info is not None)
            results["superadmin_username"] = admin_user_info.get("username") if admin_user_info else None
            results["superadmin_is_new"] = admin_user_info.get("is_new", False) if admin_user_info else False
            
        return results
    
    def create_superadmin(self, username: Optional[str] = None, password: Optional[str] = None):
        """Create a superadmin user if one does not exist.
        
        Args:
            username: Optional username (will prompt if not provided and interactive)
            password: Optional password (will prompt if not provided and interactive)
            
        Returns:
            dict: Information about the created or existing superadmin user
            Contains keys: id, username, email, is_new
        """
        return create_superadmin(self, username=username, password=password)
