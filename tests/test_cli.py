"""Tests for the CLI's settings discovery and database initialization.

Discovery scrapes a user's own source files for a database URL and secret key.
It runs before anything else and, when it guesses wrong, produces a confusing
failure a long way from the cause — so it is worth pinning down precisely.
"""

from __future__ import annotations

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

from fastauth import FastAuth
from fastauth.cli import (
    _find_in_file,
    _settings_from_file,
    create_superadmin,
    discover_settings,
    import_module_variables,
    initialize_roles,
    load_environment_variables,
)
from fastauth.models.role import Role


@pytest.fixture
def auth(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path/'cli.db'}", connect_args={"check_same_thread": False}
    )
    instance = FastAuth(secret_key="a" * 32, engine=engine)
    SQLModel.metadata.create_all(engine)
    return instance


# ---------------------------------------------------------------------------
# Reading values out of a file
# ---------------------------------------------------------------------------


def test_find_in_file_returns_none_for_missing_file():
    assert _find_in_file("/nowhere/at/all.py", [r"X\s*=\s*'([^']+)'"]) is None


def test_find_in_file_matches_the_first_pattern_that_hits(tmp_path):
    target = tmp_path / "config.py"
    target.write_text('SECRET_KEY = "from-config"\n')

    found = _find_in_file(
        str(target),
        [r"NOPE\s*=\s*['\"]([^'\"]+)['\"]", r"SECRET_KEY\s*=\s*['\"]([^'\"]+)['\"]"],
    )
    assert found == "from-config"


@pytest.mark.parametrize(
    "source, expected",
    [
        ('DATABASE_URL = "sqlite:///./a.db"', "sqlite:///./a.db"),
        ("db_url = 'sqlite:///./b.db'", "sqlite:///./b.db"),
        ('engine = create_engine("sqlite:///./c.db")', "sqlite:///./c.db"),
    ],
)
def test_settings_from_file_recognises_each_db_url_style(tmp_path, source, expected):
    target = tmp_path / "app.py"
    target.write_text(source + "\n")

    db_url, _ = _settings_from_file(str(target), None, None)
    assert db_url == expected


def test_settings_from_file_keeps_values_it_was_given(tmp_path):
    """An explicit --db-url must not be overwritten by something in a file."""
    target = tmp_path / "app.py"
    target.write_text('DATABASE_URL = "sqlite:///./from-file.db"\nSECRET_KEY = "f"\n')

    db_url, secret = _settings_from_file(str(target), "sqlite:///./explicit.db", "explicit")
    assert db_url == "sqlite:///./explicit.db"
    assert secret == "explicit"


def test_settings_from_file_reads_a_live_engine_object(tmp_path):
    """Falls back to importing the module when the regexes find nothing."""
    target = tmp_path / "database.py"
    target.write_text(
        "from sqlmodel import create_engine\n"
        "engine = create_engine('sqlite:///' + 'joined.db')\n"
    )

    db_url, _ = _settings_from_file(str(target), None, None)
    assert db_url is not None and "joined.db" in db_url


# ---------------------------------------------------------------------------
# Importing a module
# ---------------------------------------------------------------------------


def test_import_module_variables_ignores_non_python_files(tmp_path):
    target = tmp_path / "notes.txt"
    target.write_text("DATABASE_URL = 'x'")
    assert import_module_variables(str(target)) == {}


def test_import_module_variables_survives_a_broken_module(tmp_path, capsys):
    """A user's file that raises on import must not crash the CLI."""
    target = tmp_path / "broken.py"
    target.write_text("raise RuntimeError('boom')\n")

    assert import_module_variables(str(target)) == {}
    assert "Error importing module" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Environment loading
# ---------------------------------------------------------------------------


def test_env_file_is_parsed_with_comments_and_quotes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "# a comment\n"
        "\n"
        'SECRET_KEY="quoted-secret"\n'
        "DATABASE_URL='sqlite:///./env.db'\n"
        "MALFORMED\n"
        "WITH_EQUALS=a=b\n"
    )

    env = load_environment_variables()
    assert env["SECRET_KEY"] == "quoted-secret"
    assert env["DATABASE_URL"] == "sqlite:///./env.db"
    assert env["WITH_EQUALS"] == "a=b"
    assert "MALFORMED" not in env


