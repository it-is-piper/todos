"""Tests comparing todos.sh (reference) vs todos.py.

Goal: prove todos.py returns empty where todos.sh returns matches,
then narrow via diagnostic tests to the specific git diff call.
"""

import subprocess


import pytest

from tests._fixture_repo import make_repo
from tests.conftest import REAL_TODOS_SH


def run_sh(repo, *args: str) -> str:
    """Run the real todos.sh in `repo` and return stdout."""
    result = subprocess.run(
        ["bash", str(REAL_TODOS_SH), *args],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    return result.stdout


def run_py(
    repo, *, base_branch: str = "main", cached: bool = False, unstaged: bool = False
):
    """Invoke Todos.files_and_lines() from inside `repo`."""
    from todos import Todos  # imported lazily so env can set cwd
    import os

    old = os.getcwd()
    try:
        os.chdir(repo)
        t = Todos(base_branch=base_branch, cached=cached, unstaged=unstaged)
        return t.files_and_lines()
    finally:
        os.chdir(old)


def _two_commit_feature():
    """2 commits on feat/x, each adds a TODO."""
    return [
        ("c.txt", "line1\n# TODO alpha\nline3\n"),
        ("d.txt", "# TODO beta\n"),
    ]


def _one_commit_feature():
    """1 commit on feat/x with a TODO."""
    return [("c.txt", "line1\n# TODO alpha\n")]


def test_todos_py_imports():
    from todos import Todos, Line, Format

    assert Todos is not None
    assert Line is not None
    assert Format is not None


def test_sh_finds_todos_on_feature_branch(tmp_path):
    repo = make_repo(
        tmp_path,
        feature_commits=_two_commit_feature(),
    )
    out = run_sh(repo, "--parent", "main")
    assert "c.txt" in out, f"sh missed c.txt:\n{out}"
    assert "d.txt" in out, f"sh missed d.txt:\n{out}"


def test_py_finds_nothing_on_feature_branch(tmp_path):
    """THE FAILING CASE: todos.py returns empty where .sh finds lines."""
    repo = make_repo(
        tmp_path,
        feature_commits=_two_commit_feature(),
    )
    paths, lines = run_py(repo, base_branch="main")
    assert paths == [] and lines == [], (
        f"Expected empty (the bug); got paths={paths!r} lines={lines!r}"
    )


def test_py_finds_todos_with_one_commit(tmp_path):
    """Isolates the 1-commit boundary. See todo comment in todos.py."""
    repo = make_repo(
        tmp_path,
        feature_commits=_one_commit_feature(),
    )
    # .sh on the same setup
    sh_out = run_sh(repo, "--parent", "main")
    assert "c.txt" in sh_out, f"sh baseline failed on 1-commit branch:\n{sh_out}"
    # .py
    paths, lines = run_py(repo, base_branch="main")
    assert paths == [] and lines == [], (
        f"Expected empty; got paths={paths!r} lines={lines!r}"
    )


def test_unstaged_finds_todo(tmp_path):
    # NOTE: docs only promise the "feature branch vs main" use case.
    # The --unstaged and --cached modes of todos.sh don't see untracked
    # files (pickaxe scans working tree, not untracked). Skipping parity
    # check for these modes; covered separately if needed.
    pytest.skip("--unstaged mode not covered (out of PLAN scope)")


def test_cached_finds_todo(tmp_path):
    pytest.skip("--cached mode not covered (out of PLAN scope)")


def test_trunk_branch_finds_nothing(tmp_path):
    # On main, cherry has no "+" commits -> _commits() returns [].
    # This is a known crash site (commits[0]^) in todos.py.
    repo = make_repo(
        tmp_path,
        feature_commits=_two_commit_feature(),
    )
    # Make sure we're on main.
    subprocess.run(["git", "checkout", "-q", "main"], cwd=repo, check=True)
    with pytest.raises(IndexError):
        run_py(repo, base_branch="main")


# ---------- diagnostic (print-only) ----------


def test_py_cherry_hashes(tmp_path, capsys):
    repo = make_repo(tmp_path, feature_commits=_two_commit_feature())
    import os

    old = os.getcwd()
    try:
        os.chdir(repo)
        from todos import Todos

        hashes = Todos(base_branch="main")._commits()
    finally:
        os.chdir(old)
    print(f"\n[diag] cherry hashes on feat/x: {hashes}")
    assert len(hashes) == 2, f"expected 2 cherry hashes, got {hashes}"


def test_py_diff_files_arg_forms(tmp_path, capsys):
    """Try multiple forms of g.diff(...) and print the file count for each."""
    repo = make_repo(tmp_path, feature_commits=_two_commit_feature())
    import os

    old = os.getcwd()
    try:
        os.chdir(repo)
        from todos import Git
        from tests._fixture_repo import _run  # type: ignore  # reuse internal helper
    finally:
        os.chdir(old)

    g = Git(repo)

    # Get cherry hashes
    cherry = g.cherry(["-v", "main"])
    added = [c for c in cherry.split("\n") if c[:2] == "+ "]
    hashes = [c.split(" ")[1] for c in added]
    left = f"{hashes[0]}^"
    right = hashes[-1]
    key = "TODO"

    forms = {
        "current '-S\"TODO\"'": ["--name-only", f'-S"{key}"', left, right],
        "split -S TODO": ["--name-only", "-S", key, left, right],
        "split -S TODO no right": ["--name-only", "-S", key, left],
        "with HEAD as right": ["--name-only", "-S", key, left, "HEAD"],
    }

    print(f"\n[diag] left={left} right={right} hashes={hashes}")
    for name, args in forms.items():
        out = g.diff(args)
        files = [l for l in out.split("\n") if l]
        print(f"[diag] {name}: {len(files)} files -> {files}")

    # Also: shell-side, for ground truth.
    shell = subprocess.run(
        ["git", "diff", "--name-only", f"-S{key}", left, right],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    print(f"[diag] shell: {shell.stdout!r}")
