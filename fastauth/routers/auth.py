from typing import Optional, Callable
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from jwt.exceptions import InvalidTokenError

from fastauth.models.user import User, UserCreate, UserRead, UserLogin
from fastauth.models.tokens import Token


class AuthRouter:
    """Router for authentication endpoints."""
    
    def __init__(self, auth_instance):
        """Initialize router with a FastAuth instance.
        
        Args:
            auth_instance: FastAuth instance for authentication
        """
        self.auth = auth_instance
        
    def get_router(self, session_getter: Optional[Callable[[], Session]] = None) -> APIRouter:
        """Generate a router with all authentication routes.
        
        Args:
            session_getter: A function that returns a database session
            
        Returns:
            APIRouter: A router with login, refresh, register, and user info endpoints
        """
        # Use auth session as default if no session_getter provided
        if session_getter is None:
            # Create a function that returns auth.session
            session_getter = lambda: self.auth.session
            
        router = APIRouter()
        
        # Login endpoint to get access token
        @router.post("/token", response_model=Token)
        async def login_for_access_token(
            response: Response, 
            form_data: OAuth2PasswordRequestForm = Depends(), 
            session: Session = Depends(session_getter)
        ):
            user = self.auth.authenticate_user(form_data.username, form_data.password)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect username or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Create access token
            access_token = self.auth.token_manager.create_access_token(data={"sub": user.username})
            
            # Create refresh token
            refresh_token = self.auth.token_manager.create_refresh_token(data={"sub": user.username})
            
            # If using cookie auth, set the cookie
            if self.auth.use_cookie:
                response.set_cookie(
                    key="access_token",
                    value=access_token,
                    httponly=True,
                    secure=True,  # for HTTPS
                    samesite="lax"
                )
            
            return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}
        
        # Refresh token endpoint
        @router.post("/token/refresh")
        async def refresh_access_token(response: Response, body: dict):
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
                # Verify refresh token
                payload = self.auth.token_manager.verify_token(refresh_token, expected_type="refresh")
                username = payload.get("sub")
                
                # Validate user exists
                user = self.auth.get_user(self.auth.session, username=username)
                if user is None:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid user"
                    )
                    
                # Create a new access token
                access_token = self.auth.token_manager.create_access_token({"sub": username})
                
                # If using cookie auth, set the cookie
                if self.auth.use_cookie:
                    response.set_cookie(
                        key="access_token",
                        value=access_token,
                        httponly=True,
                        secure=True,
                        samesite="lax"
                    )
                
                return {"access_token": access_token, "token_type": "bearer"}
                
            except HTTPException as e:
                raise e
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token: {str(e)}"
                )
        
        # User registration endpoint
        @router.post("/users", status_code=status.HTTP_201_CREATED)
        def create_user(user: UserCreate, session: Session = Depends(session_getter)):
            # Check if username already exists
            db_user = session.exec(select(self.auth.user_model).where(
                self.auth.user_model.username == user.username
            )).first()
            
            if db_user:
                raise HTTPException(status_code=400, detail="Username already registered")
            
            # Create new user
            new_user = self.auth.user_model(
                username=user.username,
                email=user.email,
                hashed_password=self.auth.password_manager.get_password_hash(user.password),
                disabled=False
            )
            
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            
            return {"username": new_user.username, "email": new_user.email}
        
        # Get current user endpoint
        @router.get("/users/me", response_model=UserRead)
        async def read_users_me(
            current_user = Depends(self.auth.dependencies.get_current_active_user())
        ):
            # Convert User model to UserRead format
            return UserRead(
                id=current_user.id,
                username=current_user.username,
                email=current_user.email,
                disabled=current_user.disabled
            )
            
        return router
