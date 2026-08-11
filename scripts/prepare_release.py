#!/usr/bin/env python3
"""Prepare a release: bump every version location and roll the changelog.

    python scripts/prepare_release.py patch     # 0.7.0 -> 0.7.1
    python scripts/prepare_release.py minor     # 0.7.0 -> 0.8.0
    python scripts/prepare_release.py major     # 0.7.0 -> 1.0.0
    python scripts/prepare_release.py 1.2.3     # explicit
    python scripts/prepare_release.py minor --dry-run

Rolls '## [Unreleased]' into '## [X.Y.Z] - <today>' and opens a fresh
Unreleased section, so the notes you wrote as you worked become the release
notes. Refuses to run if Unreleased is empty, because a release with no notes
is the thing this exists to prevent.

Does not commit, tag, or push. It prints the commands so you stay in control.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _release_meta import ROOT, REPO_URL, VERSION_SITES  # noqa: E402


def current_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not match:
        sys.exit("Could not read version from pyproject.toml")
    return match.group(1)


def infer_bump(changelog: str) -> tuple[str, str]:
    """Work out the bump from what the Unreleased section actually says.

    The changelog already records whether something was removed, added or
    fixed, so it can answer "which number moves" without anyone deciding.

    Returns (bump, reason).
    """
    body = unreleased_body(changelog)
    headings = set(re.findall(r"^### (\w+)", body, re.MULTILINE))
    breaking = bool(re.search(r"\bBREAKING\b", body))

    if breaking:
        return "major", "the notes are marked BREAKING"
    if "Removed" in headings:
        return "major", "something was removed, which breaks callers using it"
    if headings & {"Added", "Changed", "Deprecated"}:
        why = ", ".join(sorted(headings & {"Added", "Changed", "Deprecated"}))
        return "minor", f"new or changed behaviour ({why}) with nothing removed"
    if headings & {"Fixed", "Security"}:
        return "patch", "fixes only"
    sys.exit(
        "Cannot infer the bump: the Unreleased section has no recognised\n"
        "### heading. Use Added / Changed / Deprecated / Removed / Fixed /\n"
        "Security, or pass the bump explicitly."
    )


def next_version(current: str, spec: str) -> str:
    if re.fullmatch(r"\d+\.\d+\.\d+", spec):
        return spec
    parts = current.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        sys.exit(f"Cannot bump non-numeric version {current!r}; pass an explicit version")
    major, minor, patch = (int(p) for p in parts)

    # Pre-1.0, a breaking change bumps the minor rather than declaring 1.0.
    # Reaching 1.0 is a deliberate statement about stability, never a side
    # effect of removing something.
    if spec == "major" and major == 0:
        print("  note: pre-1.0, so a breaking change bumps the minor, not to 1.0.0")
        print("        pass an explicit 1.0.0 when you mean to declare stability.")
        spec = "minor"

    if spec == "major":
        return f"{major + 1}.0.0"
    if spec == "minor":
        return f"{major}.{minor + 1}.0"
    if spec == "patch":
        return f"{major}.{minor}.{patch + 1}"
    sys.exit(f"Unknown bump {spec!r}: use major, minor, patch, auto, or an explicit X.Y.Z")


def unreleased_body(changelog: str) -> str:
    match = re.search(
        r"^## \[Unreleased\]\s*\n(.*?)(?=^## \[)", changelog, re.MULTILINE | re.DOTALL
    )
    return match.group(1).strip() if match else ""


def roll_changelog(version: str, today: str, dry_run: bool) -> None:
    path = ROOT / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")

    if not re.search(r"^## \[Unreleased\]", text, re.MULTILINE):
        sys.exit("CHANGELOG.md has no '## [Unreleased]' section to roll")

    body = unreleased_body(text)
    if not body:
        sys.exit(
            "CHANGELOG.md '## [Unreleased]' is empty.\n"
            "Write what changed there first — those notes become the release notes."
        )

    new = text.replace(
        "## [Unreleased]",
        f"## [Unreleased]\n\n## [{version}] - {today}",
        1,
    )

    # Keep the compare links at the bottom pointing somewhere sensible.
    previous = current_version()
    repo = REPO_URL
    new = re.sub(
        r"^\[Unreleased\]:.*$",
        f"[Unreleased]: {repo}/compare/v{version}...HEAD\n"
        f"[{version}]: {repo}/compare/v{previous}...v{version}",
        new,
        count=1,
        flags=re.MULTILINE,
    )

    print(f"  CHANGELOG.md: [Unreleased] -> [{version}] - {today}")
    print(f"    {len(body.splitlines())} lines of notes carried over")
    if not dry_run:
        path.write_text(new, encoding="utf-8")


def bump_versions(old: str, new: str, dry_run: bool) -> None:
    for rel, pattern in VERSION_SITES:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")
        updated, count = re.subn(
            pattern, lambda m: f"{m.group(1)}{new}{m.group(3)}", text, flags=re.MULTILINE
        )
        if count == 0:
            sys.exit(f"{rel}: no version found to bump")
        print(f"  {rel}: {old} -> {new}")
        if not dry_run:
            path.write_text(updated, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "bump",
        nargs="?",
        default="auto",
        help="auto (default), major, minor, patch, or an explicit X.Y.Z",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show changes, write nothing")
    parser.add_argument(
        "--print-version",
        action="store_true",
        help="Print only the resulting version and exit, for scripts and CI",
    )
    args = parser.parse_args()

    old = current_version()
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    spec, reason = args.bump, None
    if spec == "auto":
        spec, reason = infer_bump(changelog)

    if args.print_version:
        print(next_version(old, spec))
        return 0

    new = next_version(old, spec)
    today = dt.date.today().isoformat()

    if new == old:
        sys.exit(f"Version is already {new}")

    print(f"Preparing {old} -> {new}")
    if reason:
        print(f"  {spec} bump inferred: {reason}")
    print()
    roll_changelog(new, today, args.dry_run)
    bump_versions(old, new, args.dry_run)

    if args.dry_run:
        print("\nDry run, nothing written.")
        return 0

    print("\nVerifying...")
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_release.py"), "--changelog"],
        cwd=ROOT,
    )
    if result.returncode != 0:
        return result.returncode

    print(
        f"""
Ready. Review the diff, then:

    uv run pytest -q
    git add -A && git commit -m "v{new}: <summary>"
    git push origin main
    git tag -a v{new} -m "v{new}"
    git push origin v{new}      # this triggers the release

CI then tests, builds, publishes to PyPI, and creates the GitHub release
using the CHANGELOG section above.
"""
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
