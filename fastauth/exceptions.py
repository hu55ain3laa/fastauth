from fastapi import HTTPException, status
from typing import Optional, Dict, Any, Union


class FastAuthException(HTTPException):
    """Base exception class for FastAuth."""
    
    def __init__(
        self, 
        status_code: int, 
        detail: str,
        error_code: str = None,
        headers: Optional[Dict[str, str]] = None
    ):
        """Initialize the FastAuth exception.
        
        Args:
            status_code: HTTP status code
            detail: Human-readable error description
            error_code: Machine-readable error code
            headers: Additional HTTP headers
        """
        self.error_code = error_code or f"FASTAUTH_{status_code}"
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert the exception to a dictionary for response.
        
        Returns:
            Dict with error details
        """
        return {
            "error": {
                "code": self.error_code,
                "message": self.detail,
                "status_code": self.status_code
            }
        }


# Authentication Exceptions
class CredentialsException(FastAuthException):
    """Exception raised when credentials are invalid."""
    
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="FASTAUTH_INVALID_CREDENTIALS",
            headers={"WWW-Authenticate": "Bearer"}
        )


class TokenException(FastAuthException):
    """Exception raised when token is invalid."""
    
    def __init__(self, detail: str = "Invalid token"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="FASTAUTH_INVALID_TOKEN",
            headers={"WWW-Authenticate": "Bearer"}
        )


class RefreshTokenException(FastAuthException):
    """Exception raised when refresh token is invalid."""
    
    def __init__(self, detail: str = "Invalid refresh token"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="FASTAUTH_INVALID_REFRESH_TOKEN"
        )


class InactiveUserException(FastAuthException):
    """Exception raised when user is inactive."""
    
    def __init__(self, detail: str = "Inactive user"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="FASTAUTH_INACTIVE_USER"
        )


# User Exceptions
class UserNotFoundException(FastAuthException):
    """Exception raised when user is not found."""
    
    def __init__(self, detail: str = "User not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="FASTAUTH_USER_NOT_FOUND"
        )


class UserExistsException(FastAuthException):
    """Exception raised when user already exists."""
    
    def __init__(self, detail: str = "User already exists"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="FASTAUTH_USER_EXISTS"
        )


# Role Exceptions
class RoleNotFoundException(FastAuthException):
    """Exception raised when role is not found."""
    
    def __init__(self, detail: str = "Role not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code="FASTAUTH_ROLE_NOT_FOUND"
        )


class RoleExistsException(FastAuthException):
    """Exception raised when role already exists."""
    
    def __init__(self, detail: str = "Role already exists"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="FASTAUTH_ROLE_EXISTS"
        )


class PermissionDeniedException(FastAuthException):
    """Exception raised when permission is denied."""
    
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="FASTAUTH_PERMISSION_DENIED"
        )


# Setup a FastAPI exception handler
def setup_exception_handlers(app):
    """Setup exception handlers for FastAPI application.
    
    Args:
        app: FastAPI application
    """
    from fastapi import Request
    from fastapi.responses import JSONResponse
    
    @app.exception_handler(FastAuthException)
    async def fastauth_exception_handler(request: Request, exc: FastAuthException):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict()
        )
