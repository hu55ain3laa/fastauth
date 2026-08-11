"""Shared facts about where release metadata lives.

Both check_release.py and prepare_release.py import this, so there is exactly
one list of places the version is written. Adding a new location here teaches
the checker and the bumper at once.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (path, regex). Group 1 is the prefix, group 2 the version, group 3 the
# suffix — so the same pattern can both find a version and rewrite it.
VERSION_SITES: list[tuple[str, str]] = [
    ("pyproject.toml", r'(^version\s*=\s*")([^"]+)(")'),
    ("fastauth/__init__.py", r'(^__version__\s*=\s*")([^"]+)(")'),
    ("web/lib/site.ts", r'(^\s*version:\s*")([^"]+)(")'),
    ("README.md", r"(fastauth-iq\.svg\?v=)([0-9][^\"\s)]*)()"),
]

CANONICAL_DOMAIN = "fastauth.pythowner.com"

# Domains that used to be correct. Any of these left in the tree is a stale
# link pointing somewhere dead.
STALE_DOMAINS = [
    "fastauth.vercel.app",
    "hu55ain3laa.github.io/fastauth",
]

REPO_URL = "https://github.com/hu55ain3laa/fastauth"
