# Test Plan: todos.sh vs todos.py parity

## Goal

Prove `todos.py` finds nothing where `todos.sh` finds something, on the same repo state.
Then narrow the failure to a specific call (`git cherry`, `git diff -S`, `git diff -U`).

## Environment

- pytest
- `GitPython` (already imported by `todos.py`)
- `git` CLI on PATH
- Run from a temp worktree per test (no mutation of `/Users/piper/src/todos`).

## Repo fixtures

Build tiny throwaway repos via a pytest fixture. Avoid depending on `/Users/piper/src/todos`
history — keep fixtures hermetic.

Fixture builds a repo with this shape:

```
trunk = main
feature branch = feat/x  (off main, 2 commits, each adds a TODO)
unstaged change in working tree = 1 file with a new TODO
staged change (cached) = 1 file with a new TODO
```

Concrete seed (script in `tests/_fixture_repo.py`):

1. `git init tmp`, `git checkout -b main`.
2. Commit a clean `a.txt` (no TODO).
3. Commit `b.txt` (no TODO).
4. `git checkout -b feat/x`.
5. Commit `c.txt` with `# TODO alpha`.
6. Commit `d.txt` with `# TODO beta`.
7. Leave working tree dirty with `# TODO gamma` in `e.txt` (unstaged).
8. `git add f.txt` containing `# TODO delta` (staged only).

## Test cases

`tests/test_todos.py` — pytest functions. No unittest classes. Use
`tmp_path: Path` and a `make_repo` helper.

### 1. `test_todos_py_imports`

Sanity: `from todos import Todos, Line, Format`. Skip on ImportError with a clear msg.

### 2. `test_sh_finds_todos_on_feature_branch`

Run `bash todos.sh --parent main` from the fixture repo on `feat/x` (relative
path adjusted to point at the real `todos.sh` via copy or by running inside
`/Users/piper/src/todos`'s own copy of the script — see helper note below).

Assert stdout contains lines referencing `c.txt` and `d.txt`. Baseline: proves
the harness and the .sh script both behave as expected before comparing to .py.

### 3. `test_py_finds_nothing_on_feature_branch` ← the failing case

In same fixture, switch to `feat/x`, run `Todos(base_branch="main").files_and_lines()`.

Assert result is empty (or at minimum: assert `len(lines) == 0`).

**This is the bug.** Expected: same lines as test 2. Actual: empty list.

### 4. `test_py_finds_todos_on_single_commit_branch`

New fixture: feature branch with exactly **1** commit that adds a TODO.
This isolates the `_commits()[0]^` boundary. If `.sh` works here and `.py`
still finds nothing, the bug is in `git.diff(...)` args, not the cherry
selection. The inline comment in `todos.py` line ~95 already suspects this:
`# TODO For some reason this returns an empty change set when left is 1 commit before right`.

### 5. `test_py_finds_todos_with_two_commits`

Same as test 3 but explicitly 2 commits. Confirms whether the 1-vs-many
commit count matters.

### 6. `test_unstaged_finds_todo`

`Todos(unstaged=True).files_and_lines()`. Should pick up `e.txt` `# TODO gamma`.
Run for both `.sh` and `.py` and compare.

### 7. `test_cached_finds_todo`

`Todos(cached=True).files_and_lines()`. Should pick up `f.txt` `# TODO delta`.
Compare both impls.

### 8. `test_trunk_branch_finds_nothing`

On `main`, both impls must return empty (no diff vs `main`).

## Diagnostic sub-tests (no assertions, just prints)

After the failing case is identified, add focused tests that print intermediates
so we can see *where* the divergence happens:

### 9. `test_py_cherry_hashes`

`Todos(base_branch="main")._commits()` → print. Should be 2 hashes on `feat/x`.
Confirms cherry step works.

### 10. `test_py_diff_files_arg_forms`

Try multiple forms of `g.diff(...)` args and print output for each:
- current form: `["--name-only", '-S"TODO"', left, right]`
- split: `["--name-only", "-S", "TODO", left, right]`
- with `right=None` omitted vs `right=""` vs `right="HEAD"`

This is the prime suspect — the `-S"TODO"` quoting is non-portable through
GitPython's arg parser, and shell-side it works because the shell strips quotes.

## Helper: run shell script in a foreign cwd

The .sh script uses `git rev-parse --show-toplevel`. We must run it from inside
the temp repo. Use `subprocess.run(["bash", REAL_TODOS_SH, "--parent", "main"],
cwd=tmp_repo, capture_output=True, text=True)`.

`REAL_TODOS_SH` resolves to `/Users/piper/src/todos/todos.sh` (importable via
`conftest.py` reading `__file__` of `test_todos.py` and going up two dirs).

## File layout

```
/Users/piper/src/todos/
  tests/
    __init__.py
    conftest.py        # fixtures, paths
    _fixture_repo.py   # make_repo helper
    test_todos.py      # the 10 tests above
  PLAN.md              # this file
```

## Pass criteria

- All tests run without error.
- Tests 2, 4, 5, 6, 7, 8 pass for `.sh`.
- Test 3 fails for `.py` (this is the demonstrated bug).
- Test 10's prints show which arg form makes `.py` succeed → that is the fix.

## Out of scope

- Fixing `todos.py`. Plan only tests and localizes.
- `--format json` parity. Focus on `files_and_lines()` first.
- Performance. No benchmark tests.
