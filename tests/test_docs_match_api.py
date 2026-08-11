"""The documented API must match the API that actually exists.

Three files describe FastAuth's endpoints, and each is read by a different
audience:

  - web/app/docs/endpoints/page.mdx  humans
  - web/app/llms.txt/route.ts        AI coding agents
  - AGENTS.md                        AI coding agents, in-repo

Nothing else notices when one drifts, and a wrong endpoint in AGENTS.md becomes
confidently wrong code in somebody else's project. This turns that drift into a
test failure.

The docs live in the repository rather than the package, so the file-based
tests skip when running against an installed distribution.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi import FastAPI
from sqlmodel import create_engine

from fastauth import FastAuth

REPO = Path(__file__).resolve().parent.parent

# Every route auth.setup(app) is expected to mount. Adding an endpoint means
# updating this list and the documentation, which is the point.
EXPECTED_ROUTES = {
    ("POST", "/token"),
    ("POST", "/token/refresh"),
    ("POST", "/users"),
    ("GET", "/users/me"),
    ("POST", "/logout"),
    ("POST", "/logout/all"),
    ("POST", "/password/forgot"),
    ("POST", "/password/reset"),
    ("POST", "/password/change"),
    ("POST", "/email/verify/request"),
    ("POST", "/email/verify"),
    ("GET", "/roles/"),
    ("POST", "/roles/"),
    ("GET", "/roles/{role_id}"),
    ("PUT", "/roles/{role_id}"),
    ("DELETE", "/roles/{role_id}"),
    ("POST", "/roles/assign/{user_id}/{role_id}"),
    ("DELETE", "/roles/assign/{user_id}/{role_id}"),
    ("GET", "/roles/user/{user_id}"),
}


def build_app() -> FastAPI:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    auth = FastAuth(secret_key="a" * 32, engine=engine)
    app = FastAPI()
    auth.setup(app)
    return app


def mounted_routes() -> set[tuple[str, str]]:
    """Read the real surface from the OpenAPI schema.

    The schema is used rather than app.routes because included routers are
    wrapped rather than flattened, and the schema is the contract clients
    actually see.
    """
    paths = build_app().openapi()["paths"]
    return {
        (method.upper(), path)
        for path, operations in paths.items()
        for method in operations
    }


def read_repo_file(relative: str) -> str:
    path = REPO / relative
    if not path.exists():
        pytest.skip(f"{relative} is not present (running outside the repository)")
    return path.read_text(encoding="utf-8")


def test_mounted_routes_match_expectations():
    """auth.setup(app) mounts exactly the documented set, no more, no less."""
    actual = mounted_routes()

    missing = EXPECTED_ROUTES - actual
    unexpected = actual - EXPECTED_ROUTES

    assert not missing, f"documented routes that no longer exist: {sorted(missing)}"
    assert not unexpected, (
        f"routes exist but are undocumented: {sorted(unexpected)}. "
        "Add them to the endpoints page, llms.txt and AGENTS.md."
    )


def test_route_count_is_advertised_correctly():
    """The landing page and llms.txt both claim a specific number of routes."""
    count = len(mounted_routes())
    assert count == 19, (
        f"{count} routes are mounted, but the docs say 19. Update the claim in "
        "web/components/landing/features.tsx and web/app/llms.txt/route.ts."
    )


def test_endpoints_page_documents_every_route():
    """Every mounted path appears on the public endpoint reference."""
    content = read_repo_file("web/app/docs/endpoints/page.mdx")
    documented = set(re.findall(r'path="([^"]+)"', content))

    missing = {path for _, path in mounted_routes()} - documented
    assert not missing, (
        f"undocumented on the endpoints page: {sorted(missing)}"
    )


def test_agents_file_mentions_every_route():
    """AGENTS.md is how AI assistants learn the API; it must be complete."""
    content = read_repo_file("AGENTS.md")

    missing = sorted(
        path for _, path in mounted_routes() if path not in content
    )
    assert not missing, (
        f"missing from AGENTS.md: {missing}. Agents reading it would not know "
        "these endpoints exist."
    )


@pytest.mark.parametrize(
    "name",
    ["current_user", "admin", "required", "verified_user", "roles", "all_roles"],
)
def test_public_dependencies_are_documented(name):
    """The dependencies the docs teach must exist on the instance."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    auth = FastAuth(secret_key="a" * 32, engine=engine)
    assert hasattr(auth, name), f"docs reference auth.{name} but it does not exist"
