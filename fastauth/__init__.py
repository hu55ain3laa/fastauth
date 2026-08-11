"""
FastAuth - A comprehensive authentication library for FastAPI
"""
from fastauth.core.auth import FastAuth, OAuth2PasswordBearerWithCookie
from fastauth.models.user import (
    User,
    UserRead,
    UserReadWithRoles,
    UserCreate,
    UserUpdate,
    UserDelete,
    UserLogin,
    UserRole,
)
from fastauth.models.tokens import (
    Token,
    TokenData,
    RefreshRequest,
    PasswordForgotRequest,
    PasswordResetRequest,
    PasswordChangeRequest,
    EmailVerifyRequest,
)
from fastauth.models.role import Role, RoleRead, RoleCreate, RoleUpdate
from fastauth.dependencies.roles import RoleDependencies, RoleManager
from fastauth.security.password import PasswordManager
from fastauth.security.tokens import TokenManager
from fastauth.exceptions import (
    FastAuthException,
    CredentialsException,
    TokenException,
    RefreshTokenException,
    InactiveUserException,
    UserNotFoundException,
    UserExistsException,
    RoleNotFoundException,
    RoleExistsException,
    PermissionDeniedException,
    WeakPasswordException,
    EmailNotVerifiedException,
    setup_exception_handlers,
)

__version__ = "0.6.0"

__all__ = [
    'FastAuth',
    'OAuth2PasswordBearerWithCookie',
    'User',
    'UserRead',
    'UserReadWithRoles',
    'UserCreate',
    'UserUpdate',
    'UserDelete',
    'UserLogin',
    'UserRole',
    'Token',
    'TokenData',
    'RefreshRequest',
    'PasswordForgotRequest',
    'PasswordResetRequest',
    'PasswordChangeRequest',
    'EmailVerifyRequest',
    'Role',
    'RoleRead',
    'RoleCreate',
    'RoleUpdate',
    'RoleDependencies',
    'RoleManager',
    'PasswordManager',
    'TokenManager',
    # Exception classes
    'FastAuthException',
    'CredentialsException',
    'TokenException',
    'RefreshTokenException',
    'InactiveUserException',
    'UserNotFoundException',
    'UserExistsException',
    'RoleNotFoundException',
    'RoleExistsException',
    'PermissionDeniedException',
    'WeakPasswordException',
    'EmailNotVerifiedException',
    'setup_exception_handlers',
]
