#!/usr/bin/env python3
"""Verify everything a release depends on is consistent.

Run it locally before tagging, and CI runs it on every push and before every
publish. Stdlib only, so it needs no install.

    python scripts/check_release.py              # check the working tree
    python scripts/check_release.py --tag v0.8.0 # also require the tag to match
    python scripts/check_release.py --changelog  # also require changelog notes
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Every place a version is written, and how to find it there. Adding a new
# location here is all it takes for CI to start guarding it.
VERSION_SITES = [
    ("pyproject.toml", r'^version\s*=\s*"([^"]+)"', "version = \"X.Y.Z\""),
    ("fastauth/__init__.py", r'^__version__\s*=\s*"([^"]+)"', '__version__ = "X.Y.Z"'),
    ("web/lib/site.ts", r'^\s*version:\s*"([^"]+)"', 'version: "X.Y.Z"'),
    ("README.md", r"fastauth-iq\.svg\?v=([0-9][^\"\s)]*)", "badge ?v=X.Y.Z"),
]

CANONICAL_DOMAIN = "fastauth.pythowner.com"
STALE_DOMAINS = ["fastauth.vercel.app", "hu55ain3laa.github.io/fastauth"]

problems: list[str] = []


def fail(message: str) -> None:
    problems.append(message)


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def found_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for rel, pattern, shape in VERSION_SITES:
        text = read(rel)
        match = re.search(pattern, text, re.MULTILINE)
        if not match:
            fail(f"{rel}: no version found (expected {shape})")
            continue
        versions[rel] = match.group(1)
    return versions


def check_versions_agree(versions: dict[str, str]) -> str | None:
    if not versions:
        return None
    distinct = set(versions.values())
    if len(distinct) > 1:
        detail = "\n".join(f"    {rel}: {v}" for rel, v in versions.items())
        fail(f"version mismatch across files:\n{detail}")
        return None
    return next(iter(distinct))


def check_changelog(version: str, required: bool) -> None:
    text = read("CHANGELOG.md")
    # Must match what publish.yml's awk looks for.
    if not re.search(rf"^## \[{re.escape(version)}\]", text, re.MULTILINE):
        message = (
            f"CHANGELOG.md has no '## [{version}]' section. "
            "The release would fall back to a bare commit list."
        )
        if required:
            fail(message)
        else:
            print(f"  note: {message}")
        return

    body = re.split(rf"^## \[{re.escape(version)}\]", text, flags=re.MULTILINE)[1]
    body = re.split(r"^## \[", body, flags=re.MULTILINE)[0]
    if not body.strip().splitlines()[1:]:
        fail(f"CHANGELOG.md section for {version} is empty")


def check_domains() -> None:
    skip = {".git", "node_modules", ".next", ".venv", "dist", "build", "__pycache__"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in {".md", ".ts", ".tsx", ".toml", ".mdx"}:
            continue
        if any(part in skip for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for stale in STALE_DOMAINS:
            if stale in text:
                rel = path.relative_to(ROOT)
                fail(f"{rel}: stale domain '{stale}' (canonical is {CANONICAL_DOMAIN})")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", help="Require this git tag to match the version, e.g. v0.8.0")
    parser.add_argument(
        "--changelog",
        action="store_true",
        help="Fail if the changelog has no section for this version",
    )
    args = parser.parse_args()

    versions = found_versions()
    version = check_versions_agree(versions)

    if version:
        print(f"  version {version} consistent across {len(versions)} files")
        check_changelog(version, required=args.changelog)

        if args.tag:
            tagged = args.tag.lstrip("v")
            if tagged != version:
                fail(f"tag {args.tag} does not match project version {version}")
            else:
                print(f"  tag {args.tag} matches")

    check_domains()

    if problems:
        print("\nRelease checks failed:\n", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    print("  no stale domains")
    print("\nAll release checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
