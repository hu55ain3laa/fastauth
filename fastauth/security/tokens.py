from datetime import datetime, timedelta, timezone
import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import HTTPException, status
from fastauth.models.tokens import TokenData


class TokenManager:
    """Handles JWT token creation, validation, and management."""
    
    def __init__(
        self, 
        secret_key, 
        algorithm="HS256", 
        access_token_expires_minutes=30, 
        refresh_token_expires_days=7
    ):
        """Initialize the token manager.
        
        Args:
            secret_key: Secret key for JWT encoding/decoding
            algorithm: Algorithm for JWT signing
            access_token_expires_minutes: Access token expiration in minutes
            refresh_token_expires_days: Refresh token expiration in days
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expires_minutes = access_token_expires_minutes
        self.refresh_token_expires_days = refresh_token_expires_days
    
    def create_access_token(self, data, expires_delta=None):
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
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expires_minutes)
        to_encode.update({"exp": expire, "token_type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data, expires_delta=None):
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
            expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expires_days)
        to_encode.update({"exp": expire, "token_type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token, expected_type="access"):
        """Verify a JWT token and extract its payload.
        
        Args:
            token: The JWT token to verify
            expected_type: Expected token type ('access' or 'refresh')
            
        Returns:
            dict: The decoded token payload
            
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
            
            if username is None or token_type != expected_type:
                raise credentials_exception
                
            return payload
        except InvalidTokenError:
            raise credentials_exception
