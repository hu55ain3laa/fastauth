from typing import Annotated
from fastapi import Depends, HTTPException, status
from sqlmodel import Session

from fastauth.models.user import User
from fastauth.models.tokens import TokenData


class AuthDependencies:
    """Authentication dependencies for FastAPI applications."""
    
    def __init__(self, auth_instance):
        """Initialize dependencies with a FastAuth instance.
        
        Args:
            auth_instance: FastAuth instance for authentication
        """
        self.auth = auth_instance
    
    def get_current_user(self):
        """Get a FastAPI dependency for current user authentication.
        
        Returns:
            callable: A dependency that extracts and validates the JWT token
        """
        async def _get_current_user(token: Annotated[str, Depends(self.auth.oauth2_scheme)]):
            credentials_exception = HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
            # Special handling for debugging cookie authentication issues
            # Log the token we received for troubleshooting
            print(f"Auth dependency received token: {token[:20]}..." if token else "No token received")
            
            if not token:
                raise credentials_exception
                
            try:
                # Use token manager to verify the token
                payload = self.auth.token_manager.verify_token(token, expected_type="access")
                username = payload.get("sub")
                
                if username is None:
                    raise credentials_exception
                    
                token_data = TokenData(username=username)
            except Exception as e:
                # Add more detailed error information for debugging
                print(f"Token verification failed: {str(e)}")
                raise credentials_exception
                
            user = self.auth.get_user(self.auth.session, username=token_data.username)
            if user is None:
                raise credentials_exception
                
            return user
        return _get_current_user
        
    def get_current_active_user(self):
        """Get a FastAPI dependency for active user authentication.
        
        Returns:
            callable: A dependency that validates the user is active
        """
        async def _get_current_active_user(current_user: Annotated[User, Depends(self.get_current_user())]):
            if current_user.disabled:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
            return current_user
        return _get_current_active_user
        
    def get_db_session(self):
        """Get a database session dependency.
        
        Returns:
            callable: A dependency that yields a SQLModel session
        """
        def _get_db():
            db = Session(self.auth.engine)
            try:
                yield db
            finally:
                db.close()
        return _get_db
