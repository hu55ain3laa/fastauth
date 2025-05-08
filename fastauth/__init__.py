"""
FastAuth - A comprehensive authentication library for FastAPI
"""
from fastauth.core.auth import FastAuth
from fastauth.models.user import (
    User, 
    UserRead,
    UserReadWithRoles,
    UserCreate, 
    UserUpdate, 
    UserDelete, 
    UserLogin,
    UserRole
)
from fastauth.models.tokens import Token, TokenData
from fastauth.models.role import Role, RoleRead, RoleCreate, RoleUpdate
from fastauth.dependencies.roles import RoleDependencies, RoleManager
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
    setup_exception_handlers
)

__version__ = "0.3.4"

__all__ = [
    'FastAuth',
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
    'Role',
    'RoleRead',
    'RoleCreate',
    'RoleUpdate',
    'RoleDependencies',
    'RoleManager',
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
    'setup_exception_handlers'
]
