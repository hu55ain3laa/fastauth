# Changelog

All notable changes to FastAuth are documented here. This file is the source
for GitHub release notes, so each version's section is what you see on the
[releases page](https://github.com/hu55ain3laa/fastauth/releases).

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and FastAuth follows [semantic versioning](https://semver.org): only a major
release can break your code. See
[Versioning](https://fastauth.pythowner.com/docs/versioning) for the full policy.

## [Unreleased]

### Added

- `scripts/prepare_release.py` bumps every version location and rolls the
  changelog's `[Unreleased]` section into a dated release in one command. It
  refuses to run when there are no notes to release.
- `scripts/check_release.py` verifies the version agrees across all four files
  it is written in, that the changelog has notes for it, and that no stale
  domains remain. CI runs it on every push and again before publishing.
- CI now lints and builds the documentation site, so a broken docs build fails
  the pull request instead of surfacing on Vercel after merge.

### Changed

- The publish workflow validates the release before publishing rather than
  after, so a missing changelog section stops the release instead of producing
  one with empty notes.

## [0.7.0] - 2026-08-11

### Added

- **New documentation site** at [fastauth.pythowner.com](https://fastauth.pythowner.com),
  built with Next.js and MDX and deployed on Vercel. Includes full-text search,
  flow diagrams for the token and password reset cycles, a concepts guide that
  explains hashing, JWTs, cookies and RBAC from scratch, a symptom-first
  troubleshooting page, and a reading mode.
- **`llms.txt`** so AI coding agents integrate FastAuth correctly rather than
  guessing at the API.
- **A documented versioning and deprecation policy**, in the README and the docs.

### Changed

- **One obvious way to do each thing.** Four long-form names are superseded by
  shorter equivalents. The old names still work and now emit a
  `DeprecationWarning`; they will be removed in 1.0.

  | Deprecated | Replacement |
  | --- | --- |
  | `auth.get_current_active_user_dependency()` | `auth.current_user` |
  | `auth.is_admin()` | `auth.admin` |
  | `auth.require_roles([...])` | `auth.roles(...)` |
  | `auth.require_all_roles([...])` | `auth.all_roles(...)` |

  The replacements accept role names directly or as a list, so both
  `auth.roles("admin", "moderator")` and `auth.roles(["admin", "moderator"])`
  work. The deprecated forms now accept either shape too, rather than requiring
  a list.

- **`session_getter` is documented.** Leave it out and FastAuth opens sessions
  on the engine you gave it, which is what most apps want. Pass your own only
  when routes must share a session with the rest of your app.

### Fixed

- **`token_url` now defaults to `/token`.** It previously defaulted to `token`
  with no leading slash, while the router registers `/token`. That value is
  what Swagger's **Authorize** button posts to, and a relative URL resolves
  against the docs path, breaking as soon as the app is mounted under a prefix.
  A missing leading slash is now added automatically, so passing `"token"` is
  corrected rather than broken.

### Removed

- The previous hand-written static documentation site (`index.html`,
  `easy-mode.html`, `style.css`, `scripts.js`), replaced by the new site.

### Upgrading

No action needed. Deprecated names keep working until 1.0. To find them in your
code, make deprecation warnings fail your tests:

```toml
[tool.pytest.ini_options]
filterwarnings = ["error::DeprecationWarning"]
```

## [0.6.0] - 2026-08-11

### Added

- **Password reset**: `POST /password/forgot` + `POST /password/reset` with
  stateless single-use tokens (a token dies the moment the password changes)
- **Password change**: `POST /password/change` for logged-in users
- **Email verification**: `POST /email/verify/request` + `POST /email/verify`,
  plus the `auth.verified_user` dependency and an `email_verified` column
- **Token revocation**: `POST /logout/all` and `auth.revoke_all_tokens()`
  invalidate all sessions via a `token_version` column; password reset and
  change do this automatically
- **Delivery hooks**: `@auth.on_password_reset` and `@auth.on_email_verify`
  connect the flows to your email sending; in development, tokens print to the
  console
- **Custom JWT claims**: `@auth.token_claims` merges your claims into every
  issued token

### Changed

- A wrong `__tablename__` on a custom user model now fails at startup with
  instructions instead of breaking silently at runtime

### Upgrading

This release adds two columns to the user table. For SQLite development
databases, delete the file and restart. For live databases:

```sql
ALTER TABLE user ADD COLUMN email_verified BOOLEAN DEFAULT 0;
ALTER TABLE user ADD COLUMN token_version INTEGER DEFAULT 0;
```

Or use Alembic; see
[Going to Production](https://fastauth.pythowner.com/docs/production).

## [0.5.0]

### Added

- **Zero-config start**: `secret_key` is now optional; FastAuth reads
  `SECRET_KEY` / `FASTAUTH_SECRET_KEY` from the environment, or manages a
  development secret in `.fastauth-secret`
- **Production mode**: `production=True` (or `FASTAUTH_PRODUCTION=1`) requires a
  strong secret, secures cookies, and refuses the default admin password
- **Ready-made dependencies**: `auth.current_user`, `auth.admin`,
  `auth.roles(...)`, `auth.all_roles(...)`, `auth.required`,
  `auth.admin_required`
- **Password rules**: registration enforces `password_min_length` (default 8,
  set 0 to disable) with a `FASTAUTH_WEAK_PASSWORD` error
- **AGENTS.md**: machine-readable API reference so AI coding assistants
  integrate FastAuth correctly

### Changed

- `cookie_secure` now defaults to `False` in development and `True` in
  production mode (explicit values always win)
- An explicit `Authorization: Bearer` header now takes precedence over the auth
  cookie
- `engine` is keyword-friendly and its absence is a clear error

## [0.4.0]

### Added

- `auth.setup(app)`: one-call integration
- `POST /logout` endpoint that clears the auth cookie
- `cookie_secure` / `cookie_samesite` options; the auth cookie now expires with
  the token
- `/token/refresh` accepts a documented `RefreshRequest` body (visible in
  `/docs`)
- GitHub Actions CI running the test suite on Python 3.10–3.14

### Fixed

- Compatibility with modern `bcrypt` (≥ 4.1, including 5.x) by hashing with
  bcrypt directly. The unmaintained `passlib` dependency is gone, and existing
  password hashes keep working
- Removed the shared long-lived database session; every operation now uses a
  short-lived session, fixing thread-safety issues and a bug where one failed
  request could break all subsequent logins
- Disabled users can no longer log in or refresh tokens
- Registering with a duplicate email now returns a clean `409` instead of a
  server error
- Role checks and the CLI now respect custom user models
- Removed debug `print()` statements that leaked token prefixes to stdout
- Removed the unused `python-jose` dependency

### Removed

**Breaking changes:**

- Python 3.10+ is now required
- The deprecated root-level `fastauth.py` / `User.py` compatibility shims were
  removed; import everything from the `fastauth` package instead
- `FastAuth` no longer exposes a shared `.session` attribute; pass a session to
  `authenticate_user(..., session=...)` or let it create one automatically

[Unreleased]: https://github.com/hu55ain3laa/fastauth/compare/v0.7.0...HEAD
[0.7.0]: https://github.com/hu55ain3laa/fastauth/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/hu55ain3laa/fastauth/releases/tag/v0.6.0
[0.5.0]: https://github.com/hu55ain3laa/fastauth/releases
[0.4.0]: https://github.com/hu55ain3laa/fastauth/releases
