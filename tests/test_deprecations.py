"""The superseded method names must keep working until 1.0.

Each old name should warn once, point at the caller, and return a dependency
that behaves exactly like its replacement.
"""

import pytest
from sqlmodel import create_engine

from fastauth import FastAuth


@pytest.fixture(scope="module")
def auth():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}
    )
    return FastAuth(secret_key="a" * 32, engine=engine)


@pytest.mark.parametrize(
    "call, replacement",
    [
        (lambda a: a.get_current_active_user_dependency(), "auth.current_user"),
        (lambda a: a.is_admin(), "auth.admin"),
        (lambda a: a.require_roles(["admin", "premium"]), "auth.roles"),
        (lambda a: a.require_all_roles(["premium", "verified"]), "auth.all_roles"),
    ],
)
def test_deprecated_names_warn_and_still_work(auth, call, replacement):
    with pytest.warns(DeprecationWarning) as record:
        dependency = call(auth)

    assert callable(dependency)
    message = str(record[0].message)
    assert "deprecated" in message
    assert replacement in message
    assert "1.0" in message


def test_role_aliases_accept_the_same_arguments(auth):
    """auth.roles takes varargs or a list; the old name took a list only."""
    with pytest.warns(DeprecationWarning):
        from_old = auth.require_roles(["admin", "premium"])

    from_varargs = auth.roles("admin", "premium")
    from_list = auth.roles(["admin", "premium"])

    assert all(callable(d) for d in (from_old, from_varargs, from_list))


def test_token_url_is_absolute_by_default(auth):
    """Swagger's Authorize button breaks on a relative tokenUrl under a prefix."""
    assert auth.token_url == "/token"
    assert auth.oauth2_scheme.model.flows.password.tokenUrl == "/token"


def test_token_url_missing_slash_is_normalised():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    instance = FastAuth(secret_key="a" * 32, engine=engine, token_url="token")
    assert instance.token_url == "/token"
