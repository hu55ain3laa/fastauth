import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from jwt.exceptions import InvalidTokenError

from fastauth.exceptions import TokenException


def password_fingerprint(hashed_password: str) -> str:
    """Short fingerprint of a password hash.

    Embedded in password-reset tokens so a token stops working the moment
    the password changes, making reset tokens single-use without any
    server-side state.
    """
    return hashlib.sha256(hashed_password.encode("utf-8")).hexdigest()[:16]


class TokenManager:
    """Handles JWT token creation, validation, and management."""

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expires_minutes: int = 30,
        refresh_token_expires_days: int = 7,
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

    def _create_token(
        self,
        data: dict,
        token_type: str,
        default_lifetime: timedelta,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (expires_delta or default_lifetime)
        to_encode.update({"exp": expire, "token_type": token_type})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token.

        Args:
            data: The data to encode in the token
            expires_delta: Optional custom expiration time

        Returns:
            str: The encoded JWT token
        """
        return self._create_token(
            data, "access", timedelta(minutes=self.access_token_expires_minutes), expires_delta
        )

    def create_refresh_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT refresh token with longer expiration.

        Args:
            data: The data to encode in the token
            expires_delta: Optional custom expiration time

        Returns:
            str: The encoded JWT refresh token
        """
        return self._create_token(
            data, "refresh", timedelta(days=self.refresh_token_expires_days), expires_delta
        )

    def create_token(self, data: dict, token_type: str, lifetime: timedelta) -> str:
        """Create a JWT of an arbitrary type (e.g. password_reset, email_verify).

        Args:
            data: The data to encode in the token (must include 'sub')
            token_type: The token_type claim, checked on verification
            lifetime: How long the token stays valid

        Returns:
            str: The encoded JWT
        """
        return self._create_token(data, token_type, lifetime)

    def verify_token(self, token: str, expected_type: str = "access") -> dict:
        """Verify a JWT token and extract its payload.

        Args:
            token: The JWT token to verify
            expected_type: Expected token type ('access' or 'refresh')

        Returns:
            dict: The decoded token payload

        Raises:
            TokenException: If the token is invalid, expired, or of the wrong type
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except InvalidTokenError as exc:
            raise TokenException(f"Could not validate token: {exc}") from exc

        if payload.get("sub") is None:
            raise TokenException("Invalid token payload: missing subject")
        if payload.get("token_type") != expected_type:
            raise TokenException(f"Invalid token type: expected '{expected_type}'")

        return payload
