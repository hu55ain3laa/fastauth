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

__version__ = "0.2.2"

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
    'RoleManager'
]
