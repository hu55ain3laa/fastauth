import logging
import os
import secrets as py_secrets
import warnings
from datetime import timedelta
from pathlib import Path
from typing import Callable, Dict, List, Optional, Type, Union

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import OAuth2, OAuth2PasswordBearer
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, select
from starlette.status import HTTP_401_UNAUTHORIZED

from fastauth.security.password import PasswordManager
from fastauth.security.tokens import TokenManager
from fastauth.dependencies.auth import AuthDependencies
from fastauth.dependencies.roles import RoleDependencies
from fastauth.routers.auth import AuthRouter
from fastauth.routers.roles import RoleRouter
from fastauth.models.user import User
from fastauth.cli import create_superadmin, initialize_roles
from fastauth.exceptions import setup_exception_handlers


def _deprecated(old: str, new: str) -> None:
    """Warn that a method has been superseded, pointing at the caller.

    Old names keep working; they are scheduled for removal in 1.0. See the
    versioning policy: https://github.com/hu55ain3laa/fastauth#versioning
    """
    warnings.warn(
        f"FastAuth.{old} is deprecated and will be removed in FastAuth 1.0. "
        f"Use {new} instead.",
        DeprecationWarning,
        stacklevel=3,
    )


class OAuth2PasswordBearerWithCookie(OAuth2):
    """OAuth2 password bearer authentication with cookie support."""

    def __init__(
        self,
        tokenUrl: str,
        scheme_name: Optional[str] = None,
        scopes: Optional[Dict[str, str]] = None,
        auto_error: bool = True,
    ):
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": scopes or {}})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        # An explicit Authorization header wins; the cookie is the fallback
        # for browser clients.
        token = None
        authorization = request.headers.get("Authorization")
        scheme, param = get_authorization_scheme_param(authorization)
        if authorization and scheme.lower() == "bearer":
            token = param

        if not token:
            token = request.cookies.get("access_token")

        if not token:
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None

        return token


DEV_SECRET_FILE = ".fastauth-secret"


def _resolve_secret_key(secret_key: Optional[str], production: bool) -> str:
    """Resolve the JWT secret key from the argument, environment, or a dev file.

    Order: explicit argument, FASTAUTH_SECRET_KEY, SECRET_KEY. In development,
    a generated key is persisted to .fastauth-secret so sessions survive
    server reloads. In production a missing or short key is a hard error.
    """
    if secret_key:
        return secret_key

    env_secret = os.getenv("FASTAUTH_SECRET_KEY") or os.getenv("SECRET_KEY")
    if env_secret:
        return env_secret

    if production:
        raise ValueError(
            "FastAuth needs a secret key in production. Set the SECRET_KEY "
            "environment variable (or pass secret_key=...). Generate one with: "
            "openssl rand -hex 32"
        )

    secret_file = Path.cwd() / DEV_SECRET_FILE
    if secret_file.exists():
        return secret_file.read_text().strip()

    generated = py_secrets.token_hex(32)
    try:
        secret_file.write_text(generated + "\n")
        secret_file.chmod(0o600)
        warnings.warn(
            f"No secret_key provided; FastAuth generated one and saved it to "
            f"{DEV_SECRET_FILE} (add it to .gitignore). For production, set the "
            f"SECRET_KEY environment variable instead.",
            stacklevel=3,
        )
    except OSError:
        warnings.warn(
            "No secret_key provided; using a temporary secret. All logins will "
            "be invalidated on restart. Set SECRET_KEY for real use.",
            stacklevel=3,
        )
    return generated


