from User import User, Token, TokenData, UserCreate, UserRead, UserUpdate, UserDelete, UserLogin
from datetime import datetime, timedelta, timezone
import jwt
from sqlmodel import SQLModel, Session, select
from fastapi.security import OAuth2PasswordBearer, OAuth2, OAuth2PasswordRequestForm
from fastapi.security.utils import get_authorization_scheme_param
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import Annotated, Optional, Dict, Callable, Type, Any
from fastapi import Depends, HTTPException, status, Request, Response, APIRouter, Form
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

class OAuth2PasswordBearerWithCookie(OAuth2):
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
            scheme, token = get_authorization_scheme_param(authorization)
            if not authorization or scheme.lower() != "bearer":
                if self.auto_error:
                    raise HTTPException(
                        status_code=HTTP_401_UNAUTHORIZED,
                        detail="Not authenticated",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                else:
                    return None
        return token


class FastAuth:
    """FastAuth is a comprehensive authentication library for FastAPI applications.
    
    It provides JWT-based authentication with both cookie and bearer token support,
    password hashing, token management, and integration with SQLModel for database operations.
    
    Attributes:
        secret_key (str): Secret key used for JWT encoding/decoding
        algorithm (str): Algorithm used for JWT signing (default: HS256)
        access_token_expires_in (int): Access token expiration time in minutes (default: 15)
        refresh_token_expires_in (int): Refresh token expiration time in days (default: 7)
        engine (SQLModel): SQLModel engine for database operations
        session (Session): SQLModel session for database queries
        user_model (User): User model class for database operations
        pwd_context (CryptContext): Password context for hashing and verification
        oauth2_scheme (OAuth2): OAuth2 scheme for token extraction
        use_cookie (bool): Flag to enable cookie-based authentication
    """
    secret_key: str = 'your-secret-key'
    algorithm: str = "HS256"
    access_token_expires_in: int = 15
    refresh_token_expires_in: int = 7  # days
    engine: SQLModel = None
    session: Session = Session(engine)
    user_model: User = User
    pwd_context: CryptContext = None
    oauth2_scheme: OAuth2 = None
    use_cookie: bool = False


    def __init__(self, secret_key: str, algorithm: str, user_model: User, engine: SQLModel, use_cookie: bool = False, token_url: str = "token", access_token_expires_in: int = 15, refresh_token_expires_in: int = 7):
        """Initialize the FastAuth instance.
        
        Args:
            secret_key (str): Secret key for JWT encoding/decoding
            algorithm (str): Algorithm for JWT signing
            user_model (User): User model class for database operations
            engine (SQLModel): SQLModel engine for database operations
            use_cookie (bool, optional): Enable cookie-based authentication. Defaults to False.
            token_url (str, optional): URL for token endpoint. Defaults to "token".
            access_token_expires_in (int, optional): Access token expiration in minutes. Defaults to 15.
            refresh_token_expires_in (int, optional): Refresh token expiration in days. Defaults to 7.
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.user_model = user_model
        self.engine = engine
        self.session = Session(engine)
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.use_cookie = use_cookie
        self.access_token_expires_in = access_token_expires_in
        self.refresh_token_expires_in = refresh_token_expires_in
        
        # Choose the appropriate authentication scheme based on use_cookie flag
        if use_cookie:
            self.oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl=token_url)
        else:
            self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl=token_url)

    def verify_password(self, plain_password, hashed_password):
        """Verify a plain password against a hashed password.
        
        Args:
            plain_password: The plain text password to verify
            hashed_password: The hashed password to compare against
            
        Returns:
            bool: True if the password matches, False otherwise
        """
        return self.pwd_context.verify(plain_password, hashed_password)


    def get_password_hash(self, password):
        """Hash a password using bcrypt algorithm.
        
        Args:
            password: The plain text password to hash
            
        Returns:
            str: The hashed password
        """
        return self.pwd_context.hash(password)


    def get_user(self, session: Session, username: str):
        """Get a user from the database by username.
        
        Args:
            session: The database session
            username: The username to look up
            
        Returns:
            User: The user object if found, None otherwise
        """
        # Query by username field instead of using it as primary key
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
        if not self.verify_password(password, user.hashed_password):
            return False
        return user
    
    def create_access_token(self, data: dict, expires_delta: timedelta | None = None):
        """Create a JWT access token.
        
        Args:
            data: The data to encode in the token
            expires_delta: Optional custom expiration time
            
        Returns:
            str: The encoded JWT token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expires_in)
        to_encode.update({"exp": expire, "token_type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
        
    def create_refresh_token(self, data: dict, expires_delta: timedelta | None = None):
        """Create a JWT refresh token with longer expiration.
        
        Args:
            data: The data to encode in the token
            expires_delta: Optional custom expiration time
            
        Returns:
            str: The encoded JWT refresh token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expires_in)
        to_encode.update({"exp": expire, "token_type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
        
    def refresh_token(self, refresh_token: str):
        """Generate a new access token from a refresh token.
        
        Args:
            refresh_token: The refresh token to use
            
        Returns:
            str: A new access token if the refresh token is valid
            
        Raises:
            HTTPException: If the token is invalid or expired
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
            username = payload.get("sub")
            token_type = payload.get("token_type")
            
            if username is None or token_type != "refresh":
                raise credentials_exception
                
            user = self.get_user(self.session, username=username)
            if user is None:
                raise credentials_exception
                
            # Create a new access token
            access_token = self.create_access_token({"sub": username})
            return {"access_token": access_token, "token_type": "bearer"}
            
        except InvalidTokenError:
            raise credentials_exception

    # This method will be used as a FastAPI dependency
    def get_current_user_dependency(self):
        """Get a FastAPI dependency for current user authentication.
        
        Returns:
            callable: A dependency that extracts and validates the JWT token
        """
        async def _get_current_user(token: Annotated[str, Depends(self.oauth2_scheme)]):
            credentials_exception = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            try:
                payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
                username = payload.get("sub")
                token_type = payload.get("token_type")
                
                if username is None or token_type != "access":
                    raise credentials_exception
                    
                token_data = TokenData(username=username)
            except InvalidTokenError:
                raise credentials_exception
                
            user = self.get_user(self.session, username=token_data.username)
            if user is None:
                raise credentials_exception
                
            return user
        return _get_current_user
        
    # Legacy method for direct token verification
    async def get_current_user(self, token: str):
        """Verify a token and get the current user (legacy method).
        
        Args:
            token: The JWT token to verify
            
        Returns:
            User: The user associated with the token
            
        Raises:
            HTTPException: If the token is invalid or expired
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username = payload.get("sub")
            token_type = payload.get("token_type")
            
            if username is None or token_type != "access":
                raise credentials_exception
                
            token_data = TokenData(username=username)
        except InvalidTokenError:
            raise credentials_exception
            
        user = self.get_user(self.session, username=token_data.username)
        if user is None:
            raise credentials_exception
            
        return user


    # This method will be used as a FastAPI dependency
    def get_current_active_user_dependency(self):
        """Get a FastAPI dependency for active user authentication.
        
        Returns:
            callable: A dependency that validates the user is active
        """
        async def _get_current_active_user(current_user: Annotated[User, Depends(self.get_current_user_dependency())]):
            if current_user.disabled:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
            return current_user
        return _get_current_active_user
        
    # Legacy method for direct user verification
    async def get_current_active_user(self, current_user: User):
        """Verify that a user is active (legacy method).
        
        Args:
            current_user: The user to verify
            
        Returns:
            User: The active user
            
        Raises:
            HTTPException: If the user is disabled
        """
        if current_user.disabled:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
        return current_user
        
    def get_auth_router(self, session_getter: Callable[[], Session]) -> APIRouter:
        """Generate a router with all authentication routes.
        
        This provides a simple way to add all authentication endpoints to your FastAPI app.
        
        Args:
            session_getter: A function that returns a database session
            
        Returns:
            APIRouter: A router with login, refresh, register, and user info endpoints
        """
        router = APIRouter()
        
        # Login endpoint to get access token
        @router.post("/token", response_model=Token)
        async def login_for_access_token(response: Response, form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(session_getter)):
            user = self.authenticate_user(form_data.username, form_data.password)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Create access token
            access_token = self.create_access_token(data={"sub": user.username})
            
            # Create refresh token
            refresh_token = self.create_refresh_token(data={"sub": user.username})
            
            # If using cookie auth, set the cookie
            if self.use_cookie:
                response.set_cookie(
                    key="access_token",
                    value=access_token,
                    httponly=True,
                    secure=True,  # for HTTPS
                    samesite="lax"
                )
            
            return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}
        
        # Refresh token endpoint - using only JSON body
        @router.post("/token/refresh")
        async def refresh_access_token(
            response: Response, 
            body: dict  # Require JSON body with refresh_token
        ):
            # Get refresh token from JSON body
            if not body or "refresh_token" not in body:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="refresh_token is required in request body"
                )
                
            refresh_token = body["refresh_token"]
            
            if not refresh_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="refresh_token cannot be empty"
                )
            
            try:
                # Decode and validate the refresh token
                try:
                    payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
                    username = payload.get("sub")
                    token_type = payload.get("token_type")
                    
                    if username is None:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid refresh token: missing username"
                        )
                    
                    if token_type != "refresh":
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid token type: must be a refresh token"
                        )
                except InvalidTokenError as e:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"Invalid token: {str(e)}"
                    )
                
                # Get new tokens
                token_data = self.refresh_token(refresh_token)
                
                # If using cookie auth, set the cookie
                if self.use_cookie:
                    response.set_cookie(
                        key="access_token",
                        value=token_data["access_token"],
                        httponly=True,
                        secure=True,
                        samesite="lax"
                    )
                
                return token_data
            except HTTPException as e:
                raise e
        
        # User registration endpoint
        @router.post("/users", status_code=status.HTTP_201_CREATED)
        def create_user(user: UserCreate, session: Session = Depends(session_getter)):
            # Check if username already exists
            db_user = session.exec(select(self.user_model).where(self.user_model.username == user.username)).first()
            if db_user:
                raise HTTPException(status_code=400, detail="Username already registered")
            
            # Create new user
            new_user = self.user_model(
                username=user.username,
                email=user.email,
                hashed_password=self.get_password_hash(user.password),
                disabled=False
            )
            
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            
            return {"username": new_user.username, "email": new_user.email}
        
        # Get current user endpoint
        @router.get("/users/me", response_model=UserRead)
        async def read_users_me(current_user = Depends(self.get_current_active_user_dependency())):
            # Convert User model to UserRead format
            return UserRead(
                id=current_user.id,
                username=current_user.username,
                email=current_user.email,
                disabled=current_user.disabled
            )
            
        return router

