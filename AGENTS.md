# FastAuth (fastauth_iq): guide for AI agents

FastAuth is an authentication and authorization library for FastAPI + SQLModel.
It provides JWT access/refresh tokens, cookie support, bcrypt password hashing,
role-based access control, ready-made routes, and database initialization.

- Package name on PyPI: `fastauth_iq` (import as `fastauth`)
- Python: 3.10+ · Stack: FastAPI, SQLModel (SQLAlchemy engine), PyJWT, bcrypt
- Docs site: https://fastauth.vercel.app
- Beginner tutorial: https://fastauth.vercel.app/docs/easy-mode
- Source: https://github.com/hu55ain3laa/fastauth

## Install

```bash
uv add fastauth_iq "fastapi[standard]"
```

## Minimal integration (zero config)

```python
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from sqlmodel import create_engine
from fastauth import FastAuth, User

engine = create_engine("sqlite:///./app.db", connect_args={"check_same_thread": False})
auth = FastAuth(engine=engine)  # dev secret auto-managed in .fastauth-secret

@asynccontextmanager
async def lifespan(app: FastAPI):
    auth.initialize_db(admin_username="admin", admin_password="admin123")
    yield

app = FastAPI(lifespan=lifespan)
auth.setup(app)  # mounts all routes + error handlers

@app.get("/protected")
def protected(user: User = Depends(auth.current_user)):
    return {"hello": user.username}
```

Run: `uv run fastapi dev main.py` → interactive docs at `/docs`.

## Production

```python
auth = FastAuth(engine=engine, production=True)
```

Production mode: requires a 32+ char secret from `SECRET_KEY` /
`FASTAUTH_SECRET_KEY` env (or explicit `secret_key=`), defaults
`cookie_secure=True`, and refuses the default superadmin password
(`admin123`). `FASTAUTH_PRODUCTION=1` env also enables it.
Generate a secret: `openssl rand -hex 32`.

## FastAuth constructor

| Parameter | Default | Meaning |
|---|---|---|
| `secret_key` | `None` | JWT signing key. Fallback: env vars, then a generated `.fastauth-secret` file (dev only) |
| `engine` | required | SQLModel/SQLAlchemy engine |
| `algorithm` | `"HS256"` | JWT algorithm |
| `use_cookie` | `True` | Also accept/set an HTTP-only `access_token` cookie |
| `token_url` | `"/token"` | Login endpoint path used by the OAuth2 scheme |
| `access_token_expires_in` | `30` | Access token lifetime (minutes) |
| `refresh_token_expires_in` | `7` | Refresh token lifetime (days) |
| `user_model` | `User` | Custom SQLModel user class; must set `__tablename__ = "user"` (a clear error is raised otherwise) and should include the `email_verified` and `token_version` columns for verification/revocation features |
| `cookie_secure` | `None` | `None` → `True` in production, `False` in dev |
| `cookie_samesite` | `"lax"` | SameSite cookie policy |
| `production` | `None` | Safety checks on. Falls back to `FASTAUTH_PRODUCTION` env |
| `password_min_length` | `8` | Enforced on registration and password reset/change; `0` disables |
| `reset_token_expires_in` | `30` | Password reset token lifetime (minutes) |
| `verify_token_expires_in` | `1440` | Email verification token lifetime (minutes) |

## Ready-made dependencies (preferred API)

```python
user: User = Depends(auth.current_user)          # any logged-in, active user
user: User = Depends(auth.admin)                 # user with the admin role
user: User = Depends(auth.roles("a", "b"))       # any of these roles
user: User = Depends(auth.all_roles("a", "b"))   # all of these roles
user: User = Depends(auth.verified_user)         # requires verified email
router = APIRouter(dependencies=[auth.required])        # protect a whole router
router = APIRouter(dependencies=[auth.admin_required])  # admin-only router
```

Long-form equivalents still work but are **deprecated** and will be removed in
1.0, emitting a `DeprecationWarning`: `auth.get_current_active_user_dependency()`,
`auth.require_roles([...])`, `auth.require_all_roles([...])`, `auth.is_admin()`.

## Key methods

- `auth.setup(app, session_getter=None, include_role_router=True)`: mount everything
- `auth.initialize_db(create_tables=True, init_roles=True, create_admin=True, admin_username=..., admin_password=...)`
- `auth.create_superadmin(username=..., password=...)`
- `auth.authenticate_user(username, password, session=None)`: returns the user or `False`
- `auth.create_access_token(data)` / `auth.create_refresh_token(data)`
- `auth.get_password_hash(pw)` / `auth.verify_password(pw, hashed)`
- `auth.setup_exception_handlers(app)`: only needed without `setup()`
- `auth.revoke_all_tokens(session, user)`: invalidate every issued token (bumps `user.token_version`)

