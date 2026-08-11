from typing import Callable, Optional

from fastapi import APIRouter, Depends, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from datetime import timedelta

from fastauth.models.user import UserCreate, UserRead
from fastauth.models.tokens import (
    EmailVerifyRequest,
    PasswordChangeRequest,
    PasswordForgotRequest,
    PasswordResetRequest,
    RefreshRequest,
    Token,
)
from fastauth.security.tokens import password_fingerprint
from fastauth.dependencies.auth import token_version_matches
from fastauth.exceptions import (
    CredentialsException,
    InactiveUserException,
    RefreshTokenException,
    TokenException,
    UserExistsException,
    UserNotFoundException,
    WeakPasswordException,
)


class AuthRouter:
    """Router for authentication endpoints."""

    def __init__(self, auth_instance):
        """Initialize router with a FastAuth instance.

        Args:
            auth_instance: FastAuth instance for authentication
        """
        self.auth = auth_instance

    def _set_token_cookie(self, response: Response, access_token: str):
        """Set the access token cookie if cookie auth is enabled."""
        if not self.auth.use_cookie:
            return
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=self.auth.cookie_secure,
            samesite=self.auth.cookie_samesite,
            max_age=self.auth.access_token_expires_in * 60,
        )

    def get_router(self, session_getter: Optional[Callable] = None) -> APIRouter:
        """Generate a router with all authentication routes.

        Args:
            session_getter: A dependency that yields a database session.
                Defaults to a per-request session from the FastAuth engine.

        Returns:
            APIRouter: A router with login, refresh, register, logout,
            and user info endpoints
        """
        if session_getter is None:
            session_getter = self.auth.dependencies.get_db_session()

        router = APIRouter()

        @router.post("/token", response_model=Token)
        async def login_for_access_token(
            response: Response,
            form_data: OAuth2PasswordRequestForm = Depends(),
            session: Session = Depends(session_getter),
        ):
            user = self.auth.authenticate_user(
                form_data.username, form_data.password, session=session
            )
            if not user:
                raise CredentialsException("Incorrect username or password")
            if user.disabled:
                raise InactiveUserException()

            data = self.auth._token_data(user)
            access_token = self.auth.token_manager.create_access_token(data=data)
            refresh_token = self.auth.token_manager.create_refresh_token(data=data)

            self._set_token_cookie(response, access_token)

            return Token(
                access_token=access_token,
                token_type="bearer",
                refresh_token=refresh_token,
            )

        @router.post("/token/refresh", response_model=Token)
        async def refresh_access_token(
            response: Response,
            body: RefreshRequest,
            session: Session = Depends(session_getter),
        ):
            try:
                payload = self.auth.token_manager.verify_token(
                    body.refresh_token, expected_type="refresh"
                )
            except TokenException as exc:
                raise RefreshTokenException(exc.detail) from exc

            username = payload["sub"]
            user = self.auth.get_user(session, username=username)
            if user is None:
                raise UserNotFoundException(f"User {username} not found")
            if user.disabled:
                raise InactiveUserException()
            if not token_version_matches(payload, user):
                raise RefreshTokenException("Token has been revoked")

            access_token = self.auth.token_manager.create_access_token(
                self.auth._token_data(user)
            )
            self._set_token_cookie(response, access_token)

            return Token(access_token=access_token, token_type="bearer")

        @router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
        def create_user(user: UserCreate, session: Session = Depends(session_getter)):
            min_length = getattr(self.auth, "password_min_length", 0)
            if min_length and len(user.password) < min_length:
                raise WeakPasswordException(
                    f"Password must be at least {min_length} characters long"
                )

            existing_username = session.exec(
                select(self.auth.user_model).where(self.auth.user_model.username == user.username)
            ).first()
            if existing_username:
                raise UserExistsException(f"Username '{user.username}' already registered")

            existing_email = session.exec(
                select(self.auth.user_model).where(self.auth.user_model.email == user.email)
            ).first()
            if existing_email:
                raise UserExistsException(f"Email '{user.email}' already registered")

            new_user = self.auth.user_model(
                username=user.username,
                email=user.email,
                hashed_password=self.auth.password_manager.get_password_hash(user.password),
                disabled=False,
            )
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            return new_user

        @router.get("/users/me", response_model=UserRead)
        async def read_users_me(
            current_user=Depends(self.auth.dependencies.get_current_active_user()),
        ):
            return current_user

        @router.post("/logout")
        async def logout(response: Response):
            response.delete_cookie(key="access_token")
            return {"message": "Successfully logged out"}

        @router.post("/logout/all")
        async def logout_everywhere(
            response: Response,
            current_user=Depends(self.auth.dependencies.get_current_active_user()),
            session: Session = Depends(session_getter),
        ):
            """Invalidate every token issued to this user, on every device."""
            user = self.auth.get_user(session, username=current_user.username)
            self.auth.revoke_all_tokens(session, user)
            response.delete_cookie(key="access_token")
            return {"message": "Logged out everywhere"}

        def _check_password_strength(password: str):
            min_length = getattr(self.auth, "password_min_length", 0)
            if min_length and len(password) < min_length:
                raise WeakPasswordException(
                    f"Password must be at least {min_length} characters long"
                )

        @router.post("/password/forgot")
        async def forgot_password(
            body: PasswordForgotRequest,
            session: Session = Depends(session_getter),
        ):
            """Issue a password reset token.

            Always returns 200 so the endpoint can't be used to discover
            which email addresses have accounts.
            """
            user = session.exec(
                select(self.auth.user_model).where(self.auth.user_model.email == body.email)
            ).first()

            if user and not user.disabled:
                token = self.auth.token_manager.create_token(
                    {
                        "sub": user.username,
                        "pfp": password_fingerprint(user.hashed_password),
                    },
                    token_type="password_reset",
                    lifetime=timedelta(minutes=self.auth.reset_token_expires_in),
                )
                self.auth._deliver_token(
                    self.auth._password_reset_hook, "password reset", user, token
                )

            return {"message": "If that account exists, a reset token has been issued"}

        @router.post("/password/reset")
        async def reset_password(
            body: PasswordResetRequest,
            session: Session = Depends(session_getter),
        ):
            """Set a new password using a reset token. Tokens are single-use."""
            payload = self.auth.token_manager.verify_token(
                body.token, expected_type="password_reset"
            )
            _check_password_strength(body.new_password)

            user = self.auth.get_user(session, username=payload["sub"])
            if user is None:
                raise UserNotFoundException()
            if payload.get("pfp") != password_fingerprint(user.hashed_password):
                raise TokenException("Reset token already used or no longer valid")

            user.hashed_password = self.auth.password_manager.get_password_hash(
                body.new_password
            )
            session.add(user)
            session.commit()
            # Kill every session that was logged in with the old password
            self.auth.revoke_all_tokens(session, user)

            return {"message": "Password updated. Please log in again."}

        @router.post("/password/change")
        async def change_password(
            body: PasswordChangeRequest,
            current_user=Depends(self.auth.dependencies.get_current_active_user()),
            session: Session = Depends(session_getter),
        ):
            """Change the logged-in user's password."""
            user = self.auth.get_user(session, username=current_user.username)
            if not self.auth.password_manager.verify_password(
                body.current_password, user.hashed_password
            ):
                raise CredentialsException("Current password is incorrect")

            _check_password_strength(body.new_password)

            user.hashed_password = self.auth.password_manager.get_password_hash(
                body.new_password
            )
            session.add(user)
            session.commit()
            self.auth.revoke_all_tokens(session, user)

            return {"message": "Password updated. Please log in again."}

        @router.post("/email/verify/request")
        async def request_email_verification(
            current_user=Depends(self.auth.dependencies.get_current_active_user()),
        ):
            """Issue an email verification token for the logged-in user."""
            token = self.auth.token_manager.create_token(
                {"sub": current_user.username, "email": current_user.email},
                token_type="email_verify",
                lifetime=timedelta(minutes=self.auth.verify_token_expires_in),
            )
            self.auth._deliver_token(
                self.auth._email_verify_hook, "email verification", current_user, token
            )
            return {"message": "Verification token issued"}

        @router.post("/email/verify")
        async def verify_email(
            body: EmailVerifyRequest,
            session: Session = Depends(session_getter),
        ):
            """Confirm an email address with a verification token."""
            payload = self.auth.token_manager.verify_token(
                body.token, expected_type="email_verify"
            )
            user = self.auth.get_user(session, username=payload["sub"])
            if user is None:
                raise UserNotFoundException()
            if payload.get("email") != user.email:
                raise TokenException("Token was issued for a different email address")

            if hasattr(user, "email_verified"):
                user.email_verified = True
                session.add(user)
                session.commit()

            return {"message": "Email verified"}

        return router
