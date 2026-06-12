"""Build a hermetic git repo for tests.

Each call returns the path to a fresh temp repo with:

  trunk branch = main
  feature branch = feat/x  (off main, N commits, each adds a TODO)
  working tree: unstaged + staged TODOs
"""

import subprocess
from pathlib import Path


def _run(cwd: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )


def make_repo(
    parent: Path,
    *,
    feature_commits: list[tuple[str, str]] | None = None,
    unstaged_files: dict[str, str] | None = None,
    staged_files: dict[str, str] | None = None,
    feature_branch: str = "feat/x",
    trunk_branch: str = "main",
) -> Path:
    """Create a fresh repo under `parent/repo/`. Return its root path.

    Args:
        parent: directory to hold the new repo (e.g. pytest's tmp_path).
                A `repo/` subdirectory is created inside.
        feature_commits: list of (filename, contents) for commits on the feature branch.
                         Each is a single commit. Contents may include "TODO".
        unstaged_files: {filename: contents} written to working tree, NOT git-added.
        staged_files: {filename: contents} git-added (cached) but not committed.
    """
    parent.mkdir(parents=True, exist_ok=True)
    repo = parent / "repo"
    repo.mkdir()

    env = {
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@test.local",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@test.local",
        "PATH": "/usr/bin:/bin:/usr/local/bin",
    }
    # Preserve HOME for global config; allow caller override if needed.
    import os
    env.update({k: v for k, v in os.environ.items() if k not in env})

    _run(repo, "init", "-q", env=env)
    _run(repo, "checkout", "-q", "-b", trunk_branch, env=env)
    _run(repo, "config", "user.email", "test@test.local", env=env)
    _run(repo, "config", "user.name", "Test", env=env)

    # Trunk seed commits (no TODOs).
    (repo / "a.txt").write_text("a\n")
    _run(repo, "add", "a.txt", env=env)
    _run(repo, "commit", "-q", "-m", "init a", env=env)

    (repo / "b.txt").write_text("b\n")
    _run(repo, "add", "b.txt", env=env)
    _run(repo, "commit", "-q", "-m", "add b", env=env)

    # Feature branch.
    _run(repo, "checkout", "-q", "-b", feature_branch, env=env)
    for filename, contents in (feature_commits or []):
        (repo / filename).write_text(contents)
        _run(repo, "add", filename, env=env)
        _run(repo, "commit", "-q", "-m", f"add {filename}", env=env)

    # Staged (cached) files.
    for filename, contents in (staged_files or {}).items():
        (repo / filename).write_text(contents)
        _run(repo, "add", filename, env=env)

    # Unstaged files.
    for filename, contents in (unstaged_files or {}).items():
        (repo / filename).write_text(contents)

    return repo
