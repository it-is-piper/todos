"""Tests comparing todos.sh (reference) vs todos.py.

Goal: prove todos.py returns empty where todos.sh returns matches,
then narrow via diagnostic tests to the specific git diff call.
"""

import subprocess
from pathlib import Path
import os

from tests._fixture_repo import make_repo

TODOS_SH_PATH = Path(os.getcwd(), "tools", "todos.sh")


def run_sh(repo, *args: str) -> str:
    """Run the real todos.sh in `repo` and return stdout."""
    result = subprocess.run(
        ["bash", str(TODOS_SH_PATH), *args],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    return result.stdout


def run_py(
    repo, *, base_branch: str = "main", cached: bool = False, unstaged: bool = False
):
    """Invoke Tofix.files_and_lines() from inside `repo`."""
    from tofix import Tofix  # imported lazily so env can set cwd
    import os

    old = os.getcwd()
    try:
        os.chdir(repo)
        t = Tofix(base_branch=base_branch, cached=cached, unstaged=unstaged)
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
    from tofix import Tofix, Line, Format

    assert Tofix is not None
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
    repo = make_repo(
        tmp_path,
        feature_commits=_two_commit_feature(),
    )
    paths, lines = run_py(repo, base_branch="main")
    paths_set = set(paths) | {l.path for l in lines}
    assert "c.txt" in paths_set, f"py missed c.txt; paths={paths!r} lines={lines!r}"
    assert "d.txt" in paths_set, f"py missed d.txt; paths={paths!r} lines={lines!r}"


def test_py_finds_todos_with_one_commit(tmp_path):
    repo = make_repo(
        tmp_path,
        feature_commits=_one_commit_feature(),
    )
    sh_out = run_sh(repo, "--parent", "main")
    assert "c.txt" in sh_out, f"sh baseline failed on 1-commit branch:\n{sh_out}"

    paths, lines = run_py(repo, base_branch="main")
    paths_set = set(paths) | {l.path for l in lines}
    assert "c.txt" in paths_set, (
        f"py missed c.txt on 1-commit branch; paths={paths!r} lines={lines!r}"
    )


def test_unstaged_finds_todo(tmp_path):
    # Modify the existing tracked file c.txt with a new unstaged TODO line.
    repo = make_repo(
        tmp_path,
        feature_commits=_two_commit_feature(),
    )
    # Append an unstaged TODO to a tracked file.
    with open(repo / "c.txt", "a") as f:
        f.write("\n# TODO gamma\n")

    sh_out = run_sh(repo, "--parent", "main", "--unstaged")
    # .sh should find the unstaged TODO in c.txt.
    assert "c.txt" in sh_out and "TODO gamma" in sh_out, (
        f"sh missed unstaged TODO in c.txt:\n{sh_out}"
    )

    paths, lines = run_py(repo, base_branch="main", unstaged=True)
    hit = [l for l in lines if l.path == "c.txt" and "TODO gamma" in l.text]
    assert hit, f"py missed unstaged TODO; paths={paths!r} lines={lines!r}"


def test_cached_finds_todo(tmp_path):
    """TODO staged in index but not committed."""
    repo = make_repo(
        tmp_path,
        feature_commits=_two_commit_feature(),
    )
    # Stage a new file with a TODO.
    (repo / "f.txt").write_text("# TODO delta\n")
    subprocess.run(["git", "add", "f.txt"], cwd=repo, check=True)

    sh_out = run_sh(repo, "--parent", "main", "--cached")
    assert "f.txt" in sh_out and "TODO delta" in sh_out, (
        f"sh missed cached f.txt:\n{sh_out}"
    )

    paths, lines = run_py(repo, base_branch="main", cached=True)
    hit = [l for l in lines if l.path == "f.txt" and "TODO delta" in l.text]
    assert hit, f"py missed cached TODO; paths={paths!r} lines={lines!r}"


def test_trunk_branch_finds_nothing(tmp_path):
    """On main, cherry has no '+' commits. Should return empty cleanly, not crash."""
    repo = make_repo(
        tmp_path,
        feature_commits=_two_commit_feature(),
    )
    # Make sure we're on main.
    subprocess.run(["git", "checkout", "-q", "main"], cwd=repo, check=True)
    paths, lines = run_py(repo, base_branch="main")
    assert paths == [] and lines == [], (
        f"on trunk expected empty; got paths={paths!r} lines={lines!r}"
    )


# ---------- diagnostic (print-only) ----------


def test_py_cherry_hashes(tmp_path, capsys):
    repo = make_repo(tmp_path, feature_commits=_two_commit_feature())
    import os

    old = os.getcwd()
    try:
        os.chdir(repo)
        from tofix import Tofix

        hashes = Tofix(base_branch="main")._commits()
    finally:
        os.chdir(old)
    print(f"\n[diag] cherry hashes on feat/x: {hashes}")
    assert len(hashes) == 2, f"expected 2 cherry hashes, got {hashes}"


def test_py_diff_files_arg_forms(tmp_path, capsys):
    """Try multiple forms of g.diff(...) and print the file count for each."""
    from git import Git

    repo = make_repo(tmp_path, feature_commits=_two_commit_feature())
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