def test_real_environment_wins_over_a_dotenv_file(tmp_path, monkeypatch):
    """A stale .env must never override the deployed environment.

    Production sets SECRET_KEY in the environment. If a .env file shipped in
    the image could override it, every token would be signed with the wrong
    key and nobody would be told.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SECRET_KEY", "real-production-secret")
    (tmp_path / ".env").write_text("SECRET_KEY=stale-development-secret\n")

    env = load_environment_variables()
    assert env["SECRET_KEY"] == "real-production-secret"


def test_dotenv_still_fills_in_what_the_environment_lacks(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    (tmp_path / ".env").write_text("DATABASE_URL=sqlite:///./from-dotenv.db\n")

    env = load_environment_variables()
    assert env["DATABASE_URL"] == "sqlite:///./from-dotenv.db"


# ---------------------------------------------------------------------------
# End-to-end discovery
# ---------------------------------------------------------------------------


def test_discover_settings_prefers_explicit_arguments(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./env.db")
    monkeypatch.setenv("SECRET_KEY", "env-secret")

    db_url, secret = discover_settings(None, "sqlite:///./explicit.db", "explicit-secret")
    assert db_url == "sqlite:///./explicit.db"
    assert secret == "explicit-secret"


def test_discover_settings_falls_back_to_the_environment(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./env.db")
    monkeypatch.setenv("SECRET_KEY", "env-secret")

    db_url, secret = discover_settings(None, None, None)
    assert db_url == "sqlite:///./env.db"
    assert secret == "env-secret"


def test_discover_settings_searches_neighbouring_config_files(tmp_path, monkeypatch):
    """Values can live in config.py next to the app file, not only in it."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)

    (tmp_path / "main.py").write_text("app = None\n")
    (tmp_path / "config.py").write_text(
        'DATABASE_URL = "sqlite:///./neighbour.db"\nSECRET_KEY = "neighbour-secret"\n'
    )

    db_url, secret = discover_settings(str(tmp_path / "main.py"), None, None)
    assert db_url == "sqlite:///./neighbour.db"
    assert secret == "neighbour-secret"


def test_discover_settings_returns_none_when_nothing_is_found(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)

    assert discover_settings(None, None, None) == (None, None)


# ---------------------------------------------------------------------------
# Database initialization
# ---------------------------------------------------------------------------


def test_initialize_roles_creates_the_standard_set(auth):
    initialize_roles(auth)

    with Session(auth.engine) as session:
        names = {r.name for r in session.exec(select(Role)).all()}
    assert names == {"superadmin", "admin", "moderator", "premium", "verified", "user"}


def test_initialize_roles_is_idempotent(auth):
    initialize_roles(auth)
    initialize_roles(auth)

    with Session(auth.engine) as session:
        assert len(session.exec(select(Role)).all()) == 6


def test_create_superadmin_is_idempotent(auth):
    first = create_superadmin(auth, username="root", password="a-strong-password")
    assert first["is_new"] is True

    second = create_superadmin(auth, username="root", password="a-strong-password")
    assert second["is_new"] is False
    assert second["username"] == "root"


def test_create_superadmin_promotes_an_existing_user(auth):
    """Naming an existing user grants the role rather than failing."""
    from fastauth.models.user import User

    with Session(auth.engine) as session:
        session.add(
            User(
                username="already-here",
                email="a@b.c",
                hashed_password=auth.get_password_hash("pw"),
                disabled=False,
            )
        )
        session.commit()

    result = create_superadmin(auth, username="already-here", password="unused")
    assert result["is_new"] is False
    assert result["username"] == "already-here"


def test_production_refuses_the_default_password(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path/'prod.db'}", connect_args={"check_same_thread": False}
    )
    instance = FastAuth(secret_key="b" * 32, engine=engine, production=True)
    SQLModel.metadata.create_all(engine)

    with pytest.raises(ValueError, match="admin123"):
        create_superadmin(instance, username="root", password="admin123")


def test_production_requires_an_explicit_password(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path/'prod2.db'}", connect_args={"check_same_thread": False}
    )
    instance = FastAuth(secret_key="c" * 32, engine=engine, production=True)
    SQLModel.metadata.create_all(engine)

    with pytest.raises(ValueError, match="explicit superadmin password"):
        create_superadmin(instance, username="root")
