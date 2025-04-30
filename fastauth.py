# This file serves as a compatibility layer for existing code using the old structure
# It imports and re-exports the elements from the modular structure

from fastauth.core.auth import *
from fastauth.dependencies.auth import *
from fastauth.models.user import *
from fastauth.models.tokens import *
from fastauth.security.password import *
from fastauth.security.tokens import *
from fastauth.utils.session import *
from fastauth.routers.auth import *
from fastauth.core.auth import *

# Import warning module to notify users about the deprecated structure
import warnings

warnings.warn(
    "Importing directly from fastauth.py is deprecated and will be removed in a future version. "
    "Please use 'from fastauth import FastAuth' instead.",
    DeprecationWarning,
    stacklevel=2
)

# All elements are now imported from the modular structure
