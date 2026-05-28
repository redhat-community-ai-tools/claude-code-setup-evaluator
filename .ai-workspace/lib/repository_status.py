#!/usr/bin/env python3
"""Repository status reporting for session-start hooks.

Gathers read-only git status for each submodule (and optionally the workspace
root) and injects it into the session context so agents can make informed
decisions about branch switching, pulling, etc.
"""

from __future__ import annotations

import configparser
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from config import load_config

if TYPE_CHECKING:
    from session_context import SessionContext


def _git(args: list[str], cwd: Path) -> str | None:
    """Run a git command and return stripped stdout, or None on failure."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def _get_current_branch(repo_path: Path) -> str:
    """Get current branch name, or 'detached @ <sha>' for detached HEAD."""
    branch = _git(["rev-parse", "--abbrev-ref", "HEAD"], repo_path)
    if branch and branch != "HEAD":
        return branch

    # Detached HEAD — get short SHA
    sha = _git(["rev-parse", "--short", "HEAD"], repo_path)
    return f"detached @ {sha}" if sha else "unknown"


def _has_uncommitted_changes(repo_path: Path) -> bool:
    """Check for uncommitted changes (staged + unstaged + untracked)."""
    status = _git(["status", "--porcelain"], repo_path)
    return bool(status)


def _get_behind_count(repo_path: Path) -> str:
    """Get number of commits behind the remote tracking branch.

    Runs git fetch first for accurate results. Returns "unknown" if
    offline, no tracking branch, or fetch fails.
    """
    # Fetch from remote (fail gracefully if offline)
    _git(["fetch", "--quiet"], repo_path)

    # Get tracking branch
    upstream = _git(["rev-parse", "--abbrev-ref", "@{u}"], repo_path)
    if not upstream:
        return "unknown"

    # Count commits behind
    behind = _git(["rev-list", "--count", "HEAD..@{u}"], repo_path)
    return behind if behind is not None else "unknown"


_FALLBACK_DEFAULT_BRANCH = "main"


def _detect_default_branch(repo_path: Path) -> str | None:
    """Auto-detect default branch from git remote HEAD ref.

    Returns the branch name if refs/remotes/origin/HEAD exists, else None.
    """
    ref = _git(["symbolic-ref", "refs/remotes/origin/HEAD"], repo_path)
    if ref:
        # ref is like "refs/remotes/origin/main" -> extract "main"
        return ref.split("/")[-1]
    return None


def _guess_default_branch(repo_path: Path) -> str | None:
    """Heuristic: check if common default branch names exist as remote refs."""
    for candidate in ("main", "master"):
        result = _git(
            ["show-ref", "--verify", "--quiet", f"refs/remotes/origin/{candidate}"],
            repo_path,
        )
        if result is not None:  # exit code 0
            return candidate
    return None


def _get_default_branch(
    submodule_path: str,
    repo_path: Path,
    gitmodules: configparser.ConfigParser,
) -> str:
    """Determine default branch for a repository.

    Waterfall detection:
    1. git symbolic-ref refs/remotes/origin/HEAD (accurate when present)
    2. .gitmodules per-submodule 'branch' field (explicit per-repo config)
    3. Heuristic: check if origin/main or origin/master exists locally
    4. Hardcoded "main" fallback (with warning)
    """
    # 1. Auto-detect from remote HEAD ref
    detected = _detect_default_branch(repo_path)
    if detected:
        return detected

    # 2. Check .gitmodules branch field
    section = f'submodule "{submodule_path}"'
    if gitmodules.has_section(section):
        branch = gitmodules.get(section, "branch", fallback=None)
        if branch:
            return branch

    # 3. Heuristic: check common branch names
    guessed = _guess_default_branch(repo_path)
    if guessed:
        return guessed

    # 4. Fallback with warning
    print(
        f'  ⚠ Could not detect default branch for "{submodule_path}", '
        f'assuming "{_FALLBACK_DEFAULT_BRANCH}".\n'
        f'    Set "branch" in .gitmodules if this is incorrect.',
        file=sys.stderr,
    )
    return _FALLBACK_DEFAULT_BRANCH


def _parse_gitmodules(repo_root: Path) -> configparser.ConfigParser:
    """Parse .gitmodules file, returning empty parser if missing."""
    parser = configparser.ConfigParser()
    gitmodules_path = repo_root / ".gitmodules"
    if gitmodules_path.exists():
        parser.read(str(gitmodules_path), encoding="utf-8")
    return parser


def _get_submodule_paths(repo_root: Path) -> list[str]:
    """Get list of registered submodule paths."""
    output = _git(
        ["config", "--file", ".gitmodules", "--get-regexp", r"^submodule\..*\.path$"],
        repo_root,
    )
    if not output:
        return []

    paths = []
    for line in output.splitlines():
        # Format: submodule.<name>.path <value>
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            paths.append(parts[1])
    return sorted(paths)


def _build_repo_xml(path: str, repo_path: Path, default_branch: str) -> str:
    """Build a single <repo .../> XML element for a repository."""
    branch = _get_current_branch(repo_path)
    uncommitted = "true" if _has_uncommitted_changes(repo_path) else "false"
    behind = _get_behind_count(repo_path)

    attrs = [
        f'path="{path}"',
        f'branch="{branch}"',
        f'default-branch="{default_branch}"',
        f'uncommitted-changes="{uncommitted}"',
        f'behind="{behind}"',
    ]
    return f"<repo {' '.join(attrs)} />"


def _scan_repo_clones(repo_root: Path) -> list[dict[str, str]]:
    """Scan repositories/ for cloned git repos (not submodules)."""
    repos_dir = repo_root / "repositories"
    if not repos_dir.exists():
        return []

    repos = []
    for item in sorted(repos_dir.iterdir()):
        if not item.is_dir() or item.name.startswith("."):
            continue
        if not (item / ".git").exists():
            continue

        branch = _get_current_branch(item)
        uncommitted = _has_uncommitted_changes(item)
        uncommitted_count = ""
        if uncommitted:
            status = _git(["status", "--porcelain"], item)
            uncommitted_count = str(len(status.splitlines())) if status else "0"

        repos.append(
            {
                "name": item.name,
                "path": f"repositories/{item.name}",
                "branch": branch,
                "uncommitted": "true" if uncommitted else "false",
                "uncommitted_count": uncommitted_count,
            }
        )

    return repos


def run_repository_status(ctx: SessionContext, repo_root: Path) -> None:
    """Gather repository status and add to session context.

    Checks submodules, cloned repos in repositories/, and optionally
    the workspace root. Produces nothing if no repositories are found.
    """
    config = load_config(repo_root / "ai-workspace.toml")
    gitmodules = _parse_gitmodules(repo_root)

    repos: list[str] = []

    # Optionally include workspace root
    if config.repositories.include_workspace_root:
        root_default = _detect_default_branch(repo_root)
        if not root_default:
            root_default = _guess_default_branch(repo_root)
        if not root_default:
            root_default = _FALLBACK_DEFAULT_BRANCH
        repos.append(_build_repo_xml(".", repo_root, root_default))

    # Process submodules
    submodule_paths = _get_submodule_paths(repo_root)
    for sub_path in submodule_paths:
        full_path = repo_root / sub_path
        if not full_path.exists() or not (full_path / ".git").exists():
            continue

        default_branch = _get_default_branch(sub_path, full_path, gitmodules)
        repos.append(_build_repo_xml(sub_path, full_path, default_branch))

    # Process cloned repos in repositories/
    clones = _scan_repo_clones(repo_root)
    for clone in clones:
        # Skip if already reported as a submodule
        if any(clone["path"] in r for r in repos):
            continue
        default_branch = _detect_default_branch(repo_root / clone["path"])
        if not default_branch:
            default_branch = _guess_default_branch(repo_root / clone["path"])
        if not default_branch:
            default_branch = _FALLBACK_DEFAULT_BRANCH
        repos.append(_build_repo_xml(clone["path"], repo_root / clone["path"], default_branch))

    if repos:
        content = "<repository-status>\n" + "\n".join(repos) + "\n</repository-status>"
        ctx.add_section("repository-status", content)

    # Build available-repositories section for repo focus prompt
    if clones:
        lines = ["<available-repositories>"]
        for i, clone in enumerate(clones, 1):
            status_hint = clone["branch"]
            if clone["uncommitted"] == "true":
                status_hint += f", {clone['uncommitted_count']} uncommitted"
            else:
                status_hint += ", clean"
            lines.append(f'<repo index="{i}" name="{clone["name"]}" path="{clone["path"]}" status="{status_hint}" />')
        lines.append("</available-repositories>")
        ctx.add_section("available-repositories", "\n".join(lines))
