"""
FastAuth - A comprehensive authentication library for FastAPI
"""
from fastauth.core.auth import FastAuth
from fastauth.models.user import (
    User, 
    UserRead, 
    UserCreate, 
    UserUpdate, 
    UserDelete, 
    UserLogin
)
from fastauth.models.tokens import Token, TokenData

__version__ = "0.2.0"

__all__ = [
    'FastAuth',
    'User',
    'UserRead',
    'UserCreate',
    'UserUpdate',
    'UserDelete',
    'UserLogin',
    'Token',
    'TokenData'
]
