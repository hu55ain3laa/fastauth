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

- Dependabot pull requests for patch and minor updates now merge themselves
  once CI is green. Major updates never do: they are labelled `major-update`
  and commented with what to check. The split exists because Dependabot
  proposed `upload-artifact` 4 to 7 without the paired `download-artifact`,
  which would have broken releases in a way no CI run could have caught.
  The workflow reads every check on the commit itself and merges only when
  all of them have finished successfully, so no branch protection is needed
  and `main` stays open for the release workflow to push to.

### Fixed

- The dependency audit reported advisories against the CI runner's own build
  tooling, which users never inherit from installing `fastauth_iq`. It now
  audits the project's dependency tree rather than the whole environment, so a
  finding means something users are actually exposed to.

## [0.8.0] - 2026-08-11

### Added

- `scripts/prepare_release.py` bumps every version location and rolls the
  changelog's `[Unreleased]` section into a dated release in one command. It
  refuses to run when there are no notes to release.
- `scripts/check_release.py` verifies the version agrees across all four files
  it is written in, that the changelog has notes for it, and that no stale
  domains remain. CI runs it on every push and again before publishing.
- CI now lints and builds the documentation site, so a broken docs build fails
  the pull request instead of surfacing on Vercel after merge.
- A one-button **Release** workflow: it reads the changelog, infers whether the
  change is a patch, minor or major, bumps every version location, tests,
  commits, tags and pushes.
- `prepare_release.py` infers the bump from the `[Unreleased]` headings, so the
  version follows from what changed rather than from a judgement call.

- **Dependency and security automation**: Dependabot for Python, npm and GitHub
  Actions; CodeQL analysis; `pip-audit` and `pnpm audit` on every push and
  weekly, so a CVE published against an unchanged dependency is still found.
- Coverage measurement with a regression threshold. Currently 81% overall, with
  the security-critical paths higher: `core/auth.py` 94%, routers 96%,
  `security/` 97-100%.
- `tests/test_docs_match_api.py` asserts the documented API matches the API
  that exists: the routes the app mounts, the endpoint reference, `AGENTS.md`,
  and the route count the landing page advertises. Documentation drift is now
  a test failure rather than something noticed later by a user.
- A weekly external link check for the documentation, advisory only so a
  third-party site being briefly unreachable never fails a build.
- `tests/test_cli.py` covers settings discovery, `.env` parsing, role
  initialization and superadmin creation. CLI coverage rises from 34% to 74%
  and the project total from 81% to 89%.

### Fixed

- **The CLI could discover a wrong database URL.** A pattern like
  `create_engine("sqlite:///" + name)` matched the settings regex and yielded
  `"sqlite:///"` — a URL that looks plausible and points nowhere. The patterns
  now require the string literal to be the complete value, so a concatenated
  expression falls through to importing the module and evaluating it properly.
- **A `.env` file could override the real environment.** `SECRET_KEY` set in a
  deployment was silently replaced by a stale `.env` shipped in the image,
  signing every token with the wrong key. The real environment now always
  wins, and `.env` fills in only what is missing.
- Removed an unused import from `exceptions.py`.
- The CI consistency job failed on every dependency-update pull request. Its
  changelog check diffed against the base branch with a three-dot range, which
  needs a merge base that the default shallow clone does not fetch. The job now
  checks out full history, the check is advisory and cannot fail a build, and
  dependency bumps skip it entirely.

### Changed

- Every workflow now declares least-privilege `permissions`, so CI jobs get a
  read-only token instead of inheriting the repository default.
- The publish workflow validates the release before publishing rather than
  after, so a missing changelog section stops the release instead of producing
  one with empty notes.
- The publish workflow now runs the full Python 3.10-3.14 matrix rather than
  3.12 alone. A tag can point at a commit that never went through pull-request
  CI, so this is the only guarantee that what ships runs everywhere it claims.

### Upgrading

No action needed for most projects, but one behaviour changed deliberately:

**A `.env` file no longer overrides real environment variables.** Previously a
`.env` value won; now the environment does, and `.env` fills in only what is
missing. This matches dotenv tooling elsewhere and closes a real hazard, where
a stale `.env` in a deployed image silently replaced the production
`SECRET_KEY`.

If you relied on `.env` taking precedence, unset the variable in the
environment instead, or pass the value explicitly with `--secret-key` /
`--db-url`.

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

[Unreleased]: https://github.com/hu55ain3laa/fastauth/compare/v0.8.0...HEAD
[0.8.0]: https://github.com/hu55ain3laa/fastauth/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/hu55ain3laa/fastauth/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/hu55ain3laa/fastauth/releases/tag/v0.6.0
[0.5.0]: https://github.com/hu55ain3laa/fastauth/releases
[0.4.0]: https://github.com/hu55ain3laa/fastauth/releases