class FastAuth:
    """FastAuth is a comprehensive authentication library for FastAPI applications.

    It provides JWT-based authentication with both cookie and bearer token support,
    password hashing, token management, and integration with SQLModel for database
    operations.
    """

    def __init__(
        self,
        secret_key: Optional[str] = None,
        engine: Optional[Engine] = None,
        algorithm: str = "HS256",
        use_cookie: bool = True,
        token_url: str = "/token",
        access_token_expires_in: int = 30,
        refresh_token_expires_in: int = 7,
        user_model: Type[SQLModel] = User,
        cookie_secure: Optional[bool] = None,
        cookie_samesite: str = "lax",
        production: Optional[bool] = None,
        password_min_length: int = 8,
        reset_token_expires_in: int = 30,
        verify_token_expires_in: int = 1440,
    ):
        """Initialize the FastAuth instance.

        Args:
            secret_key: Secret key for JWT encoding/decoding. If omitted, it is
                read from the FASTAUTH_SECRET_KEY or SECRET_KEY environment
                variable; in development a generated key is stored in
                .fastauth-secret, in production a missing key is an error.
            engine: SQLAlchemy/SQLModel engine for database operations
            algorithm: Algorithm for JWT signing
            use_cookie: Enable cookie-based authentication
            token_url: Path of the login endpoint, as advertised to OpenAPI.
                This is what the "Authorize" button in /docs posts to, so it
                must match the route the auth router registers ("/token"). A
                missing leading slash is added for you.
            access_token_expires_in: Access token expiration in minutes
            refresh_token_expires_in: Refresh token expiration in days
            user_model: User model class for database operations
            cookie_secure: Send the auth cookie only over HTTPS. Defaults to
                True in production mode and False in development, so cookies
                work on http://localhost with zero configuration.
            cookie_samesite: SameSite policy for the auth cookie
            production: Enable production safety checks (strong secret required,
                secure cookies by default, no default admin password). Defaults
                to the FASTAUTH_PRODUCTION environment variable, else False.
            password_min_length: Minimum password length enforced on
                registration (set 0 to disable)
            reset_token_expires_in: Password reset token lifetime (minutes)
            verify_token_expires_in: Email verification token lifetime (minutes)
        """
        if engine is None:
            raise TypeError(
                "FastAuth requires an engine, e.g. "
                'FastAuth(engine=create_engine("sqlite:///./app.db"))'
            )

        tablename = getattr(user_model, "__tablename__", None)
        if tablename != "user":
            raise ValueError(
                f"Custom user models must set __tablename__ = 'user' "
                f"(got {tablename!r}). The role system's foreign keys point at "
                f"the 'user' table. Add __tablename__ = \"user\" to your model "
                f"and don't import fastauth's built-in User in the same app."
            )

        if production is None:
            production = os.getenv("FASTAUTH_PRODUCTION", "").strip().lower() in (
                "1", "true", "yes", "on",
            )
        self.production = production

        secret_key = _resolve_secret_key(secret_key, production)
        if production and len(secret_key) < 32:
            raise ValueError(
                "secret_key is too short for production (32+ characters needed). "
                "Generate one with: openssl rand -hex 32"
            )

        self.secret_key = secret_key
        self.algorithm = algorithm
        self.user_model = user_model
        self.engine = engine
        self.use_cookie = use_cookie
        self.access_token_expires_in = access_token_expires_in
        self.refresh_token_expires_in = refresh_token_expires_in
        self.cookie_secure = production if cookie_secure is None else cookie_secure
        self.cookie_samesite = cookie_samesite
        self.password_min_length = password_min_length
        self.reset_token_expires_in = reset_token_expires_in
        self.verify_token_expires_in = verify_token_expires_in

        # Delivery/claims hooks, set with the decorators below
        self._password_reset_hook: Optional[Callable] = None
        self._email_verify_hook: Optional[Callable] = None
        self._claims_hook: Optional[Callable] = None

        self.token_manager = TokenManager(
            secret_key=secret_key,
            algorithm=algorithm,
            access_token_expires_minutes=access_token_expires_in,
            refresh_token_expires_days=refresh_token_expires_in,
        )

        self.password_manager = PasswordManager()

        # Swagger's Authorize button posts to this URL. A relative value
        # resolves against the docs path and breaks as soon as the app is
        # mounted under a prefix, so normalise to an absolute path.
        if not token_url.startswith(("/", "http://", "https://")):
            token_url = "/" + token_url
        self.token_url = token_url

        if use_cookie:
            self.oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl=token_url)
        else:
            self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl=token_url)

        self.dependencies = AuthDependencies(self)
        self.router = AuthRouter(self)

        self.role_dependencies = RoleDependencies(self.dependencies)
        self.role_router = RoleRouter(self.role_dependencies)

        # Ready-to-use dependencies: the standard building blocks most apps need.
        #   user: User = Depends(auth.current_user)
        #   router = APIRouter(dependencies=[auth.required])
        #   admin: User = Depends(auth.admin)
        self.current_user = self.dependencies.get_current_active_user()
        self.required = Depends(self.current_user)
        self.admin = self.role_dependencies.is_admin()
        self.admin_required = Depends(self.admin)
        self.verified_user = self.dependencies.get_current_verified_user()

    # ------------------------------------------------------------------
    # Hooks
    # ------------------------------------------------------------------

    def on_password_reset(self, func: Callable) -> Callable:
        """Register the function that delivers password reset tokens.

        The function receives (user, token) and should send the token to the
        user, e.g. by email. Without a hook, the token is printed to the
        console in development so the flow can be tried locally.

        Usage:
            @auth.on_password_reset
            def send_reset(user, token):
                send_email(user.email, f"Your reset token: {token}")
        """
        self._password_reset_hook = func
        return func

    def on_email_verify(self, func: Callable) -> Callable:
        """Register the function that delivers email verification tokens.

        The function receives (user, token). Without a hook, the token is
        printed to the console in development.
        """
        self._email_verify_hook = func
        return func

    def token_claims(self, func: Callable) -> Callable:
        """Register a function that adds custom claims to issued JWTs.

        The function receives the user and returns a dict merged into the
        token payload at login and refresh.

        Usage:
            @auth.token_claims
            def claims(user):
                return {"plan": user.plan}
        """
        self._claims_hook = func
        return func

    def _token_data(self, user) -> dict:
        """Build the JWT payload for a user: subject, version, custom claims."""
        data = {"sub": user.username, "ver": getattr(user, "token_version", 0) or 0}
        if self._claims_hook:
            data.update(self._claims_hook(user) or {})
        return data

    def _deliver_token(self, hook: Optional[Callable], kind: str, user, token: str):
        """Deliver a reset/verification token via the hook, or fall back."""
        if hook:
            hook(user, token)
            return
        if not self.production:
            print(f"[fastauth] {kind} token for '{user.username}': {token}")
        else:
            logging.getLogger("fastauth").warning(
                "A %s token was issued but no delivery hook is registered. "
                "Register one with @auth.on_password_reset / @auth.on_email_verify.",
                kind,
            )

    def revoke_all_tokens(self, session: Session, user) -> None:
        """Invalidate every token previously issued to a user.

        Bumps the user's token_version; tokens carrying the old version are
        rejected everywhere. Used by password reset/change and /logout/all.
        """
        if hasattr(user, "token_version"):
            user.token_version = (user.token_version or 0) + 1
            session.add(user)
            session.commit()

    def roles(self, *role_names: Union[str, List[str]]):
        """Get a dependency that requires any of the given roles.

        Accepts role names as arguments (auth.roles("admin", "moderator"))
        or a single list (auth.roles(["admin", "moderator"])).

        Returns:
            callable: A dependency returning the user if they have any role
        """
        return self.role_dependencies.require_roles(self._role_list(role_names))

    def all_roles(self, *role_names: Union[str, List[str]]):
        """Get a dependency that requires all of the given roles.

        Returns:
            callable: A dependency returning the user if they have every role
        """
        return self.role_dependencies.require_all_roles(self._role_list(role_names))

    @staticmethod
    def _role_list(role_names) -> List[str]:
        if len(role_names) == 1 and isinstance(role_names[0], (list, tuple, set)):
            return list(role_names[0])
        return list(role_names)

    def setup(
        self,
        app: FastAPI,
        session_getter: Optional[Callable] = None,
        include_role_router: bool = True,
    ) -> FastAPI:
        """Wire FastAuth into a FastAPI app in one call.

        Includes the authentication router, optionally the role management
        router, and registers the standardized exception handlers.

        Args:
            app: FastAPI application instance
            session_getter: Optional. Leave it out and FastAuth opens sessions
                on the engine you gave it, which is what most apps want. Pass
                your own dependency only when routes must share one session
                with the rest of your app, for example when a test overrides
                it or a transaction spans several operations.
            include_role_router: Also mount the role management endpoints

        Returns:
            FastAPI: The same app, for chaining
        """
        app.include_router(self.get_auth_router(session_getter), tags=["authentication"])
        if include_role_router:
            app.include_router(self.get_role_router())
        setup_exception_handlers(app)
        return app

    def get_user(self, session: Session, username: str):
        """Get a user from the database by username.

        Args:
            session: The database session
            username: The username to look up

        Returns:
            User: The user object if found, None otherwise
        """
        return session.exec(
            select(self.user_model).where(self.user_model.username == username)
        ).first()

    def authenticate_user(self, username: str, password: str, session: Optional[Session] = None):
        """Authenticate a user by username and password.

        Args:
            username: The username to authenticate
            password: The password to verify
            session: Optional database session (a short-lived one is created
                if not provided)

        Returns:
            User: The user object if authentication succeeds, False otherwise
        """
        if session is None:
            with Session(self.engine) as session:
                return self._authenticate(session, username, password)
        return self._authenticate(session, username, password)

    def _authenticate(self, session: Session, username: str, password: str):
        user = self.get_user(session, username)
        if not user:
            return False
        if not self.password_manager.verify_password(password, user.hashed_password):
            return False
        return user

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against a hashed password.

        Args:
            plain_password: The plain text password to verify
            hashed_password: The hashed password to compare against

        Returns:
            bool: True if the password matches, False otherwise
        """
        return self.password_manager.verify_password(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash a password using the configured algorithm.

        Args:
            password: The plain text password to hash

        Returns:
            str: The hashed password
        """
        return self.password_manager.get_password_hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token.

        Args:
            data: The data to encode in the token
            expires_delta: Optional custom expiration time

        Returns:
            str: The encoded JWT token
        """
        return self.token_manager.create_access_token(data, expires_delta)

    def create_refresh_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT refresh token with longer expiration.

        Args:
            data: The data to encode in the token
            expires_delta: Optional custom expiration time

        Returns:
            str: The encoded JWT refresh token
        """
        return self.token_manager.create_refresh_token(data, expires_delta)

    def get_current_user_dependency(self):
        """Get a FastAPI dependency for current user authentication.

        Returns:
            callable: A dependency that extracts and validates the JWT token
        """
        return self.dependencies.get_current_user()

    def get_current_active_user_dependency(self):
        """Deprecated. Use the ``auth.current_user`` attribute instead.

        .. deprecated:: 0.7.0
            Superseded by :attr:`current_user`, removed in 1.0.
        """
        _deprecated("get_current_active_user_dependency()", "auth.current_user")
        return self.dependencies.get_current_active_user()

    def get_auth_router(self, session_getter: Optional[Callable] = None):
        """Get a router with authentication endpoints.

        Args:
            session_getter: Optional dependency that yields a database session

        Returns:
            APIRouter: Router with auth endpoints
        """
        return self.router.get_router(session_getter)

    def get_role_router(self):
        """Get a router with role management endpoints.

        Returns:
            APIRouter: Router with role endpoints
        """
        return self.role_router.router

    def setup_exception_handlers(self, app: FastAPI):
        """Set up exception handlers for a FastAPI application.

        This configures standardized error responses for all FastAuth exceptions.

        Args:
            app: FastAPI application instance to set up exception handlers for
        """
        setup_exception_handlers(app)

    def require_roles(self, required_roles):
        """Deprecated. Use ``auth.roles("admin", "moderator")`` instead.

        .. deprecated:: 0.7.0
            Superseded by :meth:`roles`, removed in 1.0. Note that
            :meth:`roles` takes names as arguments as well as a list.
        """
        _deprecated('require_roles([...])', 'auth.roles("admin", "moderator")')
        return self.role_dependencies.require_roles(self._role_list((required_roles,)))

    def require_all_roles(self, required_roles):
        """Deprecated. Use ``auth.all_roles("premium", "verified")`` instead.

        .. deprecated:: 0.7.0
            Superseded by :meth:`all_roles`, removed in 1.0.
        """
        _deprecated(
            'require_all_roles([...])', 'auth.all_roles("premium", "verified")'
        )
        return self.role_dependencies.require_all_roles(
            self._role_list((required_roles,))
        )

    def is_admin(self):
        """Deprecated. Use the ``auth.admin`` attribute instead.

        .. deprecated:: 0.7.0
            Superseded by :attr:`admin`, removed in 1.0.
        """
        _deprecated("is_admin()", "auth.admin")
        return self.role_dependencies.is_admin()

    def get_role_manager(self):
        """Get a RoleManager instance as a FastAPI dependency.

        Returns:
            callable: A dependency that provides a RoleManager
        """
        return self.role_dependencies.get_role_manager()

    def initialize_db(
        self,
        create_tables: bool = True,
        init_roles: bool = True,
        create_admin: bool = True,
        admin_username: Optional[str] = None,
        admin_password: Optional[str] = None,
    ):
        """Initialize the database with tables and optionally create initial roles and admin user.

        Args:
            create_tables: Whether to create database tables
            init_roles: Whether to initialize standard roles
            create_admin: Whether to create superadmin user
            admin_username: Optional username for superadmin (will prompt if None and interactive)
            admin_password: Optional password for superadmin (will prompt if None and interactive)

        Returns:
            dict: Initialization results
        """
        results = {}

        if create_tables:
            SQLModel.metadata.create_all(self.engine)
            results["tables_created"] = True

        if init_roles:
            initialize_roles(self)
            results["roles_initialized"] = True

        if create_admin:
            admin_user_info = create_superadmin(
                self, username=admin_username, password=admin_password
            )
            results["superadmin_created"] = admin_user_info is not None
            results["superadmin_username"] = admin_user_info.get("username") if admin_user_info else None
            results["superadmin_is_new"] = admin_user_info.get("is_new", False) if admin_user_info else False

        return results

    def create_superadmin(self, username: Optional[str] = None, password: Optional[str] = None):
        """Create a superadmin user if one does not exist.

        Args:
            username: Optional username (will prompt if not provided and interactive)
            password: Optional password (will prompt if not provided and interactive)

        Returns:
            dict: Information about the created or existing superadmin user
            Contains keys: id, username, email, is_new
        """
        return create_superadmin(self, username=username, password=password)
