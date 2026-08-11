from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from fastauth.models.user import User
from fastauth.exceptions import (
    CredentialsException,
    EmailNotVerifiedException,
    InactiveUserException,
    TokenException,
)


def token_version_matches(payload: dict, user) -> bool:
    """Check a token's version claim against the user's current version.

    Tokens issued before a "logout everywhere" (or password change) carry an
    older version and are rejected. Custom user models without the
    token_version column skip the check.
    """
    user_version = getattr(user, "token_version", None)
    if user_version is None:
        return True
    return payload.get("ver", 0) == (user_version or 0)


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
        # `def`, not `async def`: this reads the user from the database on every
        # authenticated request, and a blocking read inside a coroutine stalls
        # the whole event loop. FastAPI runs sync dependencies in a threadpool.
        # The token extraction it depends on stays async; that one does no I/O.
        def _get_current_user(token: Annotated[str, Depends(self.auth.oauth2_scheme)]):
            if not token:
                raise CredentialsException("No token provided")

            # Raises TokenException on invalid/expired/wrong-type tokens
            payload = self.auth.token_manager.verify_token(token, expected_type="access")
            username = payload["sub"]

            with Session(self.auth.engine) as session:
                user = self.auth.get_user(session, username=username)

            if user is None:
                raise CredentialsException("Could not validate credentials")
            if not token_version_matches(payload, user):
                raise TokenException("Token has been revoked")

            return user
        return _get_current_user

    def get_current_active_user(self):
        """Get a FastAPI dependency for active user authentication.

        Returns:
            callable: A dependency that validates the user is active
        """
        def _get_current_active_user(
            current_user: Annotated[User, Depends(self.get_current_user())]
        ):
            if current_user.disabled:
                raise InactiveUserException()
            return current_user
        return _get_current_active_user

    def get_current_verified_user(self):
        """Get a FastAPI dependency requiring a verified email address.

        Custom user models without the email_verified column are treated as
        verified (the feature is simply not in use).

        Returns:
            callable: A dependency that validates the user's email is verified
        """
        def _get_current_verified_user(
            current_user: Annotated[User, Depends(self.get_current_active_user())]
        ):
            if getattr(current_user, "email_verified", True) is False:
                raise EmailNotVerifiedException()
            return current_user
        return _get_current_verified_user

    def get_db_session(self):
        """Get a database session dependency.

        Returns:
            callable: A dependency that yields a SQLModel session
        """
        def _get_db():
            with Session(self.auth.engine) as session:
                yield session
        return _get_db