## Hooks (decorators on the auth instance)

```python
@auth.on_password_reset
def send_reset(user, token): ...     # deliver reset token (e.g. email). Dev fallback: printed to console

@auth.on_email_verify
def send_verify(user, token): ...    # deliver verification token. Dev fallback: printed to console

@auth.token_claims
def claims(user):                    # extra JWT claims merged at login/refresh
    return {"plan": user.plan}
```

## Endpoints added by `auth.setup(app)`

| Method | Path | Notes |
|---|---|---|
| POST | `/token` | OAuth2 form login → access + refresh tokens, sets cookie |
| POST | `/token/refresh` | Body `{"refresh_token": "..."}` → new access token |
| POST | `/users` | Register; username and email unique; password min length |
| GET | `/users/me` | Current user profile |
| POST | `/logout` | Clears the auth cookie |
| POST | `/logout/all` | Revokes every token for the current user (all devices) |
| POST | `/password/forgot` | Body `{"email"}`; always 200 (no user enumeration); delivers reset token via hook |
| POST | `/password/reset` | Body `{"token", "new_password"}`; single-use token; revokes old sessions |
| POST | `/password/change` | Auth required; body `{"current_password", "new_password"}`; revokes old sessions |
| POST | `/email/verify/request` | Auth required; delivers verification token via hook |
| POST | `/email/verify` | Body `{"token"}`; sets `email_verified=True` |
| GET/POST | `/roles/` | List (any user) / create (admin) |
| GET/PUT/DELETE | `/roles/{role_id}` | Read (any user) / update, delete (admin) |
| POST/DELETE | `/roles/assign/{user_id}/{role_id}` | Assign / remove role (admin) |
| GET | `/roles/user/{user_id}` | List a user's roles |

Standard roles created by init: superadmin, admin, moderator, premium, verified, user.

## Errors

All auth errors return `{"error": {"code", "message", "status_code"}}`.
Codes: `FASTAUTH_INVALID_CREDENTIALS` (401), `FASTAUTH_INVALID_TOKEN` (401),
`FASTAUTH_INVALID_REFRESH_TOKEN` (401), `FASTAUTH_INACTIVE_USER` (403),
`FASTAUTH_PERMISSION_DENIED` (403), `FASTAUTH_USER_NOT_FOUND` (404),
`FASTAUTH_ROLE_NOT_FOUND` (404), `FASTAUTH_USER_EXISTS` (409),
`FASTAUTH_ROLE_EXISTS` (409), `FASTAUTH_WEAK_PASSWORD` (422),
`FASTAUTH_EMAIL_NOT_VERIFIED` (403).
Exception classes with the same names (minus prefix) are importable from `fastauth`.

## Customization levels

1. **Zero config**: `FastAuth(engine=engine)` + `auth.setup(app)`
2. **Small**: constructor knobs (expiries, cookies, `password_min_length`, `production`)
3. **Medium**: custom `user_model`, own `session_getter`, mount routers selectively
   (`auth.get_auth_router()`, `auth.get_role_router()`), role dependencies on your routes
4. **Ultra**: build custom flows from primitives: `auth.token_manager`
   (`TokenManager`), `auth.password_manager` (`PasswordManager`), `RoleManager`,
   `auth.authenticate_user()`; see "Custom Authentication Logic" in the docs

## Repo layout / development

```
fastauth/            # the library (core/, security/, models/, routers/, dependencies/, exceptions.py, cli.py)
tests/               # pytest suite (also runs in CI on Python 3.10-3.14)
web/                 # docs site (Next.js, deployed on Vercel); content in web/app/docs/*.mdx
```

- Run tests: `pytest tests/ -v` (needs `pip install -e ".[dev]"`)
- CLI: `fastauth app.py [--init-db --init-roles --create-superadmin]`; auto-detects
  `DATABASE_URL` / `SECRET_KEY` from env, `.env`, or the app file
- Known limits: token revocation is per-user (`/logout/all`), not per-device;
  reset/verify token delivery is your hook's job (no SMTP built in); schema
  migrations are up to you (SQLModel `create_all` creates missing tables only;
  use Alembic for changes, see the docs' migrations section)
