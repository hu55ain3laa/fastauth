<div align="center">
  <img src="https://raw.githubusercontent.com/hu55ain3laa/fastauth/main/FastAuth.svg" alt="FastAuth Logo" width="350">

  <p>A comprehensive authentication and authorization library for FastAPI applications<br>with JWT-based authentication, role-based authorization, and SQLModel integration.</p>
</div>

<div align="center">
  <a href="https://badge.fury.io/py/fastauth-iq"><img src="https://badge.fury.io/py/fastauth-iq.svg?v=0.8.1" alt="PyPI version"></a>
  <a href="https://github.com/hu55ain3laa/fastauth/actions/workflows/ci.yml"><img src="https://github.com/hu55ain3laa/fastauth/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>

  <h3>📖 <a href="https://fastauth.pythowner.com">Full Documentation Available Here</a></h3>
</div>

## Documentation

This README provides a quick overview of FastAuth. For a more complete, interactive documentation with live examples and responsive design, visit our **[full documentation site](https://fastauth.pythowner.com)**.

New to FastAPI or building auth for the first time? Start with the **[Easy Mode guide for students](https://fastauth.pythowner.com/docs/easy-mode)**: one file, five minutes, every step checked.

Using an AI coding assistant? This repo ships an [AGENTS.md](AGENTS.md) with the full API surface, so agents can integrate FastAuth correctly without guessing.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Authentication](#authentication)
  - [Login and Token Management](#login-and-token-management)
  - [Protected Routes](#protected-routes)
  - [Cookie-Based Authentication](#cookie-based-authentication)
  - [Password Reset and Email Verification](#password-reset-and-email-verification)
- [Database Initialization](#database-initialization)
  - [CLI Initialization](#cli-initialization)
  - [Programmatic Initialization](#programmatic-initialization)
- [Role-Based Authorization](#role-based-authorization)
  - [Standard Roles](#standard-roles)
  - [Role Requirements](#role-requirements)
  - [Role Management API](#role-management-api)
- [Customization Levels](#customization-levels)
- [Going to Production](#going-to-production)
- [API Reference](#api-reference)
  - [Authentication Endpoints](#authentication-endpoints)
  - [Role Management Endpoints](#role-management-endpoints)
- [Error Handling](#error-handling)
- [Advanced Usage](#advanced-usage)
  - [Custom User Models](#custom-user-models)
  - [Custom Authentication Logic](#custom-authentication-logic)
- [Security Best Practices](#security-best-practices)
- [Versioning](#versioning)
- [Changelog](#changelog)
- [Project Structure](#project-structure)
- [License](#license)

## Features

- **OAuth2 and JWT authentication** built-in
- **Role-based authorization** system
- **Cookie-based authentication** option with configurable cookie settings
- **Token refresh mechanism** for extended sessions
- **Logout endpoint** that clears the auth cookie
- **SQLModel integration** for easy database operations
- **CLI utilities** for database initialization and management
- **One-call setup**: `auth.setup(app)` wires up all routes and error handlers
- **Comprehensive error handling** with standardized error responses
- **Password hashing** with bcrypt (no passlib dependency)
- **Modular architecture** for better code organization and extensibility
- **Zero-config start**: `FastAuth(engine=engine)` manages a dev secret for you
- **Production mode**: `production=True` enforces a strong secret, secure cookies, and no default passwords
- **Ready-made dependencies**: `auth.current_user`, `auth.admin`, `auth.roles(...)`, `auth.required`, `auth.verified_user`
- **Password reset and change** flows with single-use tokens and delivery hooks
- **Email verification** flow with a `verified_user` dependency
- **Token revocation**: `/logout/all` invalidates every session on every device
- **Password rules**: minimum length enforced on registration (configurable)
- **Tested on every commit** across Python 3.10–3.14 with GitHub Actions

## Installation

```bash
uv add fastauth_iq "fastapi[standard]"
```

Or install from source:

```bash
git clone https://github.com/hu55ain3laa/fastauth.git
cd fastauth
uv pip install -e .
```

Requires Python 3.10+. `fastapi[standard]` brings the `fastapi dev` server for local development.

Don't have `uv` yet? Grab it with your platform's package manager, or see the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/):

```bash
# macOS
brew install uv

# Windows
winget install --id=astral-sh.uv -e

# Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
# or as a snap
sudo snap install astral-uv --classic
```

## Quick Start

A complete working app in one file:

```python
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlmodel import Session, create_engine

from fastauth import FastAuth, User

engine = create_engine("sqlite:///./app.db", connect_args={"check_same_thread": False})


def get_session():
    with Session(engine) as session:
        yield session


# Zero config: in development FastAuth manages a dev secret for you
# (stored in .fastauth-secret, add it to .gitignore).
# In production, set SECRET_KEY in the environment and production=True.
auth = FastAuth(engine=engine)


# Create tables, standard roles, and a superadmin on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    auth.initialize_db(admin_username="superadmin", admin_password="admin123")
    yield


app = FastAPI(lifespan=lifespan)

# One call adds all auth + role routes and standardized error handling
auth.setup(app, session_getter=get_session)


# Protect your routes with the ready-made dependencies
@app.get("/protected")
def protected_route(current_user: User = Depends(auth.current_user)):
    return {"message": f"Hello, {current_user.username}!"}


@app.get("/admin-only")
def admin_only_route(current_user: User = Depends(auth.admin)):
    return {"message": f"Hello admin, {current_user.username}!"}
```

That's it. Run it with `uv run fastapi dev app.py` and open `/docs`.

`auth.setup(app)` is equivalent to the manual version:

```python
app.include_router(auth.get_auth_router(get_session), tags=["authentication"])
app.include_router(auth.get_role_router())
auth.setup_exception_handlers(app)
```

Use the manual version if you need custom prefixes or want to skip the role router
(`auth.setup(app, include_role_router=False)` also works).

## Authentication

### Login and Token Management

FastAuth implements JWT-based authentication with both access tokens and refresh tokens:

- **Access tokens** are short-lived (default: 30 minutes) and used for regular API access
- **Refresh tokens** are long-lived (default: 7 days) and used to obtain new access tokens

User authentication flow:

1. User submits credentials to `/token` endpoint
2. Server validates credentials and returns access + refresh tokens
3. Client uses access token for API requests (via header or cookie)
4. When the access token expires, the client sends `{"refresh_token": "..."}` to `/token/refresh` to get a new one
5. `/logout` clears the auth cookie

Disabled users cannot log in, refresh tokens, or access protected routes.

### Protected Routes

To protect a route, use FastAuth's dependencies:

```python
# Basic authentication - any valid, active user
@app.get("/protected")
def protected_route(user = Depends(auth.current_user)):
    return {"message": "Protected content", "user": user.username}

# Require any of these roles
@app.get("/admin-or-moderator")
def admin_or_mod_route(user = Depends(auth.roles("admin", "moderator"))):
    return {"message": f"Hello privileged user, {user.username}!"}

# Require all of these roles
@app.get("/admin-and-verified")
def admin_and_verified_route(user = Depends(auth.all_roles("admin", "verified"))):
    return {"message": f"Hello verified admin, {user.username}!"}

# Shortcut for admin-only routes
@app.get("/admin-only")
def admin_only_route(user = Depends(auth.admin)):
    return {"message": f"Hello admin, {user.username}!"}

# Protect a whole router at once
from fastapi import APIRouter
staff_area = APIRouter(dependencies=[auth.required])

# The long-form names still work but are deprecated and will be removed in 1.0:
# auth.get_current_active_user_dependency(), auth.require_roles([...]),
# auth.require_all_roles([...]), auth.is_admin()
```

### Cookie-Based Authentication

FastAuth supports both header-based and cookie-based authentication:

```python
auth = FastAuth(
    # ... other parameters ...
    use_cookie=True,        # Enable cookie support
    cookie_secure=True,     # Only send the cookie over HTTPS (set False for local dev)
    cookie_samesite="lax",  # SameSite policy
)
```

With cookie-based auth enabled:

- The `/token` endpoint sets an HTTP-only `access_token` cookie that expires together with the token
- Protected routes accept an explicit `Authorization: Bearer` header first and fall back to the cookie
- `cookie_secure` defaults to `False` in development (cookies work on `http://localhost`) and `True` in production mode
- `/logout` clears the cookie
- HTTP-only cookies protect the token from JavaScript access (XSS)

> **Local development tip:** browsers may refuse `Secure` cookies over plain HTTP.
> Pass `cookie_secure=False` while developing on `http://localhost` and keep the
> default `True` in production.

### Password Reset and Email Verification

FastAuth ships the account flows real apps need. Token *delivery* is your app's job
(usually email); register a hook for each flow. Without a hook, tokens are printed
to the console in development so you can try the flows locally:

```python
@auth.on_password_reset
def send_reset(user, token):
    send_email(user.email, f"Reset your password with this token: {token}")

@auth.on_email_verify
def send_verify(user, token):
    send_email(user.email, f"Verify your email with this token: {token}")
```

The flows themselves are already mounted by `auth.setup(app)`:

- `POST /password/forgot` `{"email"}`: always returns 200 (no account discovery); issues a single-use reset token
- `POST /password/reset` `{"token", "new_password"}`: sets the new password and logs the user out everywhere
- `POST /password/change` `{"current_password", "new_password"}` (logged in): rotates the password, revokes old sessions
- `POST /email/verify/request` (logged in) then `POST /email/verify` `{"token"}`: marks the email verified
- `POST /logout/all` (logged in): invalidates every token on every device

Require a verified email on any route:

```python
@app.get("/billing")
def billing(user: User = Depends(auth.verified_user)):
    ...
```

You can also add custom claims to every issued JWT:

```python
@auth.token_claims
def claims(user):
    return {"plan": user.plan}
```

## Database Initialization

### CLI Initialization

FastAuth provides a convenient CLI tool for database initialization:

```bash
# Just provide your app file - FastAuth will extract settings automatically
fastauth app.py

# Or use explicit parameters
fastauth --db-url="sqlite:///./app.db" --secret-key="your-secret-key"

# Customize the superadmin credentials
fastauth app.py --username="admin" --password="secure_password"

# Run specific initialization steps only
fastauth app.py --init-db --init-roles --create-superadmin
```

The CLI auto-detects `DATABASE_URL` and `SECRET_KEY` from (in order): environment
variables, a `.env` file, the app file itself, and common config files
(`config.py`, `settings.py`, `db.py`, `database.py`, `models.py`), including
imported `engine` objects.

### Programmatic Initialization

```python
# During application startup (see the lifespan example in Quick Start)
auth.initialize_db(
    create_tables=True,          # Create database tables
    init_roles=True,             # Initialize standard roles
    create_admin=True,           # Create superadmin if needed
    admin_username="superadmin",
    admin_password="admin123",   # Change this in production!
)

# Or create a superadmin at any time
auth.create_superadmin(username="admin", password="secure_password")
```

> Pass `admin_username` and `admin_password` explicitly when initializing during
> app startup. Otherwise FastAuth will prompt interactively on the console.

## Role-Based Authorization

### Standard Roles

The initialization creates these standard roles:

- `superadmin`: Super administrator with all privileges
- `admin`: Administrator with management privileges
- `moderator`: User with content moderation privileges
- `premium`: Premium tier user
- `verified`: Verified user
- `user`: Standard user with basic privileges

### Role Requirements

```python
# Require any of these roles (OR condition)
@app.get("/admin-or-moderator")
def admin_route(user = Depends(auth.roles("admin", "moderator"))):
    return {"message": "Admin or moderator area"}

# Require all of these roles (AND condition)
@app.get("/premium-and-verified")
def premium_verified_route(user = Depends(auth.all_roles("premium", "verified"))):
    return {"message": "Premium and verified area"}

# Shortcut for admin-only routes
@app.get("/admin-only")
def admin_only(user = Depends(auth.admin)):
    return {"message": "Admin only area"}
```

### Role Management API

Included automatically by `auth.setup(app)`, or add manually:

```python
role_router = auth.get_role_router()
app.include_router(role_router)
```

## Customization Levels

Every knob is optional. Start with nothing and turn dials as your project grows:

**Level 0 · Zero config**: `FastAuth(engine=engine)` + `auth.setup(app)`. FastAuth manages a development secret (in `.fastauth-secret`) and cookies work on localhost.

**Level 1 · Small tweaks**: constructor options with safe defaults: token lifetimes, `password_min_length`, `use_cookie`, `cookie_samesite`, `production`.

**Level 2 · Your models and routes**: pass a custom `user_model`, your own `session_getter`, or mount routers selectively with `auth.get_auth_router()` / `auth.get_role_router()`.

**Level 3 · Ultra custom**: build any flow from the public primitives: `auth.token_manager`, `auth.password_manager`, `auth.authenticate_user()`, and `RoleManager` (see [Custom Authentication Logic](#custom-authentication-logic)).

## Going to Production

One flag turns on the safety rails:

```python
auth = FastAuth(engine=engine, production=True)
# or set the environment variable FASTAUTH_PRODUCTION=1
```

With `production=True`, FastAuth requires a 32+ character secret from the `SECRET_KEY` environment variable (generate with `openssl rand -hex 32`), defaults `cookie_secure` to `True`, and refuses the default superadmin password.

Deploy checklist:

1. Set `SECRET_KEY` in your host's environment
2. Turn on `production=True` (or `FASTAUTH_PRODUCTION=1`)
3. Serve over HTTPS
4. Create the superadmin with a strong, unique password
5. Swap SQLite for a server database if you expect real traffic (any SQLModel/SQLAlchemy engine works)
6. Run with `uv run fastapi run main.py` instead of `fastapi dev`

For schema changes on a live database, add [Alembic](https://alembic.sqlalchemy.org/) migrations; SQLModel's `create_all` only creates missing tables.

## API Reference

### Authentication Endpoints

- `POST /token` - Login and get access + refresh tokens (sets cookie when enabled)
- `POST /token/refresh` - Send `{"refresh_token": "..."}` to get a new access token
- `POST /users` - Register a new user (username **and** email must be unique)
- `GET /users/me` - Get current user information
- `POST /logout` - Clear the authentication cookie
- `POST /logout/all` - Revoke every token for the current user (all devices)
- `POST /password/forgot` - Issue a password reset token (delivered via your hook)
- `POST /password/reset` - Set a new password with a single-use reset token
- `POST /password/change` - Change the logged-in user's password
- `POST /email/verify/request` - Issue an email verification token
- `POST /email/verify` - Confirm an email address

### Role Management Endpoints

All under `/roles` by default:

- `POST /roles/` - Create a new role (admin only)
- `GET /roles/` - Get all roles (authenticated users)
- `GET /roles/{role_id}` - Get a specific role (authenticated users)
- `PUT /roles/{role_id}` - Update a role (admin only)
- `DELETE /roles/{role_id}` - Delete a role (admin only)
- `POST /roles/assign/{user_id}/{role_id}` - Assign role to user (admin only)
- `DELETE /roles/assign/{user_id}/{role_id}` - Remove role from user (admin only)
- `GET /roles/user/{user_id}` - Get all roles for a user (authenticated users)

## Error Handling

FastAuth ships specialized exception classes and returns a consistent JSON structure
for every auth error (handlers are registered by `auth.setup(app)`):

```python
from fastauth import (
    CredentialsException,     # Authentication failures (401)
    TokenException,           # Token verification issues (401)
    RefreshTokenException,    # Refresh token problems (401)
    InactiveUserException,    # User account is disabled (403)
    PermissionDeniedException,# Insufficient permissions (403)
    UserNotFoundException,    # User doesn't exist (404)
    RoleNotFoundException,    # Role doesn't exist (404)
    UserExistsException,      # Username/email already taken (409)
    EmailNotVerifiedException,# Route requires a verified email (403)
    WeakPasswordException,    # Password below minimum length (422)
    RoleExistsException,      # Role already exists (409)
)
```

```json
{
  "error": {
    "code": "FASTAUTH_INVALID_CREDENTIALS",
    "message": "Human-readable error description",
    "status_code": 401
  }
}
```

## Advanced Usage

### Custom User Models

You can use a custom user model with FastAuth. Role checks and the CLI respect it:

```python
class CustomUser(SQLModel, table=True):
    __tablename__ = "user"  # Keep the table name expected by the role system

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True)
    hashed_password: str
    disabled: bool = Field(default=False)
    # Additional fields...
    first_name: str = Field(default="")
    last_name: str = Field(default="")

auth = FastAuth(
    # ... other parameters ...
    user_model=CustomUser,
)
```

> Don't import fastauth's built-in `User` model in the same app when using a custom
> one; two table models for the same table will conflict.

### Custom Authentication Logic

```python
@app.post("/custom-login")
async def custom_login(
    username: str,
    password: str,
    session: Session = Depends(get_session),
):
    user = auth.authenticate_user(username, password, session=session)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}
```

## Security Best Practices

1. **Deploy your FastAPI app with HTTPS** in production environments
2. **Use a strong secret key**: generate one with `openssl rand -hex 32` and store it securely (e.g., environment variables)
3. **Change the default superadmin password**. Never ship `admin123`
4. **Configure appropriate token expiration times** based on your security requirements
5. **Keep `cookie_secure=True`** in production when using cookie-based authentication
6. **Consider implementing rate limiting** on your authentication endpoints to prevent brute force attacks

## Versioning

FastAuth follows [semantic versioning](https://semver.org). Each number in
`MAJOR.MINOR.PATCH` carries a promise, so you can tell what an upgrade costs
before running it.

| Change | Bumps | You need to |
| --- | --- | --- |
| Bug fix, docs, internal refactor | **PATCH** `0.6.0 → 0.6.1` | Nothing |
| New parameter, endpoint, or helper | **MINOR** `0.6.1 → 0.7.0` | Nothing, existing code keeps working |
| Rename, removal, or changed behaviour | **MAJOR** `0.7.0 → 1.0.0` | Read the notes and migrate |

**Only a major release can break your code.** Breaking means removing or
renaming anything public, changing a default that alters behaviour, changing a
response shape or error code, requiring a new database column, or dropping a
Python version. Adding an optional parameter, a new endpoint, or a clearer
error message is not breaking.

FastAuth is pre-1.0, so the API is still settling: in the `0.x` series a minor
bump is where an unavoidable break would land, and each is called out in the
release notes. From 1.0 the rules apply strictly.

### Deprecations

Nothing public disappears without notice:

1. A replacement ships in a minor release; the old name keeps working
2. The old name emits a `DeprecationWarning` naming its replacement and the
   release that will remove it
3. Removal happens in the next major release, never sooner

Deprecated in 0.7.0, removed in 1.0:

| Deprecated | Replacement |
| --- | --- |
| `auth.get_current_active_user_dependency()` | `auth.current_user` |
| `auth.is_admin()` | `auth.admin` |
| `auth.require_roles([...])` | `auth.roles(...)` |
| `auth.require_all_roles([...])` | `auth.all_roles(...)` |

Python hides `DeprecationWarning` by default. To catch them during an upgrade,
add this to your `pyproject.toml` so deprecated calls fail your tests:

```toml
[tool.pytest.ini_options]
filterwarnings = ["error::DeprecationWarning"]
```

Version numbers describe the API, not your database. A minor release may add a
column, and SQLModel's `create_all` will not add it to an existing table;
release notes flag any release needing a migration.

## Changelog

Full release history, including upgrade notes, is in
**[CHANGELOG.md](CHANGELOG.md)**. It is also the source for the
[GitHub release notes](https://github.com/hu55ain3laa/fastauth/releases), so
the two can never drift apart.

The latest release is
**[v0.7.0](https://github.com/hu55ain3laa/fastauth/releases/tag/v0.7.0)**: a new
documentation site, four deprecated long-form dependency names, and a fix for
`token_url` breaking Swagger's Authorize button under a mount prefix.

## Project Structure

FastAuth follows a modular architecture for better maintainability:

```
fastauth/
├── core/           # The main FastAuth class
├── security/       # Password hashing and JWT token management
├── models/         # User, role, and token models/schemas
├── routers/        # Route handlers for auth and roles
├── dependencies/   # FastAPI dependencies for auth and roles
├── exceptions.py   # Standardized exception classes and handlers
├── cli.py          # Database initialization CLI
└── utils/          # Utility functions and helpers
```

## License

MIT
